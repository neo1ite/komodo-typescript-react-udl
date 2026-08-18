# -*- coding: utf-8 -*-
"""TypeScript / TSX CodeIntel for Komodo 9.3.x.

Komodo 9's JavaScript CILE parser predates modern TypeScript. This module
keeps the CodeIntel UI/protocol but delegates semantic completion, calltips
and definitions to the project TypeScript LanguageService through Node.js.
"""

import json
import logging
import os
import subprocess

import SilverCity
from SilverCity.Lexer import Lexer
from SilverCity import ScintillaConstants

from codeintel2.buffer import Buffer
from codeintel2.common import *
from codeintel2.langintel import LangIntel

try:
    import which
except ImportError:
    which = None

try:
    from xpcom.server import UnwrapObject
    _xpcom_ = True
except ImportError:
    _xpcom_ = False

log = logging.getLogger("codeintel.typescript")


_TYPESCRIPT_KEYWORDS = sorted(set("""
abstract any as async await boolean break case catch class const constructor
continue debugger declare default delete do else enum export extends false
finally for from function get if implements import in instanceof interface
is keyof let module namespace never new null number object of package private
protected public readonly require return set static string super switch symbol
this throw true try type typeof undefined unique unknown var void while with
yield
""".split()))

_KIND_MAP = {
    "method": "function",
    "function": "function",
    "constructor": "function",
    "class": "class",
    "interface": "interface",
    "enum": "enum",
    "module": "module",
    "external module name": "module",
    "var": "variable",
    "let": "variable",
    "const": "variable",
    "property": "variable",
    "getter": "variable",
    "setter": "variable",
    "parameter": "variable",
    "type": "type",
    "type parameter": "type",
    "keyword": "keyword",
    "alias": "variable",
}


def _walk_up(start):
    current = os.path.abspath(start)
    while True:
        yield current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent


def _which(executable):
    if which is not None:
        try:
            return which.which(executable)
        except Exception:
            pass
    path = os.environ.get("PATH", "")
    for directory in path.split(os.pathsep):
        candidate = os.path.join(directory, executable)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _find_typescript_js(filename):
    start = os.path.dirname(os.path.abspath(filename))
    for directory in _walk_up(start):
        candidate = os.path.join(
            directory, "node_modules", "typescript", "lib", "typescript.js"
        )
        if os.path.isfile(candidate):
            return candidate

    tsc = _which("tsc")
    if not tsc:
        return None

    real_tsc = os.path.realpath(tsc)
    candidates = [
        os.path.abspath(os.path.join(
            os.path.dirname(real_tsc), "..", "lib", "typescript.js"
        )),
        os.path.abspath(os.path.join(
            os.path.dirname(tsc), "..", "lib", "node_modules",
            "typescript", "lib", "typescript.js"
        )),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def _bridge_path():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "support", "typescript-codeintel.js")


def _buffer_text(buf):
    text = buf.accessor.text
    if isinstance(text, unicode):
        return text
    try:
        return text.decode("utf-8")
    except Exception:
        return text.decode("utf-8", "replace")


def _call_bridge(buf, action, pos):
    node = _which("node")
    typescript_js = _find_typescript_js(buf.path)
    bridge = _bridge_path()

    if not node:
        raise RuntimeError("Node.js was not found in PATH")
    if not typescript_js:
        raise RuntimeError(
            "TypeScript compiler library was not found; "
            "install project-local 'typescript'"
        )
    if not os.path.isfile(bridge):
        raise RuntimeError("TypeScript CodeIntel bridge is missing: %s" % bridge)

    payload = json.dumps({
        "action": action,
        "file": buf.path,
        "text": _buffer_text(buf),
        "pos": int(pos),
    })

    proc = subprocess.Popen(
        [node, bridge, typescript_js],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(os.path.abspath(buf.path)) or None,
        env=os.environ.copy(),
    )
    stdout, stderr = proc.communicate(payload.encode("utf-8"))
    if not stdout:
        raise RuntimeError(stderr or "TypeScript CodeIntel bridge returned no data")

    result = json.loads(stdout.decode("utf-8"))
    if result.get("error"):
        raise RuntimeError(result["error"])
    return result


def _ensure_langinfo(mgr):
    """Load extension LangInfo before registering CodeIntel lexers.

    Komodo's out-of-process CodeIntel manager receives extension pylib paths
    after its default LangInfo database has already been created. Therefore an
    extension's langinfo_*.py can be absent from mgr.lidb even though its
    codeintel_*.py has been discovered. Load this pylib explicitly.
    """
    missing = []
    for lang in ("TypeScript", "ReactTypeScript"):
        try:
            mgr.lidb.langinfo_from_lang(lang)
        except Exception:
            missing.append(lang)

    if not missing:
        return

    pylib_dir = os.path.dirname(os.path.abspath(__file__))
    mgr.lidb._load_dir(pylib_dir)

    for lang in missing:
        mgr.lidb.langinfo_from_lang(lang)


class _TypeScriptLexer(Lexer):
    lang = "TypeScript"

    def __init__(self, mgr):
        self._properties = SilverCity.PropertySet()
        self._lexer = SilverCity.find_lexer_module_by_id(
            ScintillaConstants.SCLEX_CPP
        )
        self._keyword_lists = [
            SilverCity.WordList(" ".join(_TYPESCRIPT_KEYWORDS)),
            SilverCity.WordList(),
            SilverCity.WordList(),
            SilverCity.WordList(),
            SilverCity.WordList(),
        ]


class _ReactTypeScriptLexer(_TypeScriptLexer):
    lang = "ReactTypeScript"


class _TypeScriptBuffer(Buffer):
    cb_show_if_empty = True
    cpln_stop_chars = " ()*-=+<>{}[]^&|;:'\",?~`!@#%\\/"

    def defn_trg_from_pos(self, pos, lang=None):
        return Trigger(lang or self.lang, TRG_FORM_DEFN,
                       "definition", pos, False)

    def defns_from_trg(self, trg, timeout=None, ctlr=None):
        self.async_eval_at_trg(trg, ctlr)
        ctlr.wait(timeout)
        if not ctlr.is_done():
            ctlr.done("timed out")
            raise EvalTimeout("eval for %s timed-out" % trg)
        return ctlr.defns


class TypeScriptBuffer(_TypeScriptBuffer):
    lang = "TypeScript"


class ReactTypeScriptBuffer(_TypeScriptBuffer):
    lang = "ReactTypeScript"


class _TypeScriptLangIntel(LangIntel):
    def trg_from_pos(self, buf, pos, implicit=True, DEBUG=False, ac=None):
        if pos < 1:
            return None

        accessor = buf.accessor
        ch = accessor.char_at_pos(pos - 1)

        if ch == ".":
            return Trigger(self.lang, TRG_FORM_CPLN, "members", pos, implicit)
        if ch == "(":
            return Trigger(self.lang, TRG_FORM_CALLTIP,
                           "signature", pos, implicit)

        if ch.isalnum() or ch in "_$":
            start = pos - 1
            while start > 0:
                prev = accessor.char_at_pos(start - 1)
                if not (prev.isalnum() or prev in "_$"):
                    break
                start -= 1
            if pos - start >= 2:
                return Trigger(self.lang, TRG_FORM_CPLN,
                               "names", pos, implicit)
        return None

    def preceding_trg_from_pos(self, buf, pos, curr_pos,
                               preceding_trg_terminators=None, DEBUG=False):
        if curr_pos < 0:
            return None
        return Trigger(self.lang, TRG_FORM_CPLN, "names", curr_pos, False)

    def async_eval_at_trg(self, buf, trg, ctlr):
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)

        ctlr.start(buf, trg)
        try:
            if trg.form == TRG_FORM_CPLN:
                result = _call_bridge(buf, "completion", trg.pos)
                cplns = []
                seen = set()
                for item in result.get("completions", []):
                    name = item.get("name")
                    if not name or name in seen:
                        continue
                    seen.add(name)
                    kind = _KIND_MAP.get(item.get("kind"), "variable")
                    cplns.append((kind, name))
                ctlr.set_cplns(cplns)
                ctlr.done("success")
                return

            if trg.form == TRG_FORM_CALLTIP:
                result = _call_bridge(buf, "signature", trg.pos)
                ctlr.set_calltips(result.get("calltips", []))
                ctlr.done("success")
                return

            if trg.form == TRG_FORM_DEFN:
                result = _call_bridge(buf, "definition", trg.pos)
                defns = []
                for item in result.get("definitions", []):
                    path = item.get("file")
                    if not path:
                        continue
                    name = item.get("name") or os.path.basename(path)
                    kind = _KIND_MAP.get(item.get("kind"), "variable")
                    defns.append(Definition(
                        self.lang,
                        path,
                        os.path.basename(path),
                        [name],
                        name,
                        int(item.get("line") or 1),
                        kind,
                        None,
                        None,
                        None,
                        None,
                        None,
                    ))
                ctlr.set_defns(defns)
                ctlr.done("success")
                return

            ctlr.error("Unsupported TypeScript trigger: %r" % (trg,))
            ctlr.done("error")
        except Exception, exc:
            log.exception("TypeScript CodeIntel evaluation failed")
            ctlr.error(str(exc))
            ctlr.done("error")


class TypeScriptLangIntel(_TypeScriptLangIntel):
    lang = "TypeScript"


class ReactTypeScriptLangIntel(_TypeScriptLangIntel):
    lang = "ReactTypeScript"


def register(mgr):
    _ensure_langinfo(mgr)

    mgr.set_lang_info(
        "TypeScript",
        silvercity_lexer=_TypeScriptLexer(mgr),
        buf_class=TypeScriptBuffer,
        langintel_class=TypeScriptLangIntel,
        import_handler_class=None,
        cile_driver_class=None,
        is_cpln_lang=True,
    )
    mgr.set_lang_info(
        "ReactTypeScript",
        silvercity_lexer=_ReactTypeScriptLexer(mgr),
        buf_class=ReactTypeScriptBuffer,
        langintel_class=ReactTypeScriptLangIntel,
        import_handler_class=None,
        cile_driver_class=None,
        is_cpln_lang=True,
    )
