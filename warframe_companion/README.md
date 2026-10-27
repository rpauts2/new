# Warframe Companion

Локальный помощник для планирования миссий, поиска наград реликвий и ручного учёта результатов. Не захватывает экран игры, не отправляет игровые нажатия и не автоматизирует прохождение.

## Требования

- Python 3.10+
- Сторонние Python-пакеты не нужны.
- Для графического интерфейса нужен Python со встроенным Tkinter (обычно включён в Windows-установщик с python.org).

## Графический интерфейс Windows

Запусти из корня репозитория:

```bash
python warframe_companion/gui.py
```

В приложении есть три вкладки:
- **Советник:** выбор миссии, цели и исключаемых варфреймов.
- **Реликвии:** поиск награды в локальном JSON, фильтры по эпохе и состоянию, опциональная загрузка набора данных.
- **Журнал:** ручное сохранение результата миссии, статистика и CSV-экспорт.

Данные и журнал остаются на компьютере. Вкладка реликвий обращается к сети только по кнопке загрузки. GUI не управляет игрой.

## Советник по варфреймам

```bash
python warframe_companion/advisor.py --list-missions
python warframe_companion/advisor.py --mission Survival
python warframe_companion/advisor.py --mission Spy --goal stealth --limit 5
python warframe_companion/advisor.py --mission Survival --exclude "Nekros,Nova" --limit 5
python warframe_companion/advisor.py --mission Survival --format json
```

Рекомендации основаны на общих ролях, а не на живом рейтинге меты. Сборка и обновления могут изменить результат. `--exclude` исключает варфреймы, которые у тебя не открыты или которые не хочешь использовать. `--format json` выдаёт структурированный результат для интеграций.

## Поиск наград реликвий

Модуль ищет награды в JSON-файле данных WFCD. Можно использовать `data/relics.json` из [warframe-drop-data](https://github.com/WFCD/warframe-drop-data). В README источника описана схема: каждая запись реликвии содержит эпоху, имя, состояние и список наград с записанными шансами.

```bash
# Разово скачать набор данных в указанный путь и выполнить поиск
python warframe_companion/relic_advisor.py --data ./relics.json --download --item "Forma Blueprint"

# Далее искать по сохранённому файлу без сети
python warframe_companion/relic_advisor.py --data ./relics.json --item "Forma Blueprint"
python warframe_companion/relic_advisor.py --data ./relics.json --item "Prime Part" --tier Axi
python warframe_companion/relic_advisor.py --data ./relics.json --item "Forma Blueprint" --exact
python warframe_companion/relic_advisor.py --data ./relics.json --item "Forma Blueprint" --state Radiant
```

Флаг `--download` загружает `https://raw.githubusercontent.com/WFCD/warframe-drop-data/main/data/relics.json` перед поиском. Скачанный JSON проверяется до замены файла, поэтому некорректный ответ не затрёт существующий кэш. Без `--download` модуль работает офлайн. Модуль не придумывает шансы: он выводит только значения из выбранного файла. При загрузке рядом с JSON сохраняется файл `.meta.json` с URL источника, временем загрузки и HTTP-метаданными (если сервер их отдаёт). При чтении эти сведения показываются вместе с метаданными самого набора.

В репозитории есть небольшой fixture, повторяющий структуру, документированную WFCD. Полный текущий набор данных пока не прошёл сквозную проверку в этой среде, поэтому перед использованием проверь актуальность источника и состояние улучшения реликвии.

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

В сводке дополнительно считается наблюдаемое число записанных наград в час по завершённым сессиям. Это частота твоих ручных записей, а не гарантия игрового дропа и не прогноз будущих результатов. По умолчанию журнал хранится в `~/.warframe_companion/missions.jsonl`. Чтобы использовать другой файл, передай `--log` до подкоманды:

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
