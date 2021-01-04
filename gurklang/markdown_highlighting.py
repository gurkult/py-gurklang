import json
from textwrap import dedent
from typing import Dict, Sequence
from . import parser, ast_parser, ast_tools
from markdown import Extension
from markdown.preprocessors import Preprocessor
from markdown.blockprocessors import BlockProcessor
from xml.etree.ElementTree import Element, tostring as xml_to_string
import re


def get_code_metadata(source: str) -> Dict[str, str]:
    imports = []
    try:
        ast = ast_parser.parse_as_ast(source)
        for i in ast_tools.find_imports(ast):
            imports.append({
                "modules": i.module_name,
                "alias": i.imported_name,
                "name": i.original_name
            })
    except parser.ParseError:
        pass
    return {"data-imports": json.dumps(imports)}


def make_code_block(source: str):
    source = dedent(source)

    # Replace an error (which might highlight incorrectly) with a section comment
    def replacer(m: re.Match):
        return "\n#((bad\n" + "\n".join("# " + line for line in m[0].splitlines())  + "\n#))\n"
    source = re.sub(r"(?:KeyError|Failure)(.|\n)*Type traceback\? for complete Python traceback", replacer, source)

    e1 = Element("pre")
    e = Element("code", {
        "language": "gurklang",
        **get_code_metadata(source)
    })
    e1.append(e)
    section = []
    is_section = False
    section_label = ""
    for t in parser.lex_all(source):
        if t.name == "COMMENT" and t.value.startswith("#(("):
            section_label = t.value[3:].strip()
            is_section = True
        elif t.name == "COMMENT" and t.value.startswith("#))"):
            section_element = Element(
                "span",
                {"class": f"gurklang--section gurklang--section--{section_label}"}
            )
            section_element.extend(section)
            e.append(section_element)

            is_section = False
            section = []

            linebreak = Element("span")
            linebreak.text = "\n"
            e.append(linebreak)
        else:
            extra_classes = ""
            if t.name == "NAME" and t.value in {">>>", "..."}:
                extra_classes += "gurklang--meta"
            token_element = Element(
                "span",
                {"class": f"gurklang--token gurklang--token--{t.name.lower()} {extra_classes}"}
            )
            text = t.value
            if text.endswith("\n") and text != "\n" and t.name == "WHITESPACE":
                text = text[:-1]
            token_element.text = text
            if is_section:
                section.append(token_element)
            else:
                e.append(token_element)
    return e1


class GurklangHighlighter(Preprocessor):
    RE_FENCE_START = r' *\%{3,}gurk(?:repl)? *' # start line, e.g., `   !!!! `
    RE_FENCE_END = r' *\%{3,}\s*'  # last non-blank line, e.g, '!!!\n  \n\n'

    def run(self, lines: Sequence[str]):
        block = []
        output_lines = []
        is_inside_block = False
        for line in lines:
            if re.match(r"%%%gurk(?:repl)?", line.strip()) and not is_inside_block:
                block = []
                is_inside_block = True
            elif line.strip() == "%%%" and is_inside_block:
                source = "\n".join(block)
                s = xml_to_string(make_code_block(source)).decode()
                output_lines.extend(s.splitlines())
                is_inside_block = False
            elif is_inside_block:
                block.append(line)
            else:
                output_lines.append(line)
        return output_lines


class GurklangExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(GurklangHighlighter(md), 'gurklang_highlighting', 175)


def makeExtension(*args, **kwargs):
    return GurklangExtension(*args, **kwargs)
