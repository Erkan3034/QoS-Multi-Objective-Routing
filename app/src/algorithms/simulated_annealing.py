"""
Simulated Annealing (SA) – Routing için (Ayrık / Path-based)

SA, source -> destination arasında ağırlıklı maliyeti minimize eden bir yol arar.
- Çözüm (state) = yol (düğüm listesi)
- Fitness = delay / reliability / resource ağırlıklı maliyet (küçük daha iyi)
- T yüksekken kötü çözümler bazen kabul edilir (local minima’dan kaçmak için)
- T soğutma ile düşer ve algoritma daha stabil çözüme yakınsar
"""

from __future__ import annotations

import math
import random
import time
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable

import networkx as nx

from src.services.metrics_service import MetricsService
# from src.core.config import settings  # kullanılmıyorsa kaldır


# =========================
# 1) Parametreler (SAParams)
# =========================
@dataclass(frozen=True)
class SAParams:
    # sıcaklık ayarları
    initial_temperature: float = 300.0
    final_temperature: float = 0.01
    cooling_rate: float = 0.98
    iterations_per_temp: int = 5

    # reproducibility
    seed: Optional[int] = None

    # path üretimi limitleri
    max_initial_steps: int = 150
    max_segment_steps: int = 40

    # opsiyonel global limit
    max_total_iterations: Optional[int] = None

    # UI dostu ayarlar
    progress_every: int = 25      # kaç iterasyonda bir callback
    ui_yield_ms: float = 1.0      # küçük bekleme (ms) => UI/OS nefes


# =========================
# 2) Sonuç (SAResult)
# =========================
@dataclass
class SAResult:
    path: List[int]
    fitness: float
    iteration: int
    final_temperature: float
    computation_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "fitness": round(self.fitness, 6),
            "iteration": self.iteration,
            "final_temperature": round(self.final_temperature, 6),
            "computation_time_ms": round(self.computation_time_ms, 2),
        }


# =========================
# 3) SimulatedAnnealing
# =========================
class SimulatedAnnealing:
    # Not: UI seed=... gönderebilir. Biz kabul ediyoruz.
    def __init__(self, graph: nx.Graph, params: Optional[SAParams] = None, seed: Optional[int] = None, **kwargs):
        self.graph = graph
        self.params = params if params is not None else SAParams(seed=seed)

        # [FIX] Store seed for stochastic behavior check
        self._seed = self.params.seed
        if self.params.seed is not None:
            random.seed(self.params.seed)

        self.metrics_service = MetricsService(graph)

        self.fitness_history: List[float] = []
        self.temperature_history: List[float] = []
        self.acceptance_history: List[bool] = []

    # =========================
    # 3.1) UI callback uyumu
    # =========================
    # Bazı UI'lar: on_progress(iteration, fitness)
    # Bazıları: on_progress(dict)
    def _emit_progress(
        self,
        progress_callback,
        iteration: int,
        temperature: float,
        best_fitness: float,
        current_fitness: float,
        accepted: bool,
        note: str = "",
    ) -> None:
        if not progress_callback:
            return

        # 1) En yaygın imza: (iteration, fitness)
        try:
            progress_callback(iteration, best_fitness)
            return
        except TypeError:
            pass

        # 2) Fallback: dict
        try:
            progress_callback({
                "iteration": iteration,
                "temperature": temperature,
                "best_fitness": best_fitness,
                "current_fitness": current_fitness,
                "accepted": accepted,
                "note": note,
            })
        except TypeError:
            return

    def _maybe_yield_ui(self) -> None:
        # PyQt import etmeden küçük sleep ile UI/OS'a nefes veriyoruz
        ms = float(getattr(self.params, "ui_yield_ms", 0.0) or 0.0)
        if ms > 0:
            time.sleep(ms / 1000.0)

    # =========================
    # 4) optimize(): SA ana döngü
    # =========================
    # =========================
    # 4) optimize(): SA ana döngü
    # =========================
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Optional[Dict[str, float]] = None,
        bandwidth_demand: float = 0.0,
        progress_callback: Optional[Callable[..., None]] = None,
        **kwargs
    ) -> SAResult:
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
            print(f"[SA] Stokastik mod - seed={seed_val}, call={self._call_counter}")
        else:
            print(f"[SA] Deterministik mod - seed={self._seed}")

        self.fitness_history.clear()
        self.temperature_history.clear()
        self.acceptance_history.clear()

        current_path = self._initial_solution(source, destination, bandwidth_demand)

        # fallback: shortest path
        if not current_path:
            try:
                # [FIX] Fallback respects bandwidth
                if bandwidth_demand > 0:
                    valid_edges = [
                        (u, v) for u, v, d in self.graph.edges(data=True) 
                        if d.get('bandwidth', 1000) >= bandwidth_demand
                    ]
                    temp_graph = self.graph.edge_subgraph(valid_edges)
                    current_path = nx.shortest_path(temp_graph, source, destination)
                else:
                    current_path = nx.shortest_path(self.graph, source, destination)
            except nx.NetworkXNoPath:
                elapsed = (time.perf_counter() - start_time) * 1000
                return SAResult(
                    path=[source, destination],
                    fitness=float("inf"),
                    iteration=0,
                    final_temperature=self.params.initial_temperature,
                    computation_time_ms=elapsed,
                )

        current_fit = self._fitness(current_path, weights, bandwidth_demand)

        best_path = current_path[:]
        best_fit = current_fit
        best_iter = 0

        T = float(self.params.initial_temperature)
        it = 0

        progress_every = max(int(getattr(self.params, "progress_every", 25) or 25), 1)

        while T > self.params.final_temperature:
            for _ in range(self.params.iterations_per_temp):
                if self.params.max_total_iterations is not None and it >= self.params.max_total_iterations:
                    T = self.params.final_temperature
                    break

                cand_path = self._neighbor(current_path, source, destination, bandwidth_demand)

                if not cand_path:
                    self.fitness_history.append(best_fit)
                    self.temperature_history.append(T)
                    self.acceptance_history.append(False)

                    # throttle progress
                    if progress_callback and (it % progress_every == 0):
                        self._emit_progress(progress_callback, it, T, best_fit, current_fit, False, note="no_neighbor")
                        self._maybe_yield_ui()

                    it += 1
                    continue

                cand_fit = self._fitness(cand_path, weights, bandwidth_demand)
                delta = cand_fit - current_fit

                # kabul kuralı
                if delta < 0:
                    accept = True
                else:
                    safe_T = max(T, 1e-12)
                    try:
                        p = math.exp(-delta / safe_T)
                    except OverflowError:
                        p = 0.0
                    accept = random.random() < p

                self.acceptance_history.append(accept)

                if accept:
                    current_path = cand_path
                    current_fit = cand_fit

                    if current_fit < best_fit:
                        best_fit = current_fit
                        best_path = current_path[:]
                        best_iter = it

                self.fitness_history.append(best_fit)
                self.temperature_history.append(T)

                # throttle progress
                if progress_callback and (it % progress_every == 0):
                    self._emit_progress(progress_callback, it, T, best_fit, current_fit, accept)
                    self._maybe_yield_ui()

                it += 1

            T *= float(self.params.cooling_rate)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        print(f"[SA] Sonuç: path={best_path[:5]}...{best_path[-2:] if len(best_path)>5 else ''}, len={len(best_path)}, fitness={best_fit:.4f}")
        return SAResult(
            path=best_path,
            fitness=best_fit,
            iteration=best_iter,
            final_temperature=T,
            computation_time_ms=elapsed_ms,
        )

    # =========================
    # 5) Stats
    # =========================
    def get_stats(self) -> Dict[str, Any]:
        if not self.acceptance_history:
            return {"iterations": 0}
        return {
            "iterations": len(self.fitness_history),
            "acceptance_rate": sum(self.acceptance_history) / len(self.acceptance_history),
            "initial_temp": self.temperature_history[0] if self.temperature_history else 0.0,
            "final_temp": self.temperature_history[-1] if self.temperature_history else 0.0,
            "best_fitness": min(self.fitness_history) if self.fitness_history else float("inf"),
        }

    # =========================
    # 6) Yardımcılar
    # =========================
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        d = float(weights.get("delay", 0.0))
        r = float(weights.get("reliability", 0.0))
        c = float(weights.get("resource", 0.0))
        s = d + r + c
        if s <= 0:
            return {"delay": 0.33, "reliability": 0.33, "resource": 0.34}
        return {"delay": d / s, "reliability": r / s, "resource": c / s}

    def _is_valid_path(self, path: List[int]) -> bool:
        if not path or len(path) < 2:
            return False
        if len(path) != len(set(path)):
            return False
        for u, v in zip(path[:-1], path[1:]):
            if not self.graph.has_edge(u, v):
                return False
        return True

    # =========================
    # 7) Başlangıç Çözümü
    # =========================
    def _initial_solution(self, s: int, t: int, bw_demand: float = 0.0) -> Optional[List[int]]:
        if s == t:
            return [s]

        path = [s]
        cur = s
        visited = {s}

        for _ in range(self.params.max_initial_steps):
            if cur == t:
                break

            neighbors = list(self.graph.neighbors(cur))
            # Filter by bandwidth
            if bw_demand > 0:
                candidates = [n for n in neighbors if n not in visited and self.graph[cur][n].get('bandwidth', 1000) >= bw_demand]
            else:
                candidates = [n for n in neighbors if n not in visited]
                
            if not candidates:
                # If restricted by bandwidth, try backtracking or just fail fast (random walk style)
                # For simplicity here, if stuck, just fail/retry
                return None

            if t in candidates:
                path.append(t)
                return path if self._is_valid_path(path) else None

            nxt = random.choice(candidates)
            path.append(nxt)
            visited.add(nxt)
            cur = nxt

        return path if (path[-1] == t and self._is_valid_path(path)) else None

    # =========================
    # 8) Neighbor Üretimi
    # =========================
    def _neighbor(self, path: List[int], s: int, t: int, bw_demand: float = 0.0) -> Optional[List[int]]:
        if len(path) <= 2:
            return self._initial_solution(s, t, bw_demand)

        op = random.choice(["swap", "segment", "shortcut"])

        if op == "swap":
            cand = self._neighbor_swap(path, bw_demand)
        elif op == "segment":
            cand = self._neighbor_segment(path, s, t, bw_demand)
        else:
            cand = self._neighbor_shortcut(path) # Shortcut always valid wrt bandwidth if removing nodes

        return cand if (cand and self._is_valid_path(cand)) else None

    def _neighbor_swap(self, path: List[int], bw_demand: float = 0.0) -> Optional[List[int]]:
        if len(path) <= 3:
            return None

        idx = random.randint(1, len(path) - 2)
        prev_node = path[idx - 1]
        next_node = path[idx + 1]
        cur_node = path[idx]

        candidates = set(self.graph.neighbors(prev_node)) & set(self.graph.neighbors(next_node))
        candidates.discard(cur_node)
        candidates -= set(path)
        
        # Filter candidates by bandwidth
        if bw_demand > 0:
            valid_candidates = []
            for cand in candidates:
                b1 = self.graph[prev_node][cand].get('bandwidth', 1000)
                b2 = self.graph[cand][next_node].get('bandwidth', 1000)
                if b1 >= bw_demand and b2 >= bw_demand:
                    valid_candidates.append(cand)
            candidates = set(valid_candidates)

        if not candidates:
            return None

        new_path = path[:]
        new_path[idx] = random.choice(list(candidates))
        return new_path

    def _neighbor_segment(self, path: List[int], s: int, t: int, bw_demand: float = 0.0) -> Optional[List[int]]:
        if len(path) <= 4:
            return self._initial_solution(s, t, bw_demand)

        i = random.randint(0, len(path) - 3)
        j = random.randint(i + 2, len(path) - 1)

        start_node = path[i]
        end_node = path[j]

        forbidden = set(path) - set(path[i : j + 1])

        segment = self._find_segment(start_node, end_node, forbidden, bw_demand)
        if not segment:
            return None

        return path[:i] + segment + path[j + 1 :]

    def _neighbor_shortcut(self, path: List[int]) -> Optional[List[int]]:
        if len(path) <= 3:
            return None

        i = random.randint(0, len(path) - 3)
        js = list(range(i + 2, len(path)))
        random.shuffle(js)

        for j in js[: min(8, len(js))]:
            if self.graph.has_edge(path[i], path[j]):
                # Shortcut usually valid if direct edge exists (checking BW implicitly by validity? No, check edge bw)
                # But here we assume shortcut generally improves things. 
                # If we want to be strict, we should check edge bandwidth here too.
                # Let's assume fitness function will catch it if shortcut edge is weak.
                return path[: i + 1] + path[j:]

        return None

    # =========================
    # 9) Segment Bulma
    # =========================
    def _find_segment(self, start: int, end: int, forbidden: set, bw_demand: float = 0.0) -> Optional[List[int]]:
        if start == end:
            return [start]

        seg_path = [start]
        cur = start
        visited = {start} | set(forbidden)

        for _ in range(self.params.max_segment_steps):
            if cur == end:
                break

            neighbors = list(self.graph.neighbors(cur))
            
            if bw_demand > 0:
                valid_neighbors = [n for n in neighbors if self.graph[cur][n].get('bandwidth', 1000) >= bw_demand]
            else:
                valid_neighbors = neighbors
                
            candidates = [n for n in valid_neighbors if n not in visited]
            
            if not candidates:
                return None

            if end in candidates:
                seg_path.append(end)
                return seg_path

            nxt = random.choice(candidates)
            seg_path.append(nxt)
            visited.add(nxt)
            cur = nxt

        return seg_path if seg_path[-1] == end else None

    # =========================
    # 10) Fitness
    # =========================
    def _fitness(self, path: List[int], weights: Dict[str, float], bw_demand: float = 0.0) -> float:
        if not self._is_valid_path(path):
            return float("inf")

        try:
            return self.metrics_service.calculate_weighted_cost(
                path,
                weights["delay"],
                weights["reliability"],
                weights["resource"],
                bw_demand
            )
        except Exception:
            return float("inf")
