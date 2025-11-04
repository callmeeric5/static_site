import os
from src.textnode import TextNode, TextType
from src.htmlnode import HTMLNode, LeafNode, ParentNode
from src.block import BlockType, block_to_block_type
import re


def text_node_to_html_node(text_node: TextNode):

    if text_node.text_type == TextType.TEXT:
        return LeafNode(value=text_node.text)

    if text_node.text_type == TextType.BOLD:
        return LeafNode(tag="b", value=text_node.text)

    if text_node.text_type == TextType.ITALIC:
        return LeafNode(tag="i", value=text_node.text)

    if text_node.text_type == TextType.CODE:
        return LeafNode(tag="code", value=text_node.text)

    if text_node.text_type == TextType.LINK:
        return LeafNode(tag="a", value=text_node.text, props={"href": text_node.url})

    if text_node.text_type == TextType.IMAGE:
        return LeafNode(
            tag="img", value="", props={"src": text_node.url, "alt": text_node.text}
        )

    raise Exception("above types")


def split_nodes_delimiter(old_nodes, delimiter, text_type):
    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        parts = old_node.text.split(delimiter)
        if len(parts) % 2 == 0:
            raise ValueError(f"Unmatched delimiter: {delimiter}")

        for i, part in enumerate(parts):
            if part == "":
                continue
            if i % 2 == 0:
                new_nodes.append(TextNode(part, TextType.TEXT))
            else:
                new_nodes.append(TextNode(part, text_type))

    return new_nodes


def extract_markdown_images(text):
    return re.findall(r"!\[(.*?)\]\((.*?)\)", text)


def extract_markdown_links(text):
    return re.findall(r"\[(.*?)\]\((.*?)\)", text)


def split_nodes_image(old_nodes):
    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        images = extract_markdown_images(old_node.text)
        if not images:
            new_nodes.append(old_node)
            continue

        text = old_node.text
        for alt, url in images:
            parts = text.split(f"![{alt}]({url})", 1)
            if parts[0]:
                new_nodes.append(TextNode(parts[0], TextType.TEXT))
            new_nodes.append(TextNode(alt, TextType.IMAGE, url))
            text = parts[1]

        if text:
            new_nodes.append(TextNode(text, TextType.TEXT))

    return new_nodes


def split_nodes_link(old_nodes):
    new_nodes = []
    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            new_nodes.append(old_node)
            continue

        links = extract_markdown_links(old_node.text)
        if not links:
            new_nodes.append(old_node)
            continue

        text = old_node.text
        for alt, url in links:
            parts = text.split(f"[{alt}]({url})", 1)
            if parts[0]:
                new_nodes.append(TextNode(parts[0], TextType.TEXT))
            new_nodes.append(TextNode(alt, TextType.LINK, url))
            text = parts[1]

        if text:
            new_nodes.append(TextNode(text, TextType.TEXT))

    return new_nodes


def text_to_textnodes(text):
    nodes = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    return nodes


def markdown_to_blocks(markdown):
    blocks = markdown.split("\n\n")
    ls = []
    for block in blocks:
        block = block.strip()
        if block:
            ls.append(block)
    return ls


def markdown_to_html_node(markdown):
    blocks = markdown_to_blocks(markdown)
    children = []
    for block in blocks:
        html_node = block_to_html_node(block)
        children.append(html_node)
    return ParentNode("div", children, None)


def block_to_html_node(block):
    block_type = block_to_block_type(block)

    if block_type == BlockType.HEADING:
        return heading_to_htmlnode(block)
    elif block_type == BlockType.CODE:
        return code_to_htmlnode(block)
    elif block_type == BlockType.QUOTE:
        return quote_to_htmlnode(block)
    elif block_type == BlockType.UNORDERED_LIST:
        return unorderedlist_to_htmlnode(block)
    elif block_type == BlockType.ORDERED_LIST:
        return orderedlist_to_htmlnode(block)
    else:
        return paragraph_to_html_node(block)


def text_to_children(block):
    text_nodes = text_to_textnodes(block)
    return [text_node_to_html_node(text_node) for text_node in text_nodes]


def heading_to_htmlnode(block):
    level = len(block.split(" ")[0])
    text = block[level + 1 :]
    children = text_to_children(text)
    return ParentNode(tag=f"h{level}", children=children)


def code_to_htmlnode(block):
    text = block.strip("```").strip()
    leaf_node = LeafNode(tag="code", value=text)
    return ParentNode(tag="pre", children=[leaf_node])


def orderedlist_to_htmlnode(block):
    lines = block.split("\n")
    items = [line.split(". ", 1)[1] for line in lines]
    children = [ParentNode(tag="li", children=text_to_children(item)) for item in items]
    return ParentNode(tag="ol", children=children)


def unorderedlist_to_htmlnode(block):
    lines = block.split("\n")
    items = [line[2:] for line in lines]
    children = [ParentNode(tag="li", children=text_to_children(item)) for item in items]
    return ParentNode(tag="ul", children=children)


def quote_to_htmlnode(block):
    lines = block.split("\n")
    quote_text = " ".join(line.lstrip(">").strip() for line in lines)
    children = text_to_children(quote_text)
    return ParentNode(tag="blockquote", children=children)


def paragraph_to_html_node(block):
    text = block.replace("\n", " ")
    children = text_to_children(text)
    return ParentNode(tag="p", children=children)


def extract_title(markdown):
    lines = markdown.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    raise Exception("No h1 header found in markdown")


def generate_page(from_path, template_path, dest_path, base_path):
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")
    with open(from_path) as f:
        markdown = f.read()
    with open(template_path) as f:
        template = f.read()

    html = markdown_to_html_node(markdown).to_html()
    title = extract_title(markdown)

    html_output = template.replace("{{ Title }}", title).replace("{{ Content }}", html)
    html_output = html_output.replace('href="/', 'href="{basepath}').replace('src="/', 'src="{basepath}')

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w") as f:
        f.write(html_output)


def generate_pages_recursive(dir_path_content, template_path, dest_dir_path, base_path):
    for item in os.listdir(dir_path_content):
        item_path = os.path.join(dir_path_content, item)

        if os.path.isfile(item_path) and item.endswith(".md"):
            filename = item.replace(".md", ".html")
            dest_path = os.path.join(dest_dir_path, filename)
            generate_page(item_path, template_path, dest_path,base_path)
        elif os.path.isdir(item_path):
            dest_path = os.path.join(dest_dir_path, item)
            generate_pages_recursive(item_path, template_path, dest_path,base_path)
