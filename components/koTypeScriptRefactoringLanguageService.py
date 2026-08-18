# -*- coding: utf-8 -*-
"""Komodo IDE 9 refactoring adapters for TypeScript and TSX.

Komodo IDE ships its refactoring implementation as the system extension
`refactoring@activestate.com`.  The public Komodo Edit tree does not include
those components, so load the JavaScript refactoring implementation from the
installed IDE extension at runtime and reuse its well-tested Scintilla-based
logic for the JavaScript-compatible parts of TypeScript/TSX.
"""

import imp
import os

from xpcom import components
import directoryServiceUtils


def _load_javascript_refactoring_module():
    candidates = []
    for extension_dir in directoryServiceUtils.getExtensionDirectories():
        path = os.path.join(
            extension_dir,
            "components",
            "koJavaScriptRefactoringLanguageService.py",
        )
        if os.path.isfile(path):
            candidates.append(path)

    if not candidates:
        raise ImportError(
            "Komodo JavaScript refactoring component was not found; "
            "the TypeScript refactoring adapter requires Komodo IDE's "
            "refactoring@activestate.com extension"
        )

    return imp.load_source(
        "_komodo_javascript_refactoring_for_typescript",
        candidates[0],
    )


_js_refactoring = _load_javascript_refactoring_module()
_BaseJavaScriptRefactoringService = (
    _js_refactoring._KoJavaScriptCommonRefactoringLangSvc
)


class KoTypeScriptRefactoringLanguageService(
        _BaseJavaScriptRefactoringService):
    language_name = "TypeScript"
    _com_interfaces_ = [components.interfaces.koIRefactoringLanguageService]
    _reg_clsid_ = "{58b104f0-0bc8-4b81-a537-178a323c0ff1}"
    _reg_contractid_ = (
        "@activestate.com/koRefactoringLanguageService;1?language=TypeScript"
    )
    _reg_desc_ = "Komodo TypeScript Refactoring Language Service"


class KoReactTypeScriptRefactoringLanguageService(
        _BaseJavaScriptRefactoringService):
    language_name = "ReactTypeScript"
    _com_interfaces_ = [components.interfaces.koIRefactoringLanguageService]
    _reg_clsid_ = "{629881e1-13a9-4524-a4e8-c8da94835487}"
    _reg_contractid_ = (
        "@activestate.com/koRefactoringLanguageService;1?language=ReactTypeScript"
    )
    _reg_desc_ = "Komodo ReactTypeScript Refactoring Language Service"
