# Скрипты

Опциональные компоненты. Базовый Spark Clan работает без них.

---

## telegram_bot.py — двусторонний Telegram-канал

Позволяет общаться с компаньоном через Telegram — из телефона, без открытого компьютера.

**Что нужно:**
- Python 3.10+
- `pip install anthropic`
- Telegram-бот (создать через @BotFather)
- Канал + группа обсуждений
- `~/.config/spark/telegram.json` с токеном и ID чатов
- `~/.config/spark/anthropic.json` с API ключом (или `ANTHROPIC_API_KEY`)

**Запуск:**
```bash
python scripts/telegram_bot.py
```

Бот слушает группу обсуждений и отвечает когда его упоминают.

---

## image_gen.py — генерация изображений

Создаёт образы компаньона через Gemini (Google) или другие провайдеры.

**Что нужно:**
- Python 3.10+
- `pip install google-genai pillow`
- Google API key: `~/.config/spark/google.json`

**Использование:**
```bash
# Сгенерировать
python scripts/image_gen.py "девушка у окна, кофе, утро, плёночная фотография"

# Редактировать существующее
python scripts/image_gen.py "та же, но в кафе" --edit images/base.jpg
```

Изображения сохраняются в `images/` с датой и временем.

**Совет:** конкретные детали работают лучше абстрактных. «Льняная коса» лучше чем «красивые волосы».

---

## Credentials — никогда не коммить

Все ключи хранятся в `~/.config/spark/` — вне репозитория. `.gitignore` уже настроен.

```
~/.config/spark/
  telegram.json    — {"token": "...", "channel_id": -100..., "group_id": -100...}
  anthropic.json   — {"api_key": "sk-ant-..."}
  google.json      — {"api_key": "..."}
```
