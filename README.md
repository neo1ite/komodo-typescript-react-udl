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
  - Go to Definition.

The internal TSX language name is deliberately `ReactTypeScript` without a space. Komodo 9's old chrome/XPCOM manifest parser treats whitespace inside contract identifiers as a separator.

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

After upgrading an already installed development build, it can be useful to clear the old startup cache while Komodo is closed:

```bash
rm -rf ~/.komodoide/9.3/XRE/startupCache
```

## Building

Komodo 9 uses its bundled Python 2.7 runtime. On current Linux systems, build SDK scripts through `mozpython` rather than relying on a system `python` executable:

```bash
KOMODO_HOME="${KOMODO_HOME:-$HOME/Komodo-IDE-9}"

"$KOMODO_HOME/lib/mozilla/mozpython" \
    "$KOMODO_HOME/lib/sdk/bin/koext" build
```

For a source-only ZIP-style development build, `build.sh` is also provided.

## Language layout

```text
.ts, .mts, .cts  -> TypeScript
.tsx             -> ReactTypeScript
```

`ReactTypeScript` is a separate Komodo language registration, but shares the TypeScript lexer implementation. This keeps `.tsx` association and UI identity independent while avoiding duplicated lexer code.

## CodeIntel architecture

Komodo 9's native JavaScript CILE parser predates modern TypeScript and TSX. Version 0.3.0 therefore does not try to parse TypeScript as old JavaScript.

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

## Compiler diagnostics

`components/koTypeScriptLinter.py` uses the companion Node bridge to validate the current editor content. Project-local TypeScript is preferred, and the nearest `tsconfig.json` is respected.

## Refactoring

The public Komodo Edit 9 source tree does not contain the IDE-only refactoring service implementation used by Komodo IDE 9.3. The TypeScript semantic layer is intentionally kept separate so TypeScript-aware rename/refactoring can be connected to that IDE service once its exact XPCOM contract is known from the installed IDE build.

CodeIntel does not depend on that refactoring component.

## Project layout

- `components/` — Komodo language and linter XPCOM components;
- `pylib/` — LangInfo and CodeIntel integration;
- `support/` — Node.js bridges for compiler diagnostics and semantic CodeIntel;
- `skin/` — `TS` / `TSX` icons and language-menu styling;
- `content/` — Komodo chrome resources;
- `test/` — extension tests and fixtures.

## Compatibility

Primary target and tested UI environment:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

## License

See [LICENSE](LICENSE).
