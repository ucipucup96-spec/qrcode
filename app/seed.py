from datetime import datetime
from pathlib import Path
from typing import List

from . import batches, database
from .layout import export_sheet
from .qr_utils import export_qr_images
from .serials import generate_unique_serials


SAMPLE_BATCH_NAME = "Demo Batch"
SAMPLE_COUNT = 6


def ensure_seed_data() -> None:
    database.init_db()
    database.seed_sticker_sizes()
    if database.fetch_batches():
        return
    sticker = batches.list_sticker_sizes()[0]
    serials = generate_unique_serials(SAMPLE_COUNT)
    batch = batches.create_batch(SAMPLE_BATCH_NAME, sticker.id, serials)
    export_qr_images(batch.id, serials)
    export_sheet(
        batch.id,
        serials,
        sticker.name,
        sticker.width,
        sticker.height,
        sticker.margin_x,
        sticker.margin_y,
        sticker.rows,
        sticker.cols,
    )
