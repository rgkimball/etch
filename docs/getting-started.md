# Etch Documentation

Welcome to the official documentation for **Etch**, a lightweight Python framework for building Markdown-based websites with no build step and minimal configuration.

---

## Overview

Etch is a Flask-powered web framework that treats folders full of Markdown as your content database. It's designed to be intuitive, hackable, and fast enough for personal use. Instead of requiring a build process, Etch renders pages dynamically and caches intelligently.

Use Etch if you:

* Want a simple, elegant personal site that you can stand up in minutes
* Prefer Python to JavaScript or Go
* Like seeing your content in folders, not buried in config files
  * And by extension, fear walled gardens. You can take your posts and pages with you to another platform easily if you tire of this one
* Want something you can fully understand in one afternoon

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourname/etch.git
cd etch
```

### 2. Install requirements

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Start the dev server

```bash
python app.py
```

Visit `http://localhost:5000` to see your site.

---

## Directory Structure

```bash
etch/
├── app.py                 # Flask app and routes
├── utils.py               # Core logic: loaders, cache, helpers
├── config.yml             # Site configuration
├── templates/             # Jinja2 templates
├── static/                # CSS, images, assets
├── posts/                 # Blog posts (Markdown)
├── pages/                 # Static pages (Markdown)
├── projects/              # Project writeups (Markdown)
```

---

## Writing Content

Etch supports three content types out of the box: `posts`, `pages`, and `projects`. Each content file is a Markdown document with optional YAML frontmatter:

```markdown
---
title: Hello World
date: 2025-07-01
tags: [personal, example]
summary: This is a quick intro post.
---

This is your content, written in Markdown.
```

To create a new post:

```bash
touch posts/hello-world.md
```

---

## Configuration

Edit `config.yml` to control site settings:

```yaml
site:
  title: My Site
  description: A personal site built with custom Python framework
  base_url: http://localhost:5000
  author: Your Name

paths:
  posts: posts
  pages: pages
  projects: projects
  templates: templates
  static: static

content:
  posts_per_page: 4
  allowed_extensions:
    - .md
  summary_length: 200
```

---

## Architecture & Abstractions

Etch uses a centralized `ContentType` class to define each content model:

```python
@dataclass
class ContentType:
    name: str
    path: str
    template: str
    sort_key: str = "date"
    reverse: bool = True
```

You can register new types or modify existing ones in `utils.py`. Each content type is tied to a folder and template, and sorted by a key like `date`.

Example registry:

```python
CONTENT_TYPES = {
  "posts": ContentType(name="posts", path="posts", template="post.html"),
  "pages": ContentType(name="pages", path="pages", template="page.html", reverse=False),
  "projects": ContentType(name="projects", path="projects", template="project.html"),
}
```

---

## Caching

Etch uses `functools.lru_cache` to cache parsed Markdown content. Cache is invalidated automatically when file modification times (`mtime`) change.

No need for manual clears — just edit a `.md` file and Etch reloads it fresh on next request.

---

## Authentication (Optional)

`auth.py` provides admin password hashing and session management. Admin routes are not enabled by default but can be wired up for editing or uploads.

---

## Customization

You can:

* Add routes in `app.py`
* Create or modify templates in `/templates`
* Add styling in `/static/main.css`
* Replace or extend content folders
* Build export features if you want to pre-render statics

---

## Ideas for Expansion

* Add a static site exporter
* Build an admin dashboard
* Support RSS + sitemap.xml
* Extend content model types with plugins

---

## Credits

Etch was bootstrapped with the help of Claude 3.5. You can read the full build story in `claude.md`.

You can also find a blog post about the framework [here](https://rgk.io/posts/built-by-claude)

---

## Feedback

Have ideas or want to contribute? File a GitHub issue or fork away. Etch is designed to stay small, transparent, and friendly to solo devs.
