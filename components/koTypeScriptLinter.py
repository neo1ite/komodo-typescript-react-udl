# -*- coding: utf-8 -*-
"""TypeScript compiler diagnostics for Komodo 9.3.x / Python 2.7.

Kept in a separate component module so a linter dependency can never prevent
the TypeScript language component itself from loading.

Compiler resolution order:
1. project-local node_modules/typescript;
2. compiler bundled into the 0.3.1+ XPI;
3. a global tsc installation.
"""

import json
import logging
import os
import tempfile

from xpcom import components
from koLintResult import KoLintResult
from koLintResults import koLintResults
import koprocessutils
import process
import which

log = logging.getLogger("koTypeScriptLinter")


class _KoTypeScriptLinterBase(object):
    _com_interfaces_ = [components.interfaces.koILinter]

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
        bridge = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "support", "typescript-bridge.js")
        )

        if node and typescript_js and os.path.isfile(bridge):
            return self._lint_with_bridge(
                node, typescript_js, bridge, filename, cwd, text
            )

        log.warning(
            "TypeScript compiler library not found; reinstall the 0.3.1+ "
            "XPI or install project-local 'typescript'"
        )
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
            return which.which(executable, path=self._user_path)
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

    def _extension_root(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _bundled_typescript_js(self):
        candidate = os.path.join(
            self._extension_root(),
            "vendor", "typescript", "lib", "typescript.js"
        )
        return candidate if os.path.isfile(candidate) else None

    def _find_typescript_js(self, filename):
        # Prefer the project's compiler so diagnostics match its build.
        start = os.path.dirname(os.path.abspath(filename))
        for directory in self._walk_up(start):
            candidate = os.path.join(
                directory, "node_modules", "typescript", "lib", "typescript.js"
            )
            if os.path.isfile(candidate):
                return candidate

        bundled = self._bundled_typescript_js()
        if bundled:
            return bundled

        # Compatibility fallback for development/unbundled installs.
        tsc = self._which("tsc")
        if not tsc:
            return None
        real_tsc = os.path.realpath(tsc)
        candidates = [
            os.path.join(os.path.dirname(real_tsc), "..", "lib", "typescript.js"),
            os.path.join(
                os.path.dirname(tsc), "..", "lib", "node_modules",
                "typescript", "lib", "typescript.js"
            ),
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

        try:
            payload = json.loads(stdout or "{}")
        except Exception:
            log.exception("Unable to decode TypeScript diagnostics: %r", stdout)
            return koLintResults()

        results = koLintResults()
        for diagnostic in payload.get("diagnostics", []):
            result = KoLintResult()
            result.description = diagnostic.get("message", "TypeScript error")
            result.severity = result.SEV_ERROR
            result.lineStart = int(diagnostic.get("line", 1))
            result.lineEnd = result.lineStart
            result.columnStart = int(diagnostic.get("column", 1))
            result.columnEnd = max(
                result.columnStart + 1,
                int(diagnostic.get("endColumn", result.columnStart + 1)),
            )
            results.addResult(result)
        return results


class KoTypeScriptLinter(_KoTypeScriptLinterBase):
    _reg_desc_ = "Komodo TypeScript Compiler Linter"
    _reg_clsid_ = "{96dbeeab-ec85-4f5b-a448-38837a05b3ae}"
    _reg_contractid_ = "@activestate.com/koLinter?language=TypeScript;1"
    _reg_categories_ = [("category-komodo-linter", "TypeScript")]


class KoReactTypeScriptLinter(_KoTypeScriptLinterBase):
    _reg_desc_ = "Komodo ReactTypeScript Compiler Linter"
    _reg_clsid_ = "{1ec767a8-930d-41cc-91d8-72566a6ccad3}"
    _reg_contractid_ = "@activestate.com/koLinter?language=ReactTypeScript;1"
    _reg_categories_ = [("category-komodo-linter", "ReactTypeScript")]
