from models.types import TokenType, BlockType
from models.models import Token, Block
import re
import emoji

def render_inline(text: str) -> str:
    result = []
    i = 0

    text = emoji.emojize(text)

    while i < len(text):
        # Code blocks
        if text[i] == '`':
            end = text.find('`', i + 1)
            if end != -1:
                result.append('<code>')
                result.append(text[i+1:end])
                result.append('</code>')
                i = end + 1
                continue

        # Images
        if text[i] == '!' and text[i+1] == '[':
            # Find the closing ] and check for (url)
            bracket_end = text.find(']', i + 2)
            if bracket_end != -1 and bracket_end + 1 < len(text) and text[bracket_end + 1] == '(':
                paren_end = text.find(')', bracket_end + 2)
                if paren_end != -1:
                    alt_text = text[i + 2:bracket_end]
                    url = text[bracket_end + 2:paren_end]
                    result.append(f'<img src="{url}" alt="{alt_text}" />')
                    i = paren_end + 1
                    continue

        # Links
        if text[i] == '[':
            # Find the closing ] and check for (url)
            bracket_end = text.find(']', i + 1)
            if bracket_end != -1 and bracket_end + 1 < len(text) and text[bracket_end + 1] == '(':
                paren_end = text.find(')', bracket_end + 2)
                if paren_end != -1:
                    link_text = text[i+1:bracket_end]
                    url = text[bracket_end+2:paren_end]
                    result.append(f'<a href="{url}">')
                    result.append(render_inline(link_text))
                    result.append('</a>')
                    i = paren_end + 1
                    continue

        # Bold + Italic with *** or ___
        if i + 2 < len(text) and (text[i:i+3] == '***' or text[i:i+3] == '___'):
            marker = text[i:i+3]
            end = text.find(marker, i + 3)
            if end != -1:
                result.append('<strong><em>')
                result.append(render_inline(text[i+3:end]))
                result.append('</em></strong>')
                i = end + 3
                continue

        # Bold with ** or __
        if i + 1 < len(text) and (text[i:i+2] == '**' or text[i:i+2] == '__'):
            marker = text[i:i+2]
            end = text.find(marker, i + 2)
            if end != -1:
                result.append('<strong>')
                result.append(render_inline(text[i+2:end]))
                result.append('</strong>')
                i = end + 2
                continue

        if i + 1 < len(text) and text[i:i+2] == '~~':
            end = text.find('~~', i + 2)
            if end != -1:
                result.append('<del>')
                result.append(render_inline(text[i + 2:end]))
                result.append('</del>')
                i = end + 2
                continue

        # Italic with * or _
        if text[i] in ('*', '_'):
            marker = text[i]
            # Make sure it's not part of ** or __
            if i + 1 < len(text) and text[i+1] == marker:
                result.append(text[i])
                i += 1
                continue

            # Find the matching closing marker that's not part of ** or __
            j = i + 1
            while j < len(text):
                if text[j] == marker:
                    # Check if this is a standalone marker (not part of ** or __)
                    is_double_before = j > 0 and text[j-1] == marker
                    is_double_after = j + 1 < len(text) and text[j+1] == marker

                    if not is_double_before and not is_double_after:
                        result.append('<em>')
                        result.append(render_inline(text[i+1:j]))
                        result.append('</em>')
                        i = j + 1
                        break
                j += 1
            else:
                result.append(text[i])
                i += 1
            continue

        # Regular character
        result.append(text[i])
        i += 1

    return ''.join(result)

def render_heading(block: Block):
    content = block.content[0].text

    level = len(content.lstrip()) - len(content.lstrip().lstrip('#'))

    sanitized_content = content.lstrip("#").strip()

    style = 'style="border-bottom-style: groove;"' if level in (1, 2) else ''

    return f"<h{level} {style}>{render_inline(sanitized_content)}</h{level}>"

def render_paragraph(block: Block):
    content = block.content

    content_joined = ""

    for element in content:
        content_joined += element.text.lstrip() + " "

        if element.text.rstrip().endswith("\\"):
            content_joined = content_joined.rstrip().removesuffix("\\")
            content_joined += "<br>"

    content_joined = content_joined.rstrip()

    return "<p>" + render_inline(content_joined) + "</p>"


def render_list(block: Block) -> str:
    if not block.content:
        return ""

    # Determine list type and marker pattern
    if block.block_type == BlockType.UNORDERED_LIST:
        list_tag = "ul"
        marker_pattern = r'^\s*[-*+]\s+'
    else:
        list_tag = "ol"
        marker_pattern = r'^\s*\d+\.\s+'

    html_parts = [f"<{list_tag}>"]
    indent_stack = [0]

    for token in block.content:
        text = re.sub(marker_pattern, '', token.text)
        text = render_inline(text)

        current_indent = token.indentation

        # Going deeper - open new list
        while current_indent > indent_stack[-1]:
            html_parts.append(f"<{list_tag}>")
            indent_stack.append(current_indent)

        # Going shallower - close lists
        while len(indent_stack) > 1 and current_indent < indent_stack[-1]:
            html_parts.append(f"</{list_tag}>")
            indent_stack.pop()

        html_parts.append(f"<li>{text}</li>")

    # Close all remaining nested lists
    while len(indent_stack) > 1:
        html_parts.append(f"</{list_tag}>")
        indent_stack.pop()

    html_parts.append(f"</{list_tag}>")

    return ''.join(html_parts)

def render_horizontal_rule(block: Block) -> str:
    return '<hr>'


def render_blockquote(block: Block) -> str:
    from lexer import tokenize
    from parser import parse_blocks

    lines = []
    for token in block.content:
        stripped = re.sub(r'^\s*>\s?', '', token.text)
        lines.append(stripped)

    inner_text = '\n'.join(lines)
    inner_tokens = tokenize(inner_text)
    inner_blocks = parse_blocks(inner_tokens)
    inner_html = render_html(inner_blocks)

    return f'<blockquote>{inner_html}</blockquote>'

def render_code(block: Block) -> str:
    if not block.content:
        return ""

    first_line = block.content[0].text.strip()
    language = first_line[3:].strip() if len(first_line) > 3 else ""

    code_lines = []
    for token in block.content[1:-1]:
        code_lines.append(token.text)

    code = '\n'.join(code_lines)

    code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    if language:
        return f'<pre><code class="language-{language}">{code}</code></pre>'
    else:
        return f'<pre><code>{code}</code></pre>'

def parse_table_row(line: str) -> list[str]:
    line = line.strip()
    return [col.strip() for col in line.split('|') if col.strip()]

def generate_alignment(alignment_row: list[str]) -> list[str]:
    alignment_list = []

    for column in alignment_row:
        if ":" not in column:
            alignment_list.append("left")
        elif column.startswith(":") and column.endswith(":"):
            alignment_list.append("center")
        elif column.startswith(":"):
            alignment_list.append("left")
        else:
            alignment_list.append("right")

    return alignment_list

def render_table(block: Block) -> str:
    if not block.content:
        return ""

    rows = [parse_table_row(token.text) for token in block.content]

    if len(rows) < 2:
        return "<p>" + "<br>".join([token.text for token in block.content]) + "</p>"

    if not all(set(cell) <= set(":-") for cell in rows[1]):
        return "<p>" + "<br>".join([token.text for token in block.content]) + "</p>"

    headers = rows[0]
    alignment_row = rows[1]
    data_rows = rows[2:]

    expected_cols = len(headers)

    if len(alignment_row) != expected_cols:
        return "<p>" + "<br>".join([token.text for token in block.content]) + "</p>"

    if not all(len(row) == expected_cols for row in data_rows):
        return "<p>" + "<br>".join([token.text for token in block.content]) + "</p>"

    alignment_map = {
        "left": "text-align: left",
        "center": "text-align: center",
        "right": "text-align: right",
    }

    alignment_list = generate_alignment(alignment_row)

    html = "<table><thead><tr>"

    for index, header in enumerate(headers):
        html += f"<th style='{alignment_map[alignment_list[index]]}'>{header}</th>"

    html += "</tr></thead><tbody>"

    for data_row in data_rows:
        html += "<tr>"
        for index, cell in enumerate(data_row):
            html += f"<td style='{alignment_map[alignment_list[index]]}'>{render_inline(cell)}</td>"
        html += "</tr>"


    html += "</tbody></table>"

    return html

RENDERERS = {
    BlockType.HEADING: render_heading,
    BlockType.PARAGRAPH: render_paragraph,
    BlockType.BLOCKQUOTE: render_blockquote,
    BlockType.CODE: render_code,
    BlockType.UNORDERED_LIST: render_list,
    BlockType.ORDERED_LIST: render_list,
    BlockType.HORIZONTAL_RULE: render_horizontal_rule,
    BlockType.TABLE: render_table
}

def render_html(blocks: list[Block]) -> str:
    html = []

    for block in blocks:
        if block and block.content:
            block_html = RENDERERS[block.block_type](block)
            html.append(block_html)

    return ''.join(html)