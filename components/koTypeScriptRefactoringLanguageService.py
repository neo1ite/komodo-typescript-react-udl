# -*- coding: utf-8 -*-
"""Komodo IDE 9 refactoring adapters for TypeScript and TSX.

Komodo IDE ships its refactoring implementation as the system extension
`refactoring@activestate.com`. Load the JavaScript refactoring implementation
from that extension at runtime and reuse its Scintilla-based logic for the
JavaScript-compatible parts of TypeScript/TSX.
"""

import imp
import os

from xpcom import components
import directoryServiceUtils


def _candidate_javascript_refactoring_paths():
    seen = set()

    # Normal path: enumerate enabled extension directories from XRE.
    for extension_dir in directoryServiceUtils.getExtensionDirectories():
        path = os.path.join(
            extension_dir,
            "components",
            "koJavaScriptRefactoringLanguageService.py",
        )
        if path not in seen:
            seen.add(path)
            yield path

    # Robust fallback for Komodo IDE 9: its refactoring extension pylib is
    # already on sys.path, even on installations where XREExtDL enumeration
    # does not expose the bundled extension at component-registration time.
    try:
        import koRefactoringLanguageServiceBase
    except ImportError:
        pass
    else:
        pylib_dir = os.path.dirname(
            os.path.abspath(koRefactoringLanguageServiceBase.__file__)
        )
        extension_dir = os.path.dirname(pylib_dir)
        path = os.path.join(
            extension_dir,
            "components",
            "koJavaScriptRefactoringLanguageService.py",
        )
        if path not in seen:
            yield path


def _load_javascript_refactoring_module():
    for path in _candidate_javascript_refactoring_paths():
        if not os.path.isfile(path):
            continue
        return imp.load_source(
            "_komodo_javascript_refactoring_for_typescript",
            path,
        )

    raise ImportError(
        "Komodo JavaScript refactoring component was not found; "
        "the TypeScript refactoring adapter requires Komodo IDE's "
        "refactoring@activestate.com extension"
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
