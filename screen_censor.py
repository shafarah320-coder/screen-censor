import os
import sys
import time
import threading
import tempfile
import ctypes
from pathlib import Path

import cv2
import numpy as np
import mss
import tkinter as tk
from nudenet import NudeDetector

# Labels NudeNet commonly returns for exposed nudity.
TARGET_LABELS = {
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_EXPOSED",
    "BUTTOCKS_EXPOSED",
}

class ScreenCensor:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Censor")
        self.root.geometry("360x190")
        self.root.resizable(False, False)
        self.root.configure(bg="#151923")
        self.root.attributes("-topmost", True)

        self.running = False
        self.stop_event = threading.Event()
        self.box_lock = threading.Lock()
        self.boxes = []
        self.detector = None
        self.threshold = 0.35
        self.interval = 0.8

        tk.Label(root, text="SCREEN CENSOR", fg="white", bg="#151923",
                 font=("Segoe UI", 16, "bold")).pack(pady=(15, 4))
        tk.Label(root, text="Deteksi konten eksplisit dan tutup area terdeteksi",
                 fg="#b9c2d0", bg="#151923", font=("Segoe UI", 9)).pack()

        self.status = tk.Label(root, text="Status: Mati", fg="#ff7777",
                               bg="#151923", font=("Segoe UI", 10, "bold"))
        self.status.pack(pady=10)

        row = tk.Frame(root, bg="#151923")
        row.pack()
        self.start_btn = tk.Button(row, text="Mulai sensor", width=14,
                                   command=self.start, bg="#28a36a", fg="white",
                                   relief="flat", font=("Segoe UI", 10, "bold"))
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = tk.Button(row, text="Matikan", width=12,
                                  command=self.stop, state="disabled",
                                  bg="#bd4b4b", fg="white", relief="flat",
                                  font=("Segoe UI", 10, "bold"))
        self.stop_btn.pack(side="left", padx=5)

        tk.Label(root, text="Catatan: sensor berupa kotak hitam di atas area terdeteksi.",
                 fg="#9aa5b5", bg="#151923", font=("Segoe UI", 8)).pack(pady=12)

        self.overlay = tk.Toplevel(root)
        self.overlay.withdraw()
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="magenta")
        self.overlay.wm_attributes("-transparentcolor", "magenta")
        self.canvas = tk.Canvas(self.overlay, bg="magenta", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(150, self.refresh_overlay)

    def set_clickthrough(self):
        # Make the censor overlay ignore mouse input on Windows.
        try:
            hwnd = self.overlay.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080
            get_long = ctypes.windll.user32.GetWindowLongW
            set_long = ctypes.windll.user32.SetWindowLongW
            style = get_long(hwnd, GWL_EXSTYLE)
            set_long(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW)
        except Exception:
            pass

    def start(self):
        if self.running:
            return
        self.status.config(text="Status: Menyiapkan model…", fg="#ffd166")
        self.start_btn.config(state="disabled")
        threading.Thread(target=self.worker_start, daemon=True).start()

    def worker_start(self):
        try:
            self.detector = NudeDetector()
            self.running = True
            self.stop_event.clear()
            self.root.after(0, self.started_ui)
            threading.Thread(target=self.scan_loop, daemon=True).start()
        except Exception as exc:
            self.root.after(0, lambda: self.start_failed(str(exc)))

    def started_ui(self):
        self.status.config(text="Status: Aktif — sensor berjalan", fg="#65d69a")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.overlay.deiconify()
        self.overlay.update_idletasks()
        self.overlay.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.set_clickthrough()
        self.overlay.lift()

    def start_failed(self, message):
        self.start_btn.config(state="normal")
        self.status.config(text="Gagal memuat model", fg="#ff7777")
        tk.messagebox.showerror("Screen Censor", f"Gagal memuat NudeNet:\n{message}")

    def scan_loop(self):
        # Hide the overlay briefly so its own censor rectangles are not analyzed.
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            while self.running and not self.stop_event.is_set():
                try:
                    self.overlay_hidden_request()
                    shot = np.array(sct.grab(monitor))
                    frame = cv2.cvtColor(shot, cv2.COLOR_BGRA2BGR)
                    # NudeNet accepts an image path; use a temporary JPEG.
                    tmp_name = None
                    try:
                        fd, tmp_name = tempfile.mkstemp(suffix=".jpg")
                        os.close(fd)
                        cv2.imwrite(tmp_name, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                        detections = self.detector.detect(tmp_name)
                    finally:
                        if tmp_name and os.path.exists(tmp_name):
                            os.remove(tmp_name)

                    found = []
                    for item in detections:
                        label = str(item.get("class", "")).upper()
                        score = float(item.get("score", 0))
                        if label in TARGET_LABELS and score >= self.threshold:
                            x, y, w, h = item.get("box", [0, 0, 0, 0])
                            # Expand the censor area a little for safer coverage.
                            pad_x = int(w * 0.08)
                            pad_y = int(h * 0.08)
                            x1 = max(0, int(x) - pad_x)
                            y1 = max(0, int(y) - pad_y)
                            x2 = min(frame.shape[1], int(x + w) + pad_x)
                            y2 = min(frame.shape[0], int(y + h) + pad_y)
                            found.append((x1, y1, x2, y2))
                    with self.box_lock:
                        self.boxes = found
                except Exception:
                    # Keep the app alive if a single capture/detection fails.
                    pass
                time.sleep(self.interval)

    def overlay_hidden_request(self):
        # Tk calls are scheduled on the UI thread; brief hide avoids self-detection.
        self.root.after(0, self.overlay.withdraw)
        time.sleep(0.06)
        self.root.after(0, self.overlay.deiconify)

    def refresh_overlay(self):
        if self.running:
            with self.box_lock:
                boxes = list(self.boxes)
            self.canvas.delete("all")
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.canvas.configure(width=sw, height=sh)
            for x1, y1, x2, y2 in boxes:
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="black", outline="black")
            self.overlay.lift()
        self.root.after(150, self.refresh_overlay)

    def stop(self):
        self.running = False
        self.stop_event.set()
        with self.box_lock:
            self.boxes = []
        self.overlay.withdraw()
        self.status.config(text="Status: Mati", fg="#ff7777")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def close(self):
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Aplikasi ini dirancang untuk Windows 10/11.")
    root = tk.Tk()
    # messagebox is imported lazily by tkinter on some builds.
    from tkinter import messagebox
    tk.messagebox = messagebox
    app = ScreenCensor(root)
    root.mainloop()
