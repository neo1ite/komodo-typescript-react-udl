## 0.1.1

Исправлена регистрация XPCOM-компонентов для Komodo 9.3.x:
в XPI добавлены `chrome.manifest` и `components/component.manifest`,
включая `komodo-language-info` для TypeScript и регистрацию linter-компонента.

# TypeScript для Komodo IDE 9.3.2

Backport поддержки TypeScript для старой ветки Komodo 9.3.x без изменения файлов установленной IDE.

## Что поддерживается

- язык `TypeScript` в Komodo;
- автоматическая ассоциация файлов `.ts`, `.tsx`, `.mts`, `.cts`;
- подсветка TypeScript-ключевых слов поверх штатного JavaScript/SCLEX_CPP lexer Komodo 9;
- комментарии, скобки, folding и smart indentation от штатного JavaScript language service;
- диагностика TypeScript непосредственно в редакторе через `koILinter`;
- проверка **несохранённого содержимого буфера** через TypeScript Compiler API;
- автоматическое использование ближайшего `tsconfig.json`;
- приоритет project-local `node_modules/typescript` перед глобальной установкой;
- fallback на `tsc --noEmit`, если библиотеку `typescript.js` найти не удалось.

## Ограничения версии 0.1.0

- CodeIntel Komodo 9 (автодополнение, Go to Definition, Find References) для TypeScript пока не реализован. Для этого нужен отдельный мост к `tsserver`.
- `.tsx` распознаётся и корректно проверяется TypeScript compiler'ом, но подсветка JSX-разметки ограничена возможностями старого `SCLEX_CPP`: TypeScript-часть подсвечивается нормально, JSX не будет столь точным, как в современной IDE.
- Для compiler diagnostics необходим Node.js и пакет `typescript` (локальный в проекте или глобальный).

## Установка

1. В Komodo IDE 9.3.2 открыть менеджер дополнений.
2. Выбрать установку дополнения из файла.
3. Указать `komodo-typescript-9.3.2-0.1.0.xpi`.
4. Перезапустить Komodo.
5. Открыть `test/sample.ts` или любой `.ts` проекта.

После установки в списке языков должен появиться `TypeScript`.

## TypeScript compiler

Рекомендуемый вариант для проекта:

```bash
npm install --save-dev typescript
```

Расширение ищет в первую очередь:

```text
<project>/node_modules/typescript/lib/typescript.js
```

и поднимается вверх по каталогам от текущего файла. Затем проверяется глобальный `tsc` в `PATH`.

Проверить окружение можно командами:

```bash
node --version
tsc --version
```

или для project-local установки:

```bash
./node_modules/.bin/tsc --version
```

## Как устроено

`components/koTypeScriptLanguage.py` регистрирует новый XPCOM language service и linter. Язык наследует штатный `koJavaScriptLanguage` Komodo 9.3.x, но заменяет keyword set на TypeScript и добавляет файловые ассоциации.

Для цветовых схем расширение динамически добавляет:

```python
StateMap["TypeScript"] = StateMap["JavaScript"].copy()
```

Это необходимо старому scheme service Komodo 9, который адресует карты стилей по имени языка.

Для диагностики редактор передаёт актуальное содержимое буфера в `support/typescript-bridge.js`. Мост загружает TypeScript Compiler API, читает ближайший `tsconfig.json`, создаёт compiler host с подменённым содержимым текущего файла и возвращает diagnostics в JSON. Python-компонент преобразует их в `KoLintResult`.

## Удаление

Удаляется как обычное дополнение через менеджер Add-ons; системные файлы Komodo расширение не изменяет.

## Сборка

```bash
./build.sh
```

Результат создаётся в родительском каталоге исходников.
