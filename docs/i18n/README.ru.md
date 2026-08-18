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
- диагностика компилятора для TypeScript и TSX;
- поиск ближайшего `tsconfig.json`;
- проверка текущего несохранённого содержимого редактора;
- CodeIntel на базе TypeScript LanguageService:
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

## Поиск TypeScript-компилятора

Начиная с версии 0.3.1 release-XPI является самодостаточным для семантических сервисов: `build.sh` включает в пакет закреплённую версию TypeScript compiler/LanguageService. При этом компилятор текущего проекта имеет приоритет.

Порядок поиска во время работы:

1. ближайший project-local `node_modules/typescript/lib/typescript.js`;
2. встроенный в XPI `vendor/typescript/lib/typescript.js`;
3. глобальный `tsc` как дополнительный fallback.

Поэтому для работы CodeIntel больше не требуется добавлять TypeScript-зависимость в каждый проект. Локальная зависимость проекта всё равно предпочтительнее, потому что семантика редактора тогда точно соответствует сборке проекта.

Node.js остаётся необходимым для CodeIntel на базе LanguageService и диагностики компилятора. Для одной только подсветки Node.js не требуется.

## Установка

Установите XPI через Add-ons Manager Komodo и перезапустите IDE.

После обновления промежуточной сборки при полностью закрытом Komodo удалите startup cache:

```bash
rm -rf ~/.komodoide/9.3/XRE/startupCache
```

## Сборка

`build.sh` создаёт XPI напрямую, оставляет chrome-ресурсы незапакованными в JAR и добавляет fallback TypeScript LanguageService:

```bash
./build.sh
```

Скрипт использует по порядку:

- явно заданный `TYPESCRIPT_ROOT`;
- `node_modules/typescript` в каталоге исходников расширения;
- глобальный TypeScript из npm;
- если ничего не найдено, npm загружает закреплённую версию TypeScript во временный каталог сборки.

Загруженная build-time копия не коммитится в репозиторий. В готовый XPI попадает только runtime-каталог `vendor/typescript`.

По умолчанию XPI создаётся рядом с каталогом исходников; путь назначения можно передать аргументом.

## Ассоциации языков

```text
.ts, .mts, .cts  -> TypeScript
.tsx             -> ReactTypeScript
```

`ReactTypeScript` зарегистрирован как отдельный язык, но использует общий TypeScript lexer. Это позволяет независимо развивать TSX-поддержку без дублирования основного lexer.

## Архитектура CodeIntel

Старый JavaScript CILE parser Komodo 9 появился раньше современного TypeScript/TSX, поэтому расширение не пытается разбирать TypeScript как старый JavaScript.

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

Так сохраняется штатный интерфейс Komodo для completion/calltip/definition, а семантический анализ выполняет TypeScript LanguageService.

CodeIntel bootstrap явно загружает `langinfo_typescript.py` в out-of-process LangInfo database Komodo и регистрирует TypeScript aliases в `styles.StateMap`. Это необходимо из-за порядка инициализации CodeIntel в Komodo 9.

## Диагностика компилятора

`components/koTypeScriptLinter.py` использует отдельный Node bridge для проверки текущего содержимого редактора. В 0.3.1 явно зарегистрированы linter contracts и для `TypeScript`, и для `ReactTypeScript`; используется тот же порядок поиска компилятора, что и в CodeIntel.

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
- `vendor/` — встроенный TypeScript runtime внутри собранного XPI (создаётся `build.sh`, в git не хранится);
- `test/` — тесты и fixtures.

## Совместимость

Основная целевая конфигурация:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

Подсветка ориентирована также на Komodo Edit 9.3.x. Refactoring adapters полезны только при наличии IDE refactoring extension.

## Лицензия

См. [LICENSE](../../LICENSE).
