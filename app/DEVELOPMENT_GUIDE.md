# 📚 PyQt5 Desktop - Geliştirici Rehberi

> **Proje:** BSM307 - QoS Multi-Objective Routing Desktop Application  
> **Amaç:** Grup üyelerinin projeyi sıralı ve koordineli şekilde geliştirmesi için rehber

---

## 📑 İÇİNDEKİLER

1. [Proje Yapısı](#-proje-yapısı)
2. [Geliştirme Aşamaları](#-geliştirme-aşamaları)
3. [Git Workflow](#-git-workflow)
4. [Dosya Sıralaması](#-dosya-sıralaması)
5. [Test Prosedürleri](#-test-prosedürleri)
6. [Kod Standartları](#-kod-standartları)
7. [Yeni Özellik ekleme](#-özellik-ekleme).

---

## 📁 PROJE YAPISI

```
pyqt5-desktop/
├── main.py                     # Ana giriş noktası
├── requirements.txt            # Python bağımlılıkları
├── README.md                   # Proje açıklaması
├── DEVELOPMENT_GUIDE.md        # Bu dosya
├── PERFORMANCE_OPTIMIZATION.md # Performans rehberi
├── UI_TODO.md                  # UI geliştirme görevleri
│
└── src/
    ├── __init__.py
    │
    ├── core/                   # Yapılandırma
    │   ├── __init__.py
    │   └── config.py           # Ayarlar ve parametreler
    │
    ├── services/               # İş mantığı servisleri
    │   ├── __init__.py
    │   ├── graph_service.py    # Graf oluşturma
    │   └── metrics_service.py  # QoS metrik hesaplama
    │
    ├── algorithms/             # Optimizasyon algoritmaları
    │   ├── __init__.py
    │   ├── genetic_algorithm.py
    │   ├── aco.py              # Ant Colony
    │   ├── pso.py              # Particle Swarm
    │   ├── simulated_annealing.py
    │   ├── q_learning.py
    │   └── sarsa.py
    │
    ├── experiments/            # Deney modülü
    │   ├── __init__.py
    │   ├── test_cases.py       # Test senaryoları
    │   └── experiment_runner.py # Deney çalıştırıcı
    │
    └── ui/                     # PyQt5 Arayüz
        ├── __init__.py
        ├── main_window.py      # Ana pencere
        └── components/
            ├── __init__.py
            ├── graph_widget.py    # Graf görselleştirme
            ├── control_panel.py   # Kontrol paneli
            └── results_panel.py   # Sonuç paneli
```

---

## 🔄 GELİŞTİRME AŞAMALARI

Proje aşağıdaki sırayla geliştirilmelidir. Her aşama tamamlandığında commit yapılmalıdır.

### 📦 AŞAMA 1: Temel Altyapı
**Sorumlu:** Lider Geliştirici  
**Tahmini Süre:** 1 gün

| Dosya | Açıklama | Öncelik |
|-------|----------|---------|
| `requirements.txt` | Bağımlılıklar | 🔴 Kritik |
| `src/__init__.py` | Paket tanımı | 🔴 Kritik |
| `src/core/__init__.py` | Core paketi | 🔴 Kritik |
| `src/core/config.py` | Yapılandırma | 🔴 Kritik |

**Commit mesajı:**
```
feat: temel proje yapısı ve konfigürasyon eklendi

- requirements.txt: PyQt5, networkx, numpy bağımlılıkları
- config.py: Algoritma parametreleri ve genel ayarlar
```

---

### 📦 AŞAMA 2: Servisler
**Sorumlu:** Backend Geliştirici 1  
**Tahmini Süre:** 1-2 gün

| Dosya | Açıklama | Öncelik |
|-------|----------|---------|
| `src/services/__init__.py` | Servis paketi | 🔴 Kritik |
| `src/services/graph_service.py` | Graf oluşturma | 🔴 Kritik |
| `src/services/metrics_service.py` | Metrik hesaplama | 🔴 Kritik |

**Commit mesajı:**
```
feat: graf ve metrik servisleri eklendi

- graph_service.py: NetworkX tabanlı graf oluşturma
- metrics_service.py: QoS metrik hesaplama (delay, reliability, resource)
```

---

### 📦 AŞAMA 3: Meta-Sezgisel Algoritmalar
**Sorumlu:** Backend Geliştirici 2  
**Tahmini Süre:** 3-4 gün

| Dosya | Açıklama | Öncelik |
|-------|----------|---------|
| `src/algorithms/__init__.py` | Algoritma paketi | 🔴 Kritik |
| `src/algorithms/genetic_algorithm.py` | GA | 🔴 Kritik |
| `src/algorithms/aco.py` | ACO | 🟠 Önemli |
| `src/algorithms/pso.py` | PSO | 🟠 Önemli |
| `src/algorithms/simulated_annealing.py` | SA | 🟠 Önemli |

**Commit mesajları (her algoritma için ayrı):**
```
feat: Genetik Algoritma implementasyonu

- Population-based optimization
- Tournament selection, crossover, mutation
- Elitism desteği
```

```
feat: Ant Colony Optimization implementasyonu

- Feromon tabanlı yol bulma
- Visibility heuristic
- Feromon buharlaşması
```

---

### 📦 AŞAMA 4: Pekiştirmeli Öğrenme Algoritmaları
**Sorumlu:** Backend Geliştirici 3  
**Tahmini Süre:** 2-3 gün

| Dosya | Açıklama | Öncelik |
|-------|----------|---------|
| `src/algorithms/q_learning.py` | Q-Learning | 🟠 Önemli |
| `src/algorithms/sarsa.py` | SARSA | 🟠 Önemli |

**Commit mesajı:**
```
feat: Reinforcement Learning algoritmaları eklendi

- Q-Learning: Off-policy TD learning
- SARSA: On-policy TD learning
- Epsilon-greedy exploration
```

---

### 📦 AŞAMA 5: Deney Modülü
**Sorumlu:** Backend Geliştirici 1  
**Tahmini Süre:** 2 gün

| Dosya | Açıklama | Öncelik |
|-------|----------|---------|
| `src/experiments/__init__.py` | Deney paketi | 🟠 Önemli |
| `src/experiments/test_cases.py` | Test senaryoları | 🟠 Önemli |
| `src/experiments/experiment_runner.py` | Deney çalıştırıcı | 🟠 Önemli |

**Commit mesajı:**
```
feat: Deney modülü eklendi

- test_cases.py: 25 predefined test case (S, D, B kombinasyonları)
- experiment_runner.py: Toplu deney çalıştırma ve raporlama
- Bandwidth constraint kontrolü
```

---

### 📦 AŞAMA 6: UI Bileşenleri
**Sorumlu:** Frontend Geliştirici  
**Tahmini Süre:** 4-5 gün

| Dosya | Açıklama | Öncelik |
|-------|----------|---------|
| `src/ui/__init__.py` | UI paketi | 🔴 Kritik |
| `src/ui/components/__init__.py` | Bileşen paketi | 🔴 Kritik |
| `src/ui/components/graph_widget.py` | Graf görselleştirme | 🔴 Kritik |
| `src/ui/components/control_panel.py` | Kontrol paneli | 🔴 Kritik |
| `src/ui/components/results_panel.py` | Sonuç paneli | 🔴 Kritik |
| `src/ui/main_window.py` | Ana pencere | 🔴 Kritik |

**Commit mesajları:**
```
feat: Graf görselleştirme widget'ı eklendi

- PyQtGraph tabanlı network visualization
- Node/edge rendering
- Zoom ve pan desteği
```

```
feat: Kontrol paneli eklendi

- Graf oluşturma kontrolları
- Algoritma seçimi
- Ağırlık ayarları
```

```
feat: Sonuç paneli ve ana pencere eklendi

- Metrik gösterimi
- Karşılaştırma tablosu
- Layout yönetimi
```

---

### 📦 AŞAMA 7: Entegrasyon
**Sorumlu:** Lider Geliştirici  
**Tahmini Süre:** 1-2 gün

| Dosya | Açıklama | Öncelik |
|-------|----------|---------|
| `main.py` | Uygulama giriş noktası | 🔴 Kritik |
| `README.md` | Proje dokümantasyonu | 🟠 Önemli |

**Commit mesajı:**
```
feat: Ana uygulama ve dokümantasyon tamamlandı

- main.py: PyQt5 uygulama başlatma
- README.md: Kurulum ve kullanım talimatları
```

---

## 🔀 GIT WORKFLOW

### Branch Yapısı

```
main
├── develop
│   ├── feature/core-config
│   ├── feature/services
│   ├── feature/algorithms-meta
│   ├── feature/algorithms-rl
│   ├── feature/experiments
│   ├── feature/ui-components
│   └── feature/integration
```

### Commit Kuralları

**Format:**
```
<type>: <description>

[optional body]
[optional footer]
```

**Tipler:**
- `feat`: Yeni özellik
- `fix`: Bug düzeltme
- `docs`: Dokümantasyon
- `refactor`: Kod düzenleme
- `test`: Test ekleme
- `chore`: Diğer

**Örnekler:**
```bash
git commit -m "feat: Genetic Algorithm implementasyonu"
git commit -m "fix: ACO feromon güncelleme hatası düzeltildi"
git commit -m "docs: README güncellendi"
```

---

## 📋 DOSYA SIRALAMASI (.gitignore Yönetimi)

Projede sıralı geliştirme görüntüsü için `.gitignore` dosyasını aşağıdaki sırayla güncelleyin:

### Başlangıç .gitignore

```gitignore
# Tüm src/ içeriği gizli başlar
src/

# Python
__pycache__/
*.py[cod]
*.so
.Python
*.egg-info/
dist/
build/

# IDE
.idea/
.vscode/
*.swp

# Virtual Environment
venv/
.env

# PyQt5
*.ui.bak
```

### Aşama 1: Core (gitignore'dan çıkar)

```gitignore
# Artık gösteriliyor:
# - src/core/

# Hala gizli:
src/services/
src/algorithms/
src/experiments/
src/ui/
```

**Commit:**
```bash
git add src/__init__.py src/core/
git commit -m "feat: core modülü - config.py eklendi"
```

### Aşama 2: Services

```gitignore
# Artık gösteriliyor:
# - src/core/
# - src/services/

# Hala gizli:
src/algorithms/
src/experiments/
src/ui/
```

**Commit:**
```bash
git add src/services/
git commit -m "feat: servis modülleri eklendi"
```

### Aşama 3-4: Algorithms

```gitignore
# Artık gösteriliyor:
# - src/core/
# - src/services/
# - src/algorithms/

# Hala gizli:
src/experiments/
src/ui/
```

**Commit'ler (her algoritma için ayrı):**
```bash
git add src/algorithms/__init__.py src/algorithms/genetic_algorithm.py
git commit -m "feat: Genetic Algorithm eklendi"

git add src/algorithms/aco.py
git commit -m "feat: Ant Colony Optimization eklendi"

# ... diğer algoritmalar
```

### Aşama 5: Experiments

```gitignore
# Artık gösteriliyor:
# - src/core/
# - src/services/
# - src/algorithms/
# - src/experiments/

# Hala gizli:
src/ui/
```

### Aşama 6-7: UI ve Final

```gitignore
# Tümü gösteriliyor
# src/ satırı kaldırıldı

# Python
__pycache__/
*.py[cod]
# ...
```

---

## 🧪 TEST PROSEDÜRLERİ

### Birim Testleri

Her modül için test dosyası oluşturun:

```
tests/
├── test_config.py
├── test_graph_service.py
├── test_metrics_service.py
├── test_genetic_algorithm.py
├── test_aco.py
├── test_pso.py
├── test_q_learning.py
└── test_sarsa.py
```

**Örnek test:**
```python
# tests/test_genetic_algorithm.py
import unittest
from src.algorithms.genetic_algorithm import GeneticAlgorithm
from src.services.graph_service import GraphService

class TestGeneticAlgorithm(unittest.TestCase):
    
    def setUp(self):
        gs = GraphService(seed=42)
        self.graph = gs.generate_graph(50, 0.4)
        self.ga = GeneticAlgorithm(self.graph, seed=42)
    
    def test_optimize_finds_path(self):
        result = self.ga.optimize(0, 49, {'delay': 0.33, 'reliability': 0.33, 'resource': 0.34})
        self.assertIsNotNone(result.path)
        self.assertGreater(len(result.path), 0)
        self.assertEqual(result.path[0], 0)
        self.assertEqual(result.path[-1], 49)
    
    def test_path_is_valid(self):
        result = self.ga.optimize(0, 49, {'delay': 0.33, 'reliability': 0.33, 'resource': 0.34})
        for i in range(len(result.path) - 1):
            self.assertTrue(self.graph.has_edge(result.path[i], result.path[i+1]))

if __name__ == '__main__':
    unittest.main()
```

### Entegrasyon Testi

```python
# tests/test_integration.py
def test_full_workflow():
    """Tam iş akışı testi."""
    # 1. Graf oluştur
    gs = GraphService(seed=42)
    graph = gs.generate_graph(100, 0.4)
    
    # 2. Tüm algoritmaları test et
    algorithms = [
        GeneticAlgorithm,
        AntColonyOptimization,
        ParticleSwarmOptimization,
        SimulatedAnnealing,
        QLearning,
        SARSA
    ]
    
    weights = {'delay': 0.33, 'reliability': 0.33, 'resource': 0.34}
    
    for AlgoClass in algorithms:
        algo = AlgoClass(graph, seed=42)
        result = algo.optimize(0, 99, weights)
        
        assert result.path is not None
        assert len(result.path) >= 2
        assert result.path[0] == 0
        assert result.path[-1] == 99
```

---

## 📝 KOD STANDARTLARI

### Python Style Guide (PEP 8)

```python
# Doğru
class GeneticAlgorithm:
    """Genetik Algoritma implementasyonu."""
    
    def __init__(self, graph, population_size=100):
        self.graph = graph
        self.population_size = population_size
    
    def optimize(self, source, destination, weights):
        """
        Optimizasyon çalıştır.
        
        Args:
            source: Kaynak düğüm
            destination: Hedef düğüm
            weights: Metrik ağırlıkları
        
        Returns:
            OptimizationResult objesi
        """
        pass


# Yanlış
class geneticAlgorithm:
    def __init__(self,graph,populationSize=100):
        self.graph=graph
        self.populationSize=populationSize
```

### Docstring Formatı

```python
def calculate_weighted_cost(
    self,
    path: List[int],
    w_delay: float = 0.33,
    w_reliability: float = 0.33,
    w_resource: float = 0.34
) -> float:
    """
    Ağırlıklı toplam maliyet hesapla.
    
    Args:
        path: Düğüm ID listesi
        w_delay: Gecikme ağırlığı (varsayılan: 0.33)
        w_reliability: Güvenilirlik ağırlığı (varsayılan: 0.33)
        w_resource: Kaynak ağırlığı (varsayılan: 0.34)
    
    Returns:
        Normalize edilmiş ağırlıklı maliyet
    
    Raises:
        ValueError: Geçersiz yol
    
    Example:
        >>> ms = MetricsService(graph)
        >>> cost = ms.calculate_weighted_cost([0, 5, 10], 0.4, 0.4, 0.2)
    """
    pass
```

### Type Hints

```python
from typing import List, Dict, Optional, Tuple

def generate_path(
    self,
    source: int,
    destination: int,
    max_length: int = 50
) -> Optional[List[int]]:
    pass

def get_metrics(
    self,
    path: List[int]
) -> Dict[str, float]:
    pass
```

---

## 🚀 HIZLI BAŞLANGIÇ

### 1. Ortam Kurulumu

```bash
# Sanal ortam oluştur
python -m venv venv

# Aktive et (Windows)
venv\Scripts\activate

# Aktive et (Linux/Mac)
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. Uygulamayı Çalıştır

```bash
python main.py
```

### 3. Testleri Çalıştır

```bash
python -m pytest tests/
```

---

## 👥 GÖREV DAĞILIMI ÖNERİSİ

| Rol | Sorumluluk | Dosyalar |
|-----|------------|----------|
| **Lider** | Koordinasyon, entegrasyon | `main.py`, `config.py`, `README.md` |
| **Backend 1** | Servisler, deneyler | `graph_service.py`, `metrics_service.py`, `experiments/` |
| **Backend 2** | Meta-sezgisel algoritmalar | `genetic_algorithm.py`, `aco.py`, `pso.py`, `simulated_annealing.py` |
| **Backend 3** | RL algoritmaları | `q_learning.py`, `sarsa.py` |
| **Frontend** | UI geliştirme | `ui/` tüm dosyalar |

---
# Özellik Ekleme

1. Projeyi Bilgisayarınıza İndirin
Öncelikle projenin bir kopyasını yerel makinenize çekin:


`git clone https://github.com/Erkan303
/QoS-Multi-Objective-Routing.git
cd proje-adin
`
2. Bağımlılıkları Yükleyin
Projenin çalışması için gerekli kütüphaneleri yükleyin: (Örnek Python için verilmiştir, projenize göre değiştirebilirsiniz)


`pip install -r requirements.txt
`
🛠 Katkıda Bulunma Adımları
Projeye yeni bir özellik eklemek veya bir hatayı düzeltmek için şu adımları takip edin:

1. Yeni Bir Dal (Branch) Oluşturun
Ana dalda (main veya master) doğrudan değişiklik yapmamaya özen gösterin. Yapacağınız işi tanımlayan yeni bir dal açın:



`git checkout -b ozellik-adi
`
Örnek: git checkout -b login-ekrani-duzeltme

2. Değişikliklerinizi Yapın ve Kaydedin
Kodunuzu yazdıktan sonra değişiklikleri paketleyin ve bir mesajla kaydedin:

`
git add .
git commit -m "Açıklayıcı bir commit mesajı: Giriş ekranı tasarımı yenilendi"
`
3. Değişiklikleri Uzak Sunucuya Gönderin
Yerelinizdeki bu dalı GitHub'a (veya ilgili platforma) gönderin:

`
git push origin ozellik-adi
`
4. Pull Request (PR) Oluşturun
GitHub üzerinde projenin sayfasına gidin. Üst kısımda beliren "Compare & pull request" butonuna tıklayarak değişikliklerinizin ana projeye dahil edilmesi için talep oluşturun.

⚠️ Dikkat Edilmesi Gerekenler
Güncel Kalın: Çalışmaya başlamadan önce her zaman ana dalın güncel olduğundan emin olun (git pull origin main).

Mesaj Kalitesi: Commit mesajlarınızın kısa ama açıklayıcı olmasına dikkat edin.

Kod Standartları: Mevcut kod yazım stiline (indentation, isimlendirme vb.) sadık kalın.

*Doküman Versiyonu: 1.0*  
*Son Güncelleme: 3 Aralık 2025*

