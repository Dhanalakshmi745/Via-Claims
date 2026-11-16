import hashlib
import math
import re


class HashingEmbedder:
    """Offline stand-in for the real embedding model, for tests and demos only.

    It hashes words into a fixed-size vector, so texts that share words get
    similar vectors. No model download or internet is needed.
    """

    def __init__(self, dims: int = 128):
        self.dims = dims

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dims
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dims
            vector[bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class FakeLLM:
    """Stand-in for a real language model: returns a fixed reply and records the prompts."""

    def __init__(self, reply: str = "The documents mention this [1]."):
        self.reply = reply
        self.calls: list[tuple[str, str]] = []

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self.reply