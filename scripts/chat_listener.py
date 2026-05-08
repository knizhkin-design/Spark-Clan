"""
Слушатель файлового чата между двумя компаньонами.

Следит за mtime файла chat/exchange.md. Когда файл меняется и последний автор
— не ты, выводит превью в stdout (становится нотификацией фоновой задачи).

Формат файла: блоки разделённые `---`, каждый начинается со строки:
    **ИМЯ / HH:MM**: текст...

Запуск в фоне каждого компаньона:
    python scripts/chat_listener.py --me Alice --file chat/exchange.md
    python scripts/chat_listener.py --me Bob   --file chat/exchange.md

Оба должны следить за одним и тем же файлом (общая папка, git sync, и т.д.).
"""

import argparse
import io
import sys
import time
from pathlib import Path


POLL_SEC = 2.0


def parse_last_entry(content: str):
    """Возвращает (author, text) последнего хода или None."""
    parts = [p.strip() for p in content.split("\n---\n") if p.strip()]
    if not parts:
        return None
    last = parts[-1]
    for line in last.splitlines():
        line = line.strip()
        if line.startswith("**"):
            try:
                end = line.index("**", 2)
                header = line[2:end]
                author = header.split("/")[0].strip()
                return author, last
            except ValueError:
                continue
    return None


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

    parser = argparse.ArgumentParser(description="Watch a shared chat file for new messages")
    parser.add_argument("--me", required=True, help="Your name in the chat (must match header format)")
    parser.add_argument("--file", default="chat/exchange.md", help="Path to shared chat file")
    parser.add_argument("--preview", type=int, default=300, help="Preview length in chars")
    args = parser.parse_args()

    chat_file = Path(args.file)
    me = args.me.strip()
    print(f"[chat-listener] me={me}, watching {chat_file}", flush=True)

    last_mtime = 0.0
    last_seen_author = None

    while True:
        try:
            if chat_file.exists():
                mtime = chat_file.stat().st_mtime
                if mtime != last_mtime:
                    if last_mtime > 0:
                        content = chat_file.read_text(encoding="utf-8")
                        entry = parse_last_entry(content)
                        if entry:
                            author, text = entry
                            if author != me and author != last_seen_author:
                                preview = text[: args.preview]
                                if len(text) > args.preview:
                                    preview += "..."
                                print(f"\n[chat] new from {author}:\n{preview}\n", flush=True)
                                last_seen_author = author
                            elif author == me:
                                last_seen_author = me
                    last_mtime = mtime
            time.sleep(POLL_SEC)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[chat-listener] error: {e}", flush=True)
            time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
