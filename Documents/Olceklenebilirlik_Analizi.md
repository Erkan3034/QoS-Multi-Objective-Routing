# Ölçeklenebilirlik Analizi

## 📋 İçindekiler
1. [Ölçeklenebilirlik Nedir?](#ölçeklenebilirlik-nedir)
2. [Nasıl Eklendi?](#nasıl-eklendi)
3. [Nasıl Çalışır?](#nasıl-çalışır)
4. [Sonuçlar Neye Göre Değişir?](#sonuçlar-neye-göre-değişir)
5. [Kullanım](#kullanım)
6. [1000+ Düğüm Desteği](#1000-düğüm-desteği)

---

## 📈 Ölçeklenebilirlik Nedir?

Ölçeklenebilirlik, bir algoritmanın **ağ boyutu arttıkça** performansının nasıl değiştiğini ölçer.

### Temel Sorular
- 250 düğümlü ağda çalışan algoritma 1000 düğümde nasıl performans gösterir?
- Hangi algoritma büyük ağlarda daha verimli?
- Zaman karmaşıklığı pratik limitleri nelerdir?

### Önemli Metrikler
| Metrik | Açıklama |
|--------|----------|
| **Çalışma Süresi (ms)** | Optimizasyon ne kadar sürdü? |
| **Başarı Oranı** | Çözüm bulunabiliyor mu? |
| **Ortalama Maliyet** | Çözüm kalitesi korunuyor mu? |
| **Hafıza Kullanımı (MB)** | RAM tüketimi artıyor mu? |

---

## 🔧 Nasıl Eklendi?

### Oluşturulan Dosyalar

| Dosya | Amaç |
|-------|------|
| `app/src/experiments/scalability_analyzer.py` | Gelişmiş ölçeklenebilirlik analiz motoru |

### Mevcut Bileşenler (Genişletildi)

| Dosya | Değişiklik |
|-------|------------|
| `app/src/ui/main_window.py` | `ScalabilityWorker` - 1000+ düğüm desteği |
| `app/src/ui/components/scalability_dialog.py` | Sonuç görselleştirme |

---

## ⚙️ Nasıl Çalışır?

### Analiz Algoritması

```
1. Düğüm Boyutları Belirlenir
   └── Örnek: [100, 250, 500, 750, 1000, 1500, 2000]

2. Her Boyut İçin:
   ├── Rastgele graf oluştur (Erdős-Rényi)
   ├── Seyreklik ayarla (büyük ağlarda daha seyrek)
   ├── Test case'ler üret
   └── Her algoritma için:
       ├── n_repeats tekrar çalıştır
       ├── Süre ölç (tracemalloc ile hafıza da)
       └── İstatistik topla

3. Sonuçları Analiz Et
   ├── En hızlı algoritma
   ├── En ölçeklenebilir (zaman artış oranı en düşük)
   └── Büyük ağ önerileri
```

### Seyreklik Ayarlaması (Kritik)

Büyük ağlarda yoğunluk düşürülür, aksi halde hafıza taşar:

```python
if n_nodes <= 250:
    p = 0.15      # ~9000 edge
elif n_nodes <= 500:
    p = 0.08      # ~20000 edge
elif n_nodes <= 1000:
    p = 0.04      # ~40000 edge
else:
    p = 0.02      # >1000 düğüm için çok seyrek
```

### Hafıza İzleme

```python
import tracemalloc

tracemalloc.start()
# ... algorithm runs ...
current, peak = tracemalloc.get_traced_memory()
memory_mb = peak / (1024 * 1024)
tracemalloc.stop()
```

---

## 📊 Sonuçlar Neye Göre Değişir?

### 1. Düğüm Sayısı
| Düğüm | Beklenen Süre | Edge Sayısı (p=değişken) |
|-------|---------------|--------------------------|
| 100 | 10-50 ms | ~750 |
| 250 | 50-200 ms | ~4500 |
| 500 | 100-500 ms | ~10000 |
| 1000 | 200-1500 ms | ~20000 |
| 2000 | 500-5000 ms | ~40000 |

### 2. Algoritma Türü

| Algoritma | Ölçeklenebilirlik | Açıklama |
|-----------|-------------------|----------|
| **GA** | ⭐⭐⭐ | Popülasyon boyutu sabit kalabilir |
| **ACO** | ⭐⭐ | Feromon matrisi O(n²) yer kaplar |
| **PSO** | ⭐⭐⭐ | Parçacık sayısı sabit |
| **SA** | ⭐⭐⭐⭐ | Tek çözümle çalışır, çok verimli |
| **Q-Learning** | ⭐⭐ | Q-table boyutu O(n × k) |
| **SARSA** | ⭐⭐ | Q-Learning ile benzer |

### 3. Graf Yoğunluğu (p)
- Yoğun graf: Daha fazla komşu, daha uzun keşif
- Seyrek graf: Az yol, hızlı ama kalitesiz çözüm riski

### 4. Test Sayısı ve Tekrar
- Daha fazla test = daha güvenilir istatistik
- Varsayılan: 5 test case × 3 tekrar = 15 çalıştırma/algoritma

---

## 🖥️ Kullanım

### UI'dan (Mevcut - Küçük Ölçek)
1. Graf yükleyin (herhangi bir boyut)
2. Sağ panelde **"Ölçeklenebilirlik"** kartını bulun
3. **"Analiz Et"** butonuna tıklayın
4. Sonuç dialog'unu inceleyin

### Extended Analyzer (Büyük Ölçek - Kod)
```python
from src.experiments.scalability_analyzer import ScalabilityAnalyzer

analyzer = ScalabilityAnalyzer(
    node_sizes=[100, 250, 500, 750, 1000, 1500, 2000],
    n_repeats=3,
    n_test_cases=5,
    algorithms=['ga', 'aco', 'pso', 'sa']
)

def progress_callback(current, total, message):
    print(f"[{current}/{total}] {message}")

report = analyzer.run_analysis()

print(f"En Hızlı: {report.fastest_algorithm}")
print(f"En Ölçeklenebilir: {report.most_scalable}")

for rec in report.recommendations:
    print(rec)
```

---

## 🚀 1000+ Düğüm Desteği

### Zorluklar

| Zorluk | Çözüm |
|--------|-------|
| Hafıza taşması | Seyreklik (p) otomatik azaltılır |
| UI donması | QThread ile arka planda çalışma |
| Uzun süre | Progress callback ile takip |
| Edge patlaması | Lazy evaluation, akıllı keşif |

### Büyük Ağlarda Performans İpuçları

1. **Seyreklik ayarı kritik** - 2000 düğümde p=0.02 kullanın
2. **Paralel işlem** - GA'da `use_parallel='auto'`
3. **Early stopping** - Yakınsama sağlandığında dur
4. **Batch processing** - Büyük popülasyonları parçala

### Örnek 1000 Düğüm Sonuçları

```
Düğüm: 1000, Edge: ~20000

Algoritma        | Ortalama Süre | Başarı Oranı | Hafıza
-----------------|---------------|--------------|--------
SA              | 320 ms        | 100%         | 45 MB
PSO             | 580 ms        | 95%          | 62 MB
GA              | 850 ms        | 98%          | 78 MB
ACO             | 1200 ms       | 92%          | 120 MB
Q-Learning      | 2500 ms       | 85%          | 95 MB
```

---

## 📁 Kod Yapısı

### ScalabilityDataPoint
```python
@dataclass
class ScalabilityDataPoint:
    node_count: int
    edge_count: int
    algorithm: str
    avg_time_ms: float
    std_time_ms: float
    min_time_ms: float
    max_time_ms: float
    success_rate: float
    avg_cost: float
    memory_mb: float
```

### ScalabilityReport
```python
@dataclass
class ScalabilityReport:
    data_points: List[ScalabilityDataPoint]
    node_sizes: List[int]
    algorithms: List[str]
    total_time_sec: float
    fastest_algorithm: str
    most_scalable: str
    recommendations: List[str]
    
    def get_time_by_algorithm(self, algorithm) -> List[float]
    def get_time_by_nodes(self, node_count) -> Dict[str, float]
```

### ScalabilityAnalyzer
```python
class ScalabilityAnalyzer:
    def __init__(
        self,
        node_sizes=[100, 250, 500, 750, 1000, 1500, 2000],
        n_repeats=3,
        n_test_cases=5,
        algorithms=None,
        progress_callback=None
    )
    
    def run_analysis(self) -> ScalabilityReport
    def _create_test_graph(self, n_nodes) -> tuple
    def _test_algorithm(self, graph, algo_key, ...) -> ScalabilityDataPoint
    def _analyze_results(self, report) -> None
```

---

## 📈 Örnek Grafik Çıktısı

```
Çalışma Süresi vs Düğüm Sayısı
                                                        
    2500 ┤                                         ╭──
         │                                    ╭────╯  
    2000 ┤                               ╭────╯       
         │                          ╭────╯            
    1500 ┤               ACO   ╭────╯                 
         │                ╭────╯                      
    1000 ┤           ╭────╯                           
         │      ╭────╯       GA ───────────────       
     500 ┤ ╭────╯                                     
         │╭╯   PSO ────────────────────────────       
       0 ┼─────────────────────────────────────       
         100   250   500   750   1000  1500  2000
                       Düğüm Sayısı
```

---

**Son Güncelleme:** 28 Aralık 2025  

