from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
import os
from pathlib import Path
import shutil
from typing import Callable, List, Optional

import re
from datetime import datetime
from flask import abort
from jinja2 import Environment, BaseLoader

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.toc import TocExtension
from markdown_extensions import EnhancedMarkdownExtension
import yaml


# Configure Markdown once
md = markdown.Markdown(extensions=[
    'meta',
    'tables',
    # 'markdown.extensions.lists',
    'markdown.extensions.footnotes',
    'markdown.extensions.smarty',
    'markdown.extensions.fenced_code',
    'markdown.extensions.attr_list',
    'markdown.extensions.def_list',
    TocExtension(permalink=True),
    CodeHiliteExtension(css_class='highlight'),
    FencedCodeExtension(),
    'pymdownx.arithmatex',
    EnhancedMarkdownExtension(),
], extension_configs={
    'pymdownx.arithmatex': {
        'generic': True,
    }
})

def load_config():
    """Load configuration from YAML file"""
    from auth import get_config_path
    config_path = get_config_path()
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def parse_date(date_str):
    """Parse date string into datetime object"""
    if not date_str:
        return datetime.now()

    if type(date_str) in [date, datetime]:
        return date_str

    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return datetime.now()

def determine_content_type(filepath):
    """Determine content type based on file location"""
    if 'posts/' in filepath:
        return 'post'
    elif 'projects/' in filepath:
        return 'project'
    elif 'pages/' in filepath:
        return 'page'
    return 'unknown'


@dataclass
class ContentType:
    name: str
    path: str
    template: str
    sort_key: str = "date"
    reverse: bool = True
    parser: Callable = None  # Optional custom loader if needed


CONTENT_TYPES = {
    "posts": ContentType(name="posts", path="posts", template="post.html"),
    "pages": ContentType(name="pages", path="pages", template="page.html", reverse=False),
    "projects": ContentType(name="projects", path="projects", template="project.html"),
}


@dataclass
class BaseMetadata:
    """Base metadata fields common to all content types"""
    title: str
    description: str
    template: str

@dataclass
class PageMetadata(BaseMetadata):
    """Metadata specific to pages"""
    show_in_nav: bool = False
    nav_order: int = 999
    last_updated: Optional[datetime] = None
    nav_icon: Optional[str] = None

@dataclass
class PostMetadata(BaseMetadata):
    """Metadata specific to blog posts"""
    date: Optional[datetime] = None
    updated: Optional[datetime] = None
    author: str = "Anonymous"
    tags: List[str] = None
    category: str = "Uncategorized"
    status: str = "draft"
    featured: bool = False

    def __post_init__(self):
        self.tags = self.tags or []

@dataclass
class ProjectMetadata(BaseMetadata):
    """Metadata specific to projects"""
    date_started: Optional[datetime] = None
    date_completed: Optional[datetime] = None
    status: str = "in-progress"
    technologies: List[str] = None
    github_url: str = ""
    live_url: str = ""
    featured: bool = False
    showcase_image: str = ""

    def __post_init__(self):
        self.technologies = self.technologies or []

def process_metadata(metadata: dict, content_type: str) -> BaseMetadata:
    """Process and validate metadata based on content type"""
    base_data = {
        'title': metadata.get('title', 'Untitled'),
        'description': metadata.get('description', ''),
        'template': metadata.get('template', content_type),
    }

    if content_type == 'page':
        return PageMetadata(
            **base_data,
            show_in_nav=metadata.get('show_in_nav', False),
            nav_order=metadata.get('nav_order', 999),
            last_updated=parse_date(metadata.get('last_updated')),
            nav_icon=metadata.get('nav_icon'),
        )
    elif content_type == 'post':
        return PostMetadata(
            **base_data,
            date=parse_date(metadata.get('date')),
            updated=parse_date(metadata.get('updated')),
            author=metadata.get('author', 'Anonymous'),
            tags=metadata.get('tags', []),
            category=metadata.get('category', 'Uncategorized'),
            status=metadata.get('status', 'draft'),
            featured=metadata.get('featured', False),
        )
    elif content_type == 'project':
        return ProjectMetadata(
            **base_data,
            date_started=parse_date(metadata.get('date_started')),
            date_completed=parse_date(metadata.get('date_completed')),
            status=metadata.get('status', 'in-progress'),
            technologies=metadata.get('technologies', []),
            github_url=metadata.get('github_url', ''),
            live_url=metadata.get('live_url', ''),
            featured=metadata.get('featured', False),
            showcase_image=metadata.get('showcase_image', '')
        )
    return BaseMetadata(**base_data)


def get_mtime(path):
    return os.path.getmtime(path)

def load_markdown_file(filepath):
    """Load and parse a markdown file with YAML frontmatter"""

    @lru_cache(maxsize=128)
    def _load_file(filepath, mtime):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()

                if content.startswith('---'):
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        md.reset()
                        raw_metadata = yaml.safe_load(parts[1])
                        content_type = determine_content_type(filepath)
                        metadata = process_metadata(raw_metadata, content_type)

                        try:
                            md_raw = parts[2].strip()

                            # Step 1: Extract and replace code blocks
                            code_blocks = {}

                            def mask_code_block(match):
                                i = len(code_blocks)
                                key = f"[{{CODEBLOCK_{i}}}]"
                                code_blocks[key] = match.group(0)
                                return key

                            masked_md = re.sub(r"(```.*?```|~~~.*?~~~)", mask_code_block, md_raw, flags=re.DOTALL)

                            # Step 2: Render remaining Markdown with Jinja
                            context = {
                                'now': datetime.now(),
                            }

                            rtemplate = Environment(loader=BaseLoader).from_string(masked_md)
                            jinja_rendered = rtemplate.render(**context)

                            # Step 3: Restore original code blocks
                            for key, block in code_blocks.items():
                                jinja_rendered = jinja_rendered.replace(key, block)

                            # Step 4: Convert to HTML
                            html_content = md.convert(jinja_rendered)
                            return metadata, html_content

                        except Exception as e:
                            print(f"Error converting markdown: {e}")
                            return metadata, f"<p>Error processing content: {e}</p>"

                md.reset()
                return {}, md.convert(content)
        except FileNotFoundError:
            abort(404)
        except Exception as e:
            print(f"Error processing file {filepath}: {e}")
            abort(404)

    # Check if file exists before trying to get mtime
    if not os.path.exists(filepath):
        abort(404)

    return _load_file(filepath, os.path.getmtime(filepath))


def safe_file_operation(file_path, operation_func):
    """Safely perform file operations with backup"""
    try:
        if file_path.exists():
            backup_path = file_path.with_suffix('.md.bak')
            shutil.copy2(file_path, backup_path)

        result = operation_func(file_path)
        return True, result
    except Exception as e:
        return False, str(e)

def get_content_listing(content_dir):
    """Get listing of content files with metadata"""
    files = []
    content_path = Path(content_dir)

    for file in content_path.glob('*.md'):
        metadata, _ = load_markdown_file(str(file))
        files.append({
            'slug': file.stem,
            'filename': file.name,
            'metadata': metadata or {},
            'last_modified': file.stat().st_mtime
        })

    return files

def calculate_reading_time(text, wpm=250):
    """
    Calculate reading time in minutes based on word count.

    Args:
        text (str): The text content to analyze
        wpm (int): Words per minute reading speed (default 250 for average adult)

    Returns:
        int: Estimated reading time in minutes
    """
    word_count = len(text.split())
    minutes = max(1, round(word_count / wpm))
    return minutes
