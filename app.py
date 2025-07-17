from datetime import datetime, timedelta, timezone
from functools import wraps
import os
from pathlib import Path
import random
import re
import secrets
import shutil
import time

from rfeed import Feed, Guid, Item
from flask import Flask, render_template, session
from flask import request, redirect, url_for, jsonify
import yaml

from auth import verify_admin_password
from utils import (
    CONTENT_TYPES,
    ContentType,
    PageMetadata,
    calculate_reading_time,
    get_content_listing,
    load_config,
    load_markdown_file,
    md,
)

# Load configuration
config = load_config()
app = Flask(__name__,
           template_folder=config['paths']['templates'],
           static_folder=config['paths']['static'])

app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))


def get_navigation_items():
    """Get sorted list of pages that should appear in navigation"""
    pages_dir = config['paths']['pages']
    nav_items = []

    if not os.path.exists(pages_dir):
        return nav_items

    for filename in os.listdir(pages_dir):
        if filename.endswith('.md'):
            metadata, _ = load_markdown_file(os.path.join(pages_dir, filename))

            if isinstance(metadata, PageMetadata) and metadata.show_in_nav:
                item = {
                    'slug': '-'.join(filename.split('.')[:-1]),
                    'title': metadata.title,
                    'description': metadata.description,
                    'order': metadata.nav_order,
                    'icon': metadata.nav_icon,
                }
                nav_items.append(item)

    # Sort by nav_order
    nav_items.sort(key=lambda x: x['order'])
    return nav_items


app.jinja_env.globals.update(
    now=datetime.now,
    get_navigation=get_navigation_items,
)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        # Check if session has expired
        if 'auth_time' in session:
            auth_time = datetime.fromisoformat(session['auth_time'])
            if datetime.now() - auth_time > timedelta(hours=config['admin']['session_duration']):
                session.clear()
                return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


def get_content_items(content_type: ContentType):
    directory = os.path.join(config['paths'][content_type.name])
    items = []
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            path = os.path.join(directory, filename)
            metadata, content = load_markdown_file(path)
            if metadata:
                items.append((metadata, content))
    return sorted(items, key=lambda x: getattr(x[0], content_type.sort_key, ""), reverse=content_type.reverse)



# Routes
@app.route('/')
def index():
    # Get most recent posts
    posts = []
    posts_dir = config['paths']['posts']
    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            metadata, content = load_markdown_file(os.path.join(posts_dir, filename))
            if hasattr(metadata, 'date'):
                posts.append({
                    'slug': filename[:-3],
                    'metadata': metadata,
                    'summary': content[:config['content']['summary_length']] + '...'
                    if len(content) > config['content']['summary_length'] else content
                })

    # Sort posts by date
    posts.sort(key=lambda x: x['metadata'].date, reverse=True)
    return render_template(
        'index.html',
        posts=posts[:config['content']['posts_per_page']],
        n_posts=len(posts),
    )


@app.route('/api/posts')
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = config['content']['posts_per_page']

    # Get all posts
    posts = []
    posts_dir = config['paths']['posts']

    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            metadata, content = load_markdown_file(os.path.join(posts_dir, filename))
            if hasattr(metadata, 'date'):
                post_data = {
                    'slug': filename[:-3],
                    'title': metadata.title,
                    'date': metadata.date.isoformat(),
                    'description': getattr(metadata, 'description', ''),
                }

                # Add summary if no description
                if not post_data['description']:
                    post_data['summary'] = content[:config['content']['summary_length']] + '...' \
                        if len(content) > config['content']['summary_length'] else content

                posts.append(post_data)

    # Sort posts by date
    posts.sort(key=lambda x: x['date'], reverse=True)

    # Calculate pagination
    total_posts = len(posts)
    total_pages = (total_posts + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page

    current_posts = posts[start:end]

    # Debug logging
    app.logger.debug(f"Page: {page}, Total: {total_posts}, Per page: {per_page}")
    app.logger.debug(f"Returning {len(current_posts)} posts")

    return jsonify({
        'posts': current_posts,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    })

@app.route('/<page>')
def page(page):
    metadata, content = load_markdown_file(os.path.join(config['paths']['pages'], f"{page}.md"))
    if content is None:
        return "Page not found", 404

    # Pass metadata as the page variable that the template expects
    return render_template('page.html', content=content, page=metadata)


@app.route('/posts/<slug>')
def post(slug):
    filepath = os.path.join(config['paths']['posts'], f"{slug}.md")
    metadata, content = load_markdown_file(filepath)
    if content is None:
        return "Post not found", 404

    # Calculate reading time
    reading_time = calculate_reading_time(content)

    # Add reading_time to metadata if it's an object that allows it,
    # otherwise pass it separately
    if hasattr(metadata, '__dict__'):
        metadata.reading_time = reading_time

    return render_template(
        'post.html',
        post=metadata,
        content=content,
    )

@app.route('/projects/<slug>')
def project(slug):
    filepath = os.path.join(config['paths']['projects'], f"{slug}.md")
    metadata, content = load_markdown_file(filepath)
    if content is None:
        return "Post not found", 404

    return render_template(
        'project.html',
        project=metadata,
        content=content
    )

@app.route('/projects')
def projects():
    projects_dir = config['paths']['projects']
    if not os.path.exists(projects_dir):
        return render_template('projects.html', projects=[])

    # Use the existing get_content_listing function
    project_files = get_content_listing(projects_dir)

    # Add summaries to the projects
    for project in project_files:
        _, content = load_markdown_file(os.path.join(projects_dir, f"{project['slug']}.md"))
        project['summary'] = content[:config['content']['summary_length']] + '...' \
            if content and len(content) > config['content']['summary_length'] else content

    # Sort projects by date_started (newest first)
    project_files.sort(
        key=lambda x: getattr(x['metadata'], 'date_started', datetime.now()),
        reverse=True
    )

    return render_template('projects.html', projects=project_files)

# Admin routes
@app.route('/admin', methods=['GET'])
@requires_auth
def admin():
    return render_template('admin/dashboard.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')

        if verify_admin_password(password):
            session['authenticated'] = True
            session['auth_time'] = datetime.now().isoformat()

            # Generate CSRF token for admin session
            session['csrf_token'] = secrets.token_hex(32)

            return redirect(url_for('admin'))

        # Add small delay to prevent timing attacks
        time.sleep(random.uniform(0.1, 0.3))
        return "Invalid password", 401

    return render_template('admin/login.html')


@app.route('/rss.xml')
def rss():
    # Get all posts
    posts = []
    posts_dir = config['paths']['posts']

    site_url = config.get('site', {}).get('url', request.url_root.rstrip('/'))

    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            metadata, content = load_markdown_file(os.path.join(posts_dir, filename))
            if hasattr(metadata, 'date'):
                # Convert content to HTML if it's not already
                if not content.startswith('<'):
                    md.reset()
                    content = md.convert(content)

                # Create post item
                posts.append(Item(
                    title=metadata.title,
                    link=f"{site_url}/posts/{filename[:-3]}",
                    description=getattr(metadata, 'description', '') or content[:config['content']['summary_length']],
                    author=getattr(metadata, 'author', config.get('site', {}).get('author', '')),
                    guid=Guid(f"{site_url}/posts/{filename[:-3]}"),
                    pubDate=datetime.combine(metadata.date, datetime.min.time()).replace(tzinfo=timezone.utc)
                ))

    # Sort posts by date
    posts.sort(key=lambda x: x.pubDate, reverse=True)

    # Create the feed
    feed = Feed(
        title=config.get('site', {}).get('title', 'Blog'),
        link=site_url,
        description=config.get('site', {}).get('description', 'Recent blog posts'),
        language=config.get('site', {}).get('language', 'en-US'),
        lastBuildDate=datetime.now(timezone.utc),
        items=posts
    )

    return feed.rss(), 200, {'Content-Type': 'application/rss+xml; charset=utf-8'}


@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/content/<content_type>', methods=['GET'])
@requires_auth
def list_content(content_type):
    if content_type not in config['paths']:
        return jsonify({'error': 'Invalid content type'}), 400

    content_dir = Path(config['paths'][content_type])
    files = []

    for file in content_dir.glob('*.md'):
        metadata, _ = load_markdown_file(str(file))
        files.append({
            'slug': file.stem,
            'filename': file.name,
            'metadata': metadata or {},
            'last_modified': file.stat().st_mtime
        })

    return jsonify(files)


@app.route('/api/content/<content_type>/<slug>', methods=['GET'])
@requires_auth
def get_content(content_type, slug):
    if content_type not in config['paths']:
        return jsonify({'error': 'Invalid content type'}), 400

    file_path = Path(config['paths'][content_type]) / f"{slug}.md"
    if not file_path.exists():
        return jsonify({'error': 'Content not found'}), 404

    metadata, content = load_markdown_file(str(file_path))
    with open(file_path, 'r') as f:
        raw_content = f.read()

    return jsonify({
        'slug': slug,
        'raw_content': raw_content,
        'metadata': metadata,
        'html_content': content
    })


@app.route('/api/content/<content_type>/<slug>', methods=['POST'])
@requires_auth
def save_content(content_type, slug):
    if content_type not in config['paths']:
        return jsonify({'error': 'Invalid content type'}), 400

    content = request.json.get('content')
    if not content:
        return jsonify({'error': 'No content provided'}), 400

    # Sanitize slug
    safe_slug = re.sub(r'[^a-z0-9-]', '', slug.lower())
    file_path = Path(config['paths'][content_type]) / f"{safe_slug}.md"

    # Create backup if file exists
    if file_path.exists():
        backup_path = file_path.with_suffix('.md.bak')
        shutil.copy2(file_path, backup_path)

    try:
        file_path.write_text(content)
        return jsonify({'success': True, 'slug': safe_slug})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/content/<content_type>/<slug>', methods=['DELETE'])
@requires_auth
def delete_content(content_type, slug):
    if content_type not in config['paths']:
        return jsonify({'error': 'Invalid content type'}), 400

    file_path = Path(config['paths'][content_type]) / f"{slug}.md"
    if not file_path.exists():
        return jsonify({'error': 'Content not found'}), 404

    try:
        # Create backup before deletion
        backup_path = file_path.with_suffix('.md.bak')
        shutil.copy2(file_path, backup_path)
        file_path.unlink()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/validate-content', methods=['POST'])
@requires_auth
def validate_content():
    content = request.json.get('content')
    if not content:
        return jsonify({'error': 'No content provided'}), 400

    try:
        # Split content into frontmatter and markdown
        parts = content.split('---\n')
        if len(parts) < 3:
            return jsonify({'error': 'Invalid frontmatter format'}), 400

        # Validate YAML frontmatter
        metadata = yaml.safe_load(parts[1])

        # Validate required fields based on content type
        content_type = request.json.get('content_type')
        if content_type == 'posts':
            required_fields = ['title', 'date', 'description']
        elif content_type == 'projects':
            required_fields = ['title', 'description', 'tags']
        else:  # pages
            required_fields = ['title']

        missing_fields = [field for field in required_fields if field not in metadata]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Validate markdown content
        md.reset()
        html_content = md.convert('\n'.join(parts[2:]))

        return jsonify({
            'valid': True,
            'metadata': metadata,
            'html_preview': html_content
        })
    except yaml.YAMLError as e:
        return jsonify({'error': f'Invalid YAML frontmatter: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.context_processor
def inject_now():
    return {
        'now': datetime.utcnow(),
        'title': config['site']['title'],
        'per_page': config['content']['posts_per_page'],
    }


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
