from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class StickerSize:
    id: int
    name: str
    width: float
    height: float
    margin_x: float
    margin_y: float
    rows: int
    cols: int

    @property
    def description(self) -> str:
        return f"{self.name} - {self.width}x{self.height}mm ({self.cols} cols x {self.rows} rows)"


@dataclass
class Batch:
    id: int
    name: str
    created_at: datetime
    sticker_size_id: int
    sticker_name: str
    count: int

    @property
    def created_display(self) -> str:
        return self.created_at.strftime("%Y-%m-%d %H:%M")
