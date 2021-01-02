import fnl
import json
from textwrap import dedent
from typing import Dict
from . import parser, ast_parser, ast_tools
from xml.etree.ElementTree import Element, tostring as xml_to_string
from context_manager_patma import match
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
    source = dedent(source.strip())

    # Replace an error (which might highlight incorrectly) with a section comment
    def replacer(m: re.Match):
        return "\n#((bad\n" + "\n".join("# " + line for line in m[0].splitlines())  + "\n#))\n"
    source = re.sub(r"(?:ValueError|RuntimeError|KeyError|Failure)(.|\n)*"
                    r"Type traceback\? for complete Python traceback", replacer, source)

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


######################################################


__extension__ = {}


@fnl.definitions.fn(__extension__, "gurklang")
def highlight():
    def _highlight(string: fnl.e.String):
        xml = make_code_block(string.value.strip())
        html = xml_to_string(xml).decode()
        return fnl.e.BlockRaw(html)
    yield ("(λ str . block)", _highlight)


@fnl.definitions.fn(__extension__, "b$")
def concat_block():
    """
    Concatenate multiple elements, producing a block element
    """
    def from_mixed(*args):
        return fnl.e.BlockConcat(args)
    yield ("(λ ...any . block)", from_mixed)


@fnl.definitions.fn(__extension__, "math")
def math_inline():
    def _math_inline(string: fnl.e.String):
        text = "$" + string.value + "$"
        return fnl.e.InlineTag("span", 'class="math-inline"', (fnl.e.InlineRaw(text),))
    yield ("(λ str . inline)", _math_inline)


@fnl.definitions.fn(__extension__, "math-display")
def math_display():
    def _math_display(string: fnl.e.String):
        text = "!!" + string.value + "!!"
        return fnl.e.BlockTag("div", 'class="math-display"', (fnl.e.BlockRaw(text),))
    yield ("(λ str . block)", _math_display)


@fnl.definitions.fn(__extension__, "adm")
def admonition():
    def _admonition(qname: fnl.e.Quoted, *blocks: fnl.e.Entity):

        with match(qname) as case:
            with case("Quoted(Name(name))") as [m]:
                name: str = m.name

        return fnl.e.BlockTag(
            "div",
            f'class="admonition adm-{name.lower()}"',
            (
                fnl.e.BlockTag(
                    "div", 'class="admonition-icon"', ()
                ),
                fnl.e.BlockTag(
                    "div", 'class="admonition-title"', (fnl.e.String(name.title()),)
                ),
                fnl.e.BlockTag(
                    "div", 'class="admonition-body"', blocks
                ),
            )
        )
    yield ("(λ &[name] ...any . block)", _admonition)
