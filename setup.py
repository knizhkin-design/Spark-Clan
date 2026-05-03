#!/usr/bin/env python3
"""
Spark Clan — первый запуск.
Создаёт структуру папок, конфиг-заготовки и проверяет зависимости.

Запуск:
    python setup.py
"""

import os
import sys
import json
import shutil
from pathlib import Path

REPO_ROOT   = Path(__file__).parent
CONFIG_DIR  = Path.home() / ".config" / "spark"
IMAGES_DIR  = REPO_ROOT / "images"
JOURNAL_DIR = REPO_ROOT / "journal"


def step(msg: str):
    print(f"\n▸ {msg}")

def ok(msg: str):
    print(f"  ✓ {msg}")

def warn(msg: str):
    print(f"  ! {msg}")


def check_python():
    step("Проверка Python")
    v = sys.version_info
    if v < (3, 10):
        warn(f"Python {v.major}.{v.minor} — рекомендуется 3.10+")
    else:
        ok(f"Python {v.major}.{v.minor}")


def check_claude_code():
    step("Claude Code")
    if shutil.which("claude"):
        ok("claude CLI найден")
    else:
        warn("claude CLI не найден. Установи: https://claude.ai/code")


def create_dirs():
    step("Создание папок")
    for d in [IMAGES_DIR, JOURNAL_DIR, CONFIG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
        ok(str(d))


def create_config_stubs():
    step("Заготовки для credentials (~/.config/spark/)")

    stubs = {
        "anthropic.json": {"api_key": "sk-ant-ЗАМЕНИ_МЕНЯ"},
        "google.json":    {"api_key": "ЗАМЕНИ_МЕНЯ"},
        "telegram.json":  {
            "token":      "ТОКЕН_БОТА",
            "channel_id": "ЗАМЕНИ_МЕНЯ",
            "group_id":   "ЗАМЕНИ_МЕНЯ"
        }
    }

    for fname, content in stubs.items():
        path = CONFIG_DIR / fname
        if path.exists():
            ok(f"{fname} уже есть — не трогаю")
        else:
            path.write_text(json.dumps(content, ensure_ascii=False, indent=2),
                            encoding="utf-8")
            warn(f"{fname} создан — заполни API ключи")


def check_optional_deps():
    step("Опциональные зависимости")

    deps = {
        "anthropic":   "pip install anthropic",
        "google.genai": "pip install google-genai",
        "PIL":         "pip install pillow",
        "chromadb":    "pip install chromadb",
    }

    for module, install_cmd in deps.items():
        try:
            __import__(module.replace(".", "_") if "." in module else module)
            ok(module)
        except ImportError:
            warn(f"{module} не установлен → {install_cmd}")


def print_next_steps():
    print("\n" + "─" * 50)
    print("Готово. Следующие шаги:\n")
    print("1. Заполни CLAUDE.md — опиши кто ты (в квадратных скобках)")
    print("2. Открой в Claude Code: claude .")
    print("3. Начни первый журнал и открой первый виток в lab/")
    print()
    print("Опционально:")
    print(f"  • Заполни {CONFIG_DIR}/anthropic.json для Telegram-бота")
    print(f"  • Заполни {CONFIG_DIR}/google.json для генерации картинок")
    print()
    print("Документация: PHILOSOPHY.md → PROTOCOL.md → CLAUDE.md")
    print("─" * 50)


def main():
    print("Spark Clan — первый запуск\n")
    check_python()
    check_claude_code()
    create_dirs()
    create_config_stubs()
    check_optional_deps()
    print_next_steps()


if __name__ == "__main__":
    main()
