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
- compiler diagnostics through the project TypeScript compiler;
- nearest `tsconfig.json` discovery;
- diagnostics for the current unsaved editor buffer;
- TypeScript LanguageService-backed CodeIntel in version 0.3.0:
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

Version 0.3.0 also uses a dedicated chrome package namespace (`neolitetypescript`) so stale development registrations from the old GUID build cannot shadow the current icon resources.

## Requirements

For semantic TypeScript services install Node.js and TypeScript. A project-local TypeScript installation is preferred:

```bash
npm install --save-dev typescript
```

The extension searches upward from the current file for:

```text
node_modules/typescript/lib/typescript.js
```

and uses the nearest `tsconfig.json` when present.

Syntax highlighting itself does not require Node.js or TypeScript.

## Installation

Install the XPI through Komodo's Add-ons Manager and restart Komodo.

After upgrading an already installed development build, clear the old startup cache while Komodo is closed:

```bash
rm -rf ~/.komodoide/9.3/XRE/startupCache
```

## Building

`build.sh` creates the XPI directly and keeps chrome resources unjarred, which is required for the custom TS/TSX language icons:

```bash
./build.sh
```

The script writes the package next to the source directory unless an output path is supplied.

## Language layout

```text
.ts, .mts, .cts  -> TypeScript
.tsx             -> ReactTypeScript
```

`ReactTypeScript` is a separate Komodo language registration, but shares the TypeScript lexer implementation. This keeps `.tsx` association and UI identity independent while avoiding duplicated lexer code.

## CodeIntel architecture

Komodo 9's native JavaScript CILE parser predates modern TypeScript and TSX. Version 0.3.0 therefore does not parse TypeScript as old JavaScript.

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

This preserves Komodo's completion/calltip/definition UI while delegating semantic analysis to the TypeScript compiler used by the project.

The CodeIntel bootstrap explicitly loads `langinfo_typescript.py` into Komodo's out-of-process LangInfo database. This is necessary because Komodo 9 creates that database before extension `pylib` directories are added to the CodeIntel process.

## Compiler diagnostics

`components/koTypeScriptLinter.py` uses the companion Node bridge to validate the current editor content. Project-local TypeScript is preferred, and the nearest `tsconfig.json` is respected.

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
- `test/` — extension tests and fixtures.

## Compatibility

Primary target:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

Syntax highlighting also targets Komodo Edit 9.3.x. The refactoring adapters are useful only when Komodo's IDE refactoring extension is installed.

## License

See [LICENSE](LICENSE).
