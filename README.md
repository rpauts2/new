# Warframe Companion

Инструменты-помощники для Warframe: рекомендации по миссиям и варфреймам, поиск наград реликвий, ручной журнал фарма и аналитика личных результатов.

## Быстрый старт

**Графический интерфейс:**
```bash
python warframe_companion/gui.py
```

Требуется Python 3.10+ с Tkinter. Сторонние пакеты для запуска из исходников не нужны.

**Командная строка:**
```bash
python warframe_companion/advisor.py --list-missions
python warframe_companion/advisor.py --mission survival
python warframe_companion/relic_advisor.py --data ./relics.json --item "Forma Blueprint"
python warframe_companion/session_log.py add --mission Survival --minutes 5 --frame Nekros --relic "Lith A1" --reward "Forma Blueprint"
python warframe_companion/session_log.py summary
python warframe_companion/session_log.py export-csv --output missions.csv
python -m unittest discover -s warframe_companion/tests -v
```

## Windows EXE

GitHub Actions собирает приложение для Windows в workflow **Windows desktop build**. Открой вкладку Actions, выбери последний успешный запуск и скачай артефакт `WarframeCompanion-windows-x64`. Артефакт доступен 14 дней после сборки. В репозиторий исполняемый файл не коммитится.

## Возможности

- Советник по варфреймам по типу миссии и цели, с исключением неоткрытых варфреймов.
- Поиск наград по реликвиям с фильтрами по эпохе, состоянию и точному названию.
- Опциональная загрузка JSON-данных и офлайн-поиск в локальном файле.
- Ручной журнал миссий, подсчёт времени и записанных наград.
- Экспорт результатов в CSV.
- Unit-тесты и автоматические проверки в GitHub Actions.

## Данные реликвий

Модуль использует JSON из [WFCD/warframe-drop-data](https://github.com/WFCD/warframe-drop-data). Для загрузки и поиска из командной строки смотри [инструкцию компаньона](warframe_companion/README.md). Шансы берутся из исходного файла, не генерируются приложением. Перед использованием проверь актуальность источника и состояние реликвии.

## Следующие этапы

- Проверить полный актуальный набор данных источника сквозным тестом.
- Улучшить справочник варфреймов и рекомендации на основе проверяемых источников.
- Добавить аналитику эффективности личного фарма по ручным записям.
- Уточнить упаковку и удобство первого запуска на Windows.

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
