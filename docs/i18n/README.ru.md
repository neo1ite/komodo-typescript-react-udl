# TypeScript для Komodo 9

[English](../../README.md) | **Русский**

Расширение добавляет поддержку TypeScript и TSX в **Komodo IDE / Komodo Edit 9.3.x**.

Оно переносит практически полезную поддержку TypeScript на старую архитектуру языковых сервисов Komodo 9 и не требует правки файлов самой IDE.

## Возможности

- язык `TypeScript` для `.ts`, `.mts` и `.cts`;
- язык `ReactTypeScript` для `.tsx`;
- подсветка синтаксиса на базе стабильного lexer `SCLEX_CPP` из Komodo;
- folding, комментарии, отступы по скобкам и ключевые слова TypeScript;
- отдельные иконки `TS` и `TSX`;
- диагностика компилятора через TypeScript из проекта;
- поиск ближайшего `tsconfig.json`;
- проверка текущего несохранённого содержимого редактора;
- CodeIntel на базе TypeScript LanguageService начиная с версии 0.3.0:
  - автодополнение;
  - calltips / signature help;
  - Go to Definition.

Внутреннее имя TSX-языка намеренно записано как `ReactTypeScript` без пробела. Старый parser chrome/XPCOM manifest в Komodo 9 воспринимает пробел внутри contract ID как разделитель.

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

Установите XPI через менеджер дополнений Komodo и перезапустите IDE.

При обновлении промежуточной сборки имеет смысл при полностью закрытом Komodo удалить старый startup cache:

```bash
rm -rf ~/.komodoide/9.3/XRE/startupCache
```

## Сборка

Komodo 9 использует собственный Python 2.7. На современных Linux-системах SDK нужно запускать через `mozpython`, не рассчитывая на системную команду `python`:

```bash
KOMODO_HOME="${KOMODO_HOME:-$HOME/Komodo-IDE-9}"

"$KOMODO_HOME/lib/mozilla/mozpython" \
    "$KOMODO_HOME/lib/sdk/bin/koext" build
```

Для простой ZIP/XPI-сборки исходников также имеется `build.sh`.

## Ассоциации языков

```text
.ts, .mts, .cts  -> TypeScript
.tsx             -> ReactTypeScript
```

`ReactTypeScript` зарегистрирован в Komodo как отдельный язык, но использует общий TypeScript lexer. Это позволяет независимо развивать TSX-поддержку, не дублируя основной lexer.

## Архитектура CodeIntel

Старый JavaScript CILE parser Komodo 9 появился раньше современного TypeScript/TSX. Поэтому версия 0.3.0 не пытается разбирать TypeScript как старый JavaScript.

Вместо этого используется схема:

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

Таким образом сохраняется штатный интерфейс Komodo для completion/calltip/definition, а семантический анализ выполняет TypeScript-компилятор проекта.

## Диагностика компилятора

`components/koTypeScriptLinter.py` использует отдельный Node bridge для проверки текущего содержимого редактора. Предпочтителен project-local TypeScript, учитывается ближайший `tsconfig.json`.

## Refactoring

В публичных исходниках Komodo Edit 9 отсутствует IDE-only реализация refactoring service, используемая Komodo IDE 9.3. Семантический слой TypeScript специально отделён от этого компонента: TypeScript-aware rename/refactoring можно подключить после определения точного XPCOM contract из установленной сборки IDE.

CodeIntel от refactoring-компонента не зависит.

## Структура проекта

- `components/` — XPCOM-компоненты языков и linter;
- `pylib/` — LangInfo и интеграция CodeIntel;
- `support/` — Node.js bridges для диагностики и CodeIntel;
- `skin/` — иконки `TS` / `TSX` и оформление языков;
- `content/` — chrome-ресурсы Komodo;
- `test/` — тесты и fixtures.

## Совместимость

Основная целевая и проверенная для интерфейса конфигурация:

- Komodo IDE 9.3.2 build 88191;
- Linux x86_64.

## Лицензия

См. [LICENSE](../../LICENSE).
