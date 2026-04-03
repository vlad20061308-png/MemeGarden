# MemeGarden

Telegram-игра про ферму с магазином, посадкой и сбором урожая.

## Структура

```text
app/
  config.py
  main.py
  handlers/
  services/
  ui/
  utils/
  data/
```

## Запуск

1. Создай и заполни `.env`:
   ```env
   BOT_TOKEN=...
   ```
2. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Запусти бота:
   ```bash
   python -m app.main
   ```
