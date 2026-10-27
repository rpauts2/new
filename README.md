# Warframe Companion

Инструменты-помощники для Warframe: рекомендации по миссиям и варфреймам, справочные данные, ручной журнал фарма и аналитика личных результатов.

## Текущий статус

Проект находится в разработке. Советник и журнал миссий работают локально на Python, без подключения к игре.

## Быстрый запуск

Требуется Python 3.10 или новее. Сторонние Python-пакеты не нужны.

```bash
python warframe_companion/advisor.py --list-missions
python warframe_companion/advisor.py --mission survival
python warframe_companion/advisor.py --mission spy --goal stealth
python warframe_companion/session_log.py add --mission Survival --minutes 5 --frame Nekros --relic "Lith A1" --reward "Forma Blueprint"
python warframe_companion/session_log.py summary
python warframe_companion/session_log.py export-csv --output missions.csv
python -m unittest discover -s warframe_companion/tests -v
```

Чтобы использовать альтернативный файл журнала, передай путь до подкоманды: `python warframe_companion/session_log.py --log ./missions.jsonl summary`. По умолчанию записи сохраняются в `~/.warframe_companion/missions.jsonl`.

## Что уже есть

- Советник по варфреймам по типу миссии и цели.
- Прозрачные совпавшие роли и объяснение рекомендации.
- Ручной журнал миссий в JSONL.
- Сводка длительности, числа миссий и записанных наград.
- Экспорт журнала в CSV.
- Unit-тесты и GitHub Actions workflow для автоматического запуска тестов.

## Что дальше

- Проверить и улучшить каталог варфреймов по актуальным источникам.
- Подключить поддерживаемые данные предметов и реликвий, не полагаясь на придуманные значения.
- Добавить советник по реликвиям и вероятностям наград.
- После этого развивать оверлей, статистику и упаковку для Windows.

## Принципы

- Статистика основана только на введённых пользователем данных.
- Рекомендации не являются гарантией результата и должны учитывать обновления игры.
- Компаньон предназначен для справки и анализа, а не для автономного прохождения миссий или обхода игровых проверок.
- Не храните пароли, токены и другие секреты в репозитории.

## Документация

- [План развития](ROADMAP.md)
- [Аудит исходного репозитория](AUDIT_WARFRAME_AFK_BOT.md)
- [Исследование открытых проектов и источников данных](RESEARCH_OPEN_SOURCE_WARFRAME.md)
- [Инструкция компаньона](warframe_companion/README.md)
