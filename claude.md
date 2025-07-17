# Personal Site Framework

This is a custom-built web framework for hosting and rendering simple static content that uses Python to serve and render pages. All site content is stored in Markdown files, and templates are constructed in jinja2. The Markdown header includes metadata that corresponds to the type of content, and is rendered in the 'main' section of the jinja templates. 

There are three main content types:

- Pages: Pages are infrequently-changed and belong to the main navigation. Examples may include an 'About Me' or a 'Contact' form page.
- Posts: Posts are written often and will be displayed in descending order by post date.
- Projects: Projects may include web development, design, data science or coding packages and tools.

The site will also have an admin area that is accessible through a single salted/encrypted password. There is no database and no secondary users; this salted password will be stored along with other relevant settings (like the base URL) in a config file.

The code repository should be organized as follows:

- `/pages`: a directory of Markdown files for pages
- `/projects`: a directory of Markdown files for projects
- `/posts`: a directory of Markdown files for posts
- `/templates`: jinja2 templates, like `base.tpl` for the primary HTML wrapper, and `post.tpl` for post-specific wrappers.
- `/static`: a parent directory containing subdirectories: `./js`, `./css`, `./scss` and `./media`.

When serving the app, users may access each content type as follows:

-`baseurl.com/ABC` where `ABC` corresponds to a Markdown file in `/pages`, `ABC.md`
-`baseurl.com/projects/DEF` where `DEF` corresponds to a Markdown file in `/projects`, `DEF.md`
-`baseurl.com/posts/some-post` where `some-post` is a Markdown file in `/posts`, `some-post.md`

There are also some special generated pages:
- `baseurl.com`: this will be a list of the first N post summaries in descending order by date, with a navigation bar with links to each page
- `baseurl.com/projects`: A flexbox grid of project tiles, which will expand from 1 column up to 4 depending on the viewport width.
- `baseurl.com/posts`: Redirects to `/`
- `baseurl.com/admin`: This is a password-protected page managed by 24-hour session cookies, behind which admins can use a WYSIWYG Markdown editor to make  updates to each content type.
