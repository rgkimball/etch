---
title: Etch
description: A Markdown-first site framework co-authored with AI
date_started: 2025-06-28
date_completed: 2025-06-29
status: completed
technologies:
  - Python
  - Flask
  - Jinja2
  - Markdown
github_url: https://github.com/rgkimball/etch
live_url: https://rgk.io
featured: true
---

**Etch** is a minimalist, Markdown-first framework for personal websites. It was co-authored with AI (Claude) but guided by a long-standing vision for something easier.

Etch reads directly from your file system, renders pages dynamically with Flask, and doesn’t require a build step, a database, or a fleet of plugins. It’s ideal for developers who want to maintain a personal site without maintaining a toolchain.

### Origin

Over the past 20 years, I’ve rebuilt my personal site more times than I should have, from Myspace-era HTML to a fully modular Drupal stack (complete with CI pipelines I never needed). With each version, the complexity grew and my requirements shrank. When my 2025 $600 hosting renewal invoice arrived I decided to scrap it all and start over.

Armed with a weekend and a trial of PyCharm's AI assistant, I described the framework I always wanted: Markdown files, a Jinja+SCSS templating, and no frills. Claude did most of the scut work, and I shaped the vision. The result is Etch: fast, readable, and human-scale.


**Read more of the backstory here: [This web framework was entirely built by Claude](https://rgk.io/posts/built-by-claude)**

---

## Highlights

- **Markdown-native**: All content lives in Markdown files with YAML frontmatter
- **Zero build step**: No compilation or deployment scripts required
- **Fast reads with cache**: Intelligent caching ensures great performance even at runtime
- **Templating with Jinja2**: Full control over layout, metadata, and structure
- **Flat-file architecture**: Pages, posts, and projects live as folders — no CMS needed
- **AI-assisted, human-refined**: Built using Claude, with deliberate editing and iteration

_(Yes, AI wrote that part)_

## Stack

- **Python/Flask**
- **Jinja2**: for template rendering
- **SCSS**: recommend using PyCharm's file watcher for this.
- **lru_cache**: to speed up repeated Markdown parsing

_(This part too)_

## What Makes Etch Different

Unlike Hugo, Jekyll, or Eleventy, Etch doesn’t compile anything. You write a Markdown file, drop it into a folder, and it’s live. It’s Python through and through — no JS pipelines, no build tools, and no friction. That makes it easy to read, easy to extend, and nearly impossible to break.

Etch is less a CMS, more a reflection of how you think. You write, it publishes.


_(Okay fine, AI wrote all of this)_

----

## Live Demo

> <h3><a href="https://rgk.io"><i class="uit uit-link"></i> &nbsp; rgk.io</a></h3>

Explore the live site to see Etch in action. All content, including this page, is written in Markdown and served dynamically.


## GitHub

>  <h3><a href="https://github.com/rgkimball/etch"><i class="uit uit-code-branch"></i> &nbsp; rgkimball/etch</a></h3>

Contributions, forks (and stars!) are welcome.

