"""
Particle Swarm Optimization (PSO) Algoritması

Bu modül çok amaçlı rotalama problemi için
Parçacık Sürü Optimizasyonu sağlar.

Özellikler:
- Discrete/Path-based PSO
- Velocity clipping
- Personal ve global best tracking
- Inertia weight

Referans: Kennedy & Eberhart, "Particle Swarm Optimization"
"""
import random
import time
import math
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass

from src.services.metrics_service import MetricsService
from src.core.config import settings


@dataclass
class PSOResult:
    """PSO sonuç veri sınıfı."""
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


class Particle:
    """Tek bir parçacığı temsil eder."""
    
    def __init__(
        self,
        path: List[int],
        fitness: float
    ):
        self.path = path
        self.fitness = fitness
        self.velocity: List[int] = []  # Discrete PSO için - değiştirilecek düğümler
        
        # Personal best
        self.pbest_path = path[:]
        self.pbest_fitness = fitness


class ParticleSwarmOptimization:
    """
    Particle Swarm Optimization.
    
    Parçacıklar (yollar) sürü halinde hareket eder,
    hem kendi en iyi konumlarından hem de
    global en iyi konumdan etkilenir.
    
    Discrete PSO adaptasyonu:
    - Position: Yol
    - Velocity: Değiştirilecek düğümler
    - Movement: Yol modifikasyonu
    
    Attributes:
        graph: NetworkX graf objesi
        n_particles: Parçacık sayısı
        n_iterations: İterasyon sayısı
        w: Inertia weight
        c1: Cognitive parameter (personal best)
        c2: Social parameter (global best)
    
    Example:
        >>> pso = ParticleSwarmOptimization(graph, n_particles=30)
        >>> result = pso.optimize(source=0, destination=249, weights={...})
        >>> print(f"Best path: {result.path}")
    """
    
    def __init__(
        self,
        graph: nx.Graph,
        n_particles: int = 30,
        n_iterations: int = 100,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
        seed: int = None
    ):
        """
        ParticleSwarmOptimization oluşturur.
        
        Args:
            graph: NetworkX graf objesi
            n_particles: Parçacık sayısı
            n_iterations: İterasyon sayısı
            w: Inertia weight (0-1)
            c1: Cognitive parameter
            c2: Social parameter
            seed: Rastgele seed
        """
        self.graph = graph
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        self.w = w
        self.c1 = c1
        self.c2 = c2
        
        if seed is not None:
            random.seed(seed)
        
        self.metrics_service = MetricsService(graph)
        
        # İstatistikler
        self.gbest_history: List[float] = []
        self.avg_fitness_history: List[float] = []
    
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None,
        progress_callback: Optional[Callable[[int, float], None]] = None
    ) -> PSOResult:
        """
        Optimal yolu bul.
        
        Args:
            source: Kaynak düğüm ID
            destination: Hedef düğüm ID
            weights: Metrik ağırlıkları {'delay', 'reliability', 'resource'}
        
        Returns:
            PSOResult objesi
        """
        start_time = time.perf_counter()
        
        weights = weights or {
            'delay': 0.33,
            'reliability': 0.33,
            'resource': 0.34
        }
        
        # İstatistikleri sıfırla
        self.gbest_history = []
        self.avg_fitness_history = []
        
        # Parçacıkları oluştur
        particles = self._initialize_particles(source, destination, weights)
        
        if not particles:
            try:
                fallback_path = nx.shortest_path(self.graph, source, destination)
                fitness = self._calculate_fitness(fallback_path, weights)
                return PSOResult(
                    path=fallback_path,
                    fitness=fitness,
                    iteration=0,
                    computation_time_ms=0
                )
            except Exception:
                return PSOResult(
                    path=[source, destination],
                    fitness=float('inf'),
                    iteration=0,
                    computation_time_ms=0
                )
        
        # Global best
        gbest_path = min(particles, key=lambda p: p.fitness).path[:]
        gbest_fitness = min(p.fitness for p in particles)
        best_iteration = 0
        
        for iteration in range(self.n_iterations):
            for particle in particles:
                # Velocity güncelle (discrete PSO adaptasyonu)
                self._update_velocity(particle, gbest_path)
                
                # Position güncelle (yolu modifiye et)
                new_path = self._update_position(particle, source, destination)
                
                if new_path:
                    new_fitness = self._calculate_fitness(new_path, weights)
                    
                    particle.path = new_path
                    particle.fitness = new_fitness
                    
                    # Personal best güncelle
                    if new_fitness < particle.pbest_fitness:
                        particle.pbest_path = new_path[:]
                        particle.pbest_fitness = new_fitness
                    
                    # Global best güncelle
                    if new_fitness < gbest_fitness:
                        gbest_path = new_path[:]
                        gbest_fitness = new_fitness
                        best_iteration = iteration
            
            # İstatistikleri kaydet
            self.gbest_history.append(gbest_fitness)
            valid_fitness = [p.fitness for p in particles if p.fitness != float('inf')]
            if valid_fitness:
                self.avg_fitness_history.append(sum(valid_fitness) / len(valid_fitness))
            
            # [LIVE CONVERGENCE PLOT] Progress callback for real-time visualization
            if progress_callback:
                try:
                    progress_callback(iteration, gbest_fitness)
                except Exception:
                    # Don't let callback errors break the optimization
                    pass
        
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        return PSOResult(
            path=gbest_path,
            fitness=gbest_fitness,
            iteration=best_iteration,
            computation_time_ms=elapsed_time
        )
    
    def _initialize_particles(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float]
    ) -> List[Particle]:
        """Parçacıkları oluşturur."""
        particles = []
        
        for _ in range(self.n_particles):
            path = self._generate_random_path(source, destination)
            if path:
                fitness = self._calculate_fitness(path, weights)
                particles.append(Particle(path, fitness))
        
        return particles
    
    def _generate_random_path(
        self,
        source: int,
        destination: int,
        max_length: int = 50
    ) -> Optional[List[int]]:
        """Rastgele geçerli yol oluşturur."""
        path = [source]
        current = source
        visited = {source}
        
        while current != destination and len(path) < max_length:
            neighbors = [n for n in self.graph.neighbors(current) if n not in visited]
            
            if not neighbors:
                return None
            
            if destination in neighbors:
                path.append(destination)
                return path
            
            next_node = random.choice(neighbors)
            path.append(next_node)
            visited.add(next_node)
            current = next_node
        
        return path if current == destination else None
    
    def _update_velocity(
        self,
        particle: Particle,
        gbest_path: List[int]
    ):
        """
        Velocity günceller (discrete PSO adaptasyonu).
        
        Velocity = düğüm indeksleri ve değişim yönleri
        """
        velocity = []
        
        # Personal best'e doğru hareket
        if random.random() < self.c1 / (self.c1 + self.c2):
            diff_indices = self._path_difference(particle.path, particle.pbest_path)
            velocity.extend(diff_indices[:2])  # En fazla 2 değişiklik
        
        # Global best'e doğru hareket
        if random.random() < self.c2 / (self.c1 + self.c2):
            diff_indices = self._path_difference(particle.path, gbest_path)
            velocity.extend(diff_indices[:2])
        
        # Inertia - rastgele keşif
        if random.random() < self.w:
            if len(particle.path) > 2:
                velocity.append(random.randint(1, len(particle.path) - 2))
        
        particle.velocity = velocity[:3]  # Max 3 değişiklik
    
    def _path_difference(
        self,
        path1: List[int],
        path2: List[int]
    ) -> List[int]:
        """İki yol arasındaki farklı düğüm indekslerini bulur."""
        diff_indices = []
        
        min_len = min(len(path1), len(path2))
        
        for i in range(1, min_len - 1):  # Source ve destination hariç
            if i < len(path1) and i < len(path2):
                if path1[i] != path2[i]:
                    diff_indices.append(i)
        
        return diff_indices
    
    def _update_position(
        self,
        particle: Particle,
        source: int,
        destination: int
    ) -> Optional[List[int]]:
        """
        Position (yol) günceller.
        
        Velocity'deki indekslerdeki düğümleri değiştirir.
        """
        if not particle.velocity:
            return particle.path[:]
        
        new_path = particle.path[:]
        
        for idx in particle.velocity:
            if 0 < idx < len(new_path) - 1:
                # Bu indeksteki düğümü değiştirmeyi dene
                prev_node = new_path[idx - 1]
                next_node = new_path[idx + 1]
                current_node = new_path[idx]
                
                # Alternatif düğüm bul
                candidates = set(self.graph.neighbors(prev_node)) & set(self.graph.neighbors(next_node))
                candidates.discard(current_node)
                candidates -= set(new_path)
                
                if candidates:
                    new_node = random.choice(list(candidates))
                    new_path[idx] = new_node
        
        # Yolun geçerli olduğunu kontrol et
        if self._is_valid_path(new_path):
            return new_path
        
        # Geçersizse yeni rastgele yol oluştur
        return self._generate_random_path(source, destination)
    
    def _is_valid_path(self, path: List[int]) -> bool:
        """Yolun geçerli olup olmadığını kontrol eder."""
        if len(path) < 2:
            return False
        
        # Döngü kontrolü
        if len(path) != len(set(path)):
            return False
        
        # Kenar kontrolü
        for i in range(len(path) - 1):
            if not self.graph.has_edge(path[i], path[i + 1]):
                return False
        
        return True
    
    def _calculate_fitness(
        self,
        path: List[int],
        weights: Dict[str, float]
    ) -> float:
        """Fitness değerini hesaplar."""
        try:
            return self.metrics_service.calculate_weighted_cost(
                path,
                weights['delay'],
                weights['reliability'],
                weights['resource']
            )
        except Exception:
            return float('inf')
    
    def get_stats(self) -> Dict[str, Any]:
        """Çalışma istatistiklerini döndürür."""
        if not self.gbest_history:
            return {"iterations": 0}
        
        return {
            "iterations": len(self.gbest_history),
            "final_gbest": self.gbest_history[-1],
            "improvement": self.gbest_history[0] - self.gbest_history[-1] if len(self.gbest_history) > 1 else 0,
            "convergence_iteration": self.gbest_history.index(min(self.gbest_history))
        }

