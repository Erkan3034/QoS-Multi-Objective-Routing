"""
Ant Colony Optimization (ACO) Algoritması

Bu modül çok amaçlı rotalama problemi için
Karınca Kolonisi tabanlı optimizasyon sağlar.

Özellikler:
- Feromon tabanlı yol seçimi
- Visibility (heuristic) hesaplama
- Feromon buharlaşması
- Elitist ant stratejisi

Referans: M. Dorigo et al., "Ant Colony Optimization"
"""
import random
import time
import math
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from collections import defaultdict

from src.services.metrics_service import MetricsService
from src.core.config import settings


@dataclass
class ACOResult:
    """ACO sonuç veri sınıfı."""
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


class AntColonyOptimization:
    """
    Karınca Kolonisi Optimizasyonu.
    
    Karıncalar feromon izlerini takip ederek
    en iyi yolu keşfeder.
    
    Attributes:
        graph: NetworkX graf objesi
        n_ants: Karınca sayısı
        n_iterations: İterasyon sayısı
        alpha: Feromon önem katsayısı
        beta: Visibility önem katsayısı
        evaporation_rate: Buharlaşma oranı
        q: Feromon güncelleme sabiti
    
    Example:
        >>> aco = AntColonyOptimization(graph, n_ants=50)
        >>> result = aco.optimize(source=0, destination=249, weights={...})
        >>> print(f"Best path: {result.path}")
    """
    
    def __init__(
        self,
        graph: nx.Graph,
        n_ants: int = 50,
        n_iterations: int = 100,
        alpha: float = 1.0,
        beta: float = 2.0,
        evaporation_rate: float = 0.5,
        q: float = 100.0,
        seed: int = None
    ):
        """
        AntColonyOptimization oluşturur.
        
        Args:
            graph: NetworkX graf objesi
            n_ants: Karınca sayısı
            n_iterations: İterasyon sayısı
            alpha: Feromon önem katsayısı (τ^α)
            beta: Visibility önem katsayısı (η^β)
            evaporation_rate: Buharlaşma oranı (ρ)
            q: Feromon güncelleme sabiti
            seed: Rastgele seed
        """
        self.graph = graph
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.q = q
        
        if seed is not None:
            random.seed(seed)
        
        self.metrics_service = MetricsService(graph)
        
        # Feromon matrisi: (u, v) -> pheromone
        self.pheromone: Dict[Tuple[int, int], float] = defaultdict(lambda: 1.0)
        
        # İstatistikler
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
    
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None,
        progress_callback: Optional[Callable[[int, float], None]] = None
    ) -> ACOResult:
        """
        Optimal yolu bul.
        
        Args:
            source: Kaynak düğüm ID
            destination: Hedef düğüm ID
            weights: Metrik ağırlıkları {'delay', 'reliability', 'resource'}
        
        Returns:
            ACOResult objesi
        """
        start_time = time.perf_counter()
        
        weights = weights or {
            'delay': 0.33,
            'reliability': 0.33,
            'resource': 0.34
        }
        
        # Feromonları sıfırla
        self.pheromone = defaultdict(lambda: 1.0)
        self.best_fitness_history = []
        self.avg_fitness_history = []
        
        best_path = None
        best_fitness = float('inf')
        best_iteration = 0
        
        for iteration in range(self.n_iterations):
            # Tüm karıncaları çalıştır
            ant_paths = []
            ant_fitness_scores = []
            
            for _ in range(self.n_ants):
                path = self._construct_solution(source, destination, weights)
                if path:
                    try:
                        fitness = self.metrics_service.calculate_weighted_cost(
                            path,
                            weights['delay'],
                            weights['reliability'],
                            weights['resource']
                        )
                        ant_paths.append(path)
                        ant_fitness_scores.append(fitness)
                        
                        if fitness < best_fitness:
                            best_fitness = fitness
                            best_path = path
                            best_iteration = iteration
                    except Exception:
                        pass
            
            # İstatistikleri kaydet
            self.best_fitness_history.append(best_fitness)
            if ant_fitness_scores:
                self.avg_fitness_history.append(
                    sum(ant_fitness_scores) / len(ant_fitness_scores)
                )
            
            # [LIVE CONVERGENCE PLOT] Progress callback for real-time visualization
            if progress_callback:
                try:
                    progress_callback(iteration, best_fitness)
                except Exception:
                    # Don't let callback errors break the optimization
                    pass
            
            # Feromonları güncelle
            self._update_pheromones(ant_paths, ant_fitness_scores, best_path, best_fitness)
        
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        # Fallback: en kısa yol
        if best_path is None:
            try:
                best_path = nx.shortest_path(self.graph, source, destination)
                best_fitness = self.metrics_service.calculate_weighted_cost(
                    best_path,
                    weights['delay'],
                    weights['reliability'],
                    weights['resource']
                )
            except Exception:
                best_path = [source, destination]
                best_fitness = float('inf')
        
        return ACOResult(
            path=best_path,
            fitness=best_fitness,
            iteration=best_iteration,
            computation_time_ms=elapsed_time
        )
    
    def _construct_solution(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float]
    ) -> Optional[List[int]]:
        """
        Tek karıncanın çözüm oluşturması.
        
        Olasılıksal seçim ile source'tan destination'a gider.
        """
        path = [source]
        current = source
        visited = {source}
        max_steps = 100
        
        while current != destination and len(path) < max_steps:
            neighbors = [n for n in self.graph.neighbors(current) if n not in visited]
            
            if not neighbors:
                return None
            
            # Destination varsa doğrudan git
            if destination in neighbors:
                path.append(destination)
                return path
            
            # Olasılık hesapla
            probabilities = self._calculate_probabilities(
                current, neighbors, destination, weights
            )
            
            # Roulette wheel selection
            next_node = self._roulette_select(neighbors, probabilities)
            
            path.append(next_node)
            visited.add(next_node)
            current = next_node
        
        return path if current == destination else None
    
    def _calculate_probabilities(
        self,
        current: int,
        neighbors: List[int],
        destination: int,
        weights: Dict[str, float]
    ) -> List[float]:
        """
        Geçiş olasılıklarını hesaplar.
        
        P(i,j) = (τ_ij^α × η_ij^β) / Σ(τ_ik^α × η_ik^β)
        """
        scores = []
        
        for neighbor in neighbors:
            # Feromon değeri
            pheromone = self.pheromone[(current, neighbor)]
            
            # Visibility (heuristic) - hedefe yakınlık ve kenar kalitesi
            visibility = self._calculate_visibility(current, neighbor, destination, weights)
            
            # Toplam skor
            score = (pheromone ** self.alpha) * (visibility ** self.beta)
            scores.append(score)
        
        # Normalize
        total = sum(scores)
        if total == 0:
            return [1.0 / len(neighbors)] * len(neighbors)
        
        return [s / total for s in scores]
    
    def _calculate_visibility(
        self,
        from_node: int,
        to_node: int,
        destination: int,
        weights: Dict[str, float]
    ) -> float:
        """
        Visibility (η) değerini hesaplar.
        
        Düşük maliyet = yüksek visibility
        """
        edge = self.graph.edges[from_node, to_node]
        
        # Kenar maliyeti
        delay_cost = edge['delay'] / 100
        rel_cost = -math.log(edge['reliability'])
        res_cost = 1000 / edge['bandwidth'] / 50
        
        edge_cost = (
            weights['delay'] * delay_cost +
            weights['reliability'] * rel_cost +
            weights['resource'] * res_cost
        )
        
        # Hedefe uzaklık tahmini (hop sayısı)
        try:
            distance_to_dest = nx.shortest_path_length(
                self.graph, to_node, destination
            )
            distance_factor = 1.0 / (1 + distance_to_dest)
        except nx.NetworkXNoPath:
            distance_factor = 0.01
        
        # Visibility: düşük maliyet + hedefe yakınlık
        visibility = distance_factor / (1 + edge_cost)
        
        return max(visibility, 0.001)
    
    def _roulette_select(
        self,
        neighbors: List[int],
        probabilities: List[float]
    ) -> int:
        """Roulette wheel selection."""
        r = random.random()
        cumsum = 0.0
        
        for neighbor, prob in zip(neighbors, probabilities):
            cumsum += prob
            if r <= cumsum:
                return neighbor
        
        return neighbors[-1]
    
    def _update_pheromones(
        self,
        paths: List[List[int]],
        fitness_scores: List[float],
        best_path: List[int],
        best_fitness: float
    ):
        """
        Feromon güncelleme.
        
        1. Buharlaşma: τ_ij = (1-ρ) × τ_ij
        2. Deposit: Δτ_ij = Q / L_k
        """
        # Buharlaşma
        for edge in list(self.pheromone.keys()):
            self.pheromone[edge] *= (1 - self.evaporation_rate)
            # Minimum feromon
            self.pheromone[edge] = max(self.pheromone[edge], 0.01)
        
        # Her karıncanın feromont bırakması
        for path, fitness in zip(paths, fitness_scores):
            if fitness == float('inf') or fitness <= 0:
                continue
            
            deposit = self.q / fitness
            
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                self.pheromone[(u, v)] += deposit
                self.pheromone[(v, u)] += deposit  # Undirected
        
        # Elitist ant: en iyi yol için ekstra feromon
        if best_path and best_fitness != float('inf') and best_fitness > 0:
            elite_deposit = 2 * self.q / best_fitness
            for i in range(len(best_path) - 1):
                u, v = best_path[i], best_path[i + 1]
                self.pheromone[(u, v)] += elite_deposit
                self.pheromone[(v, u)] += elite_deposit
    
    def get_pheromone_stats(self) -> Dict[str, Any]:
        """Feromon istatistiklerini döndürür."""
        if not self.pheromone:
            return {"edges": 0}
        
        values = list(self.pheromone.values())
        return {
            "edges": len(values) // 2,  # Undirected
            "max_pheromone": max(values),
            "min_pheromone": min(values),
            "avg_pheromone": sum(values) / len(values)
        }

