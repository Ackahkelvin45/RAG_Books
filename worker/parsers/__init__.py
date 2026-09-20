from dataclasses import dataclass, field


@dataclass
class Section:
    """One chapter-like unit of a book. Chunks never cross a Section."""

    text: str
    chapter: int | None = None
    title: str | None = None
    page: int | None = None
    extra: dict = field(default_factory=dict)


@dataclass
class ParsedBook:
    sections: list[Section]
    title: str | None = None
    author: str | None = None
