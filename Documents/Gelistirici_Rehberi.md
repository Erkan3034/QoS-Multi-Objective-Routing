# Geliştirici Rehberi

> QoS Rotalama projesi için kurulum, yapı ve standartlar.

---

## 1. Kurulum

Proje **Python 3.9+** gerektirir.

```bash
# 1. Proje klasörüne girin
cd app

# 2. Sanal ortam oluşturun (opsiyonel)
python -m venv venv
venv\Scripts\activate  # Windows
# veya: source venv/bin/activate  # Mac/Linux

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
PyOpenGL>=3.1
```

---

## 2. Proje Yapısı

```
📁 app/
├── main.py                        # Ana giriş noktası
├── requirements.txt               # Python bağımlılıkları
└── 📁 src/
    ├── 📁 core/
    │   └── config.py              # Konfigürasyon ayarları
    │
    ├── 📁 services/
    │   ├── graph_service.py       # Graf oluşturma (random/CSV)
    │   ├── metrics_service.py     # QoS metrik hesaplama
    │   └── report_service.py      # PDF/PNG export
    │
    ├── 📁 algorithms/
    │   ├── __init__.py            # Algoritma registry
    │   ├── genetic_algorithm.py   # Genetik Algoritma (paralel)
    │   ├── aco.py                 # Karınca Kolonisi
    │   ├── pso.py                 # Parçacık Sürüsü
    │   ├── simulated_annealing.py # Benzetilmiş Tavlama
    │   ├── q_learning.py          # Q-Learning (RL)
    │   
    │
    ├── 📁 experiments/
    │   ├── test_cases.py          # Test senaryosu üretimi
    │   ├── experiment_runner.py   # Toplu deney motoru
    │   └── scalability_analyzer.py # Ölçeklenebilirlik analizi
    │
    ├── 📁 workers/
    │   └── optimization_worker.py # QThread worker
    │
    └── 📁 ui/
        ├── main_window.py         # Ana pencere
        └── 📁 components/
            ├── graph_widget.py    # 2D/3D görselleştirme
            ├── control_panel.py   # Kontrol paneli
            ├── results_panel.py   # Sonuç paneli
            ├── experiments_panel.py # Deney paneli
            ├── test_results_dialog.py # Sonuç penceresi
            └── scalability_dialog.py  # Ölçeklenebilirlik dialog
```

---

## 3. Algoritmalar

| Algoritma | Dosya | Açıklama |
|-----------|-------|----------|
| **GA** | `genetic_algorithm.py` | Paralel, elitizm, multi-point crossover |
| **ACO** | `aco.py` | Feromon takibi, evaporasyon |
| **PSO** | `pso.py` | Parçacık sürüsü hareketi |
| **SA** | `simulated_annealing.py` | Tavlama benzetimi, soğutma |
| **Q-Learning** | `q_learning.py` | Model-free RL, ε-greedy |
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

# Sonuç objesi
print(result.path)               # [1, 5, 8, 20]
print(result.fitness)            # 0.0423
print(result.computation_time_ms) # 125.5
print(result.seed_used)          # 42 veya None
```

---

## 4. QoS Metrikleri

| Metrik | Formül | Hedef |
|--------|--------|-------|
| **TotalDelay** | `Σ(LinkDelay) + Σ(ProcessingDelay)` | Minimize |
| **ReliabilityCost** | `Σ[-log(LinkReliability)]` | Minimize |
| **ResourceCost** | `Σ(1Gbps / Bandwidth)` | Minimize |
| **TotalCost** | `w₁×Delay + w₂×Reliability + w₃×Resource` | Minimize |

> **Not:** ProcessingDelay hesabında S ve D düğümleri dahil edilmez.

---

## 5. Kodlama Standartları

| Kural | Standart | Örnek |
|-------|----------|-------|
| Değişken | `snake_case` | `best_route`, `min_delay` |
| Class | `PascalCase` | `GeneticAlgorithm`, `ACOResult` |
| Sabit | `UPPER_CASE` | `MAX_ITERATIONS`, `DEFAULT_SEED` |
| Yorumlar | Türkçe | `# Fitness hesapla` |

---

## 6. Deney Özellikleri

### Test Senaryosu Üretimi

```python
from src.experiments.test_cases import TestCaseGenerator

generator = TestCaseGenerator(graph, seed=42)
test_cases = generator.get_predefined_test_cases()  # 25 senaryo
```

### Toplu Deney Çalıştırma

```python
from src.experiments.experiment_runner import ExperimentRunner

runner = ExperimentRunner(graph, n_repeats=5)
results = runner.run_experiments(test_cases)

# results içeriği:
# - comparison_table: Algoritma özet istatistikleri
# - scenario_results: Senaryo bazlı detaylar
# - ranking_summary: Algoritma sıralama performansı
# - failure_report: Başarısızlık detayları
```

---

## 7. Export Özellikleri

| Format | Kullanım | İçerik |
|--------|----------|--------|
| **PDF** | `ReportService.export_pdf()` | Sonuçlar + graf görüntüsü |
| **PNG** | `ReportService.export_png()` | Graf ekran görüntüsü |
| **JSON** | `TestResultsDialog` → Export | Tüm deney verisi |
| **CSV** | `TestResultsDialog` → Export | Tablo formatında |

---

> Son güncelleme: 2025-12-29
