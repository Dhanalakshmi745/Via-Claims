import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import settings  # noqa: E402
from claimvision_ai.llm import LLMError, create_llm_client  # noqa: E402


def main() -> None:
    print(f"Provider: {settings.llm_provider}")
    print(f"Model:    {settings.llm_model or '(provider default)'}")
    print(f"API key:  {'set' if settings.llm_api_key else 'MISSING'}")

    try:
        client = create_llm_client(
            settings.llm_provider, settings.llm_api_key, settings.llm_model
        )
        reply = client.generate(
            "You are a test assistant.", "Reply with exactly one word: ready"
        )
    except LLMError as exc:
        print("\nThe request failed.")
        print("Reason:", repr(exc.__cause__))
        sys.exit(1)
    except (ValueError, ImportError) as exc:
        print("\nConfiguration problem:", exc)
        sys.exit(1)

    print(f"\nModel replied: {reply}")
    print("The LLM connection works.")


if __name__ == "__main__":
    main()