import os
from typing import Iterable, Sequence

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .qr_utils import ensure_batch_folder, save_qr_image

DEFAULT_PAGE_SIZE = A4


def export_sheet(
    batch_id: int,
    serials: Sequence[str],
    sticker_name: str,
    width_mm: float,
    height_mm: float,
    margin_x_mm: float,
    margin_y_mm: float,
    rows: int,
    cols: int,
) -> str:
    folder = ensure_batch_folder(batch_id)
    pdf_path = os.path.join(folder, f"{sticker_name.replace(' ', '_')}_sheet.pdf")
    c = canvas.Canvas(pdf_path, pagesize=DEFAULT_PAGE_SIZE)
    page_width, page_height = DEFAULT_PAGE_SIZE

    sticker_width = width_mm / 25.4 * 72
    sticker_height = height_mm / 25.4 * 72
    margin_x = margin_x_mm / 25.4 * 72
    margin_y = margin_y_mm / 25.4 * 72

    idx = 0
    for serial in serials:
        col_idx = idx % cols
        row_idx = (idx // cols) % rows
        if row_idx == 0 and col_idx == 0 and idx > 0 and idx % (rows * cols) == 0:
            c.showPage()
        x = margin_x + col_idx * (sticker_width + margin_x)
        y = page_height - margin_y - sticker_height - row_idx * (sticker_height + margin_y)

        img_path = os.path.join(folder, f"{serial}.png")
        if not os.path.exists(img_path):
            save_qr_image(serial, img_path)
        c.drawImage(img_path, x, y, width=sticker_width, height=sticker_height, preserveAspectRatio=True)
        c.drawCentredString(x + sticker_width / 2, y - 12, serial)
        idx += 1
        if idx % (rows * cols) == 0:
            c.showPage()
    c.save()
    return pdf_path
