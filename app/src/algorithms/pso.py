"""
Particle Swarm Optimization (PSO) – Ayrık / Yol Tabanlı

PSO, her parçacığın bir çözümü temsil ettiği ve
kişisel en iyi (pbest) ile sürünün en iyi çözümünden (gbest)
öğrenerek ilerleyen sürü tabanlı bir optimizasyon algoritmasıdır.

Bu çalışmada PSO, yönlendirme problemi için uyarlanmıştır:
- Konum   : bir yol (düğümler listesi)
- Hız     : değiştirilecek yol indeksleri (ayrık uyarlama)
- Hareket : swap, reroute ve shortcut işlemleri
- Fitness : gecikme, güvenilirlik ve kaynak maliyetlerinin ağırlıklı toplamı

Bu yaklaşım, PSO’nun temel mantığını koruyarak
ayrık grafik tabanlı routing problemlerine uygun hale getirir.
"""


import random
import time
import os
import networkx as nx
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from src.services.metrics_service import MetricsService
from src.core.config import settings


# =========================
# 1) ÇIKTI (Result) SINIFI
# =========================
# Optimizasyon sonunda dönen özet:
# - path: bulunan en iyi yol
# - fitness: yolun maliyeti (küçük daha iyi)
# - iteration: en iyi sonucun bulunduğu iterasyon
# - computation_time_ms: süre
@dataclass
class PSOResult:
    path: List[int]
    fitness: float
    iteration: int
    computation_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "fitness": round(self.fitness, 6),
            "iteration": self.iteration,
            "computation_time_ms": round(self.computation_time_ms, 2)
        }


# =========================
# 2) PARTICLE (Parçacık)
# =========================
# Her particle bir aday çözüm taşır:
# - position = path (düğümler listesi)
# - velocity = değiştirilecek indeksler (ayrık PSO proxy)
# - pbest = parçacığın kendi en iyi yolu
class Particle:
    def __init__(self, path: List[int], fitness: float):
        self.path = path
        self.fitness = fitness

        self.velocity: List[int] = []          # bu iterasyonda düzenlenecek indeksler
        self.pbest_path = path[:]              # kişisel en iyi yol
        self.pbest_fitness = fitness           # kişisel en iyi fitness


# =========================
# 3) PSO ANA SINIFI
# =========================
# PSO parametreleri:
# - n_particles: sürü büyüklüğü
# - n_iterations: iterasyon sayısı
# - w: keşif oranı (burada inertia gibi kullanılıyor)
# - c1: pbest'e yönelim (cognitive)
# - c2: gbest'e yönelim (social)
# - max_velocity: iterasyonda en fazla kaç indeks değişecek
class ParticleSwarmOptimization:
    def __init__(
        self,
        graph: nx.Graph,
        n_particles: int = 30,
        n_iterations: int = 100,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
        seed: int = None,
        max_path_len: int = 60,
        max_initial_steps: int = 150,
        max_segment_steps: int = 40,
        max_velocity: int = 4,
        # UI dostu ayarlar
        progress_every: int = 5,   # kaç iterasyonda bir callback
        ui_yield_ms: float = 1.0,  # küçük bekleme (ms)
        **kwargs
    ):
        self.graph = graph
        self.n_particles = int(n_particles)
        self.n_iterations = int(n_iterations)

        self.w = float(w)
        self.c1 = float(c1)
        self.c2 = float(c2)

        self.max_path_len = int(max_path_len)
        self.max_initial_steps = int(max_initial_steps)
        self.max_segment_steps = int(max_segment_steps)
        self.max_velocity = int(max_velocity)

        # UI throttle
        self.progress_every = max(int(progress_every), 1)
        self.ui_yield_ms = float(ui_yield_ms)

        # [FIX] Store seed for stochastic behavior check
        self._seed = seed
        if seed is not None:
            random.seed(seed)

        self.metrics_service = MetricsService(graph)

        self.gbest_history: List[float] = []
        self.avg_fitness_history: List[float] = []

    # =========================
    # UI callback uyumu
    # =========================
    # Bazı UI'lar: on_progress(iteration, fitness)
    # Bazıları: on_progress(dict)
    def _emit_progress(self, progress_callback, iteration: int, best_fitness: float, avg_fitness: float) -> None:
        if not progress_callback:
            return

        # 1) En yaygın: (iteration, fitness)
        try:
            progress_callback(iteration, best_fitness)
            return
        except TypeError:
            pass

        # 2) Fallback: dict
        try:
            progress_callback({
                "iteration": iteration,
                "best_fitness": best_fitness,
                "avg_fitness": avg_fitness,
            })
        except TypeError:
            return

    def _maybe_yield_ui(self) -> None:
        if self.ui_yield_ms and self.ui_yield_ms > 0:
            time.sleep(self.ui_yield_ms / 1000.0)

    # =========================
    # OPTIMIZE (Ana döngü)
    # =========================
    # =========================
    # OPTIMIZE (Ana döngü)
    # =========================
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None,
        bandwidth_demand: float = 0.0,
        progress_callback=None,   # ✅ UI bunu gönderiyor
        **kwargs                  # ✅ başka ekstra argüman gelirse patlamasın
    ) -> PSOResult:
        start_time = time.perf_counter()

        weights = weights or {"delay": 0.33, "reliability": 0.33, "resource": 0.34}
        weights = self._normalize_weights(weights)

        # [FIX] Reset random state if no seed was set to ensure stochastic behavior
        if not hasattr(self, '_seed') or self._seed is None:
            import time as time_module
            if not hasattr(self, '_call_counter'):
                self._call_counter = 0
            self._call_counter += 1
            seed_val = time_module.time_ns() % (2**31) + os.getpid() + self._call_counter
            random.seed(seed_val)
            print(f"[PSO] Stokastik mod - seed={seed_val}, call={self._call_counter}")
        else:
            print(f"[PSO] Deterministik mod - seed={self._seed}")

        self.gbest_history.clear()
        self.avg_fitness_history.clear()

        particles = self._initialize_particles(source, destination, weights, bandwidth_demand)

        # fallback
        if not particles:
            try:
                # [FIX] Fallback respects bandwidth
                if bandwidth_demand > 0:
                    valid_edges = [
                        (u, v) for u, v, d in self.graph.edges(data=True) 
                        if d.get('bandwidth', 1000) >= bandwidth_demand
                    ]
                    temp_graph = self.graph.edge_subgraph(valid_edges)
                    fallback = nx.shortest_path(temp_graph, source, destination)
                else:
                    fallback = nx.shortest_path(self.graph, source, destination)
                f = self._calculate_fitness(fallback, weights, bandwidth_demand)
            except Exception:
                fallback = [source, destination]
                f = float("inf")

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return PSOResult(path=fallback, fitness=f, iteration=0, computation_time_ms=elapsed_ms)

        # gbest init
        gbest_particle = min(particles, key=lambda p: p.fitness)
        gbest_path = gbest_particle.path[:]
        gbest_fitness = gbest_particle.fitness
        best_iteration = 0

        # iterasyonlar
        for iteration in range(self.n_iterations):
            valid_fitness_vals = []

            for particle in particles:
                self._update_velocity(particle, gbest_path)
                new_path = self._update_position(particle, source, destination)

                if new_path:
                    new_path = self._trim_path(new_path)
                    # Pass bandwidth_demand to fitness
                    new_fitness = self._calculate_fitness(new_path, weights, bandwidth_demand)

                    particle.path = new_path
                    particle.fitness = new_fitness

                    if new_fitness < particle.pbest_fitness:
                        particle.pbest_path = new_path[:]
                        particle.pbest_fitness = new_fitness

                    if new_fitness < gbest_fitness:
                        gbest_path = new_path[:]
                        gbest_fitness = new_fitness
                        best_iteration = iteration

                if particle.fitness != float("inf"):
                    valid_fitness_vals.append(particle.fitness)

            # history
            self.gbest_history.append(gbest_fitness)
            avg_fit = (sum(valid_fitness_vals) / len(valid_fitness_vals)) if valid_fitness_vals else float("inf")
            self.avg_fitness_history.append(avg_fit)

            # ✅ UI callback (throttle)
            if progress_callback and (iteration % self.progress_every == 0):
                self._emit_progress(progress_callback, iteration, gbest_fitness, avg_fit)
                self._maybe_yield_ui()

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        print(f"[PSO] Sonuç: path={gbest_path[:5]}...{gbest_path[-2:] if len(gbest_path)>5 else ''}, len={len(gbest_path)}, fitness={gbest_fitness:.4f}")
        return PSOResult(path=gbest_path, fitness=gbest_fitness, iteration=best_iteration, computation_time_ms=elapsed_ms)



    # =========================
    # 5) INITIALIZATION
    # =========================
    # Amaç: her particle için geçerli bir başlangıç yolu üretmek (random walk)
    def _initialize_particles(self, source: int, destination: int, weights: Dict[str, float], bw_demand: float = 0.0) -> List[Particle]:
        particles: List[Particle] = []
        attempts = self.n_particles * 4  # zor graph için daha çok deneme

        while len(particles) < self.n_particles and attempts > 0:
            attempts -= 1
            # Pass bw_demand to generator
            path = self._generate_random_path(source, destination, max_length=self.max_path_len, bw_demand=bw_demand)
            if path:
                fit = self._calculate_fitness(path, weights, bw_demand)
                particles.append(Particle(path, fit))

        return particles

    # Random walk:
    # - unvisited komşuları tercih eder (loop azalsın)
    # - tıkanırsa birkaç kez restart dener
    def _generate_random_path(self, source: int, destination: int, max_length: int = 60, bw_demand: float = 0.0) -> Optional[List[int]]:
        if source == destination:
            return [source]

        for _restart in range(5):
            path = [source]
            cur = source
            visited = {source}

            for _ in range(self.max_initial_steps):
                if cur == destination:
                    break

                neighbors = list(self.graph.neighbors(cur))
                
                # Filter by bandwidth if demand > 0
                if bw_demand > 0:
                     valid_neighbors = [n for n in neighbors if self.graph[cur][n].get('bandwidth', 1000) >= bw_demand]
                else:
                     valid_neighbors = neighbors
                     
                candidates = [n for n in valid_neighbors if n not in visited] or valid_neighbors
                if not candidates:
                    break

                if destination in candidates:
                    path.append(destination)
                    return path if self._is_valid_path(path) else None

                nxt = random.choice(candidates)
                path.append(nxt)
                cur = nxt
                visited.add(nxt)

                if len(path) >= max_length:
                    break

            if path and path[-1] == destination and self._is_valid_path(path):
                return path

        return None


    # =========================
    # 6) VELOCITY UPDATE (Ayrık)
    # =========================
    # Velocity = düzenlenecek indeksler listesi:
    # 1) pbest'e yaklaş (c1)
    # 2) gbest'e yaklaş (c2)
    # 3) keşif için random indeks (w)
    def _update_velocity(self, particle: Particle, gbest_path: List[int]) -> None:
        velocity: List[int] = []

        if random.random() < self.c1 / max(self.c1 + self.c2, 1e-9):
            velocity.extend(self._path_difference_indices(particle.path, particle.pbest_path, limit=2))

        if random.random() < self.c2 / max(self.c1 + self.c2, 1e-9):
            velocity.extend(self._path_difference_indices(particle.path, gbest_path, limit=2))

        if random.random() < self.w and len(particle.path) > 3:
            velocity.append(random.randint(1, len(particle.path) - 2))

        velocity = self._unique_keep_order(velocity)
        particle.velocity = velocity[: self.max_velocity]

    # İki yolun farklı olduğu iç pozisyonları bulur (source/dest hariç)
    def _path_difference_indices(self, path1: List[int], path2: List[int], limit: int = 2) -> List[int]:
        diff: List[int] = []
        min_len = min(len(path1), len(path2))

        for i in range(1, min_len - 1):
            if path1[i] != path2[i]:
                diff.append(i)
                if len(diff) >= limit:
                    break

        if len(diff) < limit and len(path1) > 3:
            diff.append(random.randint(1, len(path1) - 2))

        return diff[:limit]


    # =========================
    # 7) POSITION UPDATE (Hareket)
    # =========================
    # Seçilen indekslerde 3 operatör uygular:
    # (1) swap: prev ve next'e bağlı alternatif düğüm
    # (2) reroute: prev->next segmentini shortest_path ile yenile
    # (3) shortcut: prev-next direkt bağlıysa aradakini sil
    def _update_position(self, particle: Particle, source: int, destination: int) -> Optional[List[int]]:
        if not particle.velocity:
            return particle.path[:]

        new_path = particle.path[:]

        for idx in particle.velocity:
            if not (0 < idx < len(new_path) - 1):
                continue

            prev_node = new_path[idx - 1]
            next_node = new_path[idx + 1]
            cur_node = new_path[idx]

            # (1) swap
            candidates = set(self.graph.neighbors(prev_node)) & set(self.graph.neighbors(next_node))
            candidates.discard(cur_node)
            candidates -= set(new_path)  # loop engeli
            if candidates:
                new_path[idx] = random.choice(list(candidates))
                continue

            # (2) reroute segment
            try:
                seg = nx.shortest_path(self.graph, prev_node, next_node)
                new_path = new_path[:idx] + seg[1:-1] + new_path[idx + 1 :]
                continue
            except Exception:
                pass

            # (3) shortcut
            if self.graph.has_edge(prev_node, next_node):
                new_path = new_path[:idx] + new_path[idx + 1 :]

        if self._is_valid_path(new_path):
            return new_path

        # geçersizse 1 kez random fallback
        # NOTE: Position update doesn't strictly check BW here, but fitness will kill it.
        # Fallback should respect BW? Let's leave it simple as fitness check handles it.
        return self._generate_random_path(source, destination, max_length=self.max_path_len)


    # =========================
    # 8) UTILS + FITNESS
    # =========================
    # trim: çok uzun yolu kırpar
    def _trim_path(self, path: List[int]) -> List[int]:
        if not path:
            return path
        if len(path) > self.max_path_len:
            return [path[0]] + path[1:self.max_path_len - 1] + [path[-1]]
        return path

    # tekrar eden indeksleri kaldırır (sıra korunur)
    def _unique_keep_order(self, xs: List[int]) -> List[int]:
        seen = set()
        out = []
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    # ağırlıkları normalize eder (toplam 1)
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        d = float(weights.get("delay", 0.0))
        r = float(weights.get("reliability", 0.0))
        c = float(weights.get("resource", 0.0))
        s = d + r + c
        if s <= 0:
            return {"delay": 0.33, "reliability": 0.33, "resource": 0.34}
        return {"delay": d / s, "reliability": r / s, "resource": c / s}

    # yol geçerli mi? (kenarlar var mı + loop yok)
    def _is_valid_path(self, path: List[int]) -> bool:
        if not path or len(path) < 2:
            return False
        if len(path) != len(set(path)):
            return False
        for u, v in zip(path[:-1], path[1:]):
            if not self.graph.has_edge(u, v):
                return False
        return True

    # fitness = MetricsService ağırlıklı maliyeti (küçük daha iyi)
    def _calculate_fitness(self, path: List[int], weights: Dict[str, float], bandwidth_demand: float = 0.0) -> float:
        try:
            return self.metrics_service.calculate_weighted_cost(
                path,
                weights["delay"],
                weights["reliability"],
                weights["resource"],
                bandwidth_demand # Pass demand to service
            )
        except Exception:
            return float("inf")

    # rapor için basit istatistik
    def get_stats(self) -> Dict[str, Any]:
        if not self.gbest_history:
            return {"iterations": 0}
        best_val = min(self.gbest_history)
        return {
            "iterations": len(self.gbest_history),
            "final_gbest": self.gbest_history[-1],
            "best_gbest": best_val,
            "improvement": (self.gbest_history[0] - self.gbest_history[-1]) if len(self.gbest_history) > 1 else 0.0,
            "convergence_iteration": self.gbest_history.index(best_val),
        }
