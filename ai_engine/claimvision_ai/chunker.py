def chunk_text(text: str, max_chars: int = 800, overlap: int = 150) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0 or overlap >= max_chars // 2:
        raise ValueError("overlap must be between 0 and half of max_chars")

    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    total = len(text)

    while start < total:
        end = min(start + max_chars, total)

        if end < total:
            search_from = start + int(max_chars * 0.6)
            for separator in ("\n\n", "\n", ". ", " "):
                cut = text.rfind(separator, search_from, end)
                if cut != -1:
                    end = cut + len(separator)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= total:
            break

        next_start = max(end - overlap, start + 1)
        while next_start < end and not text[next_start - 1].isspace():
            next_start += 1
        start = next_start

    return chunks