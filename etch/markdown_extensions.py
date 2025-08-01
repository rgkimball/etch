from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor
from markdown.postprocessors import Postprocessor
import re
import xml.etree.ElementTree as etree

class ContainerPreprocessor(Preprocessor):
    CONTAINER_RE = re.compile(r':::(\w+)\s*(?:\{(.*?)\})?\s*\n(.*?)\n:::\s*\n', re.DOTALL)

    def run(self, lines):
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
    def run(self, root):
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
    def build_toc(self, root):
        toc = []
        for elem in root.findall('.//h1') + root.findall('.//h2') + root.findall('.//h3'):
            level = int(elem.tag[1])
            text = elem.text or ''
            if 'id' not in elem.attrib:
                elem.attrib['id'] = re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')
            toc.append((level, text, elem.attrib['id']))
        return toc

    def run(self, root):
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

                for level, text, id in toc:
                    while level <= current_level:
                        stack.pop()
                        current_level -= 1

                    if level > current_level:
                        ul = etree.SubElement(stack[-1], 'ul')
                        stack.append(ul)
                        current_level = level

                    li = etree.SubElement(stack[-1], 'li')
                    a = etree.SubElement(li, 'a')
                    a.attrib['href'] = f'#{id}'
                    a.text = text

                toc_marker.getparent().replace(toc_marker, toc_div)
        return root

class EnhancedMarkdownExtension(Extension):
    def extendMarkdown(self, md):
        # Container should run before markdown parsing
        md.preprocessors.register(ContainerPreprocessor(md), 'container', 25)
        # These should run after the markdown is parsed
        # md.treeprocessors.register(FigureCaptionProcessor(md), 'figure_caption', 15)
        # md.treeprocessors.register(TableOfContentsProcessor(md), 'toc', 25)