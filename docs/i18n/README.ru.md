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
- поиск ближайшего `tsconfig.json` для локальных проектов;
- проверка текущего несохранённого содержимого редактора;
- семантический мост к TypeScript LanguageService;
- **Go to Definition** для символов текущего буфера, включая SCP/SFTP;
- регистрация refactoring для TypeScript и TSX через совместимый слой на базе JavaScript refactoring engine Komodo.

Мост LanguageService также реализует запросы completion и signature help, но в **0.3.1** эти результаты пока не выводятся надёжно через UI CodeIntel Komodo. Это известное ограничение, которое планируется исправить в 0.3.2.

Внутреннее имя TSX-языка намеренно записано как `ReactTypeScript` без пробела: старый parser chrome/XPCOM manifest в Komodo 9 воспринимает пробел внутри contract ID как разделитель.

## Идентификатор расширения

Текущий ID:

```text
typescript_language@www.neolite.org
```

Промежуточные сборки до 0.3.0 использовали GUID. Komodo считает новый ID другим расширением, поэтому старую GUID-версию нужно удалить через Add-ons Manager перед установкой текущей. Не следует удалять каталог установленного расширения руками: Mozilla add-on registry может сохранить устаревшие записи.

## Поиск TypeScript-компилятора

Начиная с версии 0.3.1 release-XPI является самодостаточным для семантических сервисов: `build.sh` включает в пакет закреплённую версию TypeScript compiler/LanguageService. При этом для локального проекта его собственный компилятор имеет приоритет.

Порядок поиска во время работы:

1. ближайший project-local `node_modules/typescript/lib/typescript.js` для локального файла;
2. встроенный в XPI `vendor/typescript/lib/typescript.js`;
3. глобальный `tsc` как дополнительный fallback.

Встроенный fallback — **TypeScript 5.0.4**, чтобы расширение оставалось совместимым с Node.js 12.20+, который всё ещё встречается на системах со старым Komodo. Для локальных проектов локальная зависимость TypeScript всё равно предпочтительнее, потому что семантика редактора тогда точно соответствует сборке проекта.

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

Мост реализует completion, signature help и definition-запросы. В 0.3.1 **Go to Definition подтверждённо доходит до UI Komodo**, а completion и calltips ещё требуют дополнительного исправления интеграции с CodeIntel Komodo.

CodeIntel bootstrap явно загружает `langinfo_typescript.py` в out-of-process LangInfo database Komodo и регистрирует TypeScript aliases в `styles.StateMap`. Это необходимо из-за порядка инициализации CodeIntel в Komodo 9.

## Файлы по SCP/SFTP

Komodo передаёт удалённые документы в CodeIntel в виде URI, например `scp://host/path/file.ts`. Такой URI нельзя передавать в Node `path.resolve()`: иначе он превращается в ложный локальный путь вида `/home/user/scp:/host/path/file.ts`.

В версии 0.3.1 текущий SCP/SFTP-буфер внутри TypeScript LanguageService представлен синтетическим именем файла, а определения внутри этого же файла преобразуются обратно в исходный remote URI Komodo. **Go to Definition внутри текущего удалённого файла подтверждённо работает без предложения создать фиктивный локальный файл.**

Расширение пока не зеркалирует удалённый TypeScript-проект на локальную машину. Поэтому локальный Node LanguageService не может читать удалённые `tsconfig.json`, соседние исходники и `node_modules`.

В 0.3.1 это приводит к двум видимым ограничениям:

- completion/calltips пока не выводятся надёжно в Komodo;
- linter может показывать ложные семантические ошибки вроде `Cannot find module 'react'`, потому что удалённые зависимости недоступны локально.

## Диагностика компилятора

`components/koTypeScriptLinter.py` использует отдельный Node bridge для проверки текущего содержимого редактора. В 0.3.1 явно зарегистрированы linter contracts и для `TypeScript`, и для `ReactTypeScript`; используется тот же порядок поиска компилятора, что и в CodeIntel.

Для локальных проектов linter может использовать конфигурацию и зависимости проекта. Для SCP/SFTP-файлов 0.3.1 пока выполняет семантическую диагностику одного виртуального буфера, поэтому ошибки unresolved module/name могут быть ложными.

## Refactoring

Komodo IDE 9 поставляет refactoring отдельным системным расширением `refactoring@activestate.com`. TypeScript-extension регистрирует два IDE contract:

```text
@activestate.com/koRefactoringLanguageService;1?language=TypeScript
@activestate.com/koRefactoringLanguageService;1?language=ReactTypeScript
```

Адаптеры переиспользуют JavaScript refactoring engine Komodo для JavaScript-совместимого TypeScript/TSX-кода. Это включает штатный refactoring UI и устраняет предупреждение `Can't find a refactoring service`. Семантический CodeIntel по-прежнему работает через TypeScript LanguageService; слой refactoring намеренно отделён.

## План развития

### 0.3.2

- переключить SCP/SFTP-linter на **syntax-only diagnostics**, чтобы не показывать ложные `Cannot find module` и unresolved-name ошибки при отсутствии удалённых зависимостей;
- довести интеграцию completion и calltips/signature help с UI CodeIntel Komodo.

### 0.4.0

Планируется полноценный remote-project bridge для SCP/SFTP:

- удалённый `tsconfig.json`;
- соседние/импортируемые исходники;
- удалённые `node_modules` и type declarations;
- межфайловые completion, diagnostics и Go to Definition.

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

## История изменений

См. [CHANGELOG.md](../../CHANGELOG.md).

## Лицензия

См. [LICENSE](../../LICENSE).
