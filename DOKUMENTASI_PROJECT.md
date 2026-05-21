# Dokumentasi Project Deteksi Plat Nomor Kendaraan

## 1. Arsitektur Umum Sistem

Sistem terdiri dari **3 tahap utama**:

1. **Deteksi Lokasi Plat** - Mencari area plat pada gambar full
2. **Pre-processing** - Memproses potongan plat untuk segmentasi
3. **Template Matching** - Mengenali karakter satu per satu

---

## 2. Deteksi Lokasi Plat

**Fungsi**: `cari_lokasi_plat()` (baris 130-186)

**Pipeline**:

```
Image (BGR) → Grayscale → CLAHE → Gaussian Blur → Canny Edge → Morphology Close → Find Contours → Filter → Select Best
```

### Penjelasan Setiap Tahap

| Tahap | Parameter | Fungsi |
|-------|-----------|--------|
| **Grayscale** | `cv2.COLOR_BGR2GRAY` | Mengurangi 3 channel warna menjadi 1 channel intensitas. Warna tidak relevan untuk deteksi bentuk plat. |
| **CLAHE** | `clipLimit=2.0, tileGridSize=(8,8)` | Contrast Limited Adaptive Histogram Equalization. Menyeimbangkan kontras gambar yang terlalu gelap/terang akibat pencahayaan tidak merata. Berbeda dengan histogram equalization biasa, CLAHE membagi gambar menjadi grid 8x8 dan menyeimbangkan kontras lokal per-tile. |
| **Gaussian Blur** | `kernel (5,5), σ=0` | Menghilangkan noise sensor kamera dan artefak JPEG sebelum edge detection. Kernel 5x5 dipilih karena cukup besar untuk menghilangkan noise kecil tapi tidak terlalu besar sampai mengaburkan tepi plat. |
| **Canny Edge** | `threshold 100-200` | Deteksi tepi dengan hysteresis. Pixel dengan gradien >200 = strong edge (pasti tepi), 100-200 = weak edge (tepi jika terhubung strong edge), <100 = dibuang sebagai noise. |
| **Morphology Close** | `kernel (13,3), MORPH_CLOSE` | Menghubungkan tepi yang terputus. Kernel berbentuk horizontal lebar (13x3) karena plat memiliki rasio lebar:tinggi besar. Close operation = dilasi lalu erosi, menutup celah kecil antar tepi karakter. |

### Filter Kandidat Plat

```python
if not (2.0 <= rasio <= 5.5):  # Aspect ratio plat: lebar 2-5.5x tinggi
    continue
if luas < 500 or luas > luas_gambar * 0.15:  # Luas plat: 500px - 15% gambar
    continue
```

**Scoring system**:

```python
score = n_chars * 1000 + rasio_bonus * 500
```

- Kandidat dengan karakter terbanyak dan aspect ratio mendekati 3.5 mendapat skor tertinggi
- Minimal 4 karakter untuk validasi

---

## 3. Pre-processing Potongan Plat

**Fungsi**: `preprocess_plat()` (baris 198-267)

**Pipeline**:

```
Plat Crop (BGR) → Grayscale → Gaussian Blur → Canny Edge (visualisasi) → Otsu Threshold → Binary Image
```

### Penjelasan Detail

#### Tahap 1: Grayscale

```python
gray = cv2.cvtColor(plat_bgr, cv2.COLOR_BGR2GRAY)
```

**Kenapa**: Citra plat memiliki 3 channel warna (BGR). Untuk memisahkan karakter dari background, warna tidak relevan - kita hanya butuh perbedaan intensitas cahaya antara huruf (gelap) dan background plat (terang). Konversi ke 1 channel menyederhanakan proses selanjutnya.

#### Tahap 2: Gaussian Blur

```python
blur = cv2.GaussianBlur(gray, (5, 5), 0)
```

**Kenapa**: Potongan plat masih mengandung noise dari sensor kamera dan artefak kompresi JPEG. Noise berupa variasi piksel acak yang bisa membuat threshold menghasilkan titik-titik hitam/putih palsu di sekitar karakter.

Gaussian Blur kernel (5,5) menghaluskan noise menggunakan distribusi Gaussian - piksel pusat berbobot besar, piksel tepi berbobot kecil. Hasilnya: permukaan plat lebih halus tapi tepi karakter tetap terjaga.

#### Tahap 3: Canny Edge Detection

```python
edges = cv2.Canny(blur, 100, 200)
```

**Kenapa**: Ditampilkan untuk memvisualisasikan tepi karakter yang berhasil terdeteksi pada potongan plat. Canny menggunakan hysteresis thresholding:

- Gradien > 200 = pasti tepi karakter (strong edge)
- Gradien 100-200 = tepi hanya jika terhubung strong edge
- Gradien < 100 = bukan tepi (noise, dibuang)

Tahap ini ditampilkan sebagai visualisasi - menunjukkan bahwa tepi setiap karakter berhasil terdeteksi dengan jelas.

#### Tahap 4: Otsu Threshold

```python
_, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
```

**Kenapa**: Untuk segmentasi karakter, kita butuh gambar binary (hitam-putih tegas) - karakter = putih, background = hitam.

Otsu Threshold menentukan nilai threshold secara OTOMATIS dengan mencari nilai yang memaksimalkan variansi antar kelas (karakter vs background). Tidak perlu menebak threshold manual karena Otsu menghitung dari histogram gambar.

`THRESH_BINARY_INV` digunakan karena karakter pada plat berwarna gelap di atas background terang - inverse membuat karakter menjadi putih (foreground) untuk findContours.

### Perbandingan Otsu vs Threshold Manual

| Metode | Kelebihan | Kekurangan |
|--------|-----------|------------|
| **Threshold Manual** | Sederhana, cepat | Tidak adaptif, perlu tuning per-gambar |
| **Otsu Threshold** | Otomatis, adaptif terhadap histogram | Asumsi histogram bimodal |

**Rumus Otsu**: Memaksimalkan σ²_between = ω₀ω₁(μ₀ - μ₁)²

---

## 4. Segmentasi Karakter

**Lokasi**: baris 338-360

**Metode**: Connected Component Analysis via `findContours`

```python
contours, _ = cv2.findContours(plat_bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])  # Sort left-to-right
```

### Parameter findContours

| Parameter | Nilai | Fungsi |
|-----------|-------|--------|
| `RETR_EXTERNAL` | - | Hanya mengambil contour terluar (tidak termasuk hole di dalam karakter) |
| `CHAIN_APPROX_SIMPLE` | - | Mengkompresi contour horizontal/vertikal menjadi endpoint saja (hemat memori) |

### Filter Karakter

```python
if not (3 < cw < plat_w * 0.35          # Lebar: 3px - 35% lebar plat
        and plat_h * 0.2 < ch < plat_h * 0.95):  # Tinggi: 20%-95% tinggi plat
    continue
```

**Justifikasi Filter**:

| Kondisi | Alasan |
|---------|--------|
| `cw < 3` | Terlalu kecil, kemungkinan noise |
| `cw > 35% plat_w` | Terlalu lebar, kemungkinan bukan karakter tunggal |
| `ch < 20% plat_h` | Terlalu pendek, kemungkinan titik/noise |
| `ch > 95% plat_h` | Terlalu tinggi, kemungkinan border plat |

---

## 5. Template Matching dengan XOR

**Fungsi**: `cocokkan_karakter()` (baris 273-296)

### Algoritma

```
1. Resize karakter ke 30x60 (standar ukuran template)
2. Threshold binary (127)
3. XOR dengan setiap template
4. Hitung pixel berbeda (error)
5. Template dengan error terkecil = hasil
```

### Kode

```python
def cocokkan_karakter(self, char_bw):
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
```

### Kenapa XOR?

**Logic XOR**:

```
A XOR B = 1 jika A ≠ B
A XOR B = 0 jika A = B
```

Semakin kecil `cv2.countNonZero(diff)` = semakin mirip

### Perbandingan Metode Template Matching

| Metode | Kelebihan | Kekurangan |
|--------|-----------|------------|
| **cv2.matchTemplate(TM_CCOEFF)** | Normalized, robust terhadap brightness | Kompleks, butuh floating-point |
| **cv2.matchTemplate(TM_SQDIFF)** | Sederhana | Sensitif terhadap perbedaan ukuran |
| **XOR (bitwise_xor)** | Sangat cepat, integer operation, intuitif | Butuh binary image, sensitif terhadap noise |

**XOR dipilih karena**:

1. **Sederhana**: Bitwise operation sangat cepat
2. **Intuitif**: Langsung menghitung "berapa pixel yang beda"
3. **Cocok untuk binary image**: Karakter sudah di-threshold

---

## 6. Template Loading

**Fungsi**: `load_templates()` (baris 86-107)

**Struktur folder**:

```
dataset_template/
├── A.jpg, A_v2.jpg      # Template huruf A (2 variasi)
├── B.jpg, B_v2.jpg
├── 0.jpg, 0_v2.jpg      # Template angka 0
└── ...
```

### Kode

```python
def load_templates(self, folder):
    templates = {}
    for fname in os.listdir(folder):
        if fname.endswith(('.png', '.jpg', '.jpeg')):
            label = os.path.splitext(fname)[0].split("_")[0]  # A_v2.jpg -> A
            tmpl = cv2.imread(os.path.join(folder, fname), cv2.IMREAD_GRAYSCALE)
            _, tmpl = cv2.threshold(tmpl, 127, 255, cv2.THRESH_BINARY)
            tmpl = cv2.resize(tmpl, (30, 60))
            if label not in templates:
                templates[label] = []
            templates[label].append(tmpl)
    return templates
```

### Preprocessing Template

| Tahap | Parameter | Fungsi |
|-------|-----------|--------|
| Threshold | 127 | Binary standar |
| Resize | 30x60 | Rasio 1:2, konsisten dengan proporsi karakter plat Indonesia |

---

## 7. Alur Lengkap Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                    TOMBOL "PROSES" DITEKAN                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Load Gambar (cv2.imread)                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. cari_lokasi_plat()                                       │
│     ├── Grayscale                                            │
│     ├── CLAHE (contrast enhancement)                         │
│     ├── Gaussian Blur                                        │
│     ├── Canny Edge                                           │
│     ├── Morphology Close                                     │
│     ├── Find Contours                                        │
│     ├── Filter by Aspect Ratio & Area                        │
│     └── Select Best Candidate → (x, y, w, h)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Crop Plat & Upscale (jika h < 50)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. preprocess_plat()                                        │
│     ├── Grayscale          → Panel 1                         │
│     ├── Gaussian Blur      → Panel 2                         │
│     ├── Canny Edge         → Panel 3                         │
│     └── Otsu Threshold     → Panel 4 + Return binary         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. findContours → Sort left-to-right                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Untuk setiap contour yang valid:                         │
│     ├── Extract bounding box                                 │
│     ├── cocokkan_karakter() → Label                          │
│     └── Append ke string hasil                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Tampilkan hasil di GUI                                   │
│     ├── Gambar asli + kotak hijau                            │
│     ├── 4 panel pre-processing                               │
│     ├── Segmentasi + label karakter                          │
│     └── Bar hasil plat                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Parameter-Parameter Kunci

| Parameter | Nilai | Justifikasi |
|-----------|-------|-------------|
| CLAHE clipLimit | 2.0 | Batas clipping kontras. Terlalu tinggi = over-enhancement, terlalu rendah = tidak efektif |
| CLAHE tileGridSize | 8x8 | Ukuran tile untuk adaptasi lokal. 8x8 cukup untuk variasi pencahayaan lokal |
| Gaussian kernel | 5x5 | Kompromi antara noise reduction dan edge preservation |
| Canny threshold | 100-200 | Hysteresis range standar untuk edge detection |
| Morphology kernel | 13x3 | Horizontal lebar untuk menghubungkan tepi plat yang memanjang |
| Aspect ratio plat | 2.0-5.5 | Berdasarkan standar plat Indonesia (rasio ~3-4) |
| Template size | 30x60 | Rasio 1:2, proporsi karakter plat standar |
| Character width filter | 3-35% plat_w | Menghilangkan noise dan blob terlalu besar |
| Character height filter | 20-95% plat_h | Menghilangkan noise dan border |

---

## 9. Kelebihan & Keterbatasan

### Kelebihan

- Tidak butuh machine learning/deep learning
- Cepat (real-time untuk GUI)
- Template matching robust untuk font standar
- Visualisasi step-by-step membantu debugging

### Keterbatasan

- Sensitif terhadap font yang berbeda dari template
- Kesulitan pada plat kotor/rusak
- Deteksi lokasi bisa gagal pada sudut miring
- Tidak menangani plat multi-baris (plat baru)

---

## 10. Referensi Metode

| Metode | Referensi |
|--------|-----------|
| CLAHE | Zuiderveld, K. (1994). Contrast Limited Adaptive Histogram Equalization. |
| Canny Edge | Canny, J. (1986). A Computational Approach to Edge Detection. |
| Otsu Threshold | Otsu, N. (1979). A Threshold Selection Method from Gray-Level Histograms. |
| Morphology | Haralick, R. M., et al. (1987). Image Analysis Using Mathematical Morphology. |
