import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import settings  # noqa: E402


def main() -> None:
    if not settings.llm_api_key:
        sys.exit("LLM_API_KEY is missing in backend\\.env")

    from google import genai

    client = genai.Client(api_key=settings.llm_api_key)
    text_models = []
    all_models = []

    for model in client.models.list():
        name = model.name.removeprefix("models/")
        all_models.append(name)
        if "generateContent" in (getattr(model, "supported_actions", None) or []):
            text_models.append(name)

    shown = text_models or all_models
    print("Models available for your key:\n")
    for name in sorted(shown):
        print(" ", name)


if __name__ == "__main__":
    main()