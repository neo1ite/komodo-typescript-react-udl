# -*- coding: utf-8 -*-
"""TypeScript language support for Komodo 9.3.x.

The extension intentionally reuses Komodo's JavaScript/SCLEX_CPP lexer.  This
is the same basic approach ActiveState later used when TypeScript was added to
Komodo itself, but this module is self-contained for the 9.3.x API.

Python 2.7 compatibility is required because Komodo 9 embeds Python 2.
"""

import json
import logging
import os
import re
import sys
import tempfile

from xpcom import components

from koJavaScriptLanguage import koJavaScriptLanguage, KoJavaScriptLexerLanguageService
from koLintResult import KoLintResult
from koLintResults import koLintResults

import koprocessutils
import process
import which


log = logging.getLogger("koTypeScriptLanguage")


# JavaScript keywords plus TypeScript contextual/reserved/type keywords.
# SCLEX_CPP only has one primary keyword set for our purposes; keeping the
# complete set here gives Komodo 9 useful highlighting without a new lexer.
_TYPESCRIPT_KEYWORDS = sorted(set("""
abstract accessor any as asserts async await bigint boolean break case catch
class const constructor continue debugger declare default delete do else enum
export extends false finally for from function get global if implements import
in infer instanceof interface intrinsic is keyof let module namespace never new
null number object of out override package private protected public readonly
require return satisfies set static string super switch symbol this throw true
try type typeof undefined unique unknown using var void while with yield
""".split()))


# Komodo's colour-scheme service indexes style maps by language name.  Komodo
# versions that shipped TypeScript later added exactly such a mapping.  Do the
# equivalent dynamically so no core installation file has to be patched.
def _install_style_map():
    state_map = None
    try:
        from styles import StateMap
        state_map = StateMap
    except Exception:
        try:
            import koScintillaSchemeService
            state_map = koScintillaSchemeService.StateMap
        except Exception:
            log.exception("Unable to import Komodo StateMap for TypeScript")
            return

    if "TypeScript" not in state_map and "JavaScript" in state_map:
        state_map["TypeScript"] = state_map["JavaScript"].copy()


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

    accessKey = "T"
    primary = 1
    modeNames = ["typescript", "ts"]
    defaultExtension = ".ts"
    extraFileAssociations = ["*.tsx", "*.mts", "*.cts"]
    searchURL = "https://www.typescriptlang.org/docs/"

    namedBlockDescription = "TypeScript functions and classes"
    supportsSmartIndent = "brace"

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


def registerLanguage(registry):
    """Compatibility with the language-extension loader used by Komodo 9."""
    try:
        registry.registerLanguage(koTypeScriptLanguage())
    except Exception:
        # Category registration is the normal PyXPCOM path; avoid preventing
        # component loading if the loader already registered the language.
        log.debug("TypeScript language was already registered", exc_info=True)


class KoTypeScriptLinter(object):
    """TypeScript diagnostics backed by the project's TypeScript compiler.

    Preferred mode uses Node + typescript/lib/typescript.js and feeds the live
    editor buffer over stdin, so diagnostics also work before the file is
    saved.  A simpler `tsc` fallback is used when the compiler JS library
    cannot be located.
    """

    _com_interfaces_ = [components.interfaces.koILinter]
    _reg_desc_ = "Komodo TypeScript Compiler Linter"
    _reg_clsid_ = "{96dbeeab-ec85-4f5b-a448-38837a05b3ae}"
    _reg_contractid_ = "@activestate.com/koLinter?language=TypeScript&type=;1"
    _reg_categories_ = [("category-komodo-linter", "TypeScript")]

    def __init__(self):
        try:
            self._user_path = koprocessutils.getUserEnv()["PATH"].split(os.pathsep)
        except Exception:
            self._user_path = None

    def lint(self, request):
        text = request.content.encode(request.encoding.python_encoding_name)
        return self.lint_with_text(request, text)

    def lint_with_text(self, request, text):
        if not text:
            return koLintResults()

        filename = self._document_filename(request)
        cwd = request.cwd or os.path.dirname(filename) or None

        node = self._which("node")
        typescript_js = self._find_typescript_js(filename)
        bridge = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "support", "typescript-bridge.js"))

        if node and typescript_js and os.path.isfile(bridge):
            return self._lint_with_bridge(node, typescript_js, bridge, filename, cwd, text)

        tsc = self._find_tsc(filename)
        if tsc:
            return self._lint_with_tsc(tsc, filename, cwd, text)

        # No compiler is not a source-code error.  Keep the editor quiet and
        # leave a useful trace in Komodo's log instead of underlining line 1.
        log.warning("TypeScript compiler not found; install project-local or global 'typescript'")
        return koLintResults()

    def _document_filename(self, request):
        try:
            ko_file = request.koDoc.file
            if ko_file and ko_file.isLocal and ko_file.encodedPath:
                return ko_file.encodedPath
        except Exception:
            pass

        cwd = request.cwd or tempfile.gettempdir()
        return os.path.join(cwd, "__komodo_unsaved__.ts")

    def _which(self, executable):
        try:
            path = which.which(executable, path=self._user_path)
            if sys.platform.startswith("win") and not os.path.splitext(path)[1]:
                for suffix in (".cmd", ".exe", ".bat"):
                    if os.path.exists(path + suffix):
                        return path + suffix
            return path
        except Exception:
            return None

    def _walk_up(self, start):
        current = os.path.abspath(start)
        while True:
            yield current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

    def _find_tsc(self, filename):
        start = os.path.dirname(os.path.abspath(filename))
        for directory in self._walk_up(start):
            if sys.platform.startswith("win"):
                candidate = os.path.join(directory, "node_modules", ".bin", "tsc.cmd")
            else:
                candidate = os.path.join(directory, "node_modules", ".bin", "tsc")
            if os.path.isfile(candidate):
                return candidate
        return self._which("tsc")

    def _find_typescript_js(self, filename):
        start = os.path.dirname(os.path.abspath(filename))

        # Prefer the project's compiler: it matches package.json/tsconfig and
        # avoids surprising version skew with a global TypeScript installation.
        for directory in self._walk_up(start):
            candidate = os.path.join(directory, "node_modules", "typescript", "lib", "typescript.js")
            if os.path.isfile(candidate):
                return candidate

        tsc = self._find_tsc(filename)
        if not tsc:
            return None

        real_tsc = os.path.realpath(tsc)
        tsc_dir = os.path.dirname(real_tsc)
        cmd_dir = os.path.dirname(tsc)
        candidates = [
            os.path.join(os.path.dirname(tsc_dir), "lib", "typescript.js"),
            os.path.join(tsc_dir, "..", "lib", "typescript.js"),
            os.path.join(cmd_dir, "node_modules", "typescript", "lib", "typescript.js"),
            os.path.join(cmd_dir, "..", "lib", "node_modules", "typescript", "lib", "typescript.js"),
            os.path.join(cmd_dir, "..", "node_modules", "typescript", "lib", "typescript.js"),
        ]
        for candidate in candidates:
            candidate = os.path.abspath(candidate)
            if os.path.isfile(candidate):
                return candidate
        return None

    def _lint_with_bridge(self, node, typescript_js, bridge, filename, cwd, text):
        cmd = [node, bridge, typescript_js, filename]
        env = koprocessutils.getUserEnv()
        try:
            p = process.ProcessOpen(cmd, cwd=cwd, env=env, stdin=process.PIPE)
            stdout, stderr = p.communicate(input=text)
        except Exception:
            log.exception("Unable to run TypeScript compiler bridge")
            return koLintResults()

        if stderr:
            log.debug("TypeScript bridge stderr: %s", stderr)

        try:
            payload = json.loads(stdout or "{}")
        except Exception:
            log.exception("Unable to decode TypeScript diagnostics: %r", stdout)
            return koLintResults()

        if isinstance(payload, dict) and payload.get("fatal"):
            log.warning("TypeScript bridge: %s", payload.get("fatal"))
            return koLintResults()

        diagnostics = payload.get("diagnostics", []) if isinstance(payload, dict) else []
        return self._diagnostics_to_results(diagnostics, text)

    def _diagnostics_to_results(self, diagnostics, text):
        results = koLintResults()
        lines = re.split(r"\r\n|\r|\n", text)
        if not lines:
            lines = [""]

        for diagnostic in diagnostics:
            try:
                line = max(1, int(diagnostic.get("line", 1)))
                column = max(1, int(diagnostic.get("column", 1)))
                end_line = max(line, int(diagnostic.get("endLine", line)))
                end_column = max(column + 1, int(diagnostic.get("endColumn", column + 1)))

                if line > len(lines):
                    line = len(lines)
                    end_line = line
                if end_line > len(lines):
                    end_line = len(lines)

                # Komodo 9's linter rendering behaves best when the range is
                # constrained to the source line.
                line_len = len(lines[line - 1])
                column = min(column, line_len + 1)
                if end_line == line:
                    end_column = min(max(column + 1, end_column), line_len + 1)
                    if end_column <= column:
                        end_column = column + 1
                else:
                    end_column = len(lines[end_line - 1]) + 1

                category = diagnostic.get("category", "error")
                severity = KoLintResult.SEV_ERROR
                if category != "error":
                    severity = KoLintResult.SEV_WARNING

                code = diagnostic.get("code")
                message = diagnostic.get("message", "TypeScript error")
                if code is not None:
                    description = "TS%s: %s" % (code, message)
                else:
                    description = message

                result = KoLintResult()
                result.description = description
                result.severity = severity
                result.lineStart = line
                result.lineEnd = end_line
                result.columnStart = column
                result.columnEnd = end_column
                results.addResult(result)
            except Exception:
                log.exception("Unable to convert TypeScript diagnostic: %r", diagnostic)

        return results

    _tsc_re = re.compile(r"^(.+?)\((\d+),(\d+)\):\s+(error|warning)\s+TS(\d+):\s+(.*)$")

    def _lint_with_tsc(self, tsc, filename, cwd, text):
        suffix = os.path.splitext(filename)[1].lower()
        if suffix not in (".ts", ".tsx", ".mts", ".cts"):
            suffix = ".ts"

        temp_dir = cwd if cwd and os.path.isdir(cwd) and os.access(cwd, os.W_OK) else None
        fd, temp_name = tempfile.mkstemp(prefix=".komodo-ts-", suffix=suffix, dir=temp_dir)
        fout = os.fdopen(fd, "wb")
        try:
            fout.write(text)
        finally:
            fout.close()

        cmd = [tsc, "--noEmit", "--pretty", "false", "--skipLibCheck", temp_name]
        env = koprocessutils.getUserEnv()
        try:
            p = process.ProcessOpen(cmd, cwd=cwd, env=env, stdin=None)
            stdout, stderr = p.communicate()
            output = "\n".join([part for part in (stdout, stderr) if part])
        except Exception:
            log.exception("Unable to run tsc fallback")
            output = ""
        finally:
            try:
                os.unlink(temp_name)
            except OSError:
                pass

        diagnostics = []
        for line in output.splitlines():
            match = self._tsc_re.match(line)
            if not match:
                continue
            reported_file, line_no, column_no, category, code, message = match.groups()
            try:
                same_file = os.path.normcase(os.path.abspath(reported_file)) == os.path.normcase(os.path.abspath(temp_name))
            except Exception:
                same_file = reported_file == temp_name
            if not same_file:
                continue
            diagnostics.append({
                "line": int(line_no),
                "column": int(column_no),
                "endLine": int(line_no),
                "endColumn": int(column_no) + 1,
                "category": category,
                "code": int(code),
                "message": message,
            })

        return self._diagnostics_to_results(diagnostics, text)
