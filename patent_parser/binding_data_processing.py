import json
from pathlib import Path
from parse_pdfs import Patent

from config import INITIAL_PDF_CHUNK_SIZE, CHUNK_OVERLAPS, MIN_PDF_TEXT_LENGTH


def parse_patent_json(json_file_path: Path) -> Patent:
    """
    Parse a JSON file and convert it to a Patent object

    Args:
        json_file_path: Path to the JSON file

    Returns:
        Patent object
    """

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    patent = Patent(
        name=data.get("name", ""),
        country=data.get("country", ""),
        local_path=json_file_path,
        full_text=data.get("full_text", ""),
        n_pages=data.get("n_pages", 0),
        chunk_size=data.get("chunk_size", INITIAL_PDF_CHUNK_SIZE),
        chunk_overlaps=data.get("chunk_overlaps", CHUNK_OVERLAPS),
        has_binding_info=data.get("has_binding_info", False),
        is_too_short=(len(data.get("full_text", False)) < MIN_PDF_TEXT_LENGTH),
    )

    return patent


def extract_patents_with_binding_data(folder_path: Path) -> list[Patent]:
    """
    Process all JSON files in a folder and return patents with binding information

    Args:
        folder_path: Path to the folder containing JSON files

    Returns:
        List of Patent objects that have binding information
    """

    folder_path = Path(folder_path)
    patents_with_binding = []

    for json_file in folder_path.glob("*.json"):
        try:
            patent = parse_patent_json(json_file)

            if patent.has_binding_info:
                patents_with_binding.append(patent)

        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            continue

    return patents_with_binding
