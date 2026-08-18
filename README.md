# TypeScript for Komodo 9 — 0.1.3

Минимальная автономная сборка language service.

- нет зависимости от `koJavaScriptLanguage`;
- нет линтера и Node.js-моста;
- только штатные `KoLanguageBase`, `KoLexerLanguageService` и `SCLEX_CPP`;
- JavaScript StateMap переиспользуется напрямую;
- поддерживаются `.ts`, `.tsx`, `.mts`, `.cts`.
