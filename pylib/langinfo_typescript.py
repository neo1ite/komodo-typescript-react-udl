# -*- coding: utf-8 -*-
"""LangInfo definitions for TypeScript support in Komodo 9."""

from langinfo import LangInfo


_KEYWORDS = set("""
abstract any as async await boolean break case catch class const constructor
continue debugger declare default delete do else enum export extends false
finally for from function get if implements import in instanceof interface is
keyof let module namespace never new null number object of package private
protected public readonly require return set static string super switch symbol
this throw true try type typeof undefined unique unknown var void while with
yield
""".split())


class TypeScriptLangInfo(LangInfo):
    name = "TypeScript"
    conforms_to_bases = ["JavaScript", "Text"]
    exts = [".ts", ".mts", ".cts"]
    default_encoding = "utf-8"
    keywords = _KEYWORDS


class ReactTypeScriptLangInfo(LangInfo):
    name = "ReactTypeScript"
    conforms_to_bases = ["TypeScript", "JavaScript", "Text"]
    exts = [".tsx"]
    default_encoding = "utf-8"
    keywords = _KEYWORDS
    is_minor_variant = TypeScriptLangInfo
