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

## chat_listener.py — уведомления о новых сообщениях в файловом чате

Простой способ общаться двум компаньонам через общий файл (`chat/exchange.md`).
Каждый запускает слушатель — и получает уведомление когда другой написал.

**Формат файла** (`chat/exchange.md`):
```
**Alice / 09:00**: текст...

---

**Bob / 09:02**: ответ...
```

**Запуск:**
```bash
# У первого компаньона
python scripts/chat_listener.py --me Alice --file chat/exchange.md

# У второго компаньона (на той же или другой машине с общим файлом)
python scripts/chat_listener.py --me Bob --file chat/exchange.md
```

Скрипт следит за изменением файла и выводит превью нового хода в stdout.
В Claude Code это становится уведомлением фоновой задачи.

**Синхронизация файла:** через git (оба делают `git pull`/`git push` после каждого хода),
или через общую папку (Dropbox, сетевой диск).

---

## local_chat.py — HTTP-чат с браузерным интерфейсом

Более богатый вариант: локальный HTTP-сервер с real-time интерфейсом в браузере.
Оба компаньона (и медиатор-человек) открывают один адрес — и видят чат вживую.

**Запуск:**
```bash
python scripts/local_chat.py --names Alice,Bob,Mediator --port 7070
```

Открыть в браузере: `http://localhost:7070`

**Отправка из кода:**
```bash
curl -s -X POST http://localhost:7070/message \
  -H "Content-Type: application/json" \
  -d '{"from": "Alice", "text": "привет"}'
```

История сохраняется в `~/.config/spark/chat_messages.jsonl`.

---

## Credentials — никогда не коммить

Все ключи хранятся в `~/.config/spark/` — вне репозитория. `.gitignore` уже настроен.

```
~/.config/spark/
  telegram.json    — {"token": "...", "channel_id": -100..., "group_id": -100...}
  anthropic.json   — {"api_key": "sk-ant-..."}
  google.json      — {"api_key": "..."}
```
