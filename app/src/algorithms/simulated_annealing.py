"""
Simulated Annealing (SA) – Routing için (Ayrık / Path-based)

SA, kaynak (source) ile hedef (destination) arasında iyi bir yol bulmak için kullanılır.
Mantık:
- Çözüm = yol (düğüm listesi)
- Amaç = ağırlıklı maliyeti minimize etmek (delay, reliability, resource)
- Başta sıcaklık (T) yüksekken daha kötü çözümler bazen kabul edilir (local minima’dan kaçmak için)
- T zamanla düşer ve algoritma en iyi çözüme yakınsar
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import networkx as nx

from src.services.metrics_service import MetricsService
from src.core.config import settings

# =========================
# 1) Parametreler (SAParams)
# =========================
# SA ayarları:
# - Temperature schedule: başlangıç/bitiriş/cooling
# - Her sıcaklıkta kaç deneme yapılacak
# - Random walk ve segment arama limitleri
@dataclass(frozen=True)
class SAParams:
    initial_temperature: float = 1000.0
    final_temperature: float = 0.01
    cooling_rate: float = 0.995
    iterations_per_temp: int = 10
    seed: Optional[int] = None

    max_initial_steps: int = 150
    max_segment_steps: int = 40
    max_total_iterations: Optional[int] = None


# =========================
# 2) Sonuç (SAResult)
# =========================
# optimize() çıktı bilgileri:
# - path: bulunan en iyi yol
# - fitness: en iyi maliyet (küçük daha iyi)
# - iteration: en iyi yolun bulunduğu iterasyon
# - final_temperature: bittiği sıcaklık
# - computation_time_ms: çalışma süresi
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
# 3) SimulatedAnnealing Sınıfı
# =========================
# Akış:
# - başlangıç çözümü üret (random walk)
# - komşu çözüm üret (swap/segment/shortcut)
# - kabul kuralı uygula (delta ve exp(-delta/T))
# - en iyi çözümü (best) tut + history kaydet
class SimulatedAnnealing:
    def __init__(self, graph: nx.Graph, params: Optional[SAParams] = None):
        self.graph = graph
        self.params = params or SAParams()

        # aynı sonuçları tekrar üretebilmek için seed
        if self.params.seed is not None:
            random.seed(self.params.seed)

        self.metrics_service = MetricsService(graph)

        # UI / analiz için history
        self.fitness_history: List[float] = []
        self.temperature_history: List[float] = []
        self.acceptance_history: List[bool] = []

    # =========================
    # 4) optimize(): SA ana döngüsü
    # =========================
    # Adımlar:
    # 1) ağırlıkları normalize et
    # 2) initial solution üret (olmazsa shortest path fallback)
    # 3) sıcaklığı T ile döngüye gir: komşu üret, kabul et/etme, best güncelle
    # 4) T *= cooling_rate
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Optional[Dict[str, float]] = None,
    ) -> SAResult:
        start_time = time.perf_counter()

        weights = weights or {"delay": 0.33, "reliability": 0.33, "resource": 0.34}
        weights = self._normalize_weights(weights)

        self.fitness_history.clear()
        self.temperature_history.clear()
        self.acceptance_history.clear()

        # (4.1) başlangıç yolu
        current_path = self._initial_solution(source, destination)

        # (4.2) random walk başarısızsa fallback
        if not current_path:
            try:
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

        current_fit = self._fitness(current_path, weights)

        # en iyi çözüm (best) takibi
        best_path = current_path[:]
        best_fit = current_fit
        best_iter = 0

        T = float(self.params.initial_temperature)
        it = 0

        # (4.3) sıcaklık döngüsü
        while T > self.params.final_temperature:
            for _ in range(self.params.iterations_per_temp):
                # toplam iterasyon sınırı (opsiyonel)
                if self.params.max_total_iterations is not None and it >= self.params.max_total_iterations:
                    T = self.params.final_temperature
                    break

                # komşu çözüm üret
                cand_path = self._neighbor(current_path, source, destination)

                # komşu yoksa ilerle
                if not cand_path:
                    self.fitness_history.append(best_fit)
                    self.temperature_history.append(T)
                    self.acceptance_history.append(False)
                    it += 1
                    continue

                cand_fit = self._fitness(cand_path, weights)
                delta = cand_fit - current_fit

                # (4.4) kabul kuralı:
                # - daha iyi ise (delta<0) kesin kabul
                # - daha kötü ise exp(-delta/T) olasılığıyla kabul
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

                # kabul edildiyse current güncelle
                if accept:
                    current_path = cand_path
                    current_fit = cand_fit

                    # best güncelle
                    if current_fit < best_fit:
                        best_fit = current_fit
                        best_path = current_path[:]
                        best_iter = it

                # history kaydı
                self.fitness_history.append(best_fit)
                self.temperature_history.append(T)

                it += 1

            # sıcaklığı düşür (cooling)
            T *= float(self.params.cooling_rate)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return SAResult(
            path=best_path,
            fitness=best_fit,
            iteration=best_iter,
            final_temperature=T,
            computation_time_ms=elapsed_ms,
        )

    # =========================
    # 5) İstatistik (UI için)
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
    # 6) Ağırlık Normalize
    # =========================
    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        d = float(weights.get("delay", 0.0))
        r = float(weights.get("reliability", 0.0))
        c = float(weights.get("resource", 0.0))

        s = d + r + c
        if s <= 0:
            return {"delay": 0.33, "reliability": 0.33, "resource": 0.34}

        return {"delay": d / s, "reliability": r / s, "resource": c / s}

    # =========================
    # 7) Yol Geçerliliği
    # =========================
    # - tekrar eden düğüm yok (loop engeli)
    # - her ardışık düğüm arasında edge olmalı
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
    # 8) Başlangıç Çözümü (Random Walk)
    # =========================
    def _initial_solution(self, s: int, t: int) -> Optional[List[int]]:
        if s == t:
            return [s]

        path = [s]
        cur = s
        visited = {s}

        for _ in range(self.params.max_initial_steps):
            if cur == t:
                break

            neighbors = list(self.graph.neighbors(cur))
            candidates = [n for n in neighbors if n not in visited] or neighbors
            if not candidates:
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
    # 9) Komşu Üretimi (Neighbor)
    # =========================
    # 3 operatör:
    # - swap: iç düğümü değiştir
    # - segment: bir parçayı yeniden kur
    # - shortcut: gereksiz ara düğümleri kaldır
    def _neighbor(self, path: List[int], s: int, t: int) -> Optional[List[int]]:
        if len(path) <= 2:
            return self._initial_solution(s, t)

        op = random.choice(["swap", "segment", "shortcut"])

        if op == "swap":
            cand = self._neighbor_swap(path)
        elif op == "segment":
            cand = self._neighbor_segment(path, s, t)
        else:
            cand = self._neighbor_shortcut(path)

        return cand if (cand and self._is_valid_path(cand)) else None

    # =========================
    # 9.1) Swap Neighbor
    # =========================
    def _neighbor_swap(self, path: List[int]) -> Optional[List[int]]:
        if len(path) <= 3:
            return None

        idx = random.randint(1, len(path) - 2)
        prev_node = path[idx - 1]
        next_node = path[idx + 1]
        cur_node = path[idx]

        candidates = set(self.graph.neighbors(prev_node)) & set(self.graph.neighbors(next_node))
        candidates.discard(cur_node)
        candidates -= set(path)

        if not candidates:
            return None

        new_node = random.choice(list(candidates))
        new_path = path[:]
        new_path[idx] = new_node
        return new_path

    # =========================
    # 9.2) Segment Neighbor
    # =========================
    def _neighbor_segment(self, path: List[int], s: int, t: int) -> Optional[List[int]]:
        if len(path) <= 4:
            return self._initial_solution(s, t)

        i = random.randint(0, len(path) - 3)
        j = random.randint(i + 2, len(path) - 1)

        start_node = path[i]
        end_node = path[j]

        # segment dışında kalan düğümler yasak (loop riskini azaltır)
        forbidden = set(path) - set(path[i : j + 1])

        segment = self._find_segment(start_node, end_node, forbidden)
        if not segment:
            return None

        return path[:i] + segment + path[j + 1 :]

    # =========================
    # 9.3) Shortcut Neighbor
    # =========================
    def _neighbor_shortcut(self, path: List[int]) -> Optional[List[int]]:
        if len(path) <= 3:
            return None

        i = random.randint(0, len(path) - 3)
        js = list(range(i + 2, len(path)))
        random.shuffle(js)

        for j in js[: min(8, len(js))]:
            if self.graph.has_edge(path[i], path[j]):
                return path[: i + 1] + path[j:]

        return None

    # =========================
    # 10) Segment Bulma (Random Walk)
    # =========================
    def _find_segment(self, start: int, end: int, forbidden: set) -> Optional[List[int]]:
        if start == end:
            return [start]

        seg_path = [start]
        cur = start
        visited = {start} | set(forbidden)

        for _ in range(self.params.max_segment_steps):
            if cur == end:
                break

            neighbors = [n for n in self.graph.neighbors(cur) if n not in visited]
            if not neighbors:
                return None

            if end in neighbors:
                seg_path.append(end)
                return seg_path

            nxt = random.choice(neighbors)
            seg_path.append(nxt)
            visited.add(nxt)
            cur = nxt

        return seg_path if seg_path[-1] == end else None

    # =========================
    # 11) Fitness (Weighted Cost)
    # =========================
    def _fitness(self, path: List[int], weights: Dict[str, float]) -> float:
        if not self._is_valid_path(path):
            return float("inf")

        try:
            return self.metrics_service.calculate_weighted_cost(
                path,
                weights["delay"],
                weights["reliability"],
                weights["resource"],
            )
        except Exception:
            return float("inf")
