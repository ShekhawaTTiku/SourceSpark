"""Match extracted passages despite harmless document typography and wrapping."""

import re


_TYPOGRAPHY = str.maketrans({
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl",
})
# Only unwrap hyphenated words, never numerical ranges or minus signs.
_WRAPPED_WORD = re.compile(r"(?<=[^\W\d_])-\r?\n[ \t]*(?=[^\W\d_])")


def _normalized(text: str) -> tuple[str, list[tuple[int, int]]]:
    """Retain offsets so a tolerant match can recover the exact original passage."""
    skipped = {index for match in _WRAPPED_WORD.finditer(text)
               for index in range(match.start(), match.end())}
    characters: list[str] = []
    offsets: list[tuple[int, int]] = []
    for index, original in enumerate(text):
        if index in skipped or original == "\u00ad":
            continue
        for character in original.translate(_TYPOGRAPHY):
            if character.isspace():
                if not characters:
                    continue
                if characters[-1] == " ":
                    offsets[-1] = (offsets[-1][0], index + 1)
                    continue
                character = " "
            characters.append(character)
            offsets.append((index, index + 1))
    if characters and characters[-1] == " ":
        characters.pop()
        offsets.pop()
    return "".join(characters), offsets


def source_passage(excerpt: str, source: str) -> str | None:
    """Return original text, without relaxing words, numbers, units or negations."""
    if not excerpt.strip():
        return None
    if excerpt in source:
        return excerpt
    needle, _ = _normalized(excerpt)
    if not needle:
        return None
    haystack, offsets = _normalized(source)
    start = haystack.find(needle)
    if start < 0:
        return None
    return source[offsets[start][0]:offsets[start + len(needle) - 1][1]]
