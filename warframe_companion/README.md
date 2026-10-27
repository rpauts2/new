# Warframe Companion

Локальный помощник для планирования миссий, поиска наград реликвий и ручного учёта результатов. Не захватывает экран игры, не отправляет игровые нажатия и не автоматизирует прохождение.

## Требования

- Python 3.10+
- Сторонние Python-пакеты не нужны.

## Советник по варфреймам

```bash
python warframe_companion/advisor.py --list-missions
python warframe_companion/advisor.py --mission Survival
python warframe_companion/advisor.py --mission Spy --goal stealth --limit 5
```

Рекомендации основаны на общих ролях, а не на живом рейтинге меты. Сборка и обновления могут изменить результат.

## Поиск наград реликвий

Новый модуль ищет награды по локальному JSON-файлу данных WFCD. Можно использовать файл `relics.json` или общий `all.json` из [warframe-drop-data](https://github.com/WFCD/warframe-drop-data). В README источника описаны поля реликвий и вероятности выпадения.

```bash
# Разово скачать актуальный JSON в указанный путь и выполнить поиск
python warframe_companion/relic_advisor.py --data ./relics.json --download --item "Forma Blueprint"

# Дальше можно искать по сохранённому файлу без сети
python warframe_companion/relic_advisor.py --data ./relics.json --item "Forma Blueprint"
python warframe_companion/relic_advisor.py --data ./relics.json --item "Prime Part" --tier Axi
python warframe_companion/relic_advisor.py --data ./relics.json --item "Forma Blueprint" --exact
python warframe_companion/relic_advisor.py --data ./relics.json --item "Forma Blueprint" --state Radiant
```

Флаг `--download` загружает `https://drops.warframestat.us/data/relics.json` перед поиском. Скачанный JSON проверяется до замены файла, поэтому некорректный ответ не затрёт существующий кэш. Без `--download` модуль работает полностью офлайн. Модуль не придумывает шансы: он выводит только значения из выбранного файла. Если формат файла отличается от поддерживаемых вариантов, появится понятная ошибка. Сверяй дату источника и состояние улучшения реликвии, поскольку вероятности отличаются.

Источники:
- Drop tables и реликвии: https://github.com/WFCD/warframe-drop-data
- Предметы, категории и изображения: https://github.com/WFCD/warframe-items
- Официальная Wiki: https://wiki.warframe.com/w/Drop_Tables

## Ручной журнал миссий

```bash
python warframe_companion/session_log.py add --mission Survival --minutes 5 --frame Nekros --relic "Lith A1" --reward "Forma Blueprint"
python warframe_companion/session_log.py add --mission Spy --minutes 4 --failed --notes "Миссия не завершена"
python warframe_companion/session_log.py summary
python warframe_companion/session_log.py export-csv --output missions.csv
```

По умолчанию журнал хранится в `~/.warframe_companion/missions.jsonl`. Чтобы использовать другой файл, передай `--log` до подкоманды:

```bash
python warframe_companion/session_log.py --log ./my-missions.jsonl summary
```

## Тесты

```bash
python -m unittest discover -s warframe_companion/tests -v
```

GitHub Actions запускает этот набор при push и pull request.

## Границы проекта

Компаньон предназначен для справки и анализа результатов, пока игрок сам управляет игровым процессом. Статистика фарма основана только на данных, которые пользователь внёс вручную.
