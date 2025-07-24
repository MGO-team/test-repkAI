import logging

from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

import pdftotext

from config import INITIAL_PDF_CHUNK_SIZE, CHUNK_OVERLAPS, MIN_PDF_TEXT_LENGTH


logger = logging.getLogger(__name__)


class PdfReadingError(Exception):
    pass


@dataclass
class Chunk:
    """
    Dataclass to store patent data chunk
    """

    start: int
    end: int
    text: str = field(repr=False)
    has_binding_info: bool = False
    tags: list[str] = field(default_factory=list)
    compounds: list[str] = field(default_factory=list)
    connected_objs: list[Any] = field(default_factory=list)


@dataclass
class Patent:
    """
    Dataclass to store patent data
    """

    name: str
    country: str
    local_path: Path
    has_binding_info: bool = False
    is_too_short: bool = False
    full_text: str = field(default="", repr=False)
    full_text_len: int = 0
    n_pages: int = 0
    chunks: list[str] = field(default_factory=list, repr=False)
    chunk_size: int = INITIAL_PDF_CHUNK_SIZE
    chunk_overlaps: int = CHUNK_OVERLAPS

    def __post_init__(self):
        text_len = len(self.full_text)
        self.full_text_len = text_len
        size = self.chunk_size
        overlaps = max(1, self.chunk_overlaps)
        step = size // overlaps
        if step <= 0:
            raise ValueError(
                f"chunk_size ({size}) must be >= chunk_overlaps ({overlaps})"
            )

        if text_len < MIN_PDF_TEXT_LENGTH:
            self.is_too_short = True
            # If too short, don't bother creating chunks
            self.chunks = []
            return

        chunks: list[Chunk] = []
        for start in range(0, text_len, step):
            end = start + size
            if end >= text_len:
                end = text_len
                chunks.append(Chunk(start, end, self.full_text[start:end]))
                break
            chunks.append(Chunk(start, end, self.full_text[start:end]))

        self.chunks = chunks


def convert_pdf_to_text(path_to_pdf: Path | str):
    """Converts binary pdf into text"""

    with open(path_to_pdf, "rb") as f:
        try:
            pdf_text = pdftotext.PDF(f)
        except Exception as e:
            logger.warning(f"error reading pdf {path_to_pdf}")
            logger.warning(e)
            raise PdfReadingError
        return {
            "full_text": "".join([page for page in pdf_text]),
            "n_pages": len(pdf_text),
        }


def parse_pdf_to_patent(pdf_path: Path):
    """Reads patent pdf to patent object"""
    try:
        pdf_text_info = convert_pdf_to_text(pdf_path)
        return Patent(
            name=pdf_path.stem,
            country=pdf_path.name[:2],
            local_path=pdf_path,
            full_text=pdf_text_info["full_text"],
            n_pages=pdf_text_info["n_pages"],
        )

    except PdfReadingError as e:
        logger.warning(e)
        logger.warning(f"error reading {pdf_path.name}")
        logger.warning(f"will return with empty full text {pdf_path.name}")
        return Patent(
            name=pdf_path.stem,
            country=pdf_path.name[:2],
            local_path=pdf_path,
        )


def parse_pdfs_in_dir(path_to_dir: Path, limit: int | None = None) -> list[Patent]:
    """Treats all files in dir as patent pdf and tries to convert them to patent obj list"""
    patent_list = []
    for indx, patent_path in enumerate(Path(path_to_dir).iterdir()):
        patent_list.append(parse_pdf_to_patent(patent_path))

        if limit and limit is not None:
            assert isinstance(limit, float), "Limit must be a number"
            if indx >= limit:
                break

    return patent_list


def parse_pdfs(pdf_paths: list[Path]) -> list[Patent]:
    """Parse a list of PDF files into Patent objects"""
    patent_list = []
    for pdf_path in pdf_paths:
        patent = parse_pdf_to_patent(pdf_path)
        patent_list.append(patent)
    return patent_list
