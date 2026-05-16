"""
Script untuk auto-extract karakter dari dataset_kendaraan
dan menyimpannya sebagai variasi template baru.

Cara pakai:
    python generate_templates.py

Nama file foto = nomor plat (ground truth).
Contoh: H2306AK_jpg.rf.xxx.jpg -> plat = H2306AK
"""

import cv2
import numpy as np
import os

DATASET_FOLDER = "dataset_kendaraan/images"
TEMPLATE_FOLDER = "dataset_template"


def cari_lokasi_plat(img):
    """Cari lokasi plat dari gambar. Return (x, y, w, h) atau None."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    blur = cv2.bilateralFilter(gray, 11, 17, 17)

    edges = cv2.Canny(blur, 170, 250)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 3))
    morph = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    tinggi, lebar = img.shape[:2]
    luas_gambar = tinggi * lebar
    contours, _ = cv2.findContours(morph, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_score = 0

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if h == 0:
            continue
        rasio = w / float(h)
        luas = w * h

        if not (1.5 <= rasio <= 6.0):
            continue
        if luas < 500 or luas > luas_gambar * 0.3:
            continue

        crop_gray = gray[y:y+h, x:x+w]
        _, crop_bw = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        cnts, _ = cv2.findContours(crop_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        n_chars = sum(1 for c in cnts
                      if 3 < cv2.boundingRect(c)[2] < w * 0.4
                      and h * 0.2 < cv2.boundingRect(c)[3] < h * 0.95)

        if n_chars >= 4:
            score = n_chars * 100000 - luas
            if score > best_score:
                best_score = score
                best = (x, y, w, h)

    return best


def extract_chars(img, x, y, w, h):
    """Crop plat, threshold, segmentasi. Return list of (label_position, binary_char_image)."""
    plat = img[y:y+h, x:x+w]
    gray = cv2.cvtColor(plat, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, 9, 75, 75)
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    plat_h, plat_w = bw.shape[:2]
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])

    chars = []
    for cnt in contours:
        cx, cy, cw, ch = cv2.boundingRect(cnt)
        if not (3 < cw < plat_w * 0.4 and plat_h * 0.2 < ch < plat_h * 0.95):
            continue
        char_crop = bw[cy:cy+ch, cx:cx+cw]
        char_resized = cv2.resize(char_crop, (30, 60))
        _, char_bin = cv2.threshold(char_resized, 127, 255, cv2.THRESH_BINARY)
        chars.append(char_bin)

    return chars


def get_plat_from_filename(fname):
    """Extract nomor plat dari nama file. H2306AK_jpg.rf.xxx.jpg -> H2306AK"""
    # Ambil bagian sebelum _jpg atau .png
    name = fname.split("_jpg")[0].split(".png")[0].split(".jpg")[0]
    # Hanya ambil karakter alfanumerik
    plat = "".join(c for c in name if c.isalnum())
    return plat.upper()


def get_next_variant(label):
    """Cari nomor variasi berikutnya untuk label tertentu."""
    existing = []
    for f in os.listdir(TEMPLATE_FOLDER):
        base = os.path.splitext(f)[0]
        if base == label:
            existing.append(1)
        elif base.startswith(label + "_v"):
            try:
                num = int(base.split("_v")[1])
                existing.append(num)
            except ValueError:
                pass
    if not existing:
        return 2  # v2 (v1 = yang asli tanpa suffix)
    return max(existing) + 1


def main():
    if not os.path.exists(DATASET_FOLDER):
        print(f"Folder {DATASET_FOLDER} tidak ditemukan!")
        return

    files = [f for f in os.listdir(DATASET_FOLDER)
             if f.endswith(('.jpg', '.png', '.jpeg'))]

    # Hanya proses file yang nama-nya mengandung plat (bukan Cars/train)
    plat_files = [f for f in files
                  if not f.lower().startswith(("cars", "train"))]

    print(f"Total foto plat: {len(plat_files)}")

    saved_count = 0
    processed = 0
    matched = 0
    char_counts = {}  # Hitung berapa variasi per karakter

    for fname in plat_files:
        plat_text = get_plat_from_filename(fname)
        if len(plat_text) < 4:
            continue

        img = cv2.imread(os.path.join(DATASET_FOLDER, fname))
        if img is None:
            continue

        processed += 1
        lokasi = cari_lokasi_plat(img)
        if lokasi is None:
            continue

        x, y, w, h = lokasi
        chars = extract_chars(img, x, y, w, h)

        # Hanya simpan kalau jumlah karakter cocok dengan ground truth
        if len(chars) != len(plat_text):
            continue

        matched += 1

        for i, (label, char_img) in enumerate(zip(plat_text, chars)):
            # Batasi maksimal 10 variasi per karakter
            current_count = char_counts.get(label, 0)
            if current_count >= 10:
                continue

            variant_num = get_next_variant(label)
            out_path = os.path.join(TEMPLATE_FOLDER, f"{label}_v{variant_num}.jpg")
            cv2.imwrite(out_path, char_img)
            saved_count += 1
            char_counts[label] = current_count + 1

    print(f"\nHasil:")
    print(f"  Foto diproses:    {processed}")
    print(f"  Plat cocok:       {matched}")
    print(f"  Template disimpan: {saved_count}")
    print(f"\nVariasi per karakter:")
    for label in sorted(char_counts.keys()):
        print(f"  {label}: +{char_counts[label]} variasi baru")


if __name__ == "__main__":
    main()
