# Warframe Companion

Локальный помощник для планирования миссий и ручного учёта результатов. Не захватывает экран игры, не отправляет игровые нажатия и не автоматизирует прохождение.

## Требования

- Python 3.10+
- Сторонние Python-пакеты не нужны.

## Советник по варфреймам

```bash
python warframe_companion/advisor.py --list-missions
python warframe_companion/advisor.py --mission Survival
python warframe_companion/advisor.py --mission Spy --goal stealth --limit 5
```

Рекомендации основаны на общих ролях, а не на живом рейтинге меты. Сборка, модификаторы миссии, состав отряда и обновления могут изменить результат.

## Ручной журнал миссий

Запись результата (все поля кроме миссии и времени необязательны):

```bash
python warframe_companion/session_log.py add --mission Survival --minutes 5 --frame Nekros --relic "Lith A1" --reward "Forma Blueprint"
python warframe_companion/session_log.py add --mission Spy --minutes 4 --failed --notes "Миссия не завершена"
python warframe_companion/session_log.py summary
python warframe_companion/session_log.py export-csv --output missions.csv
```

По умолчанию журнал хранится в `~/.warframe_companion/missions.jsonl`. Чтобы использовать другой файл, передайте `--log` **до** подкоманды, например:

```bash
python warframe_companion/session_log.py --log ./my-missions.jsonl summary
```

Журнал хранится локально. Записи добавляются вручную, поэтому статистика отражает только то, что было внесено. Экспорт CSV открывается в табличных редакторах.

## Тесты

```bash
python -m unittest discover -s warframe_companion/tests -v
```

## Данные и источники

Каталог ролей советника пока является стартовым и должен проверяться по актуальным источникам:
- Миссии: https://wiki.warframe.com/w/Mission
- Ротации наград: https://wiki.warframe.com/w/AABC
- Предметы и варфреймы: https://github.com/WFCD/warframe-items

Проект предназначен для справки и анализа личных результатов, пока игрок сам управляет игровым процессом.
