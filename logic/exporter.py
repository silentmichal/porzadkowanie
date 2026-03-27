import os
import shutil
from pathlib import Path


class PhotoExporter:
    """Kopiuje lub przenosi zdjęcia do nowej struktury folderów."""

    def __init__(self, mode="copy"):
        # mode: "copy" | "move"
        self.mode = mode

    def _transfer(self, src, dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        # Jeśli plik docelowy już istnieje, dodaj suffix
        if os.path.exists(dst):
            base, ext = os.path.splitext(dst)
            i = 1
            while os.path.exists(f"{base}_{i}{ext}"):
                i += 1
            dst = f"{base}_{i}{ext}"
        if self.mode == "copy":
            shutil.copy2(src, dst)
        else:
            shutil.move(src, dst)
        return dst

    # ── Strategia 1: wg daty ─────────────────────────────────────────────────
    def export_by_date(self, df, output_dir, granularity="rok/miesiąc"):
        """
        granularity: "rok" | "rok/miesiąc" | "rok/miesiąc/dzień"
        """
        results = {"ok": 0, "error": 0, "skipped": 0}
        MONTHS_PL = {
            "01":"01_Styczeń","02":"02_Luty","03":"03_Marzec","04":"04_Kwiecień",
            "05":"05_Maj","06":"06_Czerwiec","07":"07_Lipiec","08":"08_Sierpień",
            "09":"09_Wrzesień","10":"10_Październik","11":"11_Listopad","12":"12_Grudzień"
        }
        for _, row in df.iterrows():
            try:
                date = str(row.get("date_taken", ""))
                if date and date != "None" and len(date) >= 7:
                    year  = date[:4]
                    month = date[5:7]
                    day   = date[8:10] if len(date) >= 10 else "01"
                    month_name = MONTHS_PL.get(month, month)
                    if granularity == "rok":
                        sub = year
                    elif granularity == "rok/miesiąc":
                        sub = os.path.join(year, month_name)
                    else:  # rok/miesiąc/dzień
                        sub = os.path.join(year, month_name, f"{day}")
                else:
                    sub = "Nieznana_data"

                dst = os.path.join(output_dir, sub, row["filename"])
                self._transfer(row["path"], dst)
                results["ok"] += 1
            except Exception as e:
                results["error"] += 1
        return results

    # ── Strategia 2: wg formatu/typu ─────────────────────────────────────────
    def export_by_type(self, df, output_dir):
        """
        Rozdziela wg rozszerzenia: JPG / PNG / RAW / Inne
        """
        TYPE_MAP = {
            ".jpg":  "JPG",
            ".jpeg": "JPG",
            ".png":  "PNG",
            ".webp": "WEBP",
            ".tif":  "TIFF",
            ".tiff": "TIFF",
            ".bmp":  "BMP",
            ".heic": "HEIC",
            ".raw":  "RAW",
            ".cr2":  "RAW",
            ".nef":  "RAW",
            ".arw":  "RAW",
            ".dng":  "RAW",
        }
        results = {"ok": 0, "error": 0}
        for _, row in df.iterrows():
            try:
                ext   = Path(row["filename"]).suffix.lower()
                group = TYPE_MAP.get(ext, "Inne")
                dst   = os.path.join(output_dir, group, row["filename"])
                self._transfer(row["path"], dst)
                results["ok"] += 1
            except:
                results["error"] += 1
        return results

    # ── Strategia 3: wg aparatu ──────────────────────────────────────────────
    def export_by_camera(self, df, output_dir):
        """
        Rozdziela wg modelu aparatu (z EXIF). Nieznane → folder 'Nieznany_aparat'.
        """
        results = {"ok": 0, "error": 0}
        for _, row in df.iterrows():
            try:
                cam = str(row.get("camera_model", "Unknown")).strip()
                if not cam or cam in ("Unknown", "None", ""):
                    cam = "Nieznany_aparat"
                # Sanitize folder name
                cam = cam.replace("/", "-").replace("\\", "-").replace(":", "-")
                dst = os.path.join(output_dir, cam, row["filename"])
                self._transfer(row["path"], dst)
                results["ok"] += 1
            except:
                results["error"] += 1
        return results
