# 🚀 PyQt5 Desktop - Performans Optimizasyon Rehberi

> **Tarih:** 3 Aralık 2025  
> **Proje:** BSM307 - QoS Multi-Objective Routing Desktop Application  
> **Amaç:** Backend performansını maksimize etmek için yapılacak iyileştirmeler

---

## 📑 İÇİNDEKİLER

1. [Mevcut Durum Analizi](#-mevcut-durum-analizi)
2. [Kritik İyileştirmeler](#-kritik-iyileştirmeler)
3. [Algoritma Optimizasyonları](#-algoritma-optimizasyonları)
4. [Bellek ve Performans](#-bellek-ve-performans)
5. [UI Thread Optimizasyonu](#-ui-thread-optimizasyonu)
6. [Uygulama Öncelikleri](#-uygulama-öncelikleri)

---

## 📊 MEVCUT DURUM ANALİZİ

| Bileşen | Durum | Verimlilik |
|---------|-------|------------|
| Algoritma Parametreleri | Varsayılan değerler | ⚡ %50 |
| Metrik Normalizasyonu | Sabit ölçekleme | ⚡ %60 |
| Bellek Yönetimi | Temel | ⚡ %65 |
| Thread Yönetimi | QThread | ⚡ %70 |
| Caching | Yok | ⚡ %40 |

---

## 🔴 KRİTİK İYİLEŞTİRMELER

### 1. Algoritma Parametre Optimizasyonu

**Dosya:** `src/core/config.py`

Mevcut varsayılan değerler optimize edilmeli:

```python
# ============================================
# GENETIC ALGORITHM - Daha agresif arama
# ============================================
GA_POPULATION_SIZE: int = 150      # 100 → 150
GA_GENERATIONS: int = 800          # 500 → 800
GA_MUTATION_RATE: float = 0.15     # 0.1 → 0.15
GA_CROSSOVER_RATE: float = 0.85    # 0.8 → 0.85
GA_ELITISM: float = 0.05           # 0.1 → 0.05

# ============================================
# ANT COLONY OPTIMIZATION
# ============================================
ACO_N_ANTS: int = 80               # 50 → 80
ACO_N_ITERATIONS: int = 150        # 100 → 150
ACO_ALPHA: float = 1.2             # 1.0 → 1.2
ACO_BETA: float = 3.0              # 2.0 → 3.0
ACO_EVAPORATION_RATE: float = 0.4  # 0.5 → 0.4

# ============================================
# PARTICLE SWARM OPTIMIZATION
# ============================================
PSO_N_PARTICLES: int = 50          # 30 → 50
PSO_N_ITERATIONS: int = 150        # 100 → 150
PSO_W: float = 0.6                 # 0.7 → 0.6
PSO_C1: float = 1.8                # 1.5 → 1.8
PSO_C2: float = 1.8                # 1.5 → 1.8

# ============================================
# SIMULATED ANNEALING
# ============================================
SA_INITIAL_TEMPERATURE: float = 2000.0   # 1000 → 2000
SA_FINAL_TEMPERATURE: float = 0.001      # 0.01 → 0.001
SA_COOLING_RATE: float = 0.998           # 0.995 → 0.998
SA_ITERATIONS_PER_TEMP: int = 15         # 10 → 15

# ============================================
# Q-LEARNING
# ============================================
QL_EPISODES: int = 8000            # 5000 → 8000
QL_LEARNING_RATE: float = 0.15     # 0.1 → 0.15
QL_DISCOUNT_FACTOR: float = 0.98   # 0.95 → 0.98
QL_EPSILON_DECAY: float = 0.998    # 0.995 → 0.998

# ============================================
# SARSA
# ============================================
SARSA_EPISODES: int = 8000         # 5000 → 8000
SARSA_LEARNING_RATE: float = 0.15
SARSA_DISCOUNT_FACTOR: float = 0.98
SARSA_EPSILON_DECAY: float = 0.998
```

---

### 2. Dinamik Metrik Normalizasyonu

**Dosya:** `src/services/metrics_service.py`

Sabit ölçekleme faktörleri yerine dinamik normalizasyon:

```python
def _calculate_normalization_factors(self) -> Dict[str, float]:
    """
    Graf'a göre dinamik normalizasyon faktörleri hesapla.
    """
    delays = []
    bandwidths = []
    reliabilities = []
    
    for u, v in self.graph.edges():
        edge = self.graph.edges[u, v]
        delays.append(edge['delay'])
        bandwidths.append(edge['bandwidth'])
        reliabilities.append(edge['reliability'])
    
    # Tahmini maksimum yol uzunluğu
    try:
        avg_path_length = nx.average_shortest_path_length(self.graph)
        estimated_max_hops = int(avg_path_length * 2)
    except:
        estimated_max_hops = 20
    
    return {
        'delay_scale': max(delays) * estimated_max_hops,
        'reliability_scale': -math.log(min(reliabilities)) * estimated_max_hops * 2,
        'resource_scale': (1000 / min(bandwidths)) * estimated_max_hops
    }
```

---

### 3. Early Stopping Mekanizması

**Yeni Dosya:** `src/algorithms/base.py`

```python
class EarlyStopper:
    """
    Yakınsama durumunda erken durdurma.
    
    Fitness değeri iyileşmezse algoritmayı durdurur.
    """
    
    def __init__(self, patience: int = 50, min_delta: float = 0.0001):
        self.patience = patience
        self.min_delta = min_delta
        self.best = float('inf')
        self.counter = 0
    
    def should_stop(self, current: float) -> bool:
        if current < self.best - self.min_delta:
            self.best = current
            self.counter = 0
            return False
        else:
            self.counter += 1
            return self.counter >= self.patience
    
    def reset(self):
        self.best = float('inf')
        self.counter = 0
```

**Kullanım (GA örneği):**

```python
def optimize(self, source, destination, weights):
    early_stopper = EarlyStopper(patience=100)
    
    for gen in range(self.generations):
        # ... optimization ...
        
        if early_stopper.should_stop(best_fitness):
            print(f"Early stopping at generation {gen}")
            break
```

---

## 🟠 ALGORİTMA OPTİMİZASYONLARI

### 4. Genetik Algoritma - Adaptive Mutation

**Dosya:** `src/algorithms/genetic_algorithm.py`

```python
def _adaptive_mutation_rate(self, generation: int) -> float:
    """
    Nesle göre adaptif mutasyon oranı.
    
    Başlangıçta yüksek (keşif), sonra düşük (sömürü).
    """
    base_rate = self.mutation_rate
    decay_factor = 1 - (generation / self.generations)
    adaptive_rate = base_rate * (0.5 + decay_factor)
    return min(0.3, max(0.05, adaptive_rate))
```

### 5. Local Search (2-opt) - Hibrit GA

```python
def _local_search_2opt(self, path: List[int]) -> List[int]:
    """2-opt local search ile yolu iyileştir."""
    if len(path) <= 3:
        return path
    
    best_path = path[:]
    best_fitness = self._calculate_fitness(best_path)
    improved = True
    
    while improved:
        improved = False
        for i in range(1, len(best_path) - 2):
            current_node = best_path[i]
            prev_node = best_path[i - 1]
            next_node = best_path[i + 1]
            
            # Alternatif düğümler bul
            alternatives = set(self.graph.neighbors(prev_node)) & \
                          set(self.graph.neighbors(next_node))
            alternatives.discard(current_node)
            alternatives -= set(best_path)
            
            for alt_node in alternatives:
                new_path = best_path[:]
                new_path[i] = alt_node
                new_fitness = self._calculate_fitness(new_path)
                
                if new_fitness < best_fitness:
                    best_path = new_path
                    best_fitness = new_fitness
                    improved = True
                    break
            
            if improved:
                break
    
    return best_path
```

### 6. ACO - Min-Max Ant System (MMAS)

**Dosya:** `src/algorithms/aco.py`

```python
class AntColonyOptimizationMmas(AntColonyOptimization):
    """
    MMAS: Feromon değerleri [tau_min, tau_max] aralığında tutulur.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tau_max = 10.0
        self.tau_min = 0.01
    
    def _update_tau_limits(self, best_fitness: float):
        """Dinamik feromon limitleri."""
        if best_fitness > 0 and best_fitness != float('inf'):
            self.tau_max = 1.0 / (self.evaporation_rate * best_fitness)
            n = self.graph.number_of_nodes()
            self.tau_min = max(0.001, self.tau_max / (2 * n))
    
    def _update_pheromones_mmas(self, best_path, best_fitness):
        """MMAS feromon güncelleme."""
        # Buharlaşma
        for edge in self.pheromone:
            self.pheromone[edge] *= (1 - self.evaporation_rate)
        
        # Sadece en iyi feromon bırakır
        if best_path and best_fitness > 0:
            deposit = self.q / best_fitness
            for i in range(len(best_path) - 1):
                u, v = best_path[i], best_path[i + 1]
                self.pheromone[(u, v)] += deposit
                self.pheromone[(v, u)] += deposit
        
        # Limitle
        self._update_tau_limits(best_fitness)
        for edge in self.pheromone:
            self.pheromone[edge] = max(self.tau_min, min(self.tau_max, self.pheromone[edge]))
```

### 7. Q-Learning - Experience Replay

**Dosya:** `src/algorithms/q_learning.py`

```python
from collections import deque
import random

class ExperienceBuffer:
    """Experience replay buffer."""
    
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
    
    def add(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int):
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))


class QLearningWithReplay(QLearning):
    """Experience Replay destekli Q-Learning."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.replay_buffer = ExperienceBuffer(capacity=10000)
        self.batch_size = 32
    
    def _learn_from_replay(self):
        """Replay buffer'dan öğren."""
        if len(self.replay_buffer.buffer) < self.batch_size:
            return
        
        batch = self.replay_buffer.sample(self.batch_size)
        
        for state, action, reward, next_state, done in batch:
            if done:
                target = reward
            else:
                next_actions = list(self.graph.neighbors(next_state))
                max_next_q = max(
                    (self.q_table[next_state][a] for a in next_actions),
                    default=0
                )
                target = reward + self.discount_factor * max_next_q
            
            current_q = self.q_table[state][action]
            self.q_table[state][action] += self.learning_rate * (target - current_q)
```

---

## 🟡 BELLEK VE PERFORMANS

### 8. Caching Mekanizması

**Dosya:** `src/services/metrics_service.py`

```python
class CachedMetricsService(MetricsService):
    """Cache destekli metrik servisi."""
    
    def __init__(self, graph, cache_size: int = 10000):
        super().__init__(graph)
        self._cache = {}
        self._cache_size = cache_size
        self._cache_hits = 0
        self._cache_misses = 0
    
    def calculate_weighted_cost_cached(
        self,
        path: tuple,  # Tuple hashable
        w_delay: float,
        w_reliability: float,
        w_resource: float
    ) -> float:
        cache_key = (path, round(w_delay, 4), round(w_reliability, 4), round(w_resource, 4))
        
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
        
        self._cache_misses += 1
        result = self.calculate_weighted_cost(list(path), w_delay, w_reliability, w_resource)
        
        # Cache boyut kontrolü
        if len(self._cache) >= self._cache_size:
            # En eski %10'u sil
            keys_to_remove = list(self._cache.keys())[:self._cache_size // 10]
            for key in keys_to_remove:
                del self._cache[key]
        
        self._cache[cache_key] = result
        return result
    
    def get_cache_stats(self) -> dict:
        total = self._cache_hits + self._cache_misses
        return {
            "size": len(self._cache),
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": self._cache_hits / total if total > 0 else 0
        }
```

### 9. A* Heuristic Başlangıç Çözümü

**Yeni Dosya:** `src/algorithms/utils.py`

```python
import math
import networkx as nx
from typing import List, Dict, Optional

def get_initial_solution_astar(
    graph: nx.Graph,
    source: int,
    destination: int,
    weights: Dict[str, float]
) -> Optional[List[int]]:
    """
    A* ile kaliteli başlangıç çözümü.
    
    Meta-sezgisel algoritmalara iyi başlangıç sağlar.
    """
    def heuristic(u, v):
        try:
            return nx.shortest_path_length(graph, u, v) * 0.5
        except:
            return float('inf')
    
    def edge_cost(u, v, d):
        delay_cost = d['delay'] / 100
        rel_cost = -math.log(d['reliability'])
        res_cost = 1000 / d['bandwidth'] / 50
        
        return (
            weights.get('delay', 0.33) * delay_cost +
            weights.get('reliability', 0.33) * rel_cost +
            weights.get('resource', 0.34) * res_cost
        )
    
    try:
        return nx.astar_path(graph, source, destination, heuristic=heuristic, weight=edge_cost)
    except:
        return None


def get_diverse_initial_solutions(
    graph: nx.Graph,
    source: int,
    destination: int,
    weights: Dict[str, float],
    n_solutions: int = 5
) -> List[List[int]]:
    """Çeşitli başlangıç çözümleri."""
    solutions = []
    
    # A* çözümü
    astar = get_initial_solution_astar(graph, source, destination, weights)
    if astar:
        solutions.append(astar)
    
    # Farklı ağırlıklarla
    variations = [
        {'delay': 0.8, 'reliability': 0.1, 'resource': 0.1},
        {'delay': 0.1, 'reliability': 0.8, 'resource': 0.1},
        {'delay': 0.1, 'reliability': 0.1, 'resource': 0.8},
    ]
    
    for w in variations:
        if len(solutions) >= n_solutions:
            break
        path = get_initial_solution_astar(graph, source, destination, w)
        if path and path not in solutions:
            solutions.append(path)
    
    return solutions
```

---

## 🟢 UI THREAD OPTİMİZASYONU

### 10. Algoritma Worker Thread

**Dosya:** `src/ui/workers.py`

```python
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, Any

class AlgorithmWorker(QThread):
    """
    Algoritmaları arka planda çalıştıran worker.
    
    UI thread'i bloklamaz.
    """
    
    # Sinyaller
    progress = pyqtSignal(int, str)  # yüzde, mesaj
    finished = pyqtSignal(dict)      # sonuç
    error = pyqtSignal(str)          # hata mesajı
    
    def __init__(
        self,
        algorithm_class,
        graph,
        source: int,
        destination: int,
        weights: Dict[str, float],
        parent=None
    ):
        super().__init__(parent)
        self.algorithm_class = algorithm_class
        self.graph = graph
        self.source = source
        self.destination = destination
        self.weights = weights
        self._is_cancelled = False
    
    def run(self):
        try:
            self.progress.emit(0, "Algoritma başlatılıyor...")
            
            algo = self.algorithm_class(graph=self.graph)
            
            self.progress.emit(10, "Optimizasyon yapılıyor...")
            
            result = algo.optimize(
                source=self.source,
                destination=self.destination,
                weights=self.weights
            )
            
            if self._is_cancelled:
                return
            
            self.progress.emit(100, "Tamamlandı!")
            
            self.finished.emit({
                'path': result.path,
                'fitness': getattr(result, 'fitness', None),
                'computation_time_ms': result.computation_time_ms
            })
            
        except Exception as e:
            self.error.emit(str(e))
    
    def cancel(self):
        self._is_cancelled = True


class CompareWorker(QThread):
    """Tüm algoritmaları paralel karşılaştıran worker."""
    
    progress = pyqtSignal(int, int, str)  # current, total, message
    result_ready = pyqtSignal(str, dict)  # algorithm_name, result
    finished = pyqtSignal(dict)           # all results
    error = pyqtSignal(str)
    
    def __init__(self, algorithms, graph, source, destination, weights, parent=None):
        super().__init__(parent)
        self.algorithms = algorithms
        self.graph = graph
        self.source = source
        self.destination = destination
        self.weights = weights
    
    def run(self):
        results = {}
        total = len(self.algorithms)
        
        for i, (name, AlgoClass) in enumerate(self.algorithms.items()):
            self.progress.emit(i, total, f"{name} çalıştırılıyor...")
            
            try:
                algo = AlgoClass(graph=self.graph)
                result = algo.optimize(
                    source=self.source,
                    destination=self.destination,
                    weights=self.weights
                )
                
                result_dict = {
                    'path': result.path,
                    'fitness': getattr(result, 'fitness', None),
                    'computation_time_ms': result.computation_time_ms,
                    'success': True
                }
                
            except Exception as e:
                result_dict = {
                    'path': [],
                    'fitness': float('inf'),
                    'computation_time_ms': 0,
                    'success': False,
                    'error': str(e)
                }
            
            results[name] = result_dict
            self.result_ready.emit(name, result_dict)
        
        self.progress.emit(total, total, "Tamamlandı!")
        self.finished.emit(results)
```

### 11. Progressive Graph Rendering

**Dosya:** `src/ui/components/graph_widget.py`

```python
class ProgressiveGraphRenderer:
    """
    Büyük grafları aşamalı olarak render eder.
    
    İlk önce önemli düğümleri (S, D, path), sonra diğerlerini çizer.
    """
    
    def __init__(self, batch_size: int = 50, interval_ms: int = 50):
        self.batch_size = batch_size
        self.interval_ms = interval_ms
        self.timer = QTimer()
        self.current_batch = 0
        self.nodes_to_render = []
    
    def start_progressive_render(self, nodes: List, important_nodes: Set):
        """
        Aşamalı render başlat.
        
        Args:
            nodes: Tüm düğümler
            important_nodes: Öncelikli düğümler (S, D, path)
        """
        # Önce önemli düğümler
        self.nodes_to_render = list(important_nodes)
        
        # Sonra diğerleri
        other_nodes = [n for n in nodes if n not in important_nodes]
        self.nodes_to_render.extend(other_nodes)
        
        self.current_batch = 0
        self.timer.timeout.connect(self._render_next_batch)
        self.timer.start(self.interval_ms)
    
    def _render_next_batch(self):
        start = self.current_batch * self.batch_size
        end = start + self.batch_size
        
        batch = self.nodes_to_render[start:end]
        
        if not batch:
            self.timer.stop()
            return
        
        # Batch'i render et
        for node in batch:
            self._draw_node(node)
        
        self.current_batch += 1
```

---

## 📋 UYGULAMA ÖNCELİKLERİ

| Sıra | İyileştirme | Etki | Zorluk | Süre |
|------|-------------|------|--------|------|
| 1 | Parametre Optimizasyonu | 🔥 Yüksek | Düşük | 1 saat |
| 2 | Dinamik Normalizasyon | 🔥 Yüksek | Orta | 2 saat |
| 3 | Early Stopping | 🔥 Yüksek | Düşük | 1 saat |
| 4 | Caching | Yüksek | Düşük | 1 saat |
| 5 | GA Adaptive Mutation | Yüksek | Orta | 2 saat |
| 6 | ACO MMAS | Yüksek | Orta | 3 saat |
| 7 | Q-Learning Replay | Orta | Yüksek | 4 saat |
| 8 | A* Initial Solution | Orta | Orta | 2 saat |
| 9 | Worker Threads | Orta | Orta | 2 saat |
| 10 | Progressive Rendering | Düşük | Orta | 2 saat |

---

## 🎯 BEKLENEN İYİLEŞMELER

| Metrik | Mevcut | Hedef | İyileşme |
|--------|--------|-------|----------|
| **Çözüm Kalitesi** | ~%85 | ~%95 | +%10 |
| **Hesaplama Süresi** | 5-30s | 2-15s | -%50 |
| **Yakınsama Hızı** | 500 iter | 200-300 iter | -%40 |
| **Başarı Oranı** | ~%90 | ~%98 | +%8 |
| **UI Responsiveness** | Orta | Yüksek | +%100 |
| **Bellek Kullanımı** | Yüksek | Orta | -%30 |

---

## ✅ UYGULAMA KONTROL LİSTESİ

### Faz 1: Kritik (Hafta 1)
- [ ] `config.py` parametre değişiklikleri
- [ ] `metrics_service.py` dinamik normalizasyon
- [ ] Early stopping mekanizması

### Faz 2: Önemli (Hafta 2)
- [ ] Caching mekanizması
- [ ] GA adaptive mutation + local search
- [ ] ACO MMAS implementasyonu

### Faz 3: İyileştirme (Hafta 3)
- [ ] Q-Learning experience replay
- [ ] A* initial solution
- [ ] Worker thread optimizasyonu

### Faz 4: Bonus (Hafta 4)
- [ ] Progressive rendering
- [ ] Online learning
- [ ] Paralel algoritma execution

---

*Doküman Versiyonu: 1.0*  
*Son Güncelleme: 3 Aralık 2025*

