"""A shared result keeps format readers independent of workspace state."""

from dataclasses import dataclass, field
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from config import settings


class ExtractionError(ValueError):
    """The upload could not provide usable, traceable source material."""


def canonical_content(locations: dict[str, str]) -> str:
    """The inspector, saved workspace and generation use exactly these blocks."""
    return "\n\n".join(f"[{location}]\n{text}" for location, text in locations.items())


@dataclass
class ExtractionResult:
    """Readable evidence indexed by stable human-readable source locations."""

    locations: dict[str, str]
    warnings: list[str] = field(default_factory=list)
    _characters: int = field(init=False, repr=False, default=0)

    def __post_init__(self) -> None:
        self._characters = len(canonical_content(self.locations))

    def add_location(self, location: str, text: str) -> None:
        """Stop extraction before an oversized source can build an unbounded context."""
        # DocumentRecord normalizes outer whitespace in location values. Do it
        # before assembling content too, so a table's empty trailing cell cannot
        # make the canonical content disagree with its validated locations.
        text = text.strip()
        if not text:
            return
        if len(self.locations) >= 10_000:
            raise ExtractionError("Source has too many evidence locations. Split it into smaller documents.")
        new_size = self._characters + len(location) + len(text) + 3 + (2 if self.locations else 0)
        if new_size > settings.MAX_CONTEXT_CHARACTERS:
            raise ExtractionError(
                f"Extracted source exceeds the {settings.MAX_CONTEXT_CHARACTERS:,}-character evidence limit. "
                "Split or reduce the document; extraction was stopped rather than truncated."
            )
        self.locations[location] = text
        self._characters = new_size

    @property
    def content(self) -> str:
        return canonical_content(self.locations)

    def require_readable(self) -> "ExtractionResult":
        if not any(text.strip() for text in self.locations.values()):
            raise ExtractionError("No readable source content was found. Try another document or export selectable text.")
        if len(self.warnings) > 1000:
            raise ExtractionError("Source has too many extraction warnings. Split it into smaller documents and review unreadable sections.")
        return self


def check_office_archive(file_bytes: bytes) -> None:
    """Office files are ZIP containers; reject excessive expansion before parsing."""
    try:
        with ZipFile(BytesIO(file_bytes)) as archive:
            if sum(member.file_size for member in archive.infolist()) > settings.MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ExtractionError("This Office document expands beyond the extraction limit. Split it into smaller documents.")
            if any(member.flag_bits & 1 for member in archive.infolist()):
                raise ExtractionError("Encrypted Office archives are unsupported. Upload an unlocked copy.")
    except BadZipFile as exc:
        raise ExtractionError("This Office file is corrupt or is not a valid DOCX/XLSX archive.") from exc
