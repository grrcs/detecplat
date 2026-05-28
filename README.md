# PlateGuardian - Sistem Deteksi dan Pembacaan Plat Nomor Kendaraan

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.x-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Deskripsi

**PlateGuardian** adalah aplikasi desktop berbasis Python untuk mendeteksi dan membaca plat nomor kendaraan menggunakan teknik **Computer Vision** dan **Template Matching**. Aplikasi ini dibangun dengan PyQt5 untuk antarmuka pengguna yang interaktif dan OpenCV untuk pemrosesan gambar.

### Fitur Utama

- ✅ **Deteksi Otomatis Lokasi Plat** - Menggunakan edge detection dan morphological operations
- ✅ **Pre-processing Multi-tahap** - Grayscale, Gaussian Blur, Canny Edge, dan Otsu Thresholding
- ✅ **Template Matching** - Pengenalan karakter dengan 116 template (A-Z, 0-9) beserta variasinya
- ✅ **Segmentasi Karakter** - Pemisahan karakter individual dari plat nomor
- ✅ **Visualisasi Real-time** - Menampilkan setiap tahap pemrosesan gambar
- ✅ **Uji Akurasi Dataset** - Evaluasi performa sistem dengan dataset lengkap
- ✅ **GUI Intuitif** - Antarmuka pengguna yang mudah digunakan

## 🖼️ Screenshot

```
┌─────────────────────────────────────────────────────────┐
│  [Buka Gambar]  [Proses Deteksi]  [Uji Akurasi Dataset] │
├─────────────────────────────────────────────────────────┤
│  Hasil Deteksi Lokasi Plat:                             │
│  [Gambar kendaraan dengan kotak hijau di plat]          │
├─────────────────────────────────────────────────────────┤
│  Pre-processing Potongan Plat:                          │
│  [Grayscale] [Gaussian] [Canny] [Otsu Threshold]        │
├─────────────────────────────────────────────────────────┤
│  Hasil Segmentasi & Template Matching:                  │
│  [Karakter-karakter yang terdeteksi]                    │
├─────────────────────────────────────────────────────────┤
│              Plat: B 1234 ABC                            │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Instalasi

### Prasyarat

- Python 3.8 atau lebih tinggi
- pip (Python package manager)

### Langkah Instalasi

1. **Clone atau download repository ini**
   ```bash
   git clone <repository-url>
   cd "PCD TUBES - Copy"
   ```

2. **Buat virtual environment (opsional tapi direkomendasikan)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install opencv-python opencv-contrib-python numpy PyQt5
   ```

   Atau jika ada file requirements.txt:
   ```bash
   pip install -r requirements.txt
   ```

## 📂 Struktur Proyek

```
PCD TUBES - Copy/
├── app.py                      # File utama aplikasi
├── README.md                   # Dokumentasi proyek
├── dataset_kendaraan/          # Dataset gambar kendaraan (29 gambar)
│   ├── AA1253BK.jpg
│   ├── AB1034QR.jpg
│   ├── B1015HKB.jpg
│   └── ...
├── dataset_template/           # Template karakter (116 template)
│   ├── A.jpg, A_v2.jpg, A_v3.jpg
│   ├── B.jpg, B_v3.jpg, B_v4.jpg
│   ├── 0.jpg, 0_v3.jpg, 0_v4.jpg
│   └── ...
└── venv/                       # Virtual environment (jika digunakan)
```

## 🎯 Cara Penggunaan

### Menjalankan Aplikasi

```bash
python app.py
```

### Workflow Penggunaan

1. **Buka Gambar**
   - Klik tombol "Buka Gambar"
   - Pilih file gambar kendaraan (format: .jpg, .jpeg, .png)
   - Gambar akan ditampilkan di area preview

2. **Proses Deteksi**
   - Klik tombol "Proses Deteksi & Baca Plat"
   - Sistem akan:
     - Mendeteksi lokasi plat (ditandai kotak hijau)
     - Melakukan pre-processing (4 tahap)
     - Segmentasi karakter
     - Template matching untuk setiap karakter
     - Menampilkan hasil pembacaan plat

3. **Uji Akurasi Dataset**
   - Klik tombol "Uji Akurasi Dataset"
   - Sistem akan memproses semua gambar di folder `dataset_kendaraan`
   - Hasil akurasi ditampilkan dalam tabel detail

## 🔬 Teknologi dan Algoritma

### 1. Deteksi Lokasi Plat
- **CLAHE (Contrast Limited Adaptive Histogram Equalization)** - Meningkatkan kontras
- **Gaussian Blur** - Mengurangi noise
- **Canny Edge Detection** - Deteksi tepi
- **Morphological Closing** - Menghubungkan tepi yang terputus
- **Contour Detection** - Mencari area berbentuk plat (rasio aspek 2:1 hingga 5:1)

### 2. Pre-processing Plat
1. **Grayscale Conversion** - Konversi ke skala abu-abu
2. **Gaussian Blur** - Smoothing untuk mengurangi noise
3. **Canny Edge Detection** - Deteksi tepi karakter
4. **Otsu Thresholding** - Binarisasi adaptif

### 3. Segmentasi Karakter
- **Contour Detection** - Mencari bounding box setiap karakter
- **Filtering** - Membuang noise berdasarkan ukuran dan rasio aspek
- **Sorting** - Mengurutkan karakter dari kiri ke kanan

### 4. Template Matching
- **Multi-template Matching** - Setiap karakter dibandingkan dengan semua variasi template
- **Normalized Cross-Correlation** - Metode `cv2.TM_CCOEFF_NORMED`
- **Best Match Selection** - Memilih template dengan skor tertinggi

## 📊 Dataset

### Dataset Kendaraan
- **Jumlah**: 29 gambar
- **Format**: JPG
- **Naming Convention**: Nama file = plat nomor sebenarnya (ground truth)
- **Contoh**: `B1015HKB.jpg`, `AB1034QR.jpg`, `D1297ALS.jpg`

### Dataset Template
- **Jumlah**: 116 template
- **Karakter**: A-Z (26 huruf) dan 0-9 (10 angka)
- **Variasi**: Setiap karakter memiliki 1-8 variasi (font, style, kondisi berbeda)
- **Format**: JPG, ukuran dinormalisasi ke 30x60 pixel
- **Contoh**: `A.jpg`, `A_v2.jpg`, `A_v3.jpg`, `0.jpg`, `0_v3.jpg`

## 📈 Evaluasi Performa

Aplikasi menyediakan fitur **Uji Akurasi Dataset** yang menghitung:

- **Akurasi Per Karakter** - Persentase karakter yang terbaca dengan benar
- **Akurasi Plat Penuh** - Persentase plat yang terbaca 100% benar
- **Detail Per Gambar** - Tabel hasil untuk setiap gambar:
  - Nama file
  - Ground truth (plat sebenarnya)
  - Hasil deteksi
  - Status (✓ Benar / ✗ Salah)

### Contoh Output Akurasi

```
=== HASIL UJI AKURASI ===
Total Gambar: 29
Plat Benar Penuh: 23 (79.31%)
Akurasi Karakter: 94.52%

┌──────────────┬────────────┬────────────┬────────┐
│ File         │ Seharusnya │ Terbaca    │ Status │
├──────────────┼────────────┼────────────┼────────┤
│ B1015HKB.jpg │ B1015HKB   │ B1015HKB   │   ✓    │
│ AB1034QR.jpg │ AB1034QR   │ AB1034QR   │   ✓    │
│ D1297ALS.jpg │ D1297ALS   │ D1297AL5   │   ✗    │
└──────────────┴────────────┴────────────┴────────┘
```

## 🛠️ Troubleshooting

### Plat Tidak Terdeteksi
- Pastikan gambar memiliki pencahayaan yang cukup
- Plat harus terlihat jelas dan tidak terlalu miring
- Coba gambar dengan resolusi lebih tinggi

### Karakter Salah Terbaca
- Tambahkan lebih banyak variasi template untuk karakter yang sering salah
- Periksa kualitas gambar input
- Sesuaikan parameter threshold jika perlu

### Error saat Menjalankan
- Pastikan semua dependencies terinstall dengan benar
- Periksa versi Python (minimal 3.8)
- Pastikan folder `dataset_template` dan `dataset_kendaraan` ada

## 🔧 Konfigurasi

### Parameter yang Dapat Disesuaikan (di `app.py`)

```python
# Ukuran template (baris 109)
tmpl = cv2.resize(tmpl, (30, 60))

# CLAHE parameters (baris 146)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

# Canny edge detection (baris 149)
edges = cv2.Canny(blur, 100, 200)

# Morphology kernel (baris 150)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 3))

# Rasio aspek plat (baris 158)
aspect_ratio = w / h
if 2.0 <= aspect_ratio <= 5.0:
```

## 📝 Lisensi

Proyek ini dilisensikan di bawah MIT License - lihat file LICENSE untuk detail.

## 👥 Kontributor

- **Tim Pengembang** - Tugas Besar Pengolahan Citra Digital

## 🙏 Acknowledgments

- OpenCV untuk library computer vision
- PyQt5 untuk framework GUI
- Dataset template karakter dari berbagai sumber

## 📞 Kontak

Untuk pertanyaan atau saran, silakan buat issue di repository ini.

---

**Version**: 1.0  
**Last Updated**: 2026  
**Status**: Production Ready ✅
