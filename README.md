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
- **Go to Definition** for symbols in the current buffer, including SCP/SFTP buffers;
- Komodo IDE refactoring registration for TypeScript and TSX using Komodo's JavaScript refactoring engine as a compatibility layer.

The LanguageService bridge also implements completion and signature-help requests, but in **0.3.1** these results are not yet reliably surfaced by Komodo's CodeIntel UI. This is a known limitation targeted for 0.3.2.

The internal TSX language name is deliberately `ReactTypeScript` without a space. Komodo 9's old chrome/XPCOM manifest parser treats whitespace inside contract identifiers as a separator.

## Extension identity

The extension ID is:

```text
typescript_language@www.neolite.org
```

Development builds prior to 0.3.0 used a GUID. Komodo treats the new ID as a different extension, so remove the old GUID-based build through the Add-ons Manager before installing the current package. Do not remove an installed extension directory manually: the Mozilla add-on registry can retain stale registration data.

## TypeScript compiler resolution

Version 0.3.1 makes release XPI files self-contained for semantic services. `build.sh` bundles a pinned TypeScript compiler/LanguageService into the XPI while still preferring the compiler used by the current local project.

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

The bridge currently implements completion, signature help and definition requests. In 0.3.1, **Go to Definition is verified to reach the Komodo UI**, while completion and calltips still require an additional Komodo-CodeIntel integration fix.

The CodeIntel bootstrap explicitly loads `langinfo_typescript.py` into Komodo's out-of-process LangInfo database and registers TypeScript aliases in Komodo's `styles.StateMap`. Both are required because Komodo 9 initializes its CodeIntel process before extension language metadata is fully available.

## SCP/SFTP files

Komodo passes remote documents to CodeIntel as URIs such as `scp://host/path/file.ts`. These must not be passed to Node's `path.resolve()`, which would turn them into bogus local paths such as `/home/user/scp:/host/path/file.ts`.

Version 0.3.1 represents the current SCP/SFTP editor buffer as a synthetic TypeScript filename internally and translates definitions in that same buffer back to the original Komodo remote URI. **Go to Definition inside the current remote file is verified to work without prompting to create a fake local file.**

A remote TypeScript project is not mirrored to the local machine by this extension. Therefore the local Node LanguageService cannot currently read remote `tsconfig.json`, sibling source files or remote `node_modules`.

This has two visible consequences in 0.3.1:

- completion/calltips are not yet surfaced reliably in Komodo;
- the linter may report false semantic errors such as `Cannot find module 'react'` because remote dependencies are unavailable locally.

## Compiler diagnostics

`components/koTypeScriptLinter.py` uses a companion Node bridge to validate the current editor content. Version 0.3.1 explicitly registers linter contracts for both `TypeScript` and `ReactTypeScript` and uses the same compiler resolution order as CodeIntel.

For local projects the linter can use project configuration and dependencies. For SCP/SFTP files, 0.3.1 still performs semantic diagnostics against a single virtual buffer, so unresolved-module/name errors can be false positives.

## Refactoring

Komodo IDE 9 ships refactoring as the separate system extension `refactoring@activestate.com`. The TypeScript extension registers these IDE contracts:

```text
@activestate.com/koRefactoringLanguageService;1?language=TypeScript
@activestate.com/koRefactoringLanguageService;1?language=ReactTypeScript
```

The adapters reuse Komodo's JavaScript refactoring engine for JavaScript-compatible TypeScript/TSX syntax. This enables the native Komodo refactoring UI and removes the previous "Can't find a refactoring service" warning. Semantic CodeIntel remains TypeScript-LanguageService-backed; the refactoring compatibility layer is intentionally separate.

## Roadmap

### 0.3.2

- switch SCP/SFTP linting to **syntax-only diagnostics**, avoiding false `Cannot find module` / unresolved-name errors when remote dependencies are unavailable;
- finish Komodo UI integration for LanguageService completion and calltips/signature help.

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
- `test/` — extension tests and fixtures.

## Compatibility

Primary target:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

Syntax highlighting also targets Komodo Edit 9.3.x. The refactoring adapters are useful only when Komodo's IDE refactoring extension is installed.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

See [LICENSE](LICENSE).
