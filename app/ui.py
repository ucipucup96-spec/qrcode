import os
import threading
from datetime import datetime
from tkinter import END, LEFT, RIGHT, BOTH, filedialog, messagebox, ttk, Tk, StringVar
from typing import List, Optional

from . import batches, database
from .layout import export_sheet
from .models import Batch, StickerSize
from .qr_utils import export_qr_images
from .serials import generate_unique_serials


class QRApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Offline QR Code Generator")
        self.root.geometry("960x640")
        self.root.minsize(840, 520)

        self.sticker_sizes: List[StickerSize] = batches.list_sticker_sizes()
        self.selected_sticker_id = StringVar()
        if self.sticker_sizes:
            self.selected_sticker_id.set(str(self.sticker_sizes[0].id))

        self.progress = StringVar()
        self.progress.set("Ready")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True)

        self.generate_tab = ttk.Frame(self.notebook, padding=16)
        self.sizes_tab = ttk.Frame(self.notebook, padding=16)
        self.history_tab = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(self.generate_tab, text="Generate")
        self.notebook.add(self.sizes_tab, text="Sticker Sizes")
        self.notebook.add(self.history_tab, text="Saved Batches")

        self._build_generate_tab()
        self._build_sizes_tab()
        self._build_history_tab()

        self.refresh_history()

    def _build_generate_tab(self) -> None:
        frame = self.generate_tab
        ttk.Label(frame, text="Number of QR codes to generate:").grid(row=0, column=0, sticky="w")
        self.count_entry = ttk.Entry(frame)
        self.count_entry.insert(0, "100")
        self.count_entry.grid(row=0, column=1, sticky="w")

        ttk.Label(frame, text="Batch name (optional):").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.batch_name_entry = ttk.Entry(frame)
        self.batch_name_entry.grid(row=1, column=1, sticky="w", pady=(8, 0))

        ttk.Label(frame, text="Sticker size:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.sticker_dropdown = ttk.Combobox(
            frame,
            state="readonly",
            values=[self._format_sticker_option(s) for s in self.sticker_sizes],
        )
        self.sticker_dropdown.grid(row=2, column=1, sticky="w", pady=(8, 0))
        if self.sticker_sizes:
            self.sticker_dropdown.current(0)

        self.generate_button = ttk.Button(frame, text="Generate QR Codes", command=self.handle_generate)
        self.generate_button.grid(row=3, column=0, columnspan=2, pady=(16, 8), sticky="w")

        self.progress_label = ttk.Label(frame, textvariable=self.progress)
        self.progress_label.grid(row=4, column=0, columnspan=2, sticky="w")

        for i in range(2):
            frame.columnconfigure(i, weight=1)

    def _build_sizes_tab(self) -> None:
        frame = self.sizes_tab
        left = ttk.Frame(frame)
        left.pack(side=LEFT, fill=BOTH, expand=True)
        right = ttk.Frame(frame, padding=(12, 0))
        right.pack(side=RIGHT, fill=BOTH, expand=True)

        columns = ("Name", "Width", "Height", "Rows", "Cols")
        self.sizes_tree = ttk.Treeview(left, columns=columns, show="headings", height=12)
        for col in columns:
            self.sizes_tree.heading(col, text=col)
        self.sizes_tree.pack(fill=BOTH, expand=True)
        self.sizes_tree.bind("<<TreeviewSelect>>", self.on_size_select)
        self._refresh_sizes_tree()

        self.form_vars = {key: StringVar() for key in [
            "name", "width", "height", "margin_x", "margin_y", "rows", "cols"
        ]}

        ttk.Label(right, text="Sticker name").grid(row=0, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.form_vars["name"]).grid(row=0, column=1, sticky="we")

        ttk.Label(right, text="Width (mm)").grid(row=1, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.form_vars["width"]).grid(row=1, column=1, sticky="we")

        ttk.Label(right, text="Height (mm)").grid(row=2, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.form_vars["height"]).grid(row=2, column=1, sticky="we")

        ttk.Label(right, text="Left/Top margin (mm)").grid(row=3, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.form_vars["margin_x"]).grid(row=3, column=1, sticky="we")
        ttk.Label(right, text="Vertical margin (mm)").grid(row=4, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.form_vars["margin_y"]).grid(row=4, column=1, sticky="we")

        ttk.Label(right, text="Rows per page").grid(row=5, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.form_vars["rows"]).grid(row=5, column=1, sticky="we")
        ttk.Label(right, text="Columns per page").grid(row=6, column=0, sticky="w")
        ttk.Entry(right, textvariable=self.form_vars["cols"]).grid(row=6, column=1, sticky="we")

        self.save_size_btn = ttk.Button(right, text="Save sticker size", command=self.save_sticker_size)
        self.save_size_btn.grid(row=7, column=0, columnspan=2, pady=(12, 0), sticky="we")
        self.delete_size_btn = ttk.Button(right, text="Delete selected", command=self.delete_sticker_size)
        self.delete_size_btn.grid(row=8, column=0, columnspan=2, pady=(8, 0), sticky="we")

        right.columnconfigure(1, weight=1)

    def _build_history_tab(self) -> None:
        frame = self.history_tab
        columns = ("ID", "Name", "Created", "Count", "Sticker")
        self.history_tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)
        for col in columns:
            self.history_tree.heading(col, text=col)
        self.history_tree.pack(fill=BOTH, expand=True)
        self.history_tree.bind("<<TreeviewSelect>>", self.on_batch_select)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=8)
        self.export_qr_btn = ttk.Button(btn_frame, text="Export QR images", command=self.export_selected_qrs, state="disabled")
        self.export_pdf_btn = ttk.Button(btn_frame, text="Export sticker sheet", command=self.export_selected_sheet, state="disabled")
        self.export_csv_btn = ttk.Button(btn_frame, text="Export CSV", command=self.export_selected_csv, state="disabled")
        self.export_qr_btn.pack(side=LEFT, padx=(0, 6))
        self.export_pdf_btn.pack(side=LEFT, padx=(0, 6))
        self.export_csv_btn.pack(side=LEFT, padx=(0, 6))

    def _format_sticker_option(self, sticker: StickerSize) -> str:
        return f"{sticker.id}: {sticker.name} ({sticker.width}x{sticker.height}mm, {sticker.cols}x{sticker.rows})"

    def _refresh_sizes_tree(self) -> None:
        for row in self.sizes_tree.get_children():
            self.sizes_tree.delete(row)
        for sticker in self.sticker_sizes:
            self.sizes_tree.insert(
                "", END, iid=str(sticker.id), values=(
                    sticker.name,
                    f"{sticker.width}",
                    f"{sticker.height}",
                    str(sticker.rows),
                    str(sticker.cols),
                )
            )

    def on_size_select(self, event=None) -> None:  # type: ignore[override]
        selection = self.sizes_tree.selection()
        if not selection:
            return
        item_id = selection[0]
        sticker = next((s for s in self.sticker_sizes if str(s.id) == item_id), None)
        if not sticker:
            return
        self.form_vars["name"].set(sticker.name)
        self.form_vars["width"].set(str(sticker.width))
        self.form_vars["height"].set(str(sticker.height))
        self.form_vars["margin_x"].set(str(sticker.margin_x))
        self.form_vars["margin_y"].set(str(sticker.margin_y))
        self.form_vars["rows"].set(str(sticker.rows))
        self.form_vars["cols"].set(str(sticker.cols))

    def save_sticker_size(self) -> None:
        try:
            sticker = StickerSize(
                id=int(self.sizes_tree.selection()[0]) if self.sizes_tree.selection() else 0,
                name=self.form_vars["name"].get() or "New sticker",
                width=float(self.form_vars["width"].get()),
                height=float(self.form_vars["height"].get()),
                margin_x=float(self.form_vars["margin_x"].get() or 0),
                margin_y=float(self.form_vars["margin_y"].get() or 0),
                rows=int(self.form_vars["rows"].get()),
                cols=int(self.form_vars["cols"].get()),
            )
        except ValueError:
            messagebox.showerror("Invalid input", "Please enter numeric values for sizes and counts.")
            return
        new_id = batches.save_sticker_size(sticker)
        self.sticker_sizes = batches.list_sticker_sizes()
        self._refresh_sizes_tree()
        self.sticker_dropdown["values"] = [self._format_sticker_option(s) for s in self.sticker_sizes]
        for idx, sticker in enumerate(self.sticker_sizes):
            if sticker.id == new_id:
                self.sticker_dropdown.current(idx)
                break
        self.progress.set("Sticker size saved")

    def delete_sticker_size(self) -> None:
        selection = self.sizes_tree.selection()
        if not selection:
            return
        sticker_id = int(selection[0])
        batches.database.delete_sticker_size(sticker_id)
        self.sticker_sizes = batches.list_sticker_sizes()
        self._refresh_sizes_tree()
        self.sticker_dropdown["values"] = [self._format_sticker_option(s) for s in self.sticker_sizes]
        if self.sticker_sizes:
            self.sticker_dropdown.current(0)
        self.progress.set("Sticker size deleted")

    def handle_generate(self) -> None:
        try:
            count = int(self.count_entry.get())
        except ValueError:
            messagebox.showerror("Invalid number", "Please enter how many QR codes to generate.")
            return
        if count <= 0:
            messagebox.showerror("Invalid number", "Please enter a positive quantity.")
            return
        sticker = self._get_selected_sticker()
        if not sticker:
            messagebox.showerror("No sticker size", "Please add at least one sticker size.")
            return
        batch_name = self.batch_name_entry.get().strip() or f"Batch {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.generate_button.configure(state="disabled")
        self.progress.set("Generating serial numbers...")
        threading.Thread(target=self._generate_batch, args=(count, sticker, batch_name), daemon=True).start()

    def _generate_batch(self, count: int, sticker: StickerSize, batch_name: str) -> None:
        serials = generate_unique_serials(count)
        batch = batches.create_batch(batch_name, sticker.id, serials)
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
        self.root.after(0, self._after_generation, batch)

    def _after_generation(self, batch: Batch) -> None:
        self.generate_button.configure(state="normal")
        self.progress.set(f"Batch {batch.id} created with {batch.count} QR codes")
        self.refresh_history()

    def refresh_history(self) -> None:
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        for batch in batches.list_batches():
            self.history_tree.insert(
                "", END, iid=str(batch.id), values=(
                    batch.id,
                    batch.name,
                    batch.created_display,
                    batch.count,
                    batch.sticker_name,
                )
            )

    def on_batch_select(self, event=None) -> None:  # type: ignore[override]
        has_selection = bool(self.history_tree.selection())
        state = "normal" if has_selection else "disabled"
        for btn in [self.export_qr_btn, self.export_pdf_btn, self.export_csv_btn]:
            btn.configure(state=state)

    def export_selected_qrs(self) -> None:
        batch = self._get_selected_batch()
        if not batch:
            return
        serials = batches.get_batch_serials(batch.id)
        folder = export_qr_images(batch.id, serials)
        messagebox.showinfo("Export complete", f"QR images saved to:\n{folder}")

    def export_selected_sheet(self) -> None:
        batch = self._get_selected_batch()
        if not batch:
            return
        serials = batches.get_batch_serials(batch.id)
        sticker_row = database.fetch_batch(batch.id)
        if not sticker_row:
            return
        pdf = export_sheet(
            batch.id,
            serials,
            sticker_row["sticker_name"],
            sticker_row["width"],
            sticker_row["height"],
            sticker_row["margin_x"],
            sticker_row["margin_y"],
            sticker_row["rows"],
            sticker_row["cols"],
        )
        messagebox.showinfo("Export complete", f"Sticker sheet saved to:\n{pdf}")

    def export_selected_csv(self) -> None:
        batch = self._get_selected_batch()
        if not batch:
            return
        serials = batches.get_batch_serials(batch.id)
        initial = os.path.join(os.path.expanduser("~"), f"batch_{batch.id}.csv")
        path = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            initialfile=os.path.basename(initial),
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        batches.export_serials_csv(batch, serials, path)
        messagebox.showinfo("Export complete", f"CSV saved to:\n{path}")

    def _get_selected_sticker(self) -> Optional[StickerSize]:
        if not self.sticker_sizes:
            return None
        idx = self.sticker_dropdown.current()
        if idx < 0:
            return None
        return self.sticker_sizes[idx]

    def _get_selected_batch(self) -> Optional[Batch]:
        selection = self.history_tree.selection()
        if not selection:
            return None
        batch_id = int(selection[0])
        return batches.load_batch(batch_id)


def launch_app() -> None:
    root = Tk()
    QRApp(root)
    root.mainloop()
