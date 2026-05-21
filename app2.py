import sys
import cv2
import numpy as np
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                              QVBoxLayout, QHBoxLayout, QWidget, QFileDialog)
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt


class PlateGuardianApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PlateGuardian - Deteksi Plat Nomor dengan Template Matching")
        self.setGeometry(50, 50, 1050, 950)

        self.templates = self.load_templates("dataset_template")
        self.image_path = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # === TOMBOL ===
        btn_layout = QHBoxLayout()
        self.btn_buka = QPushButton("Buka Gambar")
        self.btn_buka.clicked.connect(self.buka_gambar)
        self.btn_proses = QPushButton("Proses Deteksi & Baca Plat")
        self.btn_proses.clicked.connect(self.proses_gambar)
        btn_layout.addWidget(self.btn_buka)
        btn_layout.addWidget(self.btn_proses)
        self.layout.addLayout(btn_layout)

        # === GAMBAR ASLI + KOTAK HIJAU ===
        self.layout.addWidget(QLabel("<b>Hasil Deteksi Lokasi Plat:</b>"))
        self.lbl_gambar = self.buat_label("Pilih gambar kendaraan terlebih dahulu", 300)
        self.layout.addWidget(self.lbl_gambar)

        # === PRE-PROCESSING POTONGAN PLAT (4 tahap) ===
        self.layout.addWidget(QLabel("<b>Pre-processing Potongan Plat:</b>"))
        prep_layout = QHBoxLayout()
        self.lbl_step1 = self.buat_label("1. Grayscale")
        self.lbl_step2 = self.buat_label("2. Gaussian Blur")
        self.lbl_step3 = self.buat_label("3. Canny Edge")
        self.lbl_step4 = self.buat_label("4. Otsu Threshold")
        for lbl in [self.lbl_step1, self.lbl_step2, self.lbl_step3, self.lbl_step4]:
            prep_layout.addWidget(lbl)
        self.layout.addLayout(prep_layout)

        # === HASIL SEGMENTASI & TEMPLATE MATCHING ===
        self.layout.addWidget(QLabel("<b>Hasil Segmentasi & Template Matching:</b>"))
        self.lbl_plat = self.buat_label("Hasil pembacaan karakter", 120)
        self.layout.addWidget(self.lbl_plat)

        # === BAR HASIL PLAT (TAMBAHAN) ===
        self.lbl_hasil = QLabel("Plat: -")
        self.lbl_hasil.setFont(QFont("Consolas", 20, QFont.Bold))
        self.lbl_hasil.setAlignment(Qt.AlignCenter)
        self.lbl_hasil.setStyleSheet(
            "border: 2px solid #4CAF50; background-color: #f0fff0; padding: 12px;"
        )
        self.lbl_hasil.setFixedHeight(65)
        self.layout.addWidget(self.lbl_hasil)

    # ============================================================
    #  UTILITAS
    # ============================================================

    def buat_label(self, teks, tinggi=150):
        lbl = QLabel(teks)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("border: 1px solid gray; background-color: #e0e0e0;")
        lbl.setFixedHeight(tinggi)
        return lbl

    def tampilkan(self, cv_img, label, max_w=220, max_h=150):
        """Konversi gambar OpenCV -> QPixmap dan tampilkan di label."""
        if len(cv_img.shape) == 2:
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_GRAY2RGB)
        else:
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = cv_img.shape
        q_img = QImage(cv_img.data, w, h, ch * w, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(q_img).scaled(max_w, max_h, Qt.KeepAspectRatio))

    def load_templates(self, folder):
        """
        Memuat dataset template karakter (A-Z, 0-9) beserta variasinya.
        File bernama 'D.jpg' dan 'D_v2.jpg' keduanya dianggap template huruf D.
        Template di-resize ke 30x60 dan di-threshold agar siap dibandingkan.
        """
        templates = {}
        if not os.path.exists(folder):
            print("Folder dataset_template tidak ditemukan!")
            return templates
        for fname in os.listdir(folder):
            if fname.endswith(('.png', '.jpg', '.jpeg')):
                label = os.path.splitext(fname)[0].split("_")[0]
                tmpl = cv2.imread(os.path.join(folder, fname), cv2.IMREAD_GRAYSCALE)
                _, tmpl = cv2.threshold(tmpl, 127, 255, cv2.THRESH_BINARY)
                tmpl = cv2.resize(tmpl, (30, 60))
                if label not in templates:
                    templates[label] = []
                templates[label].append(tmpl)
        total = sum(len(v) for v in templates.values())
        print(f"Berhasil memuat {total} template untuk {len(templates)} karakter.")
        return templates

    # ============================================================
    #  BUKA GAMBAR
    # ============================================================

    def buka_gambar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Buka Gambar", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        self.image_path = path
        self.tampilkan(cv2.imread(path), self.lbl_gambar, 800, 300)
        for lbl in [self.lbl_step1, self.lbl_step2, self.lbl_step3,
                     self.lbl_step4, self.lbl_plat]:
            lbl.clear()
            lbl.setText("Menunggu proses...")
        self.lbl_hasil.setText("Plat: -")

    # ============================================================
    #  DETEKSI LOKASI PLAT (internal, tidak ditampilkan)
    # ============================================================

    def cari_lokasi_plat(self, img):
        """
        Mencari lokasi plat dari gambar full secara internal.
        Menggunakan CLAHE + Gaussian Blur + Canny + Morphology Closing
        untuk menemukan contour berbentuk plat.
        Return: (x, y, w, h) atau None.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 100, 200)
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

            if not (2.0 <= rasio <= 5.5):
                continue
            if luas < 500 or luas > luas_gambar * 0.15:
                continue

            # Hitung karakter di area ini
            crop = gray[y:y+h, x:x+w]
            if h < 50:
                scale = 50.0 / h
                crop = cv2.resize(crop, None, fx=scale, fy=scale,
                                  interpolation=cv2.INTER_LINEAR)
            ch_h, ch_w = crop.shape[:2]
            _, bw = cv2.threshold(crop, 0, 255,
                                  cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            char_cnts, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL,
                                            cv2.CHAIN_APPROX_SIMPLE)
            n_chars = sum(1 for c in char_cnts
                          if 3 < cv2.boundingRect(c)[2] < ch_w * 0.35
                          and ch_h * 0.2 < cv2.boundingRect(c)[3] < ch_h * 0.95)

            if n_chars >= 4:
                rasio_bonus = max(0, 1.0 - abs(rasio - 3.5) / 3.0)
                score = n_chars * 1000 + rasio_bonus * 500
                if score > best_score:
                    best_score = score
                    best = (x, y, w, h)

        return best

    # ============================================================
    #  PRE-PROCESSING POTONGAN PLAT
    #  --------------------------------------------------------
    #  Pipeline: Grayscale -> Gaussian Blur -> Canny Edge -> Otsu Threshold
    #  Output akhir (Otsu Threshold) digunakan untuk segmentasi karakter.
    # ============================================================

    def preprocess_plat(self, plat_bgr):
        """
        Melakukan 4 tahap pre-processing pada potongan plat (BGR).
        Return: binary image (hasil Otsu Threshold) untuk segmentasi karakter.
        """

        # ----------------------------------------------------------
        # TAHAP 1: GRAYSCALE
        # ----------------------------------------------------------
        gray = cv2.cvtColor(plat_bgr, cv2.COLOR_BGR2GRAY)
        self.tampilkan(gray, self.lbl_step1)

        # ----------------------------------------------------------
        # TAHAP 2: GAUSSIAN BLUR
        # ----------------------------------------------------------

        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        self.tampilkan(blur, self.lbl_step2)

        # ----------------------------------------------------------
        # TAHAP 3: CANNY EDGE DETECTION
        # ----------------------------------------------------------

        edges = cv2.Canny(blur, 100, 200)
        self.tampilkan(edges, self.lbl_step3)

        # ----------------------------------------------------------
        # TAHAP 4: OTSU THRESHOLD (Binarization)
        # ----------------------------------------------------------
        _, bw = cv2.threshold(blur, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        self.tampilkan(bw, self.lbl_step4)

        return bw

    # ============================================================
    #  TEMPLATE MATCHING (XOR)
    # ============================================================

    def cocokkan_karakter(self, char_bw):
        """
        Mencocokkan satu karakter binary dengan semua template menggunakan
        metode XOR (Exclusive OR):
          1. Resize karakter ke ukuran standar (30x60)
          2. XOR dengan setiap template - hasilnya = pixel yang BERBEDA
          3. Hitung jumlah pixel berbeda (error)
          4. Template dengan error terkecil = hasil terbaik
        """
        char_resized = cv2.resize(char_bw, (30, 60))
        _, char_bin = cv2.threshold(char_resized, 127, 255, cv2.THRESH_BINARY)

        best_label = "?"
        lowest_err = float('inf')

        for label, tmpl_list in self.templates.items():
            for tmpl in tmpl_list:
                diff = cv2.bitwise_xor(char_bin, tmpl)
                error = cv2.countNonZero(diff)
                if error < lowest_err:
                    lowest_err = error
                    best_label = label

        return best_label

    # ============================================================
    #  PROSES UTAMA
    # ============================================================

    def proses_gambar(self):
        if not self.image_path:
            return

        img = cv2.imread(self.image_path)
        img_result = img.copy()

        # LANGKAH 1: Cari lokasi plat (internal, tidak ditampilkan)
        lokasi = self.cari_lokasi_plat(img)

        if lokasi is None:
            self.tampilkan(img_result, self.lbl_gambar, 800, 300)
            self.lbl_plat.setText("Plat tidak terdeteksi")
            self.lbl_hasil.setText("Plat: TIDAK TERDETEKSI")
            for lbl in [self.lbl_step1, self.lbl_step2, self.lbl_step3,
                         self.lbl_step4]:
                lbl.setText("Plat tidak ditemukan")
            return

        x, y, w, h = lokasi
        cv2.rectangle(img_result, (x, y), (x+w, y+h), (0, 255, 0), 3)
        self.tampilkan(img_result, self.lbl_gambar, 800, 300)

        # LANGKAH 2: Crop plat & pre-processing (ditampilkan di 5 panel)
        plat_crop = img[y:y+h, x:x+w]

        # Upscale plat kecil agar pre-processing & threshold bekerja baik
        if h < 50:
            scale = 50.0 / h
            plat_crop = cv2.resize(plat_crop, None, fx=scale, fy=scale,
                                   interpolation=cv2.INTER_LINEAR)

        plat_bw = self.preprocess_plat(plat_crop)

        # LANGKAH 3: Segmentasi karakter & template matching
        plat_h, plat_w = plat_bw.shape[:2]
        contours, _ = cv2.findContours(plat_bw, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])

        # Visualisasi: gambar threshold + kotak merah di tiap karakter
        padding = 40
        plat_vis = cv2.cvtColor(plat_bw, cv2.COLOR_GRAY2BGR)
        plat_vis = cv2.copyMakeBorder(plat_vis, padding, 0, 0, 0,
                                      cv2.BORDER_CONSTANT, value=[220, 220, 220])
        teks = ""

        for cnt in contours:
            cx, cy, cw, ch = cv2.boundingRect(cnt)
            if not (3 < cw < plat_w * 0.35
                    and plat_h * 0.2 < ch < plat_h * 0.95):
                continue

            cv2.rectangle(plat_vis, (cx, cy + padding),
                          (cx + cw, cy + ch + padding), (0, 0, 255), 2)
            label = self.cocokkan_karakter(plat_bw[cy:cy+ch, cx:cx+cw])
            teks += label
            cv2.putText(plat_vis, label, (cx, cy + padding - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        print(f"Plat Terbaca: {teks}")
        self.tampilkan(plat_vis, self.lbl_plat, 500, 120)

        # Update bar hasil plat
        if teks:
            self.lbl_hasil.setText(f"Plat: {teks}")
        else:
            self.lbl_hasil.setText("Plat: TIDAK TERBACA")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PlateGuardianApp()
    window.show()
    sys.exit(app.exec_())
