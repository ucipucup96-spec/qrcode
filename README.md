# Offline QR Code Generator

A desktop-friendly Tkinter app that works fully offline to generate batches of QR codes with random serial numbers, organize them by sticker size, and export printable sticker sheets or CSVs.

## Features
- Offline QR and serial generation (no network calls)
- Sticker size management (rows, columns, margins)
- Batch history with re-export to PNG sheets, PDF sticker sheets, or CSV
- Demo sticker sizes plus a sample batch created on first launch

## Getting started (Windows)
1. Install Python 3.10+ from [python.org](https://www.python.org/downloads/windows/) and ensure `Add python.exe to PATH` is checked.
2. Download or clone this repository and open a terminal in the folder.
3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Launch the app (works completely offline once dependencies are installed):
   ```bash
   python main.py
   ```

### Running as a packaged app
If you want a single-file executable for non-technical users, install `pyinstaller` and build:
```bash
python -m pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "data;data" main.py
```
The packaged executable will be in `dist/main.exe`. Copy the `data` folder alongside it so existing batches remain available.

## Using the app
1. **Generate codes**
   - Enter the quantity and optional batch name.
   - Choose a sticker size from the dropdown.
   - Click **Generate QR Codes**. The app creates serial numbers, QR PNGs, and a PDF sticker sheet in `data/batches/<batch_id>/`.
2. **Sticker Sizes**
   - Add or edit sticker dimensions (mm) plus rows/columns per page and margins.
   - Save to reuse; sizes are stored locally in the SQLite database.
3. **Saved Batches**
   - Select a batch to re-export PNGs, PDF sheet, or CSV of serials and metadata.

## Data & storage
- All data is stored locally in `data/app.db` (SQLite).
- Generated assets live in `data/batches/<batch_id>/`.
- The first launch seeds sample sticker sizes and a **Demo Batch** with printable assets.

## Adding new sticker sizes manually
Sticker sizes are stored in SQLite. You can also preseed by adjusting `DEFAULT_STICKERS` inside `app/database.py` before first launch.

## Tech stack
- Python + Tkinter for the offline desktop UI
- `qrcode` and Pillow for QR image generation
- ReportLab for printable PDF sticker sheets
- SQLite for local persistence
