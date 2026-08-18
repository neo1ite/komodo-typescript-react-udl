# -*- coding: utf-8 -*-
"""TypeScript and React TypeScript language services for Komodo 9.3.x."""

import logging

from xpcom import components
import styles
from koLanguageServiceBase import (
    KoLanguageBase,
    KoLanguageBaseDedentMixin,
    KoLexerLanguageService,
    FastCharData,
)

log = logging.getLogger("koTypeScriptLanguage")
sci_constants = components.interfaces.ISciMoz

_TYPESCRIPT_KEYWORDS = set("""
abstract any as async await boolean break case catch class const constructor
continue debugger declare default delete do else enum export extends false
finally for from function get if implements import in instanceof interface
is keyof let module namespace never new null number object of package private
protected public readonly require return set static string super switch symbol
this throw true try type typeof undefined unique unknown var void while with
yield
""".split())


class KoTypeScriptLexerLanguageService(KoLexerLanguageService):
    def __init__(self):
        KoLexerLanguageService.__init__(self)
        self.setLexer(sci_constants.SCLEX_CPP)
        self.supportsFolding = 1
        self.setProperty("lexer.cpp.allow.dollars", "1")
        self.setProperty("lexer.cpp.backquoted.strings", "1")
        self.setProperty("fold.cpp.syntax.based", "1")
        self.setKeywords(0, _TYPESCRIPT_KEYWORDS)


class koTypeScriptLanguage(KoLanguageBase, KoLanguageBaseDedentMixin):
    name = "TypeScript"

    _reg_desc_ = "%s Language" % name
    _reg_contractid_ = "@activestate.com/koLanguage?language=%s;1" % name
    _reg_clsid_ = "{2d204ae1-e7c0-4035-85d8-90a78a2cb647}"
    _reg_categories_ = [("komodo-language", name)]
    _com_interfaces_ = KoLanguageBase._com_interfaces_[:]

    primary = 1
    internal = 0
    accessKey = "T"
    defaultExtension = ".ts"
    extraFileAssociations = ["*.mts", "*.cts"]
    modeNames = ["typescript", "ts"]

    commentDelimiterInfo = {
        "line": ["//"],
        "block": [("/*", "*/")],
        "markup": "*",
    }

    supportsSmartIndent = "brace"
    _dedenting_statements = [u"throw", u"return", u"break", u"continue"]

    namedBlockDescription = "TypeScript functions, interfaces and classes"
    namedBlockRE = (
        r"^[ |\t]*?(?:([\w|\.|_]*?)\s*=\s*function|"
        r"function\s*([\w|_]*?)|class\s+([\w|_]+)|"
        r"interface\s+([\w|_]+)).*?$"
    )

    styleStdin = sci_constants.SCE_C_STDIN
    styleStdout = sci_constants.SCE_C_STDOUT
    styleStderr = sci_constants.SCE_C_STDERR

    _stateMap = styles.StateMap["JavaScript"].copy()

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

    def __init__(self):
        KoLanguageBase.__init__(self)
        KoLanguageBaseDedentMixin.__init__(self)

        self._style_info.update(
            _block_comment_styles=[
                sci_constants.SCE_C_COMMENT,
                sci_constants.SCE_C_COMMENTDOC,
                sci_constants.SCE_C_COMMENTDOCKEYWORD,
                sci_constants.SCE_C_COMMENTDOCKEYWORDERROR,
            ],
            _variable_styles=[sci_constants.SCE_C_IDENTIFIER],
        )

        self._setupIndentCheckSoftChar()
        self._fastCharData = FastCharData(
            trigger_char=";",
            style_list=(sci_constants.SCE_C_OPERATOR,),
            skippable_chars_by_style={
                sci_constants.SCE_C_OPERATOR: "])",
            },
            for_check=True,
        )

    def get_lexer(self):
        if self._lexer is None:
            self._lexer = KoTypeScriptLexerLanguageService()
        return self._lexer


class koReactTypeScriptLanguage(koTypeScriptLanguage):
    """TSX mode.

    Komodo 9.3's Scintilla does not have a dedicated TSX lexer.  We therefore
    deliberately reuse the stable TypeScript lexer and register TSX as a
    separate language so file association, UI identity and future TSX-specific
    services can evolve independently without destabilising .ts support.
    """

    name = "React TypeScript"

    _reg_desc_ = "%s Language" % name
    _reg_contractid_ = "@activestate.com/koLanguage?language=%s;1" % name
    _reg_clsid_ = "{7f5c3ab7-3e2d-4b5f-b59d-3a1342c524e0}"
    _reg_categories_ = [("komodo-language", name)]

    accessKey = "R"
    defaultExtension = ".tsx"
    extraFileAssociations = []
    modeNames = ["reacttypescript", "tsx", "typescriptjsx"]

    namedBlockDescription = "React TypeScript functions, components, interfaces and classes"

    sample = """interface Props {
    title: string;
}

export function Header({ title }: Props) {
    return <h1>{title}</h1>;
}
"""


def registerLanguage(registry):
    log.debug("Registering language TypeScript")
    registry.registerLanguage(koTypeScriptLanguage())
    log.debug("Registering language React TypeScript")
    registry.registerLanguage(koReactTypeScriptLanguage())
