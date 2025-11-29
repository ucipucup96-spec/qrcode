import os
from typing import Iterable

import qrcode
from PIL import Image


def ensure_batch_folder(batch_id: int) -> str:
    folder = os.path.join(os.path.dirname(__file__), "..", "data", "batches", str(batch_id))
    os.makedirs(folder, exist_ok=True)
    return folder


def save_qr_image(serial: str, output_path: str, box_size: int = 10) -> None:
    qr = qrcode.QRCode(box_size=box_size, border=2)
    qr.add_data(serial)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)


def export_qr_images(batch_id: int, serials: Iterable[str]) -> str:
    folder = ensure_batch_folder(batch_id)
    for serial in serials:
        filename = f"{serial}.png"
        save_qr_image(serial, os.path.join(folder, filename))
    return folder
