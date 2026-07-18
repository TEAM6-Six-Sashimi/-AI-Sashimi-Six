from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


def load_prompt(relative_path: str) -> str:
    prompt_path = BASE_DIR / relative_path

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")