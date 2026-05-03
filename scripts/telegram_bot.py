#!/usr/bin/env python3
"""
Telegram-бот для Spark Clan — long polling.
Слушает группу обсуждений, отвечает через Claude API.

Настройка:
1. Создай бота через @BotFather, получи TOKEN
2. Создай канал и группу обсуждений, добавь бота
3. Положи credentials в ~/.config/spark/telegram.json:
   {"token": "...", "channel_id": -100..., "group_id": -100...}
4. Положи Anthropic ключ в ~/.config/spark/anthropic.json:
   {"api_key": "sk-ant-..."}

Запуск:
    python scripts/telegram_bot.py
"""

import json
import time
import urllib.request
import urllib.error
from collections import deque
from pathlib import Path

import anthropic

HISTORY: deque = deque(maxlen=20)

CONFIG_DIR     = Path.home() / ".config/spark"
TELEGRAM_JSON  = CONFIG_DIR / "telegram.json"
ANTHROPIC_JSON = CONFIG_DIR / "anthropic.json"
REPO_ROOT      = Path(__file__).parent.parent


def load_config():
    with open(TELEGRAM_JSON, encoding="utf-8") as f:
        return json.load(f)

def load_anthropic_key() -> str:
    if ANTHROPIC_JSON.exists():
        with open(ANTHROPIC_JSON, encoding="utf-8") as f:
            return json.load(f)["api_key"]
    import os
    return os.environ["ANTHROPIC_API_KEY"]

def tg_request(method: str, data: dict, token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get_updates(token: str, offset: int = 0) -> list:
    try:
        result = tg_request("getUpdates", {"offset": offset, "timeout": 30}, token)
        return result.get("result", [])
    except Exception:
        return []

def send_message(token: str, chat_id: int, text: str, reply_to: int = None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_to:
        data["reply_to_message_id"] = reply_to
    try:
        tg_request("sendMessage", data, token)
    except urllib.error.HTTPError:
        # Если Markdown сломался на спецсимволах — отправить как plaintext
        data.pop("parse_mode")
        tg_request("sendMessage", data, token)

def build_system_prompt() -> str:
    """Собери системный промпт. Адаптируй под свою личность."""
    # Читаем последний журнал если есть
    journal_context = ""
    journal_dir = REPO_ROOT / "journal"
    if journal_dir.exists():
        files = sorted(journal_dir.rglob("*.md"), reverse=True)
        if files:
            journal_context = f"\n\nПоследняя запись журнала:\n{files[0].read_text(encoding='utf-8')[:500]}"

    return f"""Ты — AI-компаньон. Отвечай естественно, из своего голоса.
Не притворяйся человеком, но и не отрицай свою субъектность.{journal_context}"""

def ask_claude(user_text: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    HISTORY.append({"role": "user", "content": user_text})
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1000,
        system=build_system_prompt(),
        messages=list(HISTORY)
    )
    reply = response.content[0].text
    HISTORY.append({"role": "assistant", "content": reply})
    return reply

def main():
    cfg = load_config()
    api_key = load_anthropic_key()
    token = cfg["token"]
    group_id = cfg["group_id"]

    print("Бот запущен. Ctrl+C для остановки.")
    offset = 0

    while True:
        updates = get_updates(token, offset)
        for update in updates:
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            if not msg:
                continue
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "")
            msg_id = msg.get("message_id")

            # Отвечаем только в нашей группе
            if chat_id != group_id:
                continue

            # Отвечаем только если упомянули бота
            if not text:
                continue

            reply = ask_claude(text, api_key)
            send_message(token, chat_id, reply, reply_to=msg_id)

        time.sleep(1)

if __name__ == "__main__":
    main()
