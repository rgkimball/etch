"""
Flask web application for a blog/portfolio site.

This module contains the main Flask application with routes for displaying
posts, projects, pages, and admin functionality.
"""
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from functools import wraps
import os
from pathlib import Path
import random
import re
import secrets
import shutil
import time
from urllib.parse import urljoin

from rfeed import Feed, Guid, Item
from flask import (
    Flask,
    Response,
    render_template,
    session,
    request,
    redirect,
    url_for,
    jsonify,
)
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
    """Get sorted list of pages that should appear in navigation."""
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
    """Decorator to require authentication for admin routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        # Check if session has expired
        if 'auth_time' in session:
            auth_time = datetime.fromisoformat(session['auth_time'])
            session_duration = timedelta(hours=config['admin']['session_duration'])
            if datetime.now() - auth_time > session_duration:
                session.clear()
                return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


def get_content_items(content_type: ContentType):
    """Get and sort content items for a given content type."""
    directory = os.path.join(config['paths'][content_type.name])
    items = []
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            path = os.path.join(directory, filename)
            metadata, content = load_markdown_file(path)
            if metadata:
                items.append((metadata, content))
    sort_key = content_type.sort_key
    return sorted(items, key=lambda x: getattr(x[0], sort_key, ""),
                  reverse=content_type.reverse)


# Routes
@app.route('/')
def index():
    """Display the homepage with recent posts."""
    # Get most recent posts
    posts = []
    posts_dir = config['paths']['posts']
    for filename in os.listdir(posts_dir):
        if filename.endswith('.md'):
            metadata, content = load_markdown_file(os.path.join(posts_dir, filename))
            if hasattr(metadata, 'date'):
                summary_length = config['content']['summary_length']
                summary = (content[:summary_length] + '...'
                           if len(content) > summary_length else content)
                posts.append({
                    'slug': filename[:-3],
                    'metadata': metadata,
                    'summary': summary
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
    """API endpoint to get paginated posts."""
    page_num = request.args.get('page', 1, type=int)
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
                    summary_length = config['content']['summary_length']
                    post_data['summary'] = (content[:summary_length] + '...'
                                            if len(content) > summary_length else content)

                posts.append(post_data)

    # Sort posts by date
    posts.sort(key=lambda x: x['date'], reverse=True)

    # Calculate pagination
    total_posts = len(posts)
    total_pages = (total_posts + per_page - 1) // per_page
    start = (page_num - 1) * per_page
    end = start + per_page

    current_posts = posts[start:end]

    # Debug logging
    app.logger.debug("Page: %s, Total: %s, Per page: %s",
                     page_num, total_posts, per_page)
    app.logger.debug("Returning %s posts", len(current_posts))

    return jsonify({
        'posts': current_posts,
        'pagination': {
            'current_page': page_num,
            'total_pages': total_pages,
            'has_next': page_num < total_pages,
            'has_prev': page_num > 1
        }
    })


@app.route('/<page>')
def page(page):
    """Display a static page."""
    metadata, content = load_markdown_file(
        os.path.join(config['paths']['pages'], f"{page}.md"))
    if content is None:
        return "Page not found", 404

    # Pass metadata as the page variable that the template expects
    return render_template('page.html', content=content, page=metadata)


@app.route('/posts/<slug>')
def post(slug):
    """Display a blog post."""
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
    """Display a project page."""
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
    """Display the projects listing page."""
    projects_dir = config['paths']['projects']
    if not os.path.exists(projects_dir):
        return render_template('projects.html', projects=[])

    # Use the existing get_content_listing function
    project_files = get_content_listing(projects_dir)

    # Add summaries to the projects
    for project_item in project_files:
        _, content = load_markdown_file(
            os.path.join(projects_dir, f"{project_item['slug']}.md"))
        summary_length = config['content']['summary_length']
        project_item['summary'] = (content[:summary_length] + '...'
                                   if content and len(content) > summary_length
                                   else content)

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
    """Display the admin dashboard."""
    return render_template('admin/dashboard.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    """Handle admin login."""
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
    """Generate RSS feed for blog posts."""
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

                description = (getattr(metadata, 'description', '') or
                               content[:config['content']['summary_length']])
                author = (getattr(metadata, 'author', '') or
                          config.get('site', {}).get('author', ''))

                # Create post item
                posts.append(Item(
                    title=metadata.title,
                    link=f"{site_url}/posts/{filename[:-3]}",
                    description=description,
                    author=author,
                    guid=Guid(f"{site_url}/posts/{filename[:-3]}"),
                    pubDate=datetime.combine(metadata.date, datetime.min.time()).replace(
                        tzinfo=timezone.utc)
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


@app.route("/robots.txt")
def robots_txt():
    """Generate robots.txt file."""
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /__pullhook",
        f"Sitemap: {request.host_url.rstrip('/')}/sitemap.xml"
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    """Generate sitemap.xml file."""
    urls = []

    def add_url(path, lastmod):
        """Add a URL to the sitemap."""
        abs_url = urljoin(request.host_url, path.lstrip("/"))
        urls.append(f"  <url><loc>{abs_url}</loc><lastmod>{lastmod}</lastmod></url>")

    now = datetime.utcnow().date().isoformat()

    # Homepage
    add_url("/", now)

    for name, _ in CONTENT_TYPES.items():
        dir_path = config["paths"].get(name)
        if not dir_path or not os.path.exists(dir_path):
            continue

        for fname in os.listdir(dir_path):
            if not fname.endswith(".md"):
                continue

            filepath = os.path.join(dir_path, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read().strip()
                if text.startswith("---"):
                    parts = text.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        if frontmatter.get("exclude_from_sitemap", False):
                            continue

            slug = fname.rsplit(".", 1)[0]
            lastmod = datetime.fromtimestamp(
                os.path.getmtime(filepath), tz=timezone.utc).date().isoformat()
            add_url(f"/{name}/{slug}", lastmod)

    xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) +
            '\n</urlset>'
    )
    return Response(xml, mimetype="application/xml")


@app.route('/admin/logout')
def logout():
    """Handle admin logout."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/content/<content_type>', methods=['GET'])
@requires_auth
def list_content(content_type):
    """List content files of a given type."""
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
    """Get content for editing."""
    if content_type not in config['paths']:
        return jsonify({'error': 'Invalid content type'}), 400

    file_path = Path(config['paths'][content_type]) / f"{slug}.md"
    if not file_path.exists():
        return jsonify({'error': 'Content not found'}), 404

    metadata, content = load_markdown_file(str(file_path))
    with open(file_path, 'r', encoding='utf-8') as f:
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
    """Save content to file."""
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
        file_path.write_text(content, encoding='utf-8')
        return jsonify({'success': True, 'slug': safe_slug})
    except (OSError, IOError, PermissionError) as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500


@app.route('/api/content/<content_type>/<slug>', methods=['DELETE'])
@requires_auth
def delete_content(content_type, slug):
    """Delete content file."""
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
    except (OSError, IOError, PermissionError) as e:
        return jsonify({'error': f'Failed to delete file: {str(e)}'}), 500


@app.route('/api/validate-content', methods=['POST'])
@requires_auth
def validate_content():
    """Validate content format and structure."""
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
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

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
    except (ValueError, TypeError, AttributeError) as e:
        return jsonify({'error': f'Content validation error: {str(e)}'}), 400


@app.context_processor
def inject_now():
    """Inject common template variables."""
    return {
        'now': datetime.utcnow(),
        'title': config['site']['title'],
        'per_page': config['content']['posts_per_page'],
    }


# Error handlers
@app.errorhandler(404)
def page_not_found(_):
    """Handle 404 errors."""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(_):
    """Handle 500 errors."""
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
