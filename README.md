# MemeGarden

Telegram-игра про ферму: покупка семян, посадка, рост/засыхание растения, сбор урожая, инвентарь и монеты.

## Что уже есть в игре

- Команды: `/start`, `/menu`, `/help`, `/shop`, `/plant`, `/farm`, `/harvest`, `/inventory`, `/tools`, `/balance`, `/level`
- Dev-команды (только при `DEV_MODE=true` и для `DEV_USER_IDS`): `/dev_ready`, `/dev_ready_one`, `/dev_wilt`, `/dev_balance_set`, `/dev_balance_add`, `/dev_balance_take`, `/dev_state`
- Мягкий антиспам с разделением по типам действий (command/nav/heavy) и редкими предупреждениями
- Магазин семян и покупка через inline-кнопки
- Посадка семян
- Рост растений (таймер)
- Засыхание/неготовность растения отображается в карточке фермы
- Сбор урожая и начисление монет
- Система XP и уровней (авто-ап уровня и авто-награды)
- Инвентарь
- Live-обновление карточки фермы кнопкой `🔄 Обновить ферму`
- Главное меню как игровой хаб: постоянная Reply-клавиатура + inline-навигация внутри экранов
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
   DEV_MODE=false
   DEV_USER_IDS=123456789
   ```

> Важно: `.env.example` — это только шаблон, без реального токена.

### Про антиспам

`ANTI_SPAM_SECONDS` задаёт окно защиты от реального флуда.  
Обычные нажатия/переходы через UI дополнительно регулируются мягкими кулдаунами, а предупреждение `Не так быстро` показывается дозированно, чтобы не раздражать пользователя.

## Запуск

Основная команда запуска:

```bash
python -m app.main
```

Альтернативная точка входа:

```bash
python bot.py
```


## Интерфейс

- Нижняя Reply-клавиатура разделов: `🚜 Ферма`, `🏪 Рынок`, `🎒 Рюкзак`, `👤 Профиль`, `⚙️ Настройки`.
- Внутри экранов используются Inline-кнопки действий и навигации.
- Action-кнопки динамические: если действие недоступно, кнопка показывает `❌` до нажатия (например, `❌ Ускорить`).
