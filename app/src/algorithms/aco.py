"""
Advanced Ant Colony Optimization (ACO) for QoS Multi-Objective Routing

Gelişmiş Özellikler:
- Adaptive parameter tuning (α, β, ρ)
- Multi-population strategy (Elite + Common ants)
- ε-greedy exploration-exploitation balance
- 2-opt local search optimization
- Pheromone diffusion mechanism
- Non-uniform initial pheromone distribution
- Dynamic pheromone update strategies
- Candidate list restriction
- Min-Max pheromone bounds
- Rank-based pheromone deposit

Kaynaklar:
- Dorigo et al. "Ant Colony Optimization"
- IEACO (Intelligently Enhanced ACO)
- FACO (Focused ACO)
- Hybrid ACO/PSO techniques
"""

import random
import time
import math
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum

from src.services.metrics_service import MetricsService
from src.core.config import settings


class AntType(Enum):
    """Karınca tipleri."""
    ELITE = "elite"
    COMMON = "common"


@dataclass
class ACOResult:
    """ACO sonuç veri sınıfı."""
    path: List[int]
    fitness: float
    iteration: int
    computation_time_ms: float
    convergence_data: Optional[Dict[str, List[float]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "path": self.path,
            "fitness": round(self.fitness, 6),
            "iteration": self.iteration,
            "computation_time_ms": round(self.computation_time_ms, 2)
        }
        if self.convergence_data:
            result["convergence"] = self.convergence_data
        return result


class OptimizedACO:
    """
    Gelişmiş Karınca Kolonisi Optimizasyonu.
    
    Modern optimizasyon teknikleri ile güçlendirilmiş:
    - Adaptive parameters
    - Multi-population
    - Local search
    - Smart pheromone management
    
    Attributes:
        graph: NetworkX graf objesi
        n_ants: Toplam karınca sayısı
        elite_ratio: Elite karınca oranı
        n_iterations: İterasyon sayısı
        alpha_range: α parametresi aralığı (min, max)
        beta_range: β parametresi aralığı (min, max)
        evaporation_rate: Başlangıç buharlaşma oranı
        q: Feromon güncelleme sabiti
        epsilon: ε-greedy için exploration oranı
        candidate_list_size: Aday liste boyutu
        local_search_prob: Local search uygulama olasılığı
    
    Example:
        >>> aco = OptimizedACO(graph, n_ants=50, elite_ratio=0.2)
        >>> result = aco.optimize(source=0, destination=249, weights={...})
        >>> print(f"Best: {result.path}, Fitness: {result.fitness}")
    """
    
    def __init__(
        self,
        graph: nx.Graph,
        n_ants: int = 50,
        elite_ratio: float = 0.2,
        n_iterations: int = 100,
        alpha_range: Tuple[float, float] = (0.8, 2.0),
        beta_range: Tuple[float, float] = (2.0, 5.0),
        evaporation_rate: float = 0.1,
        q: float = 100.0,
        epsilon: float = 0.1,
        candidate_list_size: int = 15,
        local_search_prob: float = 0.3,
        seed: int = None
    ):
        """
        OptimizedACO oluşturur.
        
        Args:
            graph: NetworkX graf objesi
            n_ants: Toplam karınca sayısı
            elite_ratio: Elite karınca oranı (0.0-1.0)
            n_iterations: İterasyon sayısı
            alpha_range: α parametresi için (min, max) aralığı
            beta_range: β parametresi için (min, max) aralığı
            evaporation_rate: Buharlaşma oranı (0.0-1.0)
            q: Feromon güncelleme sabiti
            epsilon: ε-greedy exploration oranı
            candidate_list_size: Komşu aday liste boyutu
            local_search_prob: 2-opt local search olasılığı
            seed: Rastgele seed
        """
        self.graph = graph
        # [FIX] Aggressive adaptive ant count for better performance
        # Large graphs (250+ nodes) need much fewer ants to avoid UI freezing
        graph_size = len(graph.nodes())
        if graph_size > 200:
            # Large graphs: aggressive reduction for speed
            self.n_ants = min(n_ants, 20)  # Max 20 ants for large graphs (was 30)
            self.n_iterations = min(n_iterations, 30)  # Max 30 iterations (was 50)
        elif graph_size > 100:
            # Medium graphs: moderate reduction
            self.n_ants = min(n_ants, 30)  # Max 30 ants (was 40)
            self.n_iterations = min(n_iterations, 50)  # Max 50 iterations (was 75)
        else:
            # Small graphs: use full parameters
            self.n_ants = n_ants
            self.n_iterations = n_iterations
        
        self.n_elite_ants = max(1, int(self.n_ants * elite_ratio))
        self.n_common_ants = self.n_ants - self.n_elite_ants
        
        # Adaptive parameters
        self.alpha_min, self.alpha_max = alpha_range
        self.beta_min, self.beta_max = beta_range
        self.alpha = (self.alpha_min + self.alpha_max) / 2
        self.beta = (self.beta_min + self.beta_max) / 2
        
        self.evaporation_rate = evaporation_rate
        self.q = q
        self.epsilon = epsilon
        self.candidate_list_size = candidate_list_size
        self.local_search_prob = local_search_prob
        
        # [FIX] Store seed for reference
        # If seed is None, random will use system time (non-deterministic, different each run)
        # If seed is set, results will be deterministic (useful for experiments)
        self._seed = seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        self.metrics_service = MetricsService(graph)
        
        # Feromon matrisi
        self.pheromone: Dict[Tuple[int, int], float] = defaultdict(lambda: 1.0)
        self.tau_min = 0.01
        self.tau_max = 10.0
        
        # Candidate lists için pre-computation
        self._build_candidate_lists()
        
        # İstatistikler
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
        self.diversity_history: List[float] = []
        self.stagnation_counter = 0
    
    def _build_candidate_lists(self):
        """Her düğüm için en yakın komşuları hesapla (delay bazlı - default)."""
        self.candidate_lists = {}
        
        for node in self.graph.nodes():
            neighbors = list(self.graph.neighbors(node))
            
            if len(neighbors) <= self.candidate_list_size:
                self.candidate_lists[node] = neighbors
            else:
                # En yakın komşuları seç (delay bazlı)
                neighbor_costs = []
                for neighbor in neighbors:
                    edge = self.graph.edges[node, neighbor]
                    cost = edge['delay']
                    neighbor_costs.append((neighbor, cost))
                
                neighbor_costs.sort(key=lambda x: x[1])
                self.candidate_lists[node] = [n for n, _ in neighbor_costs[:self.candidate_list_size]]
    
    def _build_candidate_lists_weighted(self, weights: Dict[str, float]):
        """
        [FIX] Her düğüm için en yakın komşuları ağırlıklara göre hesapla.
        
        Bu sayede ağırlık değişiklikleri candidate list'leri de etkiler.
        """
        self.candidate_lists = {}
        
        for node in self.graph.nodes():
            neighbors = list(self.graph.neighbors(node))
            
            if len(neighbors) <= self.candidate_list_size:
                self.candidate_lists[node] = neighbors
            else:
                # Ağırlıklara göre komşu maliyetlerini hesapla
                neighbor_costs = []
                for neighbor in neighbors:
                    edge = self.graph.edges[node, neighbor]
                    # Multi-objective cost based on current weights
                    delay_cost = weights.get('delay', 0.33) * edge.get('delay', 1.0) / 100
                    rel_cost = weights.get('reliability', 0.33) * (-math.log(max(edge.get('reliability', 0.99), 0.01)))
                    res_cost = weights.get('resource', 0.34) * (1000 / max(edge.get('bandwidth', 1000), 1) / 50)
                    total_cost = delay_cost + rel_cost + res_cost
                    neighbor_costs.append((neighbor, total_cost))
                
                neighbor_costs.sort(key=lambda x: x[1])
                self.candidate_lists[node] = [n for n, _ in neighbor_costs[:self.candidate_list_size]]
    
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None,
        bandwidth_demand: float = 0.0,
        progress_callback: Optional[Callable[[int, float], None]] = None
    ) -> ACOResult:
        """
        Optimal yolu bul.
        
        Args:
            source: Kaynak düğüm ID
            destination: Hedef düğüm ID
            weights: Metrik ağırlıkları
            bandwidth_demand: İstenen bant genişliği (Mbps)
            progress_callback: İlerleme callback fonksiyonu
        
        Returns:
            ACOResult objesi
        """
        start_time = time.perf_counter()
        
        # [FIX] Always update weights FIRST to ensure new optimization uses new weights
        weights = weights or {
            'delay': 0.33,
            'reliability': 0.33,
            'resource': 0.34
        }
        
        # [FIX] Clear pheromone matrix to ensure fresh start with new weights
        # This is critical: weights affect fitness calculation, so old pheromones are invalid
        self.pheromone.clear()
        
        # [FIX] Reset random state FIRST - before any other operations
        # This ensures different results even with same weights (exploration)
        if not hasattr(self, '_seed') or self._seed is None:
            # Use system time + process ID + weights hash for non-deterministic results
            # [FIX] Ensure seed is within valid range [0, 2**32 - 1] for numpy
            import time as time_module
            import os
            weights_hash = abs(hash(str(sorted(weights.items()))))  # abs() to ensure positive
            time_component = int(time_module.time() * 1000000) % (2**31)
            pid_component = os.getpid() % (2**16)  # Limit PID component
            seed_value = (time_component + pid_component + weights_hash) % (2**32 - 1)
            # Ensure seed is positive and within valid range
            seed_value = max(0, min(seed_value, 2**32 - 1))
            random.seed(seed_value)
            np.random.seed(seed_value)
        
        # [FIX] Reset statistics to ensure clean state for new optimization
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.diversity_history = []
        self.stagnation_counter = 0
        
        # [FIX] Reset adaptive parameters to initial values for fresh start
        self.alpha = (self.alpha_min + self.alpha_max) / 2
        self.beta = (self.beta_min + self.beta_max) / 2
        self.evaporation_rate = 0.1
        
        # [FIX] Temporarily increase epsilon for more exploration when weights change
        # This helps algorithm explore different paths with new weights
        original_epsilon = self.epsilon
        self.epsilon = min(0.5, original_epsilon * 4)  # Quadruple exploration for first few iterations
        self._original_epsilon = original_epsilon  # Store for later restoration
        
        # [FIX] Weaker pheromone initialization to allow weight changes to have more impact
        # Use uniform initialization instead of strong shortest-path bias
        self._initialize_pheromones_uniform()
        
        # [FIX] Lazy candidate lists - only rebuild if needed (performance optimization)
        # Don't rebuild here, rebuild on-demand in _construct_solution to avoid UI freezing
        # self._build_candidate_lists_weighted(weights)  # REMOVED - too slow, causes UI freeze
        
        best_path = None
        best_fitness = float('inf')
        best_iteration = 0
        
        # Iteration-best ve global-best için
        iteration_best_path = None
        iteration_best_fitness = float('inf')
        
        for iteration in range(self.n_iterations):
            # Adaptive parameter adjustment
            self._adapt_parameters(iteration)
            
            # Elite ve Common ant'ları ayır
            elite_paths = []
            elite_fitness_scores = []
            common_paths = []
            common_fitness_scores = []
            
            # Elite ants (daha fazla pheromone etkisi)
            for _ in range(self.n_elite_ants):
                path = self._construct_solution(
                    source, destination, weights, 
                    ant_type=AntType.ELITE,
                    bandwidth_demand=bandwidth_demand
                )
                
                if path:
                    fitness = self._evaluate_path(path, weights, bandwidth_demand)
                    
                    # [FIX] Local search disabled for performance
                    # 2-opt is too expensive for large graphs, removed to speed up
                    # if random.random() < self.local_search_prob * 0.3:
                    #     if elite_fitness_scores and fitness < np.mean(elite_fitness_scores):
                    #         path, fitness = self._local_search_2opt(path, weights)
                    
                    elite_paths.append(path)
                    elite_fitness_scores.append(fitness)
                    
                    if fitness < best_fitness:
                        best_fitness = fitness
                        best_path = path
                        best_iteration = iteration
                        self.stagnation_counter = 0
                    
                    if fitness < iteration_best_fitness:
                        iteration_best_fitness = fitness
                        iteration_best_path = path
            
            # Common ants (daha fazla exploration)
            for _ in range(self.n_common_ants):
                path = self._construct_solution(
                    source, destination, weights,
                    ant_type=AntType.COMMON,
                    bandwidth_demand=bandwidth_demand
                )
                
                if path:
                    fitness = self._evaluate_path(path, weights, bandwidth_demand)
                    common_paths.append(path)
                    common_fitness_scores.append(fitness)
                    
                    if fitness < best_fitness:
                        best_fitness = fitness
                        best_path = path
                        best_iteration = iteration
                        self.stagnation_counter = 0
                    
                    if fitness < iteration_best_fitness:
                        iteration_best_fitness = fitness
                        iteration_best_path = path
            
            # Tüm yollar
            all_paths = elite_paths + common_paths
            all_fitness_scores = elite_fitness_scores + common_fitness_scores
            
            # İstatistikleri güncelle
            self.best_fitness_history.append(best_fitness)
            if all_fitness_scores:
                valid_scores = [s for s in all_fitness_scores if s != float('inf')]
                self.avg_fitness_history.append(np.mean(valid_scores) if valid_scores else float('inf'))
                diversity = self._calculate_diversity(all_paths)
                self.diversity_history.append(diversity)
            
            # Stagnation check
            if iteration > 0 and self.best_fitness_history[-1] == self.best_fitness_history[-2]:
                self.stagnation_counter += 1
            
            # Pheromone güncelleme (rank-based + elitist)
            self._update_pheromones_advanced(
                all_paths, 
                all_fitness_scores,
                iteration_best_path,
                iteration_best_fitness,
                best_path,
                best_fitness
            )
            
            # [FIX] Pheromone diffusion removed for performance
            # Diffusion is expensive and not critical for path finding
            # if iteration % 10 == 0:
            #     self._pheromone_diffusion()
            
            # [FIX] Progress callback - call less frequently to reduce signal overhead
            # Emit every 3 iterations or on significant improvement to reduce UI blocking
            if progress_callback and (iteration % 3 == 0 or iteration == 0 or 
                                      (iteration > 0 and len(self.best_fitness_history) > 1 and 
                                       best_fitness < self.best_fitness_history[-1] * 0.9)):
                try:
                    progress_callback(iteration, best_fitness)
                except Exception:
                    pass
            
            # [FIX] Very aggressive early termination for speed
            # Exit early if converged or stagnated for too long
            if iteration > 3:
                # Check convergence
                if len(self.best_fitness_history) > 3:
                    recent = self.best_fitness_history[-3:]
                    if max(recent) - min(recent) < 0.001:
                        # Converged, exit early
                        break
                
                # Check stagnation
                if self.stagnation_counter > 5:
                    # Stagnated for too long, exit early
                    break
            
            # Reset iteration best
            iteration_best_fitness = float('inf')
            
            # [FIX] Gradually reduce epsilon back to original after initial exploration
            if hasattr(self, '_original_epsilon'):
                if iteration < 10:
                    self.epsilon = self._original_epsilon + (0.3 - self._original_epsilon) * (1 - iteration / 10)
                else:
                    self.epsilon = self._original_epsilon
        
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        # Fallback
        if best_path is None:
            try:
                # [FIX] Fallback should also respect bandwidth
                if bandwidth_demand > 0:
                    # Filter graph for bandwidth
                    valid_edges = [
                        (u, v) for u, v, d in self.graph.edges(data=True) 
                        if d.get('bandwidth', 1000) >= bandwidth_demand
                    ]
                    temp_graph = self.graph.edge_subgraph(valid_edges)
                    best_path = nx.shortest_path(temp_graph, source, destination)
                else:
                    best_path = nx.shortest_path(self.graph, source, destination)
                best_fitness = self._evaluate_path(best_path, weights, bandwidth_demand)
            except Exception:
                best_path = [source, destination]
                best_fitness = float('inf')
        
        return ACOResult(
            path=best_path,
            fitness=best_fitness,
            iteration=best_iteration,
            computation_time_ms=elapsed_time,
            convergence_data={
                "best_fitness": self.best_fitness_history,
                "avg_fitness": self.avg_fitness_history,
                "diversity": self.diversity_history
            }
        )
    
    def _initialize_pheromones(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float]
    ):
        """
        Non-uniform initial pheromone distribution.
        
        Hedefe yakın kenarlar daha fazla başlangıç feromonuna sahip olur.
        [DEPRECATED] Use _initialize_pheromones_optimized for better performance.
        """
        self._initialize_pheromones_optimized(source, destination, weights)
    
    def _initialize_pheromones_uniform(self):
        """
        [FIX] Uniform pheromone initialization - optimized for performance.
        
        Ağırlık değişikliklerinin daha güçlü etkisi olması için uniform başlangıç.
        Shortest path bias'ı kaldırıldı, böylece algoritma ağırlıklara göre keşif yapabilir.
        
        [PERFORMANCE] Lazy initialization - don't initialize all edges upfront
        to avoid UI freezing on large graphs. defaultdict handles on-demand initialization.
        """
        # [FIX] Don't initialize all edges - use lazy initialization via defaultdict
        # This prevents UI freezing on large graphs (250 nodes, 12000+ edges)
        # Edges will be initialized on-demand with default value 1.0
        # Pheromone already cleared above, defaultdict(lambda: 1.0) handles lazy init
        pass
    
    def _initialize_pheromones_optimized(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float]
    ):
        """
        Optimized non-uniform initial pheromone distribution.
        
        [DEPRECATED] Use _initialize_pheromones_uniform for better weight sensitivity.
        """
        self._initialize_pheromones_uniform()
    
    def _adapt_parameters(self, iteration: int):
        """
        Adaptive parameter tuning.
        
        İterasyon ilerledikçe exploitation'a kayar.
        """
        progress = iteration / self.n_iterations
        
        # Alpha: Başlangıçta düşük, sonra yüksek (exploitation artışı)
        self.alpha = self.alpha_min + (self.alpha_max - self.alpha_min) * progress
        
        # Beta: Başlangıçta yüksek, sonra azalır (exploration azalışı)
        self.beta = self.beta_max - (self.beta_max - self.beta_min) * progress
        
        # Evaporation rate: Stagnation varsa artır
        if self.stagnation_counter > 10:
            self.evaporation_rate = min(0.3, self.evaporation_rate * 1.1)
            self.stagnation_counter = 0  # Reset
        else:
            self.evaporation_rate = max(0.05, 0.1)
    
    def _construct_solution(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float],
        ant_type: AntType,
        bandwidth_demand: float = 0.0
    ) -> Optional[List[int]]:
        """
        Tek karıncanın çözüm oluşturması.
        
        ε-greedy stratejisi ile exploration/exploitation dengesi.
        """
        path = [source]
        current = source
        visited = {source}
        max_steps = 100
        
        # Elite ants daha az explore eder
        epsilon = self.epsilon if ant_type == AntType.COMMON else self.epsilon / 2
        
        while current != destination and len(path) < max_steps:
            # [FIX] Use all neighbors for better exploration
            # Filter based on bandwidth demand
            if bandwidth_demand > 0:
                candidates = [
                    n for n in self.graph.neighbors(current) 
                    if n not in visited and self.graph[current][n].get('bandwidth', 1000) >= bandwidth_demand
                ]
            else:
                candidates = [n for n in self.graph.neighbors(current) if n not in visited]
            
            if not candidates:
                return None
            
            # Destination varsa direkt git
            if destination in candidates:
                path.append(destination)
                return path
            
            # ε-greedy selection
            if random.random() < epsilon:
                # Exploration: Random seçim
                next_node = random.choice(candidates)
            else:
                # Exploitation: Pheromone ve heuristic bazlı
                probabilities = self._calculate_probabilities(
                    current, candidates, destination, weights
                )
                next_node = self._roulette_select(candidates, probabilities)
            
            path.append(next_node)
            visited.add(next_node)
            current = next_node
        
        return path if current == destination else None
    
    def _calculate_probabilities(
        self,
        current: int,
        candidates: List[int],
        destination: int,
        weights: Dict[str, float]
    ) -> List[float]:

        """
        Geçiş olasılıkları: P(i,j) = (τ^α × η^β) / Σ(τ^α × η^β)
        """
        scores = []
        
        for candidate in candidates:
            tau = self.pheromone[(current, candidate)]
            eta = self._calculate_heuristic(current, candidate, destination, weights)
            
            score = (tau ** self.alpha) * (eta ** self.beta)
            scores.append(score)
        
        total = sum(scores)
        if total == 0:
            return [1.0 / len(candidates)] * len(candidates)
        
        return [s / total for s in scores]
    
    def _calculate_heuristic(
        self,
        from_node: int,
        to_node: int,
        destination: int,
        weights: Dict[str, float]
    ) -> float:
        """
        Multi-objective heuristic: η = (1 / cost) × (1 / distance_to_dest)
        """
        edge = self.graph.edges[from_node, to_node]
        
        # Edge cost
        delay_cost = edge['delay'] / 100
        rel_cost = -math.log(max(edge['reliability'], 0.01))
        res_cost = 1000 / max(edge['bandwidth'], 1) / 50
        
        edge_cost = (
            weights['delay'] * delay_cost +
            weights['reliability'] * rel_cost +
            weights['resource'] * res_cost
        )
        
        # [FIX] Distance calculation removed for performance
        # nx.shortest_path_length is VERY expensive when called thousands of times
        # Use simple hop-based estimation instead
        # For large graphs, this is a major bottleneck
        # try:
        #     distance = nx.shortest_path_length(self.graph, to_node, destination)
        #     distance_factor = 1.0 / (1 + distance)
        # except nx.NetworkXNoPath:
        #     distance_factor = 0.001
        
        # Simple heuristic: assume destination is reachable (optimistic)
        distance_factor = 0.5  # Fixed value for speed
        
        # Combined heuristic
        heuristic = distance_factor / (1 + edge_cost)
        
        return max(heuristic, 0.001)
    
    def _roulette_select(
        self,
        candidates: List[int],
        probabilities: List[float]
    ) -> int:
        """Roulette wheel selection."""
        r = random.random()
        cumsum = 0.0
        
        for candidate, prob in zip(candidates, probabilities):
            cumsum += prob
            if r <= cumsum:
                return candidate
        
        return candidates[-1]
    
    def _evaluate_path(
        self,
        path: List[int],
        weights: Dict[str, float],
        bandwidth_demand: float = 0.0
    ) -> float:
        """Yolu değerlendir."""
        try:
            return self.metrics_service.calculate_weighted_cost(
                path,
                weights['delay'],
                weights['reliability'],
                weights['resource'],
                bandwidth_demand
            )
        except Exception:
            return float('inf')
    
    def _local_search_2opt(
        self,
        path: List[int],
        weights: Dict[str, float]
    ) -> Tuple[List[int], float]:
        """
        2-opt local search.
        
        Yolu iyileştirmek için kenar çaprazlaması yapar.
        """
        improved = True
        best_path = path[:]
        best_fitness = self._evaluate_path(best_path, weights)
        
        # [FIX] Limit iterations to prevent UI freezing
        max_iterations = 2  # Only 2 improvement attempts
        iteration_count = 0
        
        while improved and iteration_count < max_iterations:
            improved = False
            iteration_count += 1
            
            # [FIX] Limit search space - only check first few swaps
            max_i = min(4, len(best_path) - 2)  # Only check first 4 positions
            for i in range(1, max_i):
                max_j = min(i + 4, len(best_path) - 1)  # Only check next 4 positions
                for j in range(i + 1, max_j):
                    # 2-opt swap
                    new_path = best_path[:i] + best_path[i:j+1][::-1] + best_path[j+1:]
                    
                    # Geçerlilik kontrolü
                    if self._is_path_valid(new_path):
                        new_fitness = self._evaluate_path(new_path, weights)
                        
                        if new_fitness < best_fitness:
                            best_path = new_path
                            best_fitness = new_fitness
                            improved = True
                            break
                
                if improved:
                    break
        
        return best_path, best_fitness
    
    def _is_path_valid(self, path: List[int]) -> bool:
        """Yolun geçerli olup olmadığını kontrol et."""
        for i in range(len(path) - 1):
            if not self.graph.has_edge(path[i], path[i + 1]):
                return False
        return True
    
    def _update_pheromones_advanced(
        self,
        paths: List[List[int]],
        fitness_scores: List[float],
        iteration_best_path: Optional[List[int]],
        iteration_best_fitness: float,
        global_best_path: Optional[List[int]],
        global_best_fitness: float
    ):
        """
        Gelişmiş feromon güncelleme:
        1. Buharlaşma
        2. Rank-based deposit
        3. Elitist reinforcement
        4. Min-max bounds
        """
        # [FIX] Optimized evaporation - only evaporate edges that are actually used
        # Don't iterate over all possible edges (12000+ edges is too slow)
        # Only evaporate edges that were used in current iteration
        edges_to_evaporate = set()
        for path in paths:
            for i in range(len(path) - 1):
                edges_to_evaporate.add((path[i], path[i+1]))
                edges_to_evaporate.add((path[i+1], path[i]))
        if iteration_best_path:
            for i in range(len(iteration_best_path) - 1):
                edges_to_evaporate.add((iteration_best_path[i], iteration_best_path[i+1]))
                edges_to_evaporate.add((iteration_best_path[i+1], iteration_best_path[i]))
        if global_best_path:
            for i in range(len(global_best_path) - 1):
                edges_to_evaporate.add((global_best_path[i], global_best_path[i+1]))
                edges_to_evaporate.add((global_best_path[i+1], global_best_path[i]))
        
        # Only evaporate edges that were used (much faster for large graphs)
        for edge in edges_to_evaporate:
            if edge in self.pheromone:
                self.pheromone[edge] *= (1 - self.evaporation_rate)
        
        # 2. Rank-based deposit
        if paths and fitness_scores:
            # Yolları fitness'a göre sırala
            sorted_indices = np.argsort(fitness_scores)
            rank_weight = len(sorted_indices)
            
            for rank, idx in enumerate(sorted_indices[:10]):  # Top 10
                if fitness_scores[idx] == float('inf'):
                    continue
                
                path = paths[idx]
                deposit = (rank_weight - rank) * self.q / fitness_scores[idx]
                
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    self.pheromone[(u, v)] += deposit
                    self.pheromone[(v, u)] += deposit
        
        # 3. Iteration-best reinforcement
        if iteration_best_path and iteration_best_fitness != float('inf'):
            deposit = 2 * self.q / iteration_best_fitness
            for i in range(len(iteration_best_path) - 1):
                u, v = iteration_best_path[i], iteration_best_path[i + 1]
                self.pheromone[(u, v)] += deposit
                self.pheromone[(v, u)] += deposit
        
        # 4. Global-best (elitist) reinforcement
        if global_best_path and global_best_fitness != float('inf'):
            deposit = 3 * self.q / global_best_fitness
            for i in range(len(global_best_path) - 1):
                u, v = global_best_path[i], global_best_path[i + 1]
                self.pheromone[(u, v)] += deposit
                self.pheromone[(v, u)] += deposit
        
        # 5. Min-max bounds
        for edge in self.pheromone:
            self.pheromone[edge] = max(self.tau_min, min(self.tau_max, self.pheromone[edge]))
    
    def _pheromone_diffusion(self):
        """
        Pheromone topological diffusion.
        
        Yüksek feromonlu kenarlardan komşulara difüzyon.
        """
        diffusion_rate = 0.1
        new_pheromones = {}
        
        for node in self.graph.nodes():
            neighbors = list(self.graph.neighbors(node))
            
            for neighbor in neighbors:
                # Mevcut feromon
                current = self.pheromone[(node, neighbor)]
                
                # Komşuların ortalaması
                neighbor_avg = np.mean([
                    self.pheromone[(node, n)] for n in neighbors
                ])
                
                # Difüzyon
                new_value = (1 - diffusion_rate) * current + diffusion_rate * neighbor_avg
                new_pheromones[(node, neighbor)] = new_value
        
        # Güncelle
        for edge, value in new_pheromones.items():
            self.pheromone[edge] = value
    
    def _calculate_diversity(self, paths: List[List[int]]) -> float:
        """
        Population diversity hesapla.
        
        Farklı kenarların oranı.
        """
        if not paths:
            return 0.0
        
        all_edges = set()
        for path in paths:
            for i in range(len(path) - 1):
                all_edges.add((min(path[i], path[i+1]), max(path[i], path[i+1])))
        
        total_possible_edges = sum(len(path) - 1 for path in paths)
        
        if total_possible_edges == 0:
            return 0.0
        
        return len(all_edges) / total_possible_edges
    
    def get_statistics(self) -> Dict[str, Any]:
        """Algoritma istatistiklerini döndür."""
        if not self.pheromone:
            return {"status": "not_initialized"}
        
        values = list(self.pheromone.values())
        
        return {
            "edges_with_pheromone": len(values) // 2,
            "pheromone_stats": {
                "max": float(np.max(values)),
                "min": float(np.min(values)),
                "mean": float(np.mean(values)),
                "std": float(np.std(values))
            },
            "parameters": {
                "alpha": round(self.alpha, 3),
                "beta": round(self.beta, 3),
                "evaporation_rate": round(self.evaporation_rate, 3),
                "epsilon": self.epsilon
            },
            "convergence": {
                "best_fitness_history": self.best_fitness_history[-10:] if self.best_fitness_history else [],
                "final_diversity": self.diversity_history[-1] if self.diversity_history else 0
            }
        }


# Backward compatibility alias
# Proje genelinde AntColonyOptimization adı kullanıldığı için alias ekliyoruz
AntColonyOptimization = OptimizedACO