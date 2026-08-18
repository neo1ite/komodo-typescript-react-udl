# TypeScript for Komodo 9

Версия 0.2.0 для Komodo IDE/Edit 9.3.x.

## Языки

- `TypeScript`: `.ts`, `.mts`, `.cts`
- `React TypeScript`: `.tsx`

`React TypeScript` реализован внутри того же XPI, а не отдельным расширением:
оба режима используют один стабильный TypeScript/Scintilla lexer, но имеют
разные XPCOM language services, файловые ассоциации и иконки.

Komodo 9.3 не содержит отдельного TSX lexer, поэтому JSX-разметка внутри
`.tsx` использует тот же SCLEX_CPP, что и основной TypeScript. Отдельный
режим нужен уже сейчас для корректной идентификации `.tsx` и оставляет
возможность позже подключить TSX-aware parser/language service.

## Иконки

Использованы собственные Komodo-style плашки `TS` и `TSX`, а не официальные
брендовые логотипы. Это намеренно: официального логотипа "React TypeScript"
нет, а единый визуальный стиль лучше соответствует Komodo 9.

## Установка

Установить XPI через Add-ons и перезапустить Komodo.
При обновлении со старой версии при необходимости удалить:
`~/.komodoide/9.3/XRE/startupCache`.
