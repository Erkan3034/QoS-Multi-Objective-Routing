"""
Karınca Kolonisi Optimizasyonu (ACO) - QoS Yönlendirme
Olasılık formülü: P(i,j) = [τ(i,j)^α · η(i,j)^β] / Σ[τ(i,k)^α · η(i,k)^β]
Feromon güncelleme: τ(i,j) ← (1-ρ)·τ(i,j) + Σ[Δτ_k(i,j)]
"""
import random, time, math, os
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from collections import defaultdict
from src.services.metrics_service import MetricsService


@dataclass
class ACOResult:
    """ACO algoritması sonuç yapısı"""
    path: List[int]                    # Bulunan en iyi yol
    fitness: float                     # Yolun toplam maliyeti
    iteration: int                     # Çözümün bulunduğu iterasyon
    computation_time_ms: float         # Hesaplama süresi (ms)
    convergence_data: Optional[Dict] = None  # Yakınsama verileri
    seed_used: Optional[int] = None    # Kullanılan seed değeri
    
    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "fitness": round(self.fitness, 6), "iteration": self.iteration,
                "computation_time_ms": round(self.computation_time_ms, 2), "seed_used": self.seed_used}


class OptimizedACO:
    """
    Gelişmiş Karınca Kolonisi Optimizasyonu
    - Adaptif α/β parametreleri (keşif↔sömürü dengesi)
    - Rank-based feromon güncellemesi
    - ε-greedy seçim stratejisi
    """
    
    def __init__(self, graph: nx.Graph, n_ants: int = 50, n_iterations: int = 100,
                 alpha_range: Tuple[float, float] = (0.8, 2.0), beta_range: Tuple[float, float] = (2.0, 5.0),
                 evaporation_rate: float = 0.1, q: float = 100.0, epsilon: float = 0.1, seed: int = None):
        self.graph, self.metrics = graph, MetricsService(graph)
        # Graf boyutuna göre karınca/iterasyon sayısı adaptasyonu
        gs = len(graph.nodes())
        self.n_ants = min(n_ants, 20 if gs > 200 else 30 if gs > 100 else n_ants)
        self.n_iter = min(n_iterations, 30 if gs > 200 else 50 if gs > 100 else n_iterations)
        # Parametre aralıkları ve başlangıç değerleri
        self.a_range, self.b_range = alpha_range, beta_range
        self.alpha, self.beta = sum(alpha_range)/2, sum(beta_range)/2
        self.rho, self.q, self.eps, self._seed = evaporation_rate, q, epsilon, seed
        self._actual_seed = None
        # Feromon matrisi (lazy init, min-max sınırları)
        self.pheromone: Dict[Tuple[int,int], float] = defaultdict(lambda: 1.0)
        self.tau_min, self.tau_max = 0.01, 10.0
        self.best_hist, self.stag = [], 0  # Yakınsama takibi
    
    def optimize(self, source: int, destination: int, weights: Dict[str, float] = None,
                 bandwidth_demand: float = 0.0, progress_callback: Callable = None) -> ACOResult:
        """Ana optimizasyon döngüsü"""
        t0, weights = time.perf_counter(), weights or {'delay': 0.33, 'reliability': 0.33, 'resource': 0.34}
        # Seed ayarla (verilen veya rastgele)
        self._actual_seed = self._seed if self._seed else (time.time_ns() + os.getpid()) % (2**32-1)
        random.seed(self._actual_seed); np.random.seed(self._actual_seed)
        # State sıfırla
        self.pheromone.clear(); self.best_hist, self.stag = [], 0
        self.alpha, self.beta, self.rho = sum(self.a_range)/2, sum(self.b_range)/2, 0.1
        
        best_path, best_fit, best_iter = None, float('inf'), 0
        
        for it in range(self.n_iter):
            # Adaptif parametre güncellemesi: ilerleme arttıkça α↑ β↓ (sömürüye geçiş)
            p = it / self.n_iter
            self.alpha = self.a_range[0] + (self.a_range[1] - self.a_range[0]) * p
            self.beta = self.b_range[1] - (self.b_range[1] - self.b_range[0]) * p
            if self.stag > 10: self.rho = min(0.3, self.rho * 1.1); self.stag = 0
            
            # Tüm karıncaları çalıştır
            paths, fits = [], []
            for _ in range(self.n_ants):
                path = self._build_path(source, destination, weights, bandwidth_demand)
                if path:
                    paths.append(path)
                    fits.append(self.metrics.calculate_weighted_cost(path, weights['delay'], weights['reliability'], weights['resource'], bandwidth_demand))
            
            # Global en iyi güncelle
            if fits:
                idx = int(np.argmin(fits))
                if fits[idx] < best_fit:
                    best_fit, best_path, best_iter, self.stag = fits[idx], paths[idx], it, 0
                else: self.stag += 1
            self.best_hist.append(best_fit)
            
            # Feromon güncelle
            self._update_pheromones(paths, fits, best_path, best_fit)
            if progress_callback and it % 3 == 0:
                try: progress_callback(it, best_fit)
                except: pass
            # Erken durdurma (yakınsama veya stagnasyon)
            if len(self.best_hist) > 3 and max(self.best_hist[-3:]) - min(self.best_hist[-3:]) < 0.001: break
            if self.stag > 5: break
        
        # Fallback: ACO başarısızsa en kısa yolu kullan
        if not best_path:
            try: best_path = nx.shortest_path(self.graph, source, destination)
            except: best_path = [source, destination]
            try: best_fit = self.metrics.calculate_weighted_cost(best_path, weights['delay'], weights['reliability'], weights['resource'], bandwidth_demand)
            except: best_fit = float('inf')
        
        return ACOResult(best_path, best_fit, best_iter, (time.perf_counter()-t0)*1000,
                        {"best_fitness": self.best_hist}, self._actual_seed)
    
    def _build_path(self, src: int, dst: int, w: Dict, bw: float) -> Optional[List[int]]:
        """Tek karınca için yol inşası (ε-greedy strateji)"""
        path, cur, visited = [src], src, {src}
        for _ in range(100):
            if cur == dst: return path
            # Geçerli komşuları filtrele (bandwidth kısıtı)
            cands = [n for n in self.graph.neighbors(cur) if n not in visited and (bw <= 0 or self.graph[cur][n].get('bandwidth', 1000) >= bw)]
            if not cands: return None
            if dst in cands: return path + [dst]
            # Sonraki düğüm seçimi: ε olasılıkla rastgele, (1-ε) olasılıkla feromon-sezgisel
            if random.random() < self.eps:
                nxt = random.choice(cands)
            else:
                # P(i,j) ∝ τ^α · η^β hesapla
                scores = [(self.pheromone[(cur,c)] ** self.alpha) * (self._eta(cur,c,w) ** self.beta) for c in cands]
                tot = sum(scores); probs = [s/tot for s in scores] if tot > 0 else [1/len(cands)]*len(cands)
                r, cum = random.random(), 0.0
                for c, p in zip(cands, probs):
                    cum += p
                    if r <= cum: nxt = c; break
                else: nxt = cands[-1]
            path.append(nxt); visited.add(nxt); cur = nxt
        return None
    
    def _eta(self, u: int, v: int, w: Dict) -> float:
        """Sezgisel değer η = 1/(1+maliyet) - düşük maliyet = yüksek çekicilik"""
        e = self.graph.edges[u, v]
        cost = (w['delay'] * e['delay']/100 + 
                w['reliability'] * (-math.log(max(e['reliability'], 0.01)) - math.log(max(self.graph.nodes[v].get('reliability', 0.99), 0.01))) +
                w['resource'] * (1000/max(e['bandwidth'], 1))/100)
        return max(1/(1+cost), 0.001)
    
    def _update_pheromones(self, paths: List, fits: List, best: List, best_f: float):
        """Feromon güncelleme: buharlaşma + rank-based deposit + global-best bonus"""
        # 1) Buharlaşma (sadece kullanılan kenarlar)
        edges = set()
        for p in paths:
            for i in range(len(p)-1): edges.add((p[i],p[i+1])); edges.add((p[i+1],p[i]))
        for e in edges:
            if e in self.pheromone: self.pheromone[e] *= (1 - self.rho)
        # 2) Rank-based deposit (en iyi 10)
        if paths and fits:
            for rank, idx in enumerate(np.argsort(fits)[:10]):
                if fits[idx] == float('inf'): continue
                dep = (len(fits)-rank) * self.q / fits[idx]
                for i in range(len(paths[idx])-1):
                    self.pheromone[(paths[idx][i], paths[idx][i+1])] += dep
                    self.pheromone[(paths[idx][i+1], paths[idx][i])] += dep
        # 3) Global-best bonus (3x ağırlık)
        if best and best_f != float('inf'):
            dep = 3 * self.q / best_f
            for i in range(len(best)-1):
                self.pheromone[(best[i], best[i+1])] += dep
                self.pheromone[(best[i+1], best[i])] += dep
        # 4) Min-max sınırları uygula
        for e in self.pheromone: self.pheromone[e] = max(self.tau_min, min(self.tau_max, self.pheromone[e]))


AntColonyOptimization = OptimizedACO  # Geriye uyumluluk