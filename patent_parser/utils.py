from typing import Any

def batch_list(lst: list[Any], batch_size: int) -> list[list[Any]]:
    """Split a list into batches of fixed size."""
    for i in range(0, len(lst), batch_size):
        yield lst[i : i + batch_size]