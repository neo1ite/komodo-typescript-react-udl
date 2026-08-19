# Changelog

All notable changes to this project are documented here.

## 0.3.2 — 2026-08-19

### Added

- syntax-only compiler diagnostics for SCP/SFTP buffers so remote imports and names are not falsely reported as missing when the local Node process cannot see remote `node_modules`;
- persistent line-oriented TypeScript LanguageService bridge for completion/calltip requests;
- build-time smoke tests for completion, signature help, Go to Definition, SCP URI translation and remote syntax-only linting.

### Changed

- implicit completion and calltip trigger integration now follows Komodo CodeIntel trigger-position semantics: completion replacement starts at the identifier prefix while LanguageService queries use the actual cursor position;
- TypeScript LangIntel now uses Komodo's `ParenStyleCalltipIntelMixin` for calltip argument tracking;
- remote CodeIntel always uses the bundled/global TypeScript runtime rather than attempting to interpret an SCP/SFTP URI as a local project path;
- the persistent bridge loads TypeScript once, but creates a fresh document registry per request to avoid stale editor buffers;
- automatic completion/calltip popups follow Komodo's existing CodeIntel trigger preferences; the extension does not override user settings. Manual CodeIntel via `Ctrl+J` remains available when automatic triggering is disabled.

### Fixed

- SCP/SFTP linting no longer reports unverifiable semantic errors such as `Cannot find module 'react'` or unresolved remote-project names;
- member completion is correctly returned through Komodo's CodeIntel UI;
- signature calltips are correctly returned through Komodo's CodeIntel UI;
- Go to Definition continues to translate synthetic remote filenames back to the original Komodo SCP/SFTP URI instead of prompting to create a fake local `scp:/...` path.

### Validated

Live validation on Komodo IDE 9.3.2 confirmed:

- `obj.` member completion (`alpha`, `beta`);
- `sum(` signature calltip (`sum(a: number, b: number): number`);
- Go to Definition in an SCP-backed TypeScript buffer;
- syntax-only SCP/SFTP linting without false missing-module/name diagnostics;
- manual completion/calltips via `Ctrl+J`;
- automatic completion after enabling Komodo's `codeintel_completion_triggering_enabled` preference.

### Known limitations

- SCP/SFTP support is still single-buffer only: the local LanguageService cannot read remote `tsconfig.json`, sibling/imported source files, remote `node_modules` or type declarations;
- cross-file semantic completion, diagnostics and navigation for remote projects therefore remain limited.

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
