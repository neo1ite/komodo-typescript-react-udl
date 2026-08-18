# TypeScript for Komodo 9

Версия 0.2.1 для Komodo IDE/Edit 9.3.x.

Поддерживаемые режимы:

- `TypeScript`: `.ts`, `.mts`, `.cts`;
- `ReactTypeScript`: `.tsx`.

`ReactTypeScript` намеренно записан без пробела во внутреннем имени:
старый chrome/XPCOM manifest parser Komodo 9.3 разбивает contract ID по
пробелам и не может зарегистрировать язык с пробелом в имени.

Иконки `TS` и `TSX` подключаются как глобальная stylesheet через
`agent-style-sheets`; XUL overlay для этого не требуется.

После обновления рекомендуется полностью закрыть Komodo и удалить
`~/.komodoide/9.3/XRE/startupCache`.
