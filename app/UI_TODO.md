# 🎨 PyQt5 UI Geliştirme Görevleri

> **Son Güncelleme:** 2025-12-07
> **Amaç:** Fonksiyonel ve kullanıcı dostu bir masaüstü arayüzü

---

## 📊 Mevcut Durum

| Özellik | Durum | Notlar |
|---------|-------|--------|
| Karanlık Tema | ✅ Tamamlandı | QPalette ile slate renkleri |
| Ana Pencere Layout | ✅ Tamamlandı | 3 panel: kontrol, graf, sonuçlar |
| Kontrol Paneli | ✅ Tamamlandı | Parametre ayarları |
| CSV Yükleme Butonu | ✅ Tamamlandı | Hocanın verisini yükler |
| Demand Seçici | ✅ Tamamlandı | 30 talep çiftinden seçim |
| Graf Görselleştirme | ✅ Tamamlandı | PyQtGraph, 250+ düğüm |
| Sonuç Paneli | ✅ Tamamlandı | Tek sonuç ve karşılaştırma |
| Zoom Kontrolleri | ✅ Tamamlandı | +, -, Fit butonları |
| Status Bar | ✅ Tamamlandı | Durum mesajları |
| Header | ❌ Eksik | Logo ve proje bilgisi |
| Footer | ❌ Eksik | Algoritma listesi |
| Deney Paneli | ❌ Eksik | Toplu test çalıştırma |
| Tooltip'ler | ❌ Eksik | Düğüm/kenar bilgisi |
| Legend | ❌ Eksik | Renk açıklamaları |
| Path Animasyonu | ❌ Eksik | Parçacık efekti |
| Fullscreen | ❌ Eksik | Graf tam ekran |

---

## ✅ TAMAMLANAN ÖZELLİKLER

### 1. CSV Veri Yükleme (Yeni Eklendi)

**Dosya:** `src/ui/components/control_panel.py`

```
┌─────────────────────────────────────┐
│ 📁 Proje Verisini Yükle (CSV)       │  ← Yeşil buton
├─────────────────────────────────────┤
│ — veya Rastgele Oluştur —           │
│ Düğüm (n): [250]                    │
│ Olasılık (p): [0.4]                 │
│ Seed: [42]                          │
│ 🔄 Rastgele Graf Oluştur            │
└─────────────────────────────────────┘
```

**Özellikler:**
- [x] CSV yükleme butonu (yeşil, öne çıkarılmış)
- [x] `graph_data/` klasöründen otomatik yükleme
- [x] NodeData, EdgeData, DemandData parsing
- [x] Yükleme sonrası graf bilgisi gösterimi

---

### 2. Demand Seçici (Yeni Eklendi)

**Dosya:** `src/ui/components/control_panel.py`

```
┌─────────────────────────────────────┐
│ 📋 Talep Çiftleri:                  │
│ [#1: 8 → 44 (200 Mbps)         ▼]  │
├─────────────────────────────────────┤
│ — veya Manuel Seçim —               │
│ Kaynak (S): [8]                     │
│ Hedef (D): [44]                     │
└─────────────────────────────────────┘
```

**Özellikler:**
- [x] ComboBox ile 30 talep çifti
- [x] Format: `#N: kaynak → hedef (bandwidth Mbps)`
- [x] Seçim yapınca source/dest otomatik güncellenir
- [x] Graf üzerinde kaynak/hedef işaretlenir
- [x] CSV yüklenmediğinde gizli kalır

---

### 3. Graf Görselleştirme (Güncellendi)

**Dosya:** `src/ui/components/graph_widget.py`

**Özellikler:**
- [x] PyQtGraph ile performanslı render
- [x] 12,452 kenar sorunsuz gösterim
- [x] Kaynak düğüm: Yeşil, büyük (20px)
- [x] Hedef düğüm: Kırmızı, büyük (20px)
- [x] Path düğümleri: Amber, orta (14px)
- [x] Diğer düğümler: Gri, küçük (8px)
- [x] Path kenarları: Amber, kalın (4px)
- [x] Diğer kenarlar: Gri, ince (0.5px)
- [x] Zoom in/out/fit butonları
- [x] Düğüme tıklama (kaynak/hedef seçimi)
- [x] Python 3.13 + numpy uyumluluğu (np.nan kullanımı)

---

## 🔴 KRİTİK EKSİKLER (Öncelik 1)

### 1. Experiments Panel (Deney Paneli)

**Dosya:** `src/ui/components/experiments_panel.py` (Yeni oluşturulacak)

```
┌─────────────────────────────────────┐
│ 🧪 Deneyler                         │
├─────────────────────────────────────┤
│ Test Sayısı:    [20        ]        │
│ Tekrar Sayısı:  [5         ]        │
│                                     │
│ Algoritmalar:                       │
│ [x] Genetic Algorithm               │
│ [x] Ant Colony (ACO)                │
│ [x] Particle Swarm (PSO)            │
│ [x] Simulated Annealing             │
│ [x] Q-Learning                      │
│ [x] SARSA                           │
│                                     │
│ [▶️ Deneyleri Çalıştır           ]  │
│                                     │
│ ████████████░░░░░░░░ 60%            │
│ Test 12/20 - ACO çalışıyor...       │
├─────────────────────────────────────┤
│ [📄 CSV Export] [📋 JSON Export]    │
└─────────────────────────────────────┘
```

**Yapılacaklar:**
- [ ] ExperimentsPanel widget oluştur
- [ ] Test sayısı SpinBox (min: 1, max: 100, default: 20)
- [ ] Tekrar sayısı SpinBox (min: 1, max: 20, default: 5)
- [ ] Algoritma seçim checkboxları (6 adet)
- [ ] "Deneyleri Çalıştır" butonu
- [ ] Progress bar (deney ilerlemesi)
- [ ] Durum label (hangi test, hangi algoritma)
- [ ] CSV/JSON export butonları
- [ ] main_window.py'ye entegrasyon
- [ ] experiment_runner.py ile bağlantı

**Sinyaller:**
```python
run_experiments_requested = pyqtSignal(int, int, list)  # n_tests, n_repeats, algorithms
export_csv_requested = pyqtSignal()
export_json_requested = pyqtSignal()
```

---

### 2. Header Bileşeni

**Dosya:** `src/ui/components/header_widget.py` (Yeni oluşturulacak)

```
┌─────────────────────────────────────────────────────────────────┐
│ [🔷] QoS Routing Optimizer          Düğüm: 250 | Kenar: 12,452 │
│      BSM307 - Bilgisayar Ağları                    [Bağlı ✓]   │
└─────────────────────────────────────────────────────────────────┘
```

**Yapılacaklar:**
- [ ] HeaderWidget sınıfı oluştur
- [ ] Logo ikonu (gradient veya basit ikon)
- [ ] Ana başlık: "QoS Routing Optimizer"
- [ ] Alt başlık: "BSM307 - Bilgisayar Ağları Projesi"
- [ ] Düğüm sayısı göstergesi
- [ ] Kenar sayısı göstergesi
- [ ] Bağlantı durumu badge (is_connected)
- [ ] Graf yüklendiğinde güncelleme

---

### 3. Sonuç Export

**Dosya:** `src/ui/components/results_panel.py` (Güncelleme)

**Yapılacaklar:**
- [ ] "CSV Export" butonu ekle
- [ ] "JSON Export" butonu ekle
- [ ] Karşılaştırma tablosunu dışa aktarma
- [ ] Dosya kaydetme dialogu

---

## 🟠 ÖNEMLİ EKSİKLER (Öncelik 2)

### 4. Tooltip'ler

**Dosya:** `src/ui/components/graph_widget.py` (Güncelleme)

**Düğüm Tooltip:**
```
┌──────────────────────┐
│ Node 42              │
│ Gecikme: 1.23 ms     │
│ Güvenilirlik: 98.5%  │
└──────────────────────┘
```

**Kenar Tooltip:**
```
┌─────────────────────────┐
│ Edge 42 → 67            │
│ Bant genişliği: 500 Mbps│
│ Gecikme: 8.5 ms         │
│ Güvenilirlik: 97.2%     │
└─────────────────────────┘
```

**Yapılacaklar:**
- [ ] Düğüm hover event'i yakala
- [ ] QToolTip ile bilgi göster
- [ ] Kenar hover (daha zor, öncelik düşük)

---

### 5. Legend (Açıklama)

**Dosya:** `src/ui/components/graph_widget.py` içinde

```
┌────────────────────────────────────┐
│ ● Kaynak  ● Hedef  ● Yol  ● Diğer │
└────────────────────────────────────┘
```

**Yapılacaklar:**
- [ ] Legend widget oluştur (graph_widget içinde)
- [ ] Sol alt köşede konumlandır
- [ ] Renkli daireler + etiketler
- [ ] Yarı saydam arka plan

---

### 6. Path Bilgi Kutusu

**Dosya:** `src/ui/components/graph_widget.py` içinde

```
┌─────────────────────────────────────┐
│ 📍 Bulunan Yol                      │
│ 5 hop: 8 → 23 → 67 → 156 → 44      │
└─────────────────────────────────────┘
```

**Yapılacaklar:**
- [ ] Path info widget oluştur
- [ ] Sol üst köşede konumlandır
- [ ] Hop sayısı göster
- [ ] Yolu kısaltarak göster (max 5 düğüm + ...)

---

## 🟢 DÜŞÜK ÖNCELİK (Öncelik 3)

### 7. Footer Bileşeni

```
┌─────────────────────────────────────────────────────────────────┐
│ BSM307 QoS Routing • GA • ACO • PSO • SA • Q-Learning • SARSA  │
└─────────────────────────────────────────────────────────────────┘
```

- [ ] FooterWidget oluştur
- [ ] Algoritma listesi (• ile ayrılmış)
- [ ] Ortalanmış metin

---

### 8. Fullscreen Modu

- [ ] Graf için fullscreen butonu
- [ ] ESC ile çıkış
- [ ] İpucu mesajı

---

### 9. Path Animasyonu

- [ ] Parçacık efekti (QTimer ile)
- [ ] Path boyunca hareket
- [ ] Amber renk (#fcd34d)

---

### 10. Glow Efekti

- [ ] Kaynak düğüm yeşil glow
- [ ] Hedef düğüm kırmızı glow
- [ ] Path düğümleri amber glow

---

## 📁 Dosya Yapısı

```
src/ui/
├── __init__.py
├── main_window.py              # ✅ Ana pencere
├── styles.py                   # 📝 TODO: Ortak stiller
└── components/
    ├── __init__.py
    ├── control_panel.py        # ✅ Kontrol paneli + CSV + Demand
    ├── graph_widget.py         # ✅ Graf görselleştirme
    ├── results_panel.py        # ✅ Sonuç paneli
    ├── header_widget.py        # 🆕 TODO: Header
    ├── footer_widget.py        # 🆕 TODO: Footer
    └── experiments_panel.py    # 🆕 TODO: Deney paneli
```

---

## 🎨 Renk Paleti

| Kullanım | Renk | Hex |
|----------|------|-----|
| Ana arka plan | Slate 900 | `#0f172a` |
| Panel arka plan | Slate 800 | `#1e293b` |
| Border | Slate 700 | `#334155` |
| İkincil metin | Slate 400 | `#94a3b8` |
| Ana metin | Slate 200 | `#e2e8f0` |
| Kaynak düğüm | Green 500 | `#22c55e` |
| Hedef düğüm | Red 500 | `#ef4444` |
| Path düğümler | Amber 500 | `#f59e0b` |
| Normal düğümler | Slate 600 | `#475569` |
| Graf oluştur | Blue 500 | `#3b82f6` |
| Optimize et | Purple 500 | `#8b5cf6` |
| Karşılaştır | Pink 500 | `#ec4899` |
| CSV yükle | Green 500 | `#10b981` |

---

## 📏 Boyutlar

| Eleman | Değer |
|--------|-------|
| Minimum pencere | 1200 x 800 px |
| Header yüksekliği | 60 px |
| Footer yüksekliği | 30 px |
| Sol panel genişliği | 300 px |
| Sağ panel genişliği | 320 px |
| Düğüm boyutu (normal) | 8 px |
| Düğüm boyutu (S/D) | 20 px |
| Düğüm boyutu (path) | 14 px |
| Kenar kalınlığı (normal) | 0.5 px |
| Kenar kalınlığı (path) | 4 px |

---

## ✅ Tamamlanma Durumu

```
Temel UI:              ████████████████████ 100%
CSV Yükleme:           ████████████████████ 100%
Demand Seçici:         ████████████████████ 100%
Graf Görselleştirme:   ████████████████████ 100%
Sonuç Paneli:          ████████████████████ 100%
Header:                ░░░░░░░░░░░░░░░░░░░░   0%
Footer:                ░░░░░░░░░░░░░░░░░░░░   0%
Deney Paneli:          ░░░░░░░░░░░░░░░░░░░░   0%
Tooltip'ler:           ░░░░░░░░░░░░░░░░░░░░   0%
Legend:                ░░░░░░░░░░░░░░░░░░░░   0%
Export:                ░░░░░░░░░░░░░░░░░░░░   0%

GENEL UI:              ████████████░░░░░░░░  60%
```

---

## 🔗 İlgili Dosyalar

- `backend-todo.md` - Backend yapılacaklar
- `project_status.md` - Genel proje durumu
- `DEVELOPMENT_GUIDE.md` - Geliştirme kılavuzu

---

*Doküman Versiyonu: 2.0*
*Son Güncelleme: 7 Aralık 2025*
