# TypeScript для Komodo 9

[English](../../README.md) | **Русский**

Расширение добавляет поддержку TypeScript и TSX в **Komodo IDE / Komodo Edit 9.3.x**.

Оно переносит практически полезную поддержку TypeScript на старую архитектуру языковых сервисов Komodo 9 и не требует правки файлов самой IDE.

## Возможности

- язык `TypeScript` для `.ts`, `.mts` и `.cts`;
- язык `ReactTypeScript` для `.tsx`;
- подсветка на базе стабильного lexer `SCLEX_CPP` из Komodo;
- folding, комментарии, отступы по скобкам и ключевые слова TypeScript;
- отдельные иконки `TS` и `TSX`;
- диагностика через TypeScript-компилятор проекта;
- поиск ближайшего `tsconfig.json`;
- проверка текущего несохранённого содержимого редактора;
- CodeIntel на базе TypeScript LanguageService начиная с версии 0.3.0:
  - автодополнение;
  - calltips / signature help;
  - Go to Definition;
- интеграция со штатным refactoring UI Komodo IDE для TypeScript и TSX через совместимый слой на базе JavaScript refactoring engine.

Внутреннее имя TSX-языка намеренно записано как `ReactTypeScript` без пробела: старый parser chrome/XPCOM manifest в Komodo 9 воспринимает пробел внутри contract ID как разделитель.

## Идентификатор расширения

Текущий ID:

```text
typescript_language@www.neolite.org
```

Промежуточные сборки до 0.3.0 использовали GUID. Komodo считает новый ID другим расширением, поэтому старую GUID-версию нужно удалить через Add-ons Manager перед установкой текущей. Не следует удалять каталог установленного расширения руками: Mozilla add-on registry может сохранить устаревшие записи.

В 0.3.0 также используется отдельный chrome namespace `neolitetypescript`, чтобы старые регистрации GUID-сборки не могли перехватить ресурсы иконок.

## Требования

Для семантических сервисов нужны Node.js и TypeScript. Предпочтительна локальная зависимость проекта:

```bash
npm install --save-dev typescript
```

Расширение ищет вверх от текущего файла:

```text
node_modules/typescript/lib/typescript.js
```

и использует ближайший `tsconfig.json`, если он существует.

Для одной только подсветки Node.js и TypeScript не требуются.

## Установка

Установите XPI через Add-ons Manager Komodo и перезапустите IDE.

После обновления промежуточной сборки при полностью закрытом Komodo удалите startup cache:

```bash
rm -rf ~/.komodoide/9.3/XRE/startupCache
```

## Сборка

`build.sh` создаёт XPI напрямую и оставляет chrome-ресурсы незапакованными в JAR — это нужно для пользовательских иконок TS/TSX:

```bash
./build.sh
```

По умолчанию XPI создаётся рядом с каталогом исходников; путь назначения можно передать аргументом.

## Ассоциации языков

```text
.ts, .mts, .cts  -> TypeScript
.tsx             -> ReactTypeScript
```

`ReactTypeScript` зарегистрирован как отдельный язык, но использует общий TypeScript lexer. Это позволяет независимо развивать TSX-поддержку без дублирования основного lexer.

## Архитектура CodeIntel

Старый JavaScript CILE parser Komodo 9 появился раньше современного TypeScript/TSX. Поэтому 0.3.0 не пытается разбирать TypeScript как старый JavaScript.

Используется схема:

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

Так сохраняется штатный интерфейс Komodo для completion/calltip/definition, а семантический анализ выполняет TypeScript-компилятор проекта.

CodeIntel bootstrap явно загружает `langinfo_typescript.py` в out-of-process LangInfo database Komodo. Это необходимо, потому что Komodo 9 создаёт базу LangInfo раньше, чем добавляет `pylib` каталог расширения в процесс CodeIntel.

## Диагностика компилятора

`components/koTypeScriptLinter.py` использует отдельный Node bridge для проверки текущего содержимого редактора. Предпочтителен project-local TypeScript, учитывается ближайший `tsconfig.json`.

## Refactoring

Komodo IDE 9 поставляет refactoring отдельным системным расширением `refactoring@activestate.com`. TypeScript-extension регистрирует два IDE contract:

```text
@activestate.com/koRefactoringLanguageService;1?language=TypeScript
@activestate.com/koRefactoringLanguageService;1?language=ReactTypeScript
```

Адаптеры переиспользуют JavaScript refactoring engine Komodo для JavaScript-совместимого TypeScript/TSX-кода. Это включает штатный refactoring UI и устраняет предупреждение `Can't find a refactoring service`. Семантические completion и Go to Definition по-прежнему работают через TypeScript LanguageService; слой refactoring намеренно отделён.

## Структура проекта

- `components/` — XPCOM-компоненты языков, linter и refactoring;
- `pylib/` — LangInfo и интеграция CodeIntel;
- `support/` — Node.js bridges для диагностики и семантического CodeIntel;
- `skin/` — иконки `TS` / `TSX` и оформление языков;
- `test/` — тесты и fixtures.

## Совместимость

Основная целевая конфигурация:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

Подсветка ориентирована также на Komodo Edit 9.3.x. Refactoring adapters полезны только при наличии IDE refactoring extension.

## Лицензия

См. [LICENSE](../../LICENSE).
