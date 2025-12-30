# Geliştirici Rehberi (Developer Guide)

> QoS Rotalama projesi için standartlar ve prosedürler.

---

## 1. Kurulum

Proje **Python 3.9+** gerektirir.

### Ortamın Hazırlanması

```bash
# 1. Proje klasörüne girin
cd app

# 2. Sanal ortam oluşturun
# Windows:
python -m venv venv
venv\Scripts\activate

# Mac/Linux:
python3 -m venv venv
source venv/bin/activate

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt

# 4. Uygulamayı çalıştırın
python main.py
```

### `requirements.txt`

```txt
networkx>=3.1
matplotlib>=3.7
PyQt5>=5.15
numpy>=1.24
reportlab>=4.0
Pillow>=10.0
```

---

## 2. Proje Yapısı

```
📁 app/
├── main.py                    # Ana giriş noktası
├── requirements.txt           # Python bağımlılıkları
└── 📁 src/
    ├── 📁 core/
    │   └── config.py          # Konfigürasyon ayarları
    │
    ├── 📁 services/
    │   ├── graph_service.py   # Graf oluşturma (random/file)
    │   ├── metrics_service.py # QoS metrik hesaplama
    │   └── report_service.py  # PDF/PNG export
    │
    ├── 📁 algorithms/
    │   ├── genetic_algorithm.py  # Genetik Algoritma
    │   ├── aco.py                # Karınca Kolonisi
    │   ├── pso.py                # Parçacık Sürüsü
    │   ├── simulated_annealing.py
    │   ├── q_learning.py         # Q-Learning RL
    │   └── sarsa.py              # SARSA RL
    │
    └── 📁 ui/
        ├── main_window.py         # Ana pencere
        ├── 📁 components/
        │   ├── graph_widget.py    # 2D/3D görselleştirme
        │   ├── control_panel.py   # Kontrol paneli
        │   └── results_panel.py   # Sonuç paneli
        └── 📁 dialogs/
            └── experiment_dialog.py  # Deney arayüzü
```

---

## 3. Algoritmalar

| Algoritma | Dosya | Açıklama |
|-----------|-------|----------|
| **GA** | `genetic_algorithm.py` | Darwin evrim, crossover+mutasyon |
| **ACO** | `aco.py` | Karınca feromon takibi |
| **PSO** | `pso.py` | Parçacık sürüsü hareketi |
| **SA** | `simulated_annealing.py` | Tavlama benzetimi |
| **Q-Learning** | `q_learning.py` | Model-free RL |
| **SARSA** | `sarsa.py` | On-policy RL |

### Ortak Arayüz

Tüm algoritmalar aynı `optimize()` metodunu kullanır:

```python
result = algorithm.optimize(
    source=1,
    destination=20,
    weights={'delay': 0.33, 'reliability': 0.33, 'resource': 0.34},
    bandwidth_demand=100.0,
    progress_callback=lambda gen, fit: print(f"Gen {gen}: {fit}")
)
```

---

## 4. QoS Metrikleri (Proje Yönergesi)

### Formüller

| Metrik | Formül |
|--------|--------|
| **TotalDelay** | `Σ(LinkDelay) + Σ(ProcessingDelay)` (k ≠ S,D) |
| **ReliabilityCost** | `Σ[-log(LinkReliability)] + Σ[-log(NodeReliability)]` |
| **ResourceCost** | `Σ(1Gbps / Bandwidth)` |
| **TotalCost** | `w₁×Delay + w₂×Reliability + w₃×Resource` |

---

## 5. Kodlama Standartları

| Kural | Standart | Örnek |
|-------|----------|-------|
| Değişken | `snake_case` | `best_route`, `min_delay` |
| Class | `PascalCase` | `GeneticAlgorithm`, `ACOResult` |
| Sabit | `UPPER_CASE` | `MAX_ITERATIONS`, `DEFAULT_SEED` |

### Docstring Örneği

```python
def calculate_fitness(path: List[int], weights: Dict) -> float:
    """
    Yolun fitness değerini hesaplar.
    
    Args:
        path: Düğüm ID listesi [1, 3, 5, 7]
        weights: {'delay': 0.33, 'reliability': 0.33, 'resource': 0.34}
        
    Returns:
        Fitness skoru (düşük = iyi)
    """
```

---

## 6. Çalıştırma Komutları

```bash
# Uygulamayı başlat
cd app
python main.py

# Belirli bir seed ile
python main.py --seed 42
```

---

## 7. Export Özellikleri

| Format | Metod | İçerik |
|--------|-------|--------|
| **PDF** | `ReportService.export_pdf()` | Sonuçlar + graf görüntüsü |
| **PNG** | `ReportService.export_png()` | Graf ekran görüntüsü |
| **JSON** | `result.to_dict()` | Makine okunabilir veri |

---

> Erkan Turgut (30.12.2025)
