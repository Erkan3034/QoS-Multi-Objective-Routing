# Pareto Optimalite Analizi

## 📋 İçindekiler
1. [Pareto Optimalite Nedir?](#pareto-optimalite-nedir)
2. [Nasıl Eklendi?](#nasıl-eklendi)
3. [Nasıl Çalışır?](#nasıl-çalışır)
4. [Sonuçlar Neye Göre Değişir?](#sonuçlar-neye-göre-değişir)
5. [Kullanım](#kullanım)
6. [Kod Yapısı](#kod-yapısı)

---

## 🎯 Pareto Optimalite Nedir?

**Pareto Optimalite**, çok amaçlı optimizasyonda kullanılan temel bir kavramdır.

### Tanım
Bir çözüm **Pareto Optimal** ise:
- O çözümün hedeflerinden herhangi birini iyileştirmek için
- Diğer hedeflerden en az birini **feda etmek** (kötüleştirmek) zorundasınız

### Dominasyon Kavramı
- **Çözüm A, Çözüm B'yi domine eder** eğer:
  - A, tüm metriklerde B'ye eşit veya daha iyi
  - A, en az bir metrikte B'den kesinlikle daha iyi

### Pareto Sınırı (Pareto Frontier)
Tüm **domine edilmeyen** çözümlerin kümesine **Pareto Sınırı** denir.

### Projeden Örnek

```
Üç yol bulundu:

Yol A: Gecikme=10ms, Güvenilirlik=0.99, Maliyet=50
Yol B: Gecikme=12ms, Güvenilirlik=0.999, Maliyet=45
Yol C: Gecikme=15ms, Güvenilirlik=0.98, Maliyet=55
```

**Analiz:**
- Yol A ve Yol B: İkisi de Pareto Optimal (birbirlerini domine etmiyorlar)
- Yol C: Yol A tarafından **domine ediliyor** (A her açıdan daha iyi)

**Sonuç:** Pareto Sınırı = {Yol A, Yol B}

---

## 🔧 Nasıl Eklendi?

### Oluşturulan Dosyalar

| Dosya | Amaç |
|-------|------|
| `app/src/experiments/pareto_analyzer.py` | Pareto analiz motoru |
| `app/src/ui/components/pareto_dialog.py` | Görselleştirme penceresi |

### Modifikasyonlar

| Dosya | Değişiklik |
|-------|------------|
| `app/src/experiments/__init__.py` | Yeni modüller export edildi |
| `app/src/ui/components/experiments_panel.py` | Pareto butonu eklendi |
| `app/src/ui/main_window.py` | `_on_run_pareto_analysis()` handler eklendi |

---

## ⚙️ Nasıl Çalışır?

### Algoritma Adımları

```
1. Çözüm Üretimi
   ├── Tek-metrik optimizasyonları (sadece gecikme, sadece güvenilirlik, sadece kaynak)
   ├── Rastgele ağırlık kombinasyonları (Dirichlet dağılımı)
   └── K-en kısa yol varyasyonları

2. Dominasyon Analizi
   └── Her çözüm çifti için dominasyon kontrolü

3. Pareto Sınırı Çıkarımı
   └── Domine edilmeyen çözümleri ayır

4. Görselleştirme
   ├── 2D Scatter Plot (Gecikme vs Güvenilirlik)
   ├── Pareto sınırı tablosu
   └── İstatistikler
```

### Dominasyon Kontrolü Kodu

```python
def dominates(self, sol1: ParetoSolution, sol2: ParetoSolution) -> bool:
    # Delay: düşük daha iyi
    delay_better_or_equal = sol1.delay <= sol2.delay
    delay_strictly_better = sol1.delay < sol2.delay
    
    # Reliability: yüksek daha iyi
    rel_better_or_equal = sol1.reliability >= sol2.reliability
    rel_strictly_better = sol1.reliability > sol2.reliability
    
    # Resource: düşük daha iyi
    res_better_or_equal = sol1.resource_cost <= sol2.resource_cost
    res_strictly_better = sol1.resource_cost < sol2.resource_cost
    
    # Tüm metriklerde eşit veya daha iyi + en az birinde kesinlikle daha iyi
    all_better_or_equal = (delay_better_or_equal and 
                           rel_better_or_equal and 
                           res_better_or_equal)
    at_least_one_better = (delay_strictly_better or 
                           rel_strictly_better or 
                           res_strictly_better)
    
    return all_better_or_equal and at_least_one_better
```

---

## 📊 Sonuçlar Neye Göre Değişir?

### 1. Kaynak-Hedef Çifti
- Farklı düğümler = farklı yol alternatifleri
- Uzak düğümler genellikle daha fazla Pareto çözümü

### 2. Ağ Topolojisi
- Seyrek ağlar: Az yol, az Pareto çözümü
- Yoğun ağlar: Çok yol, çok Pareto çözümü

### 3. Metrik Dağılımları
- Homojen metrikler: Benzer çözümler (az Pareto)
- Heterojen metrikler: Çeşitli trade-off'lar (çok Pareto)

### 4. Çözüm Sayısı (n_solutions)
- Daha fazla aday = daha iyi Pareto yaklaşımı
- Default: 100 çözüm

---

## 🖥️ Kullanım

### UI'dan
1. Graf yükleyin/oluşturun
2. Kaynak ve hedef düğümleri seçin
3. Sağ panelde **"Pareto Optimalite"** kartını bulun
4. **"🔍 Analiz Başlat"** butonuna tıklayın
5. Sonuç penceresini inceleyin

### Koddan
```python
from src.experiments.pareto_analyzer import ParetoAnalyzer

analyzer = ParetoAnalyzer(graph)
result = analyzer.find_pareto_frontier(
    source=0, 
    destination=249, 
    n_solutions=100
)

print(f"Pareto Optimal: {result.pareto_count}")
print(f"Domine Edilen: {result.dominated_count}")

for sol in result.pareto_frontier:
    print(f"Gecikme: {sol.delay:.2f}ms, Güvenilirlik: {sol.reliability:.6f}")
```

---

## 📁 Kod Yapısı

### ParetoSolution
```python
@dataclass
class ParetoSolution:
    path: List[int]
    delay: float
    reliability: float
    resource_cost: float
    is_dominated: bool = False
    domination_count: int = 0
```

### ParetoAnalysisResult
```python
@dataclass
class ParetoAnalysisResult:
    pareto_frontier: List[ParetoSolution]
    all_solutions: List[ParetoSolution]
    computation_time_ms: float
    total_solutions: int
    pareto_count: int
    dominated_count: int
    delay_range: Tuple[float, float]
    reliability_range: Tuple[float, float]
    resource_range: Tuple[float, float]
```

### ParetoAnalyzer
```python
class ParetoAnalyzer:
    def __init__(self, graph, seed=None)
    def dominates(self, sol1, sol2) -> bool
    def find_pareto_frontier(self, source, dest, n_solutions) -> ParetoAnalysisResult
    def _generate_diverse_solutions(self, source, dest, ...) -> List[ParetoSolution]
    def _analyze_domination(self, solutions) -> None
```

---

## 📈 Beklenen Çıktılar

| Metrik | Tipik Değer | Açıklama |
|--------|-------------|----------|
| Total Solutions | 50-150 | Üretilen toplam çözüm |
| Pareto Count | 5-20 | Pareto optimal çözüm sayısı |
| Dominated Count | 30-130 | Domine edilen çözüm sayısı |
| Computation Time | 100-500ms | Analiz süresi |

---

**Son Güncelleme:** 28 Aralık 2025  

