# TypeScript для Komodo 9

[English](../../README.md) | **Русский**

Расширение добавляет поддержку TypeScript и TSX в **Komodo IDE / Komodo Edit 9.3.x**.

Оно переносит практически полезную поддержку TypeScript на старую архитектуру языковых сервисов Komodo 9 без модификации самой IDE.

## Возможности

- язык `TypeScript` для `.ts`, `.mts` и `.cts`;
- язык `ReactTypeScript` для `.tsx`;
- подсветка на базе стабильного lexer `SCLEX_CPP`;
- folding, комментарии, отступы по скобкам и ключевые слова TypeScript;
- отдельные иконки `TS` и `TSX`;
- диагностика компилятора для TypeScript и TSX;
- поиск ближайшего `tsconfig.json` для локальных проектов;
- диагностика текущего несохранённого буфера;
- семантический CodeIntel на базе TypeScript LanguageService;
- completion, signature help и Go to Definition;
- поддержка текущего файла при работе по SCP/SFTP;
- регистрация refactoring-сервисов TypeScript/TSX через совместимый слой штатного JavaScript refactoring engine Komodo IDE.

Внутреннее имя TSX-языка намеренно записано как `ReactTypeScript` без пробела: старый parser chrome/XPCOM manifest Komodo 9 воспринимает пробел внутри contract ID как разделитель.

## Текущая разрабатываемая версия: 0.3.2

0.3.2 закрывает два основных ограничения 0.3.1:

- linter для SCP/SFTP переключён на **только синтаксическую диагностику**, чтобы не показывать ложные `Cannot find module` и ошибки неизвестных имён, когда локальный Node не видит удалённые зависимости;
- completion и calltips переведены на постоянный процесс TypeScript LanguageService и исправленную семантику trigger-позиций Komodo, чтобы не запускать Node и не загружать TypeScript заново на каждый символ.

`build.sh` теперь запускает smoke-тесты до создания XPI. Они проверяют backend completion, signature help, Go to Definition, обратное преобразование SCP URI и syntax-only linting. Перед тегированием 0.3.2 остаётся проверить отображение completion/calltips непосредственно в Komodo 9.3.2.

## Идентификатор расширения

```text
typescript_language@www.neolite.org
```

Промежуточные сборки до 0.3.0 использовали GUID. Старую GUID-версию нужно удалять через Add-ons Manager, а не удалением каталога руками, иначе Mozilla registry может сохранить устаревшие записи.

## TypeScript runtime

Release-XPI самодостаточен для семантических сервисов. Порядок выбора TypeScript:

1. ближайший project-local `node_modules/typescript/lib/typescript.js` для локального файла;
2. встроенный в XPI `vendor/typescript/lib/typescript.js`;
3. глобальный `tsc` как fallback.

Встроенный runtime — **TypeScript 5.0.4**, совместимый с Node.js 12.20+.

Node.js нужен для LanguageService CodeIntel и compiler diagnostics; для одной подсветки он не требуется.

## Установка

Установите XPI через Add-ons Manager и перезапустите Komodo.

После обновления промежуточной сборки при полностью закрытом Komodo удалите startup cache:

```bash
rm -rf ~/.komodoide/9.3/XRE/startupCache
```

## Сборка

```bash
./build.sh
```

Скрипт:

- находит или загружает закреплённый TypeScript 5.0.4;
- запускает `test/smoke-codeintel.js`;
- останавливает сборку, если smoke-тесты completion/signature/definition или remote syntax-only linting не прошли;
- создаёт `komodo-typescript-9.3.2-<version>.xpi` рядом с исходниками.

## Ассоциации

```text
.ts, .mts, .cts  -> TypeScript
.tsx             -> ReactTypeScript
```

## Архитектура CodeIntel

```text
Komodo CodeIntel UI
        |
        v
pylib/codeintel_typescript.py
        |
        v
постоянный support/typescript-codeintel.js
        |
        v
TypeScript LanguageService
```

Постоянный Node-процесс загружает TypeScript один раз и принимает построчные JSON-запросы completion, signature help и definition. При этом для каждого запроса создаётся новый TypeScript document registry, чтобы несохранённый буфер не кэшировался в устаревшем состоянии.

Для completion теперь разделены две позиции: `Trigger.pos` указывает Scintilla начало заменяемого префикса, а `query_pos` — реальную позицию курсора для TypeScript LanguageService.

Calltips используют штатный `ParenStyleCalltipIntelMixin` Komodo.

## SCP/SFTP

Удалённый документ Komodo передаёт как URI вида `scp://host/path/file.ts`. Внутри LanguageService текущий remote-buffer получает синтетическое имя файла, а определение символа внутри этого же буфера преобразуется обратно в исходный URI Komodo.

В 0.3.2:

- **SCP/SFTP:** только синтаксическая диагностика;
- **локальные файлы:** полная project-aware TypeScript diagnostics при наличии файлов проекта.

Это намеренно убирает semantic false positives, которые невозможно проверить без удалённых `tsconfig.json`, соседних файлов и `node_modules`.

CodeIntel для SCP/SFTP пока остаётся **single-buffer**. Локальный Node всё ещё не может читать remote imports и type declarations.

## Refactoring

Расширение регистрирует:

```text
@activestate.com/koRefactoringLanguageService;1?language=TypeScript
@activestate.com/koRefactoringLanguageService;1?language=ReactTypeScript
```

Адаптеры используют JavaScript refactoring engine Komodo для совместимого TypeScript/TSX-синтаксиса. Семантический CodeIntel остаётся на TypeScript LanguageService.

## Roadmap

### 0.3.2

- syntax-only диагностика SCP/SFTP;
- надёжное отображение completion и calltips в UI Komodo;
- сохранение работающего Go to Definition для текущего remote-buffer.

### 0.4.0

Полноценный remote-project bridge:

- удалённый `tsconfig.json`;
- imported/sibling `.ts`/`.tsx`;
- удалённые `node_modules` и `.d.ts`;
- cross-file completion, diagnostics и Go to Definition.

## Структура проекта

- `components/` — XPCOM-компоненты языков, linter и refactoring;
- `pylib/` — LangInfo и CodeIntel;
- `support/` — Node.js bridges;
- `skin/` — иконки `TS` / `TSX`;
- `vendor/` — TypeScript runtime внутри собранного XPI;
- `test/` — тесты и build-time smoke checks.

## Совместимость

Основная целевая конфигурация:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

## История изменений

См. [CHANGELOG.md](../../CHANGELOG.md).

## Лицензия

См. [LICENSE](../../LICENSE).
