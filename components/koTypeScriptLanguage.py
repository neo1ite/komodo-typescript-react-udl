# -*- coding: utf-8 -*-
"""Minimal TypeScript language component for Komodo 9.3.x / Python 2.7."""

import logging
from xpcom import components
from koJavaScriptLanguage import (
    koJavaScriptLanguage,
    KoJavaScriptLexerLanguageService,
)

log = logging.getLogger("koTypeScriptLanguage")

_TYPESCRIPT_KEYWORDS = sorted(set("""
abstract accessor any as asserts async await bigint boolean break case catch
class const constructor continue debugger declare default delete do else enum
export extends false finally for from function get global if implements import
in infer instanceof interface intrinsic is keyof let module namespace never new
null number object of out override package private protected public readonly
require return satisfies set static string super switch symbol this throw true
try type typeof undefined unique unknown using var void while with yield
""".split()))


def _install_style_map():
    """Give TypeScript the same Scintilla style mapping as JavaScript."""
    try:
        from styles import StateMap
    except Exception:
        try:
            import koScintillaSchemeService
            StateMap = koScintillaSchemeService.StateMap
        except Exception:
            log.exception("Unable to install TypeScript StateMap")
            return

    if "TypeScript" not in StateMap and "JavaScript" in StateMap:
        StateMap["TypeScript"] = StateMap["JavaScript"].copy()


_install_style_map()


class KoTypeScriptLexerLanguageService(KoJavaScriptLexerLanguageService):
    def __init__(self):
        KoJavaScriptLexerLanguageService.__init__(self)
        self.setKeywords(0, _TYPESCRIPT_KEYWORDS)


class koTypeScriptLanguage(koJavaScriptLanguage):
    name = "TypeScript"
    _reg_desc_ = "%s Language" % name
    _reg_contractid_ = "@activestate.com/koLanguage?language=%s;1" % name
    _reg_clsid_ = "{2d204ae1-e7c0-4035-85d8-90a78a2cb647}"
    _reg_categories_ = [("komodo-language", name)]

    # Explicitly expose the base language interfaces.  This mirrors the
    # approach used by Komodo's external Go language extension and avoids
    # relying on PyXPCOM discovering an inherited registration attribute.
    _com_interfaces_ = koJavaScriptLanguage._com_interfaces_[:]

    primary = 1
    internal = 0
    accessKey = "T"
    defaultExtension = ".ts"
    extraFileAssociations = ["*.tsx", "*.mts", "*.cts"]
    modeNames = ["typescript", "ts"]

    commentDelimiterInfo = {
        "line": ["//"],
        "block": [("/*", "*/")],
        "markup": "*",
    }
    supportsSmartIndent = "brace"
    namedBlockDescription = "TypeScript functions and classes"

    sample = """interface Person {
    name: string;
    age?: number;
}

class Greeter {
    constructor(private person: Person) {}

    greet(): string {
        return `Hello, ${this.person.name}`;
    }
}
"""

    def get_lexer(self):
        if self._lexer is None:
            self._lexer = KoTypeScriptLexerLanguageService()
        return self._lexer


# Compatibility with the pre-category language-extension loader.
def registerLanguage(registry):
    registry.registerLanguage(koTypeScriptLanguage())
