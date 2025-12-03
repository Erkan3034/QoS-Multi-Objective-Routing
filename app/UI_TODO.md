# 🎨 PyQt5 UI Geliştirme Görevleri

> **Amaç:** Web (React) arayüzüyle birebir aynı görünüm ve işlevsellik

---

## 📊 Mevcut Durum vs Hedef

| Özellik | Web (React) | PyQt5 Mevcut | Durum |
|---------|-------------|--------------|-------|
| Header (Logo/Başlık) | ✅ | ❌ | 🔴 Eksik |
| Graf Bilgi Göstergesi | ✅ | ❌ | 🔴 Eksik |
| Graf Görselleştirme | react-force-graph | PyQtGraph | 🟡 Farklı |
| Force-directed Layout | ✅ Animasyonlu | ✅ Statik | 🟡 Kısmen |
| Düğüm Hover Tooltip | ✅ Detaylı | ❌ | 🔴 Eksik |
| Kenar Hover Tooltip | ✅ Detaylı | ❌ | 🔴 Eksik |
| Path Parçacık Animasyonu | ✅ | ❌ | 🔴 Eksik |
| Düğüm Glow Efekti | ✅ | ❌ | 🔴 Eksik |
| Kontrol Paneli | ✅ | ✅ | ✅ Tamam |
| Sonuç Paneli | ✅ | ✅ | ✅ Tamam |
| Karşılaştırma Tablosu | ✅ | ✅ | ✅ Tamam |
| **Deney Paneli** | ✅ ExperimentsPanel | ❌ | 🔴 Eksik |
| Footer | ✅ | StatusBar | 🟡 Farklı |
| Dark Theme | ✅ Tailwind | ✅ QPalette | ✅ Tamam |
| Responsive Layout | ✅ Flex | ❌ Sabit | 🔴 Eksik |
| Zoom Kontrolleri | ✅ | ✅ | ✅ Tamam |
| Fullscreen Modu | ✅ | ❌ | 🔴 Eksik |
| Etiket Göster/Gizle | ✅ | ❌ | 🔴 Eksik |
| Legend (Açıklama) | ✅ | ❌ | 🔴 Eksik |
| Path Bilgi Kutusu | ✅ | ❌ | 🔴 Eksik |

---

## 🔴 KRİTİK EKSİKLER (Öncelik 1)

### 1. Header Bileşeni

**Dosya:** `src/ui/components/header_widget.py`

```python
class HeaderWidget(QWidget):
    """
    Header bileşeni - Logo, başlık ve graf bilgileri gösterir.
    
    Görünüm:
    ┌─────────────────────────────────────────────────────────────────┐
    │ [Logo] QoS Routing Optimizer          Düğüm: 250 | Kenar: 12450 │
    │        BSM307 -bBilgisayar Ağları                   [Bağlı ✓]   │
    └─────────────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        # Logo (gradient ikon)
        # Başlık ve alt başlık
        # Graf bilgileri (düğüm, kenar sayısı)
        # Bağlantı durumu badge
```

**Gerekli Özellikler:**
- [ ] Logo ikonu (gradient arka plan)
- [ ] "QoS Routing Optimizer" başlığı
- [ ] "BSM307 - Bilgisayar Ağları Projesi" alt başlığı
- [ ] Düğüm sayısı göstergesi
- [ ] Kenar sayısı göstergesi
- [ ] Bağlantı durumu badge'i (yeşil/kırmızı)

---

### 2. Experiments Panel (Deney Paneli)

**Dosya:** `src/ui/components/experiments_panel.py`

```python
class ExperimentsPanel(QWidget):
    """
    Toplu deney çalıştırma paneli.
    
    Özellikler:
    - Predefined test case'leri çalıştırma
    - n_tests ve n_repeats ayarları
    - Progress bar
    - Sonuç export (CSV/JSON)
    """
    
    # Sinyaller
    run_experiments_requested = pyqtSignal(int, int)  # n_tests, n_repeats
    export_requested = pyqtSignal(str)  # format
```

**Gerekli Özellikler:**
- [ ] Test sayısı spinbox (varsayılan: 20)
- [ ] Tekrar sayısı spinbox (varsayılan: 5)
- [ ] "Deneyleri Çalıştır" butonu
- [ ] Progress bar (deney ilerlemesi)
- [ ] Sonuç özeti label
- [ ] "CSV Export" butonu
- [ ] "JSON Export" butonu

---

### 3. Graf Görselleştirme İyileştirmeleri

**Dosya:** `src/ui/components/graph_widget.py`

#### 3.1 Düğüm Hover Tooltip

```python
def _create_tooltip(self, node_id: int) -> str:
    """
    Düğüm tooltip içeriği.
    
    Görünüm:
    ┌──────────────────────┐
    │ Node 42              │
    │ Gecikme: 1.23ms      │
    │ Güvenilirlik: 98.5%  │
    └──────────────────────┘
    """
    node = self.graph.nodes[node_id]
    return f"""
    <b>Node {node_id}</b><br>
    Gecikme: {node['processing_delay']:.2f}ms<br>
    Güvenilirlik: {node['reliability']*100:.1f}%
    """
```

**Gerekli Özellikler:**
- [ ] Düğüm hover'da tooltip göster
- [ ] Kenar hover'da tooltip göster (bandwidth, delay, reliability)
- [ ] Tooltip styling (dark theme)

#### 3.2 Parçacık Animasyonu (Path üzerinde)

```python
class PathParticle:
    """Yol üzerinde hareket eden parçacık."""
    def __init__(self, path, speed=0.006):
        self.path = path
        self.position = 0.0
        self.speed = speed
    
    def update(self):
        self.position += self.speed
        if self.position >= len(self.path) - 1:
            self.position = 0.0
        return self.get_coordinates()
```

**Gerekli Özellikler:**
- [ ] Path boyunca hareket eden parçacıklar
- [ ] QTimer ile animasyon güncelleme
- [ ] Parçacık sayısı: 4 (web'deki gibi)
- [ ] Parçacık rengi: amber (#fcd34d)

#### 3.3 Glow Efekti

```python
def _draw_node_glow(self, painter, x, y, size, color):
    """Düğüm etrafında glow efekti."""
    # Blur efekti için birden fazla daire çiz
    for i in range(3):
        alpha = 100 - i * 30
        painter.setBrush(QColor(color.red(), color.green(), color.blue(), alpha))
        painter.drawEllipse(x - size - i*2, y - size - i*2, 
                           (size + i*2) * 2, (size + i*2) * 2)
```

**Gerekli Özellikler:**
- [ ] Kaynak düğüm için yeşil glow
- [ ] Hedef düğüm için kırmızı glow
- [ ] Path düğümleri için amber glow

---

### 4. Legend (Açıklama) Paneli

**Dosya:** `src/ui/components/graph_widget.py` içinde

```python
class LegendWidget(QWidget):
    """
    Graf açıklaması.
    
    Görünüm:
    ┌────────────────────────────────┐
    │ [●] Kaynak  [●] Hedef  [●] Yol │
    └────────────────────────────────┘
    """
```

**Gerekli Özellikler:**
- [ ] Kaynak (yeşil daire + "S" label)
- [ ] Hedef (kırmızı daire + "D" label)
- [ ] Yol düğümleri (amber daire)
- [ ] Diğer düğümler (gri daire)
- [ ] Glass morphism stil

---

### 5. Path Bilgi Kutusu

**Dosya:** `src/ui/components/graph_widget.py` içinde

```python
class PathInfoWidget(QWidget):
    """
    Bulunan yol bilgisi.
    
    Görünüm:
    ┌─────────────────────────────────────┐
    │ Bulunan Yol                         │
    │ 5 hop: 0 → 23 → 45 → ... → 249     │
    └─────────────────────────────────────┘
    """
```

**Gerekli Özellikler:**
- [ ] Hop sayısı
- [ ] Kısaltılmış yol gösterimi (ilk 5 + son 1)
- [ ] Sol üst köşede konumlandırma
- [ ] Glass morphism stil

---

## 🟠 ÖNEMLİ EKSİKLER (Öncelik 2)

### 6. Fullscreen Modu

```python
def toggle_fullscreen(self):
    """Graf widget'ını fullscreen yap."""
    if self.isFullScreen():
        self.showNormal()
    else:
        self.showFullScreen()
```

**Gerekli Özellikler:**
- [ ] Fullscreen toggle butonu (sağ üst)
- [ ] ESC ile çıkış
- [ ] Fullscreen'de "ESC ile çık" ipucu

---

### 7. Etiket Göster/Gizle Toggle

```python
class GraphWidget:
    def toggle_labels(self):
        """Tüm düğüm etiketlerini göster/gizle."""
        self.show_all_labels = not self.show_all_labels
        self._redraw()
```

**Gerekli Özellikler:**
- [ ] Toggle butonu (sağ üst, zoom butonlarının altında)
- [ ] Aktif durumda mavi highlight
- [ ] Default: Sadece özel düğümler (S, D, path)

---

### 8. Footer Bileşeni

**Dosya:** `src/ui/components/footer_widget.py`

```python
class FooterWidget(QWidget):
    """
    Footer - Algoritma listesi ve copyright.
    
    Görünüm:
    ┌─────────────────────────────────────────────────────────────────┐
    │ BSM307 QoS Routing • GA • ACO • PSO • SA • Q-Learning • SARSA  │
    └─────────────────────────────────────────────────────────────────┘
    """
```

**Gerekli Özellikler:**
- [ ] Proje adı
- [ ] Algoritma listesi (• ile ayrılmış)
- [ ] Glass morphism border-top
- [ ] Ortalanmış metin

---

### 9. Responsive Layout

```python
def resizeEvent(self, event):
    """Pencere boyutu değiştiğinde layout ayarla."""
    width = event.size().width()
    
    if width < 1000:
        # Dar ekran - panel'ları gizle veya küçült
        self.control_panel.setFixedWidth(220)
        self.results_panel.setFixedWidth(260)
    else:
        # Geniş ekran
        self.control_panel.setFixedWidth(280)
        self.results_panel.setFixedWidth(320)
```

**Gerekli Özellikler:**
- [ ] Minimum pencere boyutu: 1000x600
- [ ] Panel genişlikleri dinamik
- [ ] Graph widget stretch

---

## 🟡 İYİLEŞTİRMELER (Öncelik 3)

### 10. Kenar Hover Efekti

```python
def _on_edge_hover(self, u, v):
    """Kenar üzerine gelince highlight."""
    # Kenar kalınlığını artır
    # Tooltip göster
```

---

### 11. Düğüm Drag & Drop

```python
def _enable_node_drag(self):
    """Düğümleri sürükleyerek pozisyon değiştir."""
    # Mouse press/move/release event'leri
```

---

### 12. Zoom Animasyonu

```python
def _animated_zoom(self, factor, duration_ms=300):
    """Smooth zoom animasyonu."""
    # QPropertyAnimation kullan
```

---

### 13. Graf Export

```python
def export_graph_image(self, filename: str):
    """Grafı PNG/SVG olarak kaydet."""
    # QPixmap veya SVG generator
```

---

## 📁 Dosya Yapısı (Hedef)

```
src/ui/
├── __init__.py
├── main_window.py
├── styles.py                  # Ortak stiller (QSS)
└── components/
    ├── __init__.py
    ├── header_widget.py       # 🆕 Yeni
    ├── footer_widget.py       # 🆕 Yeni
    ├── graph_widget.py        # ✏️ Güncelleme
    ├── control_panel.py       # ✅ Mevcut
    ├── results_panel.py       # ✅ Mevcut
    ├── experiments_panel.py   # 🆕 Yeni
    ├── legend_widget.py       # 🆕 Yeni
    └── path_info_widget.py    # 🆕 Yeni
```

---

## ✅ Tamamlama Kontrol Listesi

### Kritik (Deadline: ...)
- [ ] Header bileşeni
- [ ] Experiments Panel
- [ ] Düğüm tooltip
- [ ] Kenar tooltip
- [ ] Path parçacık animasyonu
- [ ] Legend

### Önemli
- [ ] Glow efekti
- [ ] Fullscreen modu
- [ ] Etiket toggle
- [ ] Footer
- [ ] Path bilgi kutusu

### İsteğe Bağlı
- [ ] Responsive layout
- [ ] Kenar hover efekti
- [ ] Düğüm drag & drop
- [ ] Zoom animasyonu
- [ ] Graf export

---

## 🎨 Renk Paleti (Tailwind → Qt)

| Tailwind | Hex | Qt Kullanım |
|----------|-----|-------------|
| slate-900 | #0f172a | Ana arka plan |
| slate-800 | #1e293b | Panel arka plan |
| slate-700 | #334155 | Border |
| slate-600 | #475569 | İkincil düğümler |
| slate-400 | #94a3b8 | İkincil metin |
| slate-200 | #e2e8f0 | Ana metin |
| green-500 | #22c55e | Kaynak düğüm |
| green-300 | #86efac | Kaynak glow |
| red-500 | #ef4444 | Hedef düğüm |
| red-300 | #fca5a5 | Hedef glow |
| amber-500 | #f59e0b | Path düğümler |
| amber-300 | #fcd34d | Path glow/parçacık |
| blue-500 | #3b82f6 | Butonlar, link |
| purple-500 | #8b5cf6 | Optimize butonu |
| pink-500 | #ec4899 | Karşılaştır butonu |

---

## 📏 Boyutlar

| Eleman | Web | PyQt5 Hedef |
|--------|-----|-------------|
| Header yüksekliği | ~56px | 60px |
| Footer yüksekliği | ~32px | 30px |
| Sol panel genişliği | 320px (w-80) | 280px |
| Sağ panel genişliği | 320px (w-80) | 320px |
| Düğüm boyutu (normal) | 4px | 8px |
| Düğüm boyutu (S/D) | 14px | 20px |
| Düğüm boyutu (path) | 10px | 14px |
| Kenar kalınlığı (normal) | 0.5px | 0.5px |
| Kenar kalınlığı (path) | 5px | 4px |

---

*Doküman Versiyonu: 1.0*
*Oluşturma Tarihi: 3 Aralık 2025*

