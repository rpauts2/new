# Warframe Companion

Инструменты-помощники для Warframe: рекомендации по миссиям и варфреймам, поиск наград реликвий, ручной журнал фарма и аналитика личных результатов.

## Текущий статус

Проект в разработке. Советник по миссиям, поиск наград реликвий по локальному JSON и журнал результатов работают локально на Python, без подключения к игре.

## Быстрый запуск

Требуется Python 3.10 или новее. Сторонние Python-пакеты не нужны.

```bash
python warframe_companion/advisor.py --list-missions
python warframe_companion/advisor.py --mission survival
python warframe_companion/relic_advisor.py --data ./relics.json --item "Forma Blueprint"
python warframe_companion/session_log.py add --mission Survival --minutes 5 --frame Nekros --relic "Lith A1" --reward "Forma Blueprint"
python warframe_companion/session_log.py summary
python warframe_companion/session_log.py export-csv --output missions.csv
python -m unittest discover -s warframe_companion/tests -v
```

Для поиска реликвий сначала получи JSON-данные из [WFCD/warframe-drop-data](https://github.com/WFCD/warframe-drop-data) и передай путь через `--data`. Модуль показывает шансы из файла, а не генерирует оценки сам.

## Возможности

- Советник по варфреймам по типу миссии и цели.
- Поиск наград по реликвиям с фильтрами по эпохе, состоянию и точному названию.
- Ручной журнал миссий, подсчёт времени и записанных наград.
- Экспорт результатов в CSV.
- Unit-тесты и GitHub Actions workflow для автоматического запуска тестов.

## Следующие этапы

- Проверить реальные версии источников данных и обработку их схем.
- Добавить сравнение вариантов реликвий с явными вероятностями и ограничениями.
- Улучшить справочник варфреймов и сборок на основе актуальных источников.
- Развить интерфейс-компаньон и упаковку для Windows.

## Принципы

- Статистика основана только на введённых пользователем данных.
- Рекомендации и вероятности зависят от актуальности исходного набора данных.
- Компаньон предназначен для справки и анализа, а не для автономного прохождения миссий или обхода игровых проверок.
- Не храните пароли, токены и другие секреты в репозитории.

## Документация

- [План развития](ROADMAP.md)
- [Аудит исходного репозитория](AUDIT_WARFRAME_AFK_BOT.md)
- [Исследование открытых проектов и источников данных](RESEARCH_OPEN_SOURCE_WARFRAME.md)
- [Инструкция компаньона](warframe_companion/README.md)
