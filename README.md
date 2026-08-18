# TypeScript for Komodo IDE/Edit 9.3.x

Версия 0.1.2.

Изменения относительно 0.1.1:
- языковой XPCOM-компонент отделён от линтера;
- язык больше не импортирует process/which/koLint* при загрузке;
- `_com_interfaces_` задан явно, как в официальном komodo-go;
- contract линтера приведён к стандартному виду Komodo;
- сохранены `.ts`, `.tsx`, `.mts`, `.cts`, folding и TypeScript keywords.

После обновления рекомендуется полностью закрыть Komodo и удалить
`~/.komodoide/9.3/XRE/startupCache` перед первым запуском.
