# TypeScript for Komodo 9

**English** | [Русский](docs/i18n/README.ru.md)

TypeScript and TSX language support for **Komodo IDE / Komodo Edit 9.3.x**.

The extension backports practical TypeScript support to the old Komodo 9 language-service architecture without modifying the Komodo installation itself.

## Features

- `TypeScript` language for `.ts`, `.mts` and `.cts`;
- `ReactTypeScript` language for `.tsx`;
- syntax highlighting based on Komodo's stable `SCLEX_CPP` lexer;
- folding, comments, brace-aware indentation and TypeScript keywords;
- dedicated `TS` and `TSX` icons;
- compiler diagnostics for TypeScript and TSX;
- nearest `tsconfig.json` discovery for local projects;
- diagnostics for the current unsaved editor buffer;
- TypeScript LanguageService-backed semantic bridge;
- completion, signature-help and Go to Definition requests;
- current-buffer semantic support for SCP/SFTP documents;
- Komodo IDE refactoring registration for TypeScript and TSX using Komodo's JavaScript refactoring engine as a compatibility layer.

The internal TSX language name is deliberately `ReactTypeScript` without a space. Komodo 9's old chrome/XPCOM manifest parser treats whitespace inside contract identifiers as a separator.

## Current development version: 0.3.2

0.3.2 focuses on the two gaps left by 0.3.1:

- SCP/SFTP linting now uses **syntax-only diagnostics**, avoiding false `Cannot find module` and unresolved-name errors when remote dependencies are invisible to the local Node process;
- completion and calltips use a persistent TypeScript LanguageService bridge plus corrected Komodo trigger positions so implicit editor requests no longer pay the cost of starting Node and loading TypeScript for every keystroke.

`build.sh` runs bridge smoke tests before creating the XPI. These tests validate backend member completion, signature help, Go to Definition, SCP URI translation and syntax-only remote linting. Live Komodo UI verification is still required before tagging 0.3.2.

## Extension identity

The extension ID is:

```text
typescript_language@www.neolite.org
```

Development builds prior to 0.3.0 used a GUID. Komodo treats the new ID as a different extension, so remove the old GUID-based build through the Add-ons Manager before installing the current package. Do not remove an installed extension directory manually: the Mozilla add-on registry can retain stale registration data.

## TypeScript compiler resolution

Release XPI files are self-contained for semantic services. `build.sh` bundles a pinned TypeScript compiler/LanguageService into the XPI while still preferring the compiler used by the current local project.

Runtime resolution order is:

1. nearest project-local `node_modules/typescript/lib/typescript.js` for local files;
2. bundled `vendor/typescript/lib/typescript.js` from the XPI;
3. a global `tsc` installation as a compatibility fallback.

The bundled fallback is **TypeScript 5.0.4** so the extension remains usable with Node.js 12.20+ installations commonly found alongside older Komodo systems. A project-local TypeScript installation is still preferred for local projects because its semantics exactly match that project's build.

Node.js remains required for LanguageService-backed CodeIntel and compiler diagnostics. Syntax highlighting itself does not require Node.js.

## Installation

Install the XPI through Komodo's Add-ons Manager and restart Komodo.

After upgrading an already installed development build, clear the old startup cache while Komodo is closed:

```bash
rm -rf ~/.komodoide/9.3/XRE/startupCache
```

## Building

```bash
./build.sh
```

The build script:

- resolves or downloads the pinned TypeScript 5.0.4 JavaScript API runtime;
- runs `test/smoke-codeintel.js` against the CodeIntel and linter bridges;
- aborts the build if completion/signature/definition or syntax-only linting smoke tests fail;
- creates `komodo-typescript-9.3.2-<version>.xpi` next to the source tree.

The TypeScript runtime is selected from `TYPESCRIPT_ROOT`, project `node_modules`, global npm, or a temporary npm download in that order. Build-time downloads are not committed to git.

## Language layout

```text
.ts, .mts, .cts  -> TypeScript
.tsx             -> ReactTypeScript
```

`ReactTypeScript` is a separate Komodo language registration, but shares the TypeScript lexer implementation.

## CodeIntel architecture

```text
Komodo CodeIntel UI
        |
        v
pylib/codeintel_typescript.py
        |
        v
persistent support/typescript-codeintel.js process
        |
        v
TypeScript LanguageService
```

The persistent bridge loads the TypeScript runtime once and processes line-oriented JSON requests for completion, signature help and definitions. A fresh TypeScript document registry is created per request so unsaved editor contents cannot become stale between requests.

Komodo trigger integration keeps two cursor positions where needed: `Trigger.pos` identifies the completion prefix that Scintilla should replace, while `query_pos` records the actual TypeScript LanguageService cursor position.

Calltips use Komodo's `ParenStyleCalltipIntelMixin` for argument-region tracking.

## SCP/SFTP files

Komodo passes remote documents to CodeIntel as URIs such as `scp://host/path/file.ts`. The extension represents the current remote editor buffer as a synthetic TypeScript filename internally and translates definitions in that same buffer back to the original Komodo URI.

In 0.3.2 the linter treats SCP/SFTP documents differently from local files:

- **remote:** syntax-only diagnostics;
- **local:** full project-aware TypeScript diagnostics when project files are available.

This deliberately suppresses semantic errors that cannot be verified without access to remote `tsconfig.json`, sibling source files and `node_modules`.

SCP/SFTP CodeIntel remains a **single-buffer** implementation. A local Node LanguageService still cannot read remote imports or type declarations, so project-wide semantic features remain limited.

## Refactoring

Komodo IDE 9 ships refactoring as the separate system extension `refactoring@activestate.com`. The extension registers:

```text
@activestate.com/koRefactoringLanguageService;1?language=TypeScript
@activestate.com/koRefactoringLanguageService;1?language=ReactTypeScript
```

The adapters reuse Komodo's JavaScript refactoring engine for JavaScript-compatible TypeScript/TSX syntax. Semantic CodeIntel remains TypeScript-LanguageService-backed.

## Roadmap

### 0.3.2

- syntax-only SCP/SFTP diagnostics;
- reliable completion and calltip integration in the Komodo UI;
- preserve current-buffer SCP/SFTP Go to Definition.

### 0.4.0

Planned remote-project bridge for SCP/SFTP:

- remote `tsconfig.json`;
- sibling/imported source files;
- remote `node_modules` and type declarations;
- cross-file completion, diagnostics and Go to Definition.

## Project layout

- `components/` — Komodo language, linter and refactoring XPCOM components;
- `pylib/` — LangInfo and CodeIntel integration;
- `support/` — Node.js bridges for diagnostics and semantic CodeIntel;
- `skin/` — `TS` / `TSX` icons and language-menu styling;
- `vendor/` — bundled TypeScript runtime inside built XPI files (generated by `build.sh`, not committed);
- `test/` — extension tests and build-time smoke checks.

## Compatibility

Primary target:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

Syntax highlighting also targets Komodo Edit 9.3.x. The refactoring adapters are useful only when Komodo's IDE refactoring extension is installed.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

See [LICENSE](LICENSE).
