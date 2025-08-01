<p align="center">
<img src="https://rgk.io/static/media/etch.svg" width="200" alt="Etch Logo - Courtesy of SocialSight AI" />
</p>

# Etch

**Etch** is a minimalist, Python-based web framework for content-driven websites. It uses plain Markdown files, zero build steps, and Flask to serve content dynamically — perfect for personal blogs, digital résumés, and project portfolios.

Etch was designed with a bias toward simplicity and transparency. If you're a Python developer who wants to avoid bloated static site generators, Etch might feel like home.

---

## Features

* Markdown-first publishing model with YAML frontmatter
* No build step — content is rendered at request time
* Fully Pythonic and hackable (Flask + Jinja2)
* Easy customization with minimal boilerplate
* Smart caching for fast reads
* AI-assisted architecture (Claude 3.5)

---

## Project Structure

```bash
etch/
├── app.py                  # Main Flask app and routes
├── utils.py                # Markdown parsing, helpers, caching
├── config.yml              # Site config (paths, author info, etc.)
├── auth.py                 # Admin login + password hashing
├── templates/              # Jinja2 HTML templates
├── posts/                  # Markdown files for blog posts
├── pages/                  # Static pages (e.g., About)
├── projects/               # Markdown-based project entries
├── static/                 # CSS, JS, images
```

---

## Quickstart - from PyPI

### 1. Install the package
```bash
pip install -i https://test.pypi.org/simple/ etch
```

### 2. Create a new project

Where `new-site` is the name of your folder (or `.` if you want to create the app in your current directory):

```bash
etch new-site
```_
_
_Optionally, add `--bare`/`-b` if you don't want the demo content!_

### 3. Run the app server
```bash
cd new-site
flask run  # or python app.py
```

Visit [http://localhost:5000](http://localhost:5000)

---

## Quickstart - from source

### 1. Clone the repo

```bash
git clone https://github.com/rgkimball/etch.git
cd etch
```

### 2. Create a virtual environment (optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the development server

```bash
python app.py
```

Visit [http://localhost:5000](http://localhost:5000)

Now make an edit, add a page or a post and your content will be live &mdash; no need to restart the app!

---

## Writing Content

All content lives in the `posts/`, `pages/`, and `projects/` directories. Each file must:

* Be written in **Markdown**
* Begin with a **YAML frontmatter** block like this:

```markdown
---
title: My First Post
date: 2025-07-01
tags: [ai, flask]
summary: A quick walkthrough of building Etch with Claude 3.5
---

Here's the main content...
```

---

## Configuration

Edit `config.yml` to change:

* Site title, author, description
* Post pagination
* Content directory paths
* Admin password hash (for future features)

---

## Customizing

* Templates live in `/templates` and use Jinja2
* CSS and assets go in `/static`
* Routes can be edited in `app.py`
* Add or remove content types by modifying the `CONTENT_TYPES` registry in `utils.py`

---

## Admin

`auth.py` includes login helpers, but admin routes are not enabled by default. Future versions may include editing from the browser.

---

## Why Etch?

Because sometimes you don’t need a JS toolchain, Go templates, or a megabyte of YAML. You just want to write, commit, and publish in a familiar language.
