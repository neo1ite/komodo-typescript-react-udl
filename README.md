# TypeScript for Komodo 9

**English** | [Русский](docs/i18n/README.ru.md)

TypeScript and TSX language support for **Komodo IDE / Komodo Edit 9.3.x**.

The extension backports a practical TypeScript editing experience to the old Komodo 9 language-service architecture without modifying the Komodo installation itself.

## Features

- `TypeScript` language for `.ts`, `.mts` and `.cts`;
- `ReactTypeScript` language for `.tsx`;
- syntax highlighting based on Komodo's stable `SCLEX_CPP` lexer;
- folding, comments, brace-aware indentation and TypeScript keywords;
- dedicated `TS` and `TSX` icons;
- compiler diagnostics for both TypeScript and TSX;
- nearest `tsconfig.json` discovery;
- diagnostics for the current unsaved editor buffer;
- TypeScript LanguageService-backed CodeIntel:
  - completion;
  - calltips / signature help;
  - Go to Definition;
- Komodo IDE refactoring integration for TypeScript and TSX using Komodo's JavaScript refactoring engine as a compatibility layer.

The internal TSX language name is deliberately `ReactTypeScript` without a space. Komodo 9's old chrome/XPCOM manifest parser treats whitespace inside contract identifiers as a separator.

## Extension identity

The extension ID is:

```text
typescript_language@www.neolite.org
```

Development builds prior to 0.3.0 used a GUID. Komodo treats the new ID as a different extension, so remove the old GUID-based build through the Add-ons Manager before installing the current package. Do not remove an installed extension directory manually: the Mozilla add-on registry can retain stale registration data.

## TypeScript compiler resolution

Version 0.3.1 makes release XPI files self-contained for semantic services. `build.sh` bundles a pinned TypeScript compiler/LanguageService into the XPI while still preferring the compiler used by the current project.

Runtime resolution order is:

1. nearest project-local `node_modules/typescript/lib/typescript.js`;
2. bundled `vendor/typescript/lib/typescript.js` from the XPI;
3. a global `tsc` installation as a compatibility fallback.

This means users no longer have to add TypeScript to every project just to enable Komodo CodeIntel. A project-local TypeScript installation is still preferred because its semantics exactly match that project's build.

Node.js remains required for LanguageService-backed CodeIntel and compiler diagnostics. Syntax highlighting itself does not require Node.js.

## Installation

Install the XPI through Komodo's Add-ons Manager and restart Komodo.

After upgrading an already installed development build, clear the old startup cache while Komodo is closed:

```bash
rm -rf ~/.komodoide/9.3/XRE/startupCache
```

## Building

`build.sh` creates the XPI directly, keeps chrome resources unjarred, and bundles a fallback TypeScript LanguageService:

```bash
./build.sh
```

The script uses, in order:

- `TYPESCRIPT_ROOT` when explicitly supplied;
- `node_modules/typescript` in this source tree;
- global npm TypeScript;
- otherwise npm downloads the pinned TypeScript version into a temporary build directory.

The downloaded/build-time copy is not committed to the repository. The release XPI contains only the required `vendor/typescript` runtime payload.

The script writes the package next to the source directory unless an output path is supplied.

## Language layout

```text
.ts, .mts, .cts  -> TypeScript
.tsx             -> ReactTypeScript
```

`ReactTypeScript` is a separate Komodo language registration, but shares the TypeScript lexer implementation. This keeps `.tsx` association and UI identity independent while avoiding duplicated lexer code.

## CodeIntel architecture

Komodo 9's native JavaScript CILE parser predates modern TypeScript and TSX. The extension therefore does not parse TypeScript as old JavaScript.

Instead:

```text
Komodo CodeIntel UI
        |
        v
pylib/codeintel_typescript.py
        |
        v
support/typescript-codeintel.js
        |
        v
TypeScript LanguageService
```

This preserves Komodo's completion/calltip/definition UI while delegating semantic analysis to TypeScript LanguageService.

The CodeIntel bootstrap explicitly loads `langinfo_typescript.py` into Komodo's out-of-process LangInfo database and registers TypeScript aliases in Komodo's `styles.StateMap`. Both are required because Komodo 9 initializes its CodeIntel process before extension language metadata is fully available.

## Compiler diagnostics

`components/koTypeScriptLinter.py` uses the companion Node bridge to validate the current editor content. Version 0.3.1 explicitly registers linter contracts for both `TypeScript` and `ReactTypeScript` and uses the same compiler resolution order as CodeIntel.

## Refactoring

Komodo IDE 9 ships refactoring as the separate system extension `refactoring@activestate.com`. The TypeScript extension registers these IDE contracts:

```text
@activestate.com/koRefactoringLanguageService;1?language=TypeScript
@activestate.com/koRefactoringLanguageService;1?language=ReactTypeScript
```

The adapters reuse Komodo's JavaScript refactoring engine for JavaScript-compatible TypeScript/TSX syntax. This enables the native Komodo refactoring UI and removes the previous "Can't find a refactoring service" warning. Semantic completion and Go to Definition remain TypeScript-LanguageService-backed; the refactoring compatibility layer is intentionally separate.

## Project layout

- `components/` — Komodo language, linter and refactoring XPCOM components;
- `pylib/` — LangInfo and CodeIntel integration;
- `support/` — Node.js bridges for diagnostics and semantic CodeIntel;
- `skin/` — `TS` / `TSX` icons and language-menu styling;
- `vendor/` — bundled TypeScript runtime inside built XPI files (generated by `build.sh`, not committed);
- `test/` — extension tests and fixtures.

## Compatibility

Primary target:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

Syntax highlighting also targets Komodo Edit 9.3.x. The refactoring adapters are useful only when Komodo's IDE refactoring extension is installed.

## License

See [LICENSE](LICENSE).
