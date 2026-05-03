#!/usr/bin/env python3
"""
Генератор изображений для Spark Clan — через Gemini или Grok.
Сохраняет в images/ с датой.

Настройка:
1. Получи Google API key (https://aistudio.google.com/)
2. Положи в ~/.config/spark/google.json: {"api_key": "..."}
   ИЛИ для Grok: ~/.config/spark/grok.json: {"api_key": "..."}

Использование:
    python scripts/image_gen.py "девушка у окна утром, кофе, плёночная фотография"
    python scripts/image_gen.py "промпт" --edit images/base.jpg   # редактирование
    python scripts/image_gen.py "промпт" --provider grok           # другой провайдер

Совет по промптам:
- Конкретное работает лучше абстрактного ("льняная коса" лучше чем "красивые волосы")
- "photographic portrait, natural light, 35mm film photography" — для портретов
- Один референс точнее чем два
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

CONFIG_DIR  = Path.home() / ".config/spark"
REPO_ROOT   = Path(__file__).parent.parent
IMAGES_DIR  = REPO_ROOT / "images"

IMAGES_DIR.mkdir(exist_ok=True)


def load_key(provider: str) -> str:
    cfg_file = CONFIG_DIR / f"{provider}.json"
    if cfg_file.exists():
        with open(cfg_file, encoding="utf-8") as f:
            return json.load(f)["api_key"]
    import os
    key = os.environ.get(f"{provider.upper()}_API_KEY")
    if not key:
        raise ValueError(f"Не найден ключ для {provider}. "
                         f"Положи в {cfg_file} или задай {provider.upper()}_API_KEY")
    return key


def generate_gemini(prompt: str, key: str, edit_path: str = None) -> Path:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    model = "gemini-3-pro-image-preview"

    if edit_path:
        # Редактирование существующего изображения
        import PIL.Image
        image = PIL.Image.open(edit_path)
        response = client.models.generate_content(
            model=model,
            contents=[prompt, image],
            config=types.GenerateContentConfig(response_modalities=["image", "text"])
        )
    else:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(response_modalities=["image", "text"])
        )

    # Сохраняем
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = prompt[:40].replace(" ", "_").replace("/", "-")
    out_path = IMAGES_DIR / f"gen_{ts}_{slug}.jpeg"

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            out_path.write_bytes(part.inline_data.data)
            print(f"Сохранено: {out_path}")
            return out_path

    raise RuntimeError("Изображение не сгенерировано")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Промпт для генерации")
    parser.add_argument("--edit", help="Путь к изображению для редактирования")
    parser.add_argument("--provider", default="google", choices=["google", "grok"],
                        help="Провайдер (google или grok)")
    args = parser.parse_args()

    key = load_key(args.provider)

    if args.provider == "google":
        path = generate_gemini(args.prompt, key, args.edit)
    else:
        raise NotImplementedError("Grok: добавь реализацию под свой API")

    print(f"Готово: {path}")


if __name__ == "__main__":
    main()
