[README.md](https://github.com/user-attachments/files/28355331/README.md)
<![CDATA[# 🛡️ PlateGuardian

> **Deteksi & Pembacaan Plat Nomor Kendaraan Indonesia menggunakan Template Matching (XOR)**

Aplikasi desktop berbasis **Python + PyQt5 + OpenCV** untuk mendeteksi lokasi plat nomor pada gambar kendaraan, kemudian membaca karakter plat menggunakan metode **Template Matching** dengan operasi **Bitwise XOR**.

---

## 📋 Daftar Isi

- [Fitur](#-fitur)
- [Screenshot](#-screenshot)
- [Teknologi](#-teknologi)
- [Struktur Project](#-struktur-project)
- [Instalasi](#-instalasi)
- [Cara Penggunaan](#-cara-penggunaan)
- [Pipeline Pemrosesan](#-pipeline-pemrosesan)
- [Metode Template Matching (XOR)](#-metode-template-matching-xor)
- [Pengujian Akurasi](#-pengujian-akurasi)
- [Dataset](#-dataset)

---

## ✨ Fitur

| Fitur | Deskripsi |
|---|---|
| 🔍 **Deteksi Lokasi Plat** | Mendeteksi area plat nomor secara otomatis dari gambar kendaraan |
| 🖼️ **Visualisasi Pre-processing** | Menampilkan 4 tahap pre-processing (Grayscale → Blur → Canny → Otsu) |
| 🔤 **Pembacaan Karakter** | Mengenali karakter plat (A-Z, 0-9) menggunakan Template Matching XOR |
| 📊 **Uji Akurasi Dataset** | Menguji seluruh dataset secara batch dan menampilkan hasil akurasi |
| 💾 **Ekspor CSV** | Menyimpan hasil pengujian akurasi ke file CSV |
| 🖥️ **GUI Interaktif** | Antarmuka desktop yang mudah digunakan dengan PyQt5 |

---

## 🛠️ Teknologi

| Komponen | Teknologi |
|---|---|
| Bahasa | Python 3.x |
| GUI | PyQt5 |
| Image Processing | OpenCV (`cv2`) |
| Komputasi | NumPy |

---

## 📁 Struktur Project

```
PlateGuardian/
├── app2.py                  # File utama aplikasi
├── dataset_kendaraan/       # 29 gambar kendaraan untuk pengujian
│   ├── AA1253BK.jpg
│   ├── B1338SMP.jpg
│   ├── D1522AIP.jpg
│   └── ...
├── dataset_template/        # 116 template karakter (A-Z, 0-9) + variasi
│   ├── A.jpg
│   ├── A_v2.jpg
│   ├── 0.jpg
│   ├── 0_v3.jpg
│   └── ...
├── README.md
└── requirements.txt
```

---

## ⚙️ Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/username/PlateGuardian.git
cd PlateGuardian
```

### 2. Buat Virtual Environment (Opsional)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install opencv-python numpy PyQt5
```

### 4. Jalankan Aplikasi

```bash
python app2.py
```

---

## 🚀 Cara Penggunaan

### Mode Deteksi (Gambar Tunggal)

1. Klik **"Buka Gambar"** → pilih foto kendaraan
2. Klik **"Proses Deteksi & Baca Plat"**
3. Lihat hasil:
   - Lokasi plat terdeteksi (kotak hijau)
   - 4 tahap pre-processing
   - Segmentasi & pengenalan karakter
   - Teks plat terbaca

### Mode Uji Akurasi (Batch Testing)

1. Klik **"Uji Akurasi Dataset"**
2. Program memproses seluruh 29 gambar di `dataset_kendaraan/`
3. Muncul dialog hasil berisi:
   - Tabel perbandingan **Ground Truth** vs **Prediksi**
   - Persentase **Akurasi Full Match** dan **Akurasi Per-Karakter**
4. Klik **"💾 Simpan Hasil ke CSV"** untuk ekspor hasil

---

## 🔬 Pipeline Pemrosesan

Proses deteksi dan pembacaan plat nomor terdiri dari beberapa tahap:

```
┌─────────────────┐
│  Gambar Input    │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Deteksi Lokasi  │  ← CLAHE + Gaussian Blur + Canny Edge + Morphology
│ Plat Nomor      │    Closing + Contour Analysis
└────────┬────────┘
         ▼
┌─────────────────┐
│ Pre-processing   │
│ Potongan Plat   │
│                  │
│ 1. Grayscale    │
│ 2. Gaussian Blur│
│ 3. Canny Edge   │
│ 4. Otsu Thresh  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Segmentasi       │  ← Contour detection pada citra biner
│ Karakter        │    Filter berdasarkan rasio lebar/tinggi
└────────┬────────┘
         ▼
┌─────────────────┐
│ Template         │  ← Bitwise XOR matching
│ Matching (XOR)  │    Karakter di-resize ke 30×60 px
└────────┬────────┘
         ▼
┌─────────────────┐
│ Hasil Plat      │  → Contoh: "B1338SMP"
└─────────────────┘
```

### Detail Tiap Tahap

| Tahap | Metode | Fungsi |
|---|---|---|
| **1. Grayscale** | `cv2.cvtColor(BGR2GRAY)` | Konversi ke citra abu-abu |
| **2. Gaussian Blur** | `cv2.GaussianBlur(5,5)` | Reduksi noise |
| **3. Canny Edge** | `cv2.Canny(100, 200)` | Deteksi tepi karakter |
| **4. Otsu Threshold** | `cv2.threshold(OTSU)` | Binarisasi adaptif untuk segmentasi |

---

## 🔣 Metode Template Matching (XOR)

Pengenalan karakter menggunakan metode **Bitwise XOR**:

```
Karakter Input (30×60)     Template "B" (30×60)
┌──────────┐               ┌──────────┐
│ ██████   │               │ ██████   │
│ █    █   │    XOR        │ █    █   │
│ ██████   │  ═══════►     │ ██████   │
│ █    █   │               │ █    █   │
│ ██████   │               │ ██████   │
└──────────┘               └──────────┘

Hasil XOR = pixel yang BERBEDA
Error = jumlah pixel putih (non-zero) pada hasil XOR
Template dengan error TERKECIL = karakter terbaik
```

**Langkah-langkah:**
1. Resize karakter ke ukuran standar **30 × 60 pixel**
2. Threshold ke citra biner (hitam-putih)
3. Operasi **XOR** dengan setiap template → menghasilkan pixel yang berbeda
4. Hitung jumlah pixel berbeda (`cv2.countNonZero`) sebagai **error**
5. Template dengan **error terkecil** = hasil prediksi

---

## 📊 Pengujian Akurasi

### Rumus

```
Akurasi (%) = (Jumlah Benar / Jumlah Dataset) × 100
```

### Contoh Perhitungan

```
Misal dari 29 gambar, 10 diprediksi benar:

Akurasi = (10 / 29) × 100 = 34.5%
```

### Metrik yang Diukur

| Metrik | Deskripsi |
|---|---|
| **Akurasi Full Match** | Persentase gambar yang seluruh karakter platnya diprediksi benar |
| **Akurasi Per-Karakter** | Persentase karakter yang cocok posisi per posisi dengan ground truth |

### Ekspor Hasil

Hasil pengujian dapat diekspor ke file **CSV** dengan format:

```csv
No,Nama File,Plat Sebenarnya (Ground Truth),Hasil Prediksi,Keterangan
1,AA1253BK.jpg,AA1253BK,AA1253BK,Benar
2,AB1034QR.jpg,AB1034QR,AB1O34QR,Salah
...

Jumlah Dataset,29
Jumlah Benar,10
Akurasi Full Match,(10/29) x 100,34.5%
Akurasi Per-Karakter,(150/200) x 100,75.0%
```

---

## 📂 Dataset

### Dataset Kendaraan (`dataset_kendaraan/`)
- **Jumlah:** 29 gambar
- **Format:** JPG
- **Ground Truth:** Nama file = plat sebenarnya (contoh: `B1338SMP.jpg`)
- **Kode Wilayah:** AA, AB, AD, B, BM, D, H, K

### Dataset Template (`dataset_template/`)
- **Jumlah:** 116 template
- **Karakter:** A-Z (26 huruf) + 0-9 (10 angka)
- **Variasi:** Setiap karakter memiliki beberapa variasi (contoh: `D.jpg`, `D_v2.jpg`, `D_v3.jpg`)
- **Ukuran Standar:** Di-resize ke 30 × 60 pixel saat dimuat

---

## 📄 Lisensi

Project ini dibuat untuk keperluan **Tugas Besar mata kuliah Pengolahan Citra Digital (PCD)**.

---

<p align="center">
  Dibuat dengan ❤️ menggunakan Python, OpenCV, dan PyQt5
</p>
]]>
