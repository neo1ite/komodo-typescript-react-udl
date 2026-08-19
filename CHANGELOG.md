# Changelog

All notable changes to this project are documented here.

## 0.3.2 — unreleased

### Added

- syntax-only compiler diagnostics for SCP/SFTP buffers so remote imports and names are not falsely reported as missing when the local Node process cannot see remote `node_modules`;
- persistent line-oriented TypeScript LanguageService bridge for completion/calltip requests;
- build-time smoke tests for completion, signature help, Go to Definition, SCP URI translation and remote syntax-only linting.

### Changed

- implicit completion and calltip trigger integration now follows Komodo CodeIntel trigger-position semantics: completion replacement starts at the identifier prefix while LanguageService queries use the actual cursor position;
- TypeScript LangIntel now uses Komodo's `ParenStyleCalltipIntelMixin` for calltip argument tracking;
- remote CodeIntel always uses the bundled/global TypeScript runtime rather than attempting to interpret an SCP/SFTP URI as a local project path;
- the persistent bridge loads TypeScript once, but creates a fresh document registry per request to avoid stale editor buffers.

### Validation target

Before tagging 0.3.2, verify in Komodo IDE 9.3.2 on both `.ts` and `.tsx`:

- `obj.` shows member completion;
- `sum(` shows a signature calltip;
- Go to Definition still works in local and SCP/SFTP buffers;
- SCP/SFTP linting reports syntax errors but no false `Cannot find module` / unresolved-name diagnostics.

### Deferred to 0.4.0

- remote-project bridge for SCP/SFTP `tsconfig.json`, imported files, remote `node_modules`, type declarations and cross-file semantic navigation.

## 0.3.1 — 2026-08-19

### Added

- self-contained release XPI with bundled TypeScript 5.0.4 LanguageService runtime;
- explicit linter registration for both `TypeScript` and `ReactTypeScript`;
- TypeScript LanguageService bridge for semantic requests;
- Go to Definition support for symbols in the current buffer;
- SCP/SFTP current-buffer support using a synthetic internal filename and translation back to the original Komodo remote URI;
- TypeScript/TSX refactoring service registration through Komodo IDE's JavaScript refactoring engine compatibility layer;
- bilingual documentation (`README.md` + `docs/i18n/README.ru.md`).

### Fixed

- TypeScript LangInfo registration in Komodo's out-of-process CodeIntel;
- `styles.StateMap` registration for TypeScript and ReactTypeScript;
- extension identity changed to the stable `typescript_language@www.neolite.org` ID;
- TypeScript/ReactTypeScript icons and language-menu styling;
- false local-path creation attempts such as `/home/user/scp:/host/...` during Go to Definition on SCP/SFTP files;
- CodeIntel subprocess startup when the original working directory does not exist;
- reproducible build of the bundled TypeScript runtime.

### Known limitations

- completion and calltips/signature help requests exist in the LanguageService bridge but are not yet reliably surfaced through Komodo 9's CodeIntel UI;
- SCP/SFTP linting still performs semantic diagnostics without access to remote dependencies, so messages such as `Cannot find module 'react'` can be false positives;
- SCP/SFTP support is currently single-buffer only: remote `tsconfig.json`, sibling source files and `node_modules` are not available to the local LanguageService;
- cross-file semantic navigation for remote projects is therefore not yet supported.

## 0.3.0

- introduced dedicated `TypeScript` and `ReactTypeScript` language registrations;
- added `.ts`/`.mts`/`.cts` and `.tsx` associations;
- added dedicated TS/TSX icons;
- established the initial TypeScript LanguageService-backed CodeIntel architecture.
