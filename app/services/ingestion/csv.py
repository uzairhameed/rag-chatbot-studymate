from pathlib import Path

import pandas as pd


def extract_csv(file_path: str | Path) -> list[str]:
    """Convert CSV rows into text while keeping each value with its column."""
    try:
        # Read as text to preserve values like IDs and leading zeroes.
        # Keep strings such as "NA" as actual cell contents.
        dataframe = pd.read_csv(
            file_path,
            dtype=str,
            keep_default_na=False,
        )
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The CSV file is empty") from exc

    if len(dataframe.columns) == 0:
        raise ValueError("The CSV file has no columns")

    column_names = [str(column).strip() for column in dataframe.columns]

    # A CSV with headers but no rows still contains useful column information.
    if dataframe.empty:
        return ["CSV columns: " + " | ".join(column_names)]

    text_rows: list[str] = []

    for row in dataframe.to_dict(orient="records"):
        # Label each value with its column so the meaning survives retrieval.
        fields = [
            f"{column}: {str(row[column]).strip()}"
            for column in dataframe.columns
            if str(row[column]).strip()
        ]
        if fields:
            text_rows.append(" | ".join(fields))

    if not text_rows:
        raise ValueError("The CSV file contains no readable row values")

    return text_rows
