from typing import Protocol

DEFAULT_MODELS = {"gemini": "gemini-3.5-flash", "openai": "gpt-5-mini"}


class LLMError(Exception):
    """Raised when the language model could not produce an answer."""


class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        from google.genai import types

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
        except Exception as exc:
            raise LLMError("The Gemini request failed") from exc

        text = (response.text or "").strip()
        if not text:
            raise LLMError("The model returned an empty answer")
        return text


class OpenAIClient:
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=system_prompt,
                input=user_prompt,
            )
        except Exception as exc:
            raise LLMError("The OpenAI request failed") from exc

        text = (response.output_text or "").strip()
        if not text:
            raise LLMError("The model returned an empty answer")
        return text


def create_llm_client(provider: str, api_key: str, model: str = "") -> LLMClient:
    provider = provider.lower().strip()
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    if not api_key:
        raise ValueError("LLM_API_KEY is not set")

    model = model or DEFAULT_MODELS[provider]
    if provider == "gemini":
        return GeminiClient(api_key, model)
    return OpenAIClient(api_key, model)