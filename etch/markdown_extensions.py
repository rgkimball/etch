# pylint: disable=too-few-public-methods
"""
Additional Markdown extensions for Etch, adding ToC, figures, and more.

This module provides custom Markdown extensions including container support,
figure captions, and table of contents generation.
"""
import re
import xml.etree.ElementTree as etree

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor


class ContainerPreprocessor(Preprocessor):
    """
    Preprocessor for handling container blocks in Markdown.

    Converts :::container syntax into HTML div elements with appropriate classes.
    """
    CONTAINER_RE = re.compile(r':::(\w+)\s*(?:\{(.*?)\})?\s*\n(.*?)\n:::\s*\n', re.DOTALL)

    def run(self, lines):
        """Process lines to convert container blocks to HTML."""
        new_lines = []
        current_block = []
        in_container = False

        for line in lines:
            if not in_container:
                # Check for container start
                match = re.match(r':::(\w+)\s*(?:\{(.*?)\})?\s*$', line)
                if match:
                    in_container = True
                    container_type = match.group(1)
                    attrs = match.group(2) or ''
                    attr_html = f' {attrs}' if attrs else ''
                    new_lines.append(f'<div class="container {container_type}"{attr_html}>')
                else:
                    new_lines.append(line)
            else:
                # Check for container end
                if line.strip() == ':::':
                    in_container = False
                    # Process and add the content
                    new_lines.extend(current_block)
                    new_lines.append('</div>')
                    current_block = []
                else:
                    current_block.append(line)

        # Handle any remaining content
        if current_block:
            new_lines.extend(current_block)

        return new_lines


class FigureCaptionProcessor(Treeprocessor):
    """
    Tree processor for converting images with titles to figure/figcaption elements.

    Wraps img elements that have a title attribute in figure tags and converts
    the title to a figcaption element.
    """

    def run(self, root):
        """Process the element tree to wrap images in figure elements."""
        for img in root.findall('.//img'):
            if 'title' in img.attrib:
                # Create figure element
                figure = etree.Element('figure')
                # Move img into figure
                img_parent = img.getparent()
                img_parent.replace(img, figure)
                figure.append(img)
                # Add figcaption
                figcaption = etree.SubElement(figure, 'figcaption')
                figcaption.text = img.attrib['title']
        return root


class TableOfContentsProcessor(Treeprocessor):
    """
    Tree processor for generating table of contents from heading elements.

    Finds [TOC] markers and replaces them with a nested list of links
    to all heading elements in the document.
    """

    def build_toc(self, root):
        """Build table of contents data from heading elements."""
        toc = []
        for elem in root.findall('.//h1') + root.findall('.//h2') + root.findall('.//h3'):
            level = int(elem.tag[1])
            text = elem.text or ''
            if 'id' not in elem.attrib:
                elem.attrib['id'] = re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')
            toc.append((level, text, elem.attrib['id']))
        return toc

    def run(self, root):
        """Process the element tree to generate table of contents."""
        # Find TOC marker by iterating through paragraphs
        toc_marker = None
        for p in root.findall('.//p'):
            if p.text == '[TOC]':
                toc_marker = p
                break

        if toc_marker is not None:
            toc = self.build_toc(root)
            if toc:
                toc_div = etree.Element('div')
                toc_div.attrib['class'] = 'table-of-contents'
                toc_nav = etree.SubElement(toc_div, 'nav')

                current_level = 0
                stack = [toc_nav]

                for level, text, element_id in toc:
                    while level <= current_level:
                        stack.pop()
                        current_level -= 1

                    if level > current_level:
                        ul = etree.SubElement(stack[-1], 'ul')
                        stack.append(ul)
                        current_level = level

                    li = etree.SubElement(stack[-1], 'li')
                    a = etree.SubElement(li, 'a')
                    a.attrib['href'] = f'#{element_id}'
                    a.text = text

                toc_marker.getparent().replace(toc_marker, toc_div)
        return root


class EnhancedMarkdownExtension(Extension):
    """
    Main extension class that registers all custom processors.

    This extension adds container support, figure captions, and table of
    contents functionality to Markdown processing.
    """

    def extendMarkdown(self, md):
        """Register custom processors with the Markdown instance."""
        # Container should run before markdown parsing
        md.preprocessors.register(ContainerPreprocessor(md), 'container', 25)
        # These should run after the markdown is parsed
        # md.treeprocessors.register(FigureCaptionProcessor(md), 'figure_caption', 15)
        # md.treeprocessors.register(TableOfContentsProcessor(md), 'toc', 25)
