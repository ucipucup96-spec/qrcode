from datetime import datetime
from typing import List, Optional

import pandas as pd

from . import database
from .models import Batch, StickerSize


def row_to_sticker(row) -> StickerSize:
    return StickerSize(
        id=row["id"],
        name=row["name"],
        width=row["width"],
        height=row["height"],
        margin_x=row["margin_x"],
        margin_y=row["margin_y"],
        rows=row["rows"],
        cols=row["cols"],
    )


def list_sticker_sizes() -> List[StickerSize]:
    return [row_to_sticker(row) for row in database.fetch_sticker_sizes()]


def save_sticker_size(sticker: StickerSize) -> int:
    if sticker.id:
        database.update_sticker_size(
            sticker.id,
            sticker.name,
            sticker.width,
            sticker.height,
            sticker.margin_x,
            sticker.margin_y,
            sticker.rows,
            sticker.cols,
        )
        return sticker.id
    return database.insert_sticker_size(
        sticker.name,
        sticker.width,
        sticker.height,
        sticker.margin_x,
        sticker.margin_y,
        sticker.rows,
        sticker.cols,
    )


def create_batch(name: str, sticker_size_id: int, serials: List[str]) -> Batch:
    created_at = datetime.now().isoformat(timespec="seconds")
    batch_id = database.insert_batch(name, created_at, sticker_size_id, len(serials))
    database.insert_serials(batch_id, serials)
    row = database.fetch_batch(batch_id)
    return Batch(
        id=batch_id,
        name=row["name"],
        created_at=datetime.fromisoformat(row["created_at"]),
        sticker_size_id=row["sticker_size_id"],
        sticker_name=row["sticker_name"],
        count=row["count"],
    )


def list_batches() -> List[Batch]:
    batches: List[Batch] = []
    for row in database.fetch_batches():
        batches.append(
            Batch(
                id=row["id"],
                name=row["name"],
                created_at=datetime.fromisoformat(row["created_at"]),
                sticker_size_id=0,
                sticker_name=row["sticker_name"] or "Unknown",
                count=row["count"],
            )
        )
    return batches


def load_batch(batch_id: int) -> Optional[Batch]:
    row = database.fetch_batch(batch_id)
    if not row:
        return None
    return Batch(
        id=row["id"],
        name=row["name"],
        created_at=datetime.fromisoformat(row["created_at"]),
        sticker_size_id=row["sticker_size_id"],
        sticker_name=row["sticker_name"],
        count=row["count"],
    )


def get_batch_serials(batch_id: int) -> List[str]:
    return database.fetch_serials(batch_id)


def export_serials_csv(batch: Batch, serials: List[str], output_path: str) -> None:
    df = pd.DataFrame(
        {
            "batch_id": batch.id,
            "batch_name": batch.name,
            "created_at": batch.created_at,
            "sticker_size": batch.sticker_name,
            "serial": serials,
        }
    )
    df.to_csv(output_path, index=False)
