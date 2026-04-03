# MemeGarden

Telegram-игра про ферму: покупка семян, посадка, рост/засыхание растения, сбор урожая, инвентарь и монеты.

## Что уже есть в игре

- Команды: `/start`, `/help`, `/shop`, `/plant`, `/farm`, `/harvest`, `/inventory`, `/balance`
- Антиспам
- Магазин семян и покупка через inline-кнопки
- Посадка семян
- Рост растений (таймер)
- Засыхание/неготовность растения отображается в карточке фермы
- Сбор урожая и начисление монет
- Инвентарь
- Live-обновление карточки фермы кнопкой `🔄 Обновить ферму`
- Сохранение состояния игры в JSON

## Структура проекта

```text
bot.py
app/
  main.py
  config.py
  handlers/
    command_handlers.py
    callback_handlers.py
    deps.py
    router.py
  services/
    anti_spam.py
    game_service.py
  ui/
    cards.py
    keyboards.py
  utils/
    storage.py
    time_utils.py
  data/
    constants.py
    models.py
    storage.py  # shim для обратной совместимости импортов
```

## Установка

1. Создай виртуальное окружение (рекомендуется):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Установи зависимости:

   ```bash
   pip install -r requirements.txt
   ```

## Настройка `.env`

1. Скопируй шаблон:

   ```bash
   cp .env.example .env
   ```

2. Заполни `.env`:

   ```env
   BOT_TOKEN=your_real_bot_token
   DATA_FILE=app/data/game_state.json
   ANTI_SPAM_SECONDS=1.0
   ```

> Важно: `.env.example` — это только шаблон, без реального токена.

## Запуск

Основная команда запуска:

```bash
python -m app.main
```

Альтернативная точка входа:

```bash
python bot.py
```
