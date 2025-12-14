"""
Simulated Annealing (SA) Algoritması

Bu modül çok amaçlı rotalama problemi için
Benzetilmiş Tavlama tabanlı optimizasyon sağlar.

Özellikler:
- Sıcaklık bazlı kabul olasılığı
- Neighborhood-based exploration
- Gradual cooling schedule
- Global optimum arayışı

Referans: Kirkpatrick et al., "Optimization by Simulated Annealing"
"""
import random
import time
import math
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.services.metrics_service import MetricsService
from src.core.config import settings


@dataclass
class SAResult:
    """Simulated Annealing sonuç veri sınıfı."""
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
            "computation_time_ms": round(self.computation_time_ms, 2)
        }


class SimulatedAnnealing:
    """
    Simulated Annealing optimizasyonu.
    
    Metalurjiden ilham alan optimizasyon yöntemi.
    Yüksek sıcaklıkta kötü çözümleri kabul eder,
    soğudukça daha seçici olur.
    
    Kabul olasılığı:
    P(accept) = exp(-(f_new - f_old) / T)
    
    Attributes:
        graph: NetworkX graf objesi
        initial_temperature: Başlangıç sıcaklığı
        final_temperature: Bitiş sıcaklığı
        cooling_rate: Soğuma oranı
        iterations_per_temp: Her sıcaklıkta iterasyon sayısı
    
    Example:
        >>> sa = SimulatedAnnealing(graph)
        >>> result = sa.optimize(source=0, destination=249, weights={...})
        >>> print(f"Best path: {result.path}")
    """
    
    def __init__(
        self,
        graph: nx.Graph,
        initial_temperature: float = 1000.0,
        final_temperature: float = 0.01,
        cooling_rate: float = 0.995,
        iterations_per_temp: int = 10,
        seed: int = None
    ):
        """
        SimulatedAnnealing oluşturur.
        
        Args:
            graph: NetworkX graf objesi
            initial_temperature: Başlangıç sıcaklığı (T0)
            final_temperature: Bitiş sıcaklığı
            cooling_rate: Soğuma oranı (α)
            iterations_per_temp: Her sıcaklıkta iterasyon sayısı
            seed: Rastgele seed
        """
        self.graph = graph
        self.initial_temperature = initial_temperature
        self.final_temperature = final_temperature
        self.cooling_rate = cooling_rate
        self.iterations_per_temp = iterations_per_temp
        
        if seed is not None:
            random.seed(seed)
        
        self.metrics_service = MetricsService(graph)
        
        # İstatistikler
        self.fitness_history: List[float] = []
        self.temperature_history: List[float] = []
        self.acceptance_history: List[bool] = []
    
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None
    ) -> SAResult:
        """
        Optimal yolu bul.
        
        Args:
            source: Kaynak düğüm ID
            destination: Hedef düğüm ID
            weights: Metrik ağırlıkları {'delay', 'reliability', 'resource'}
        
        Returns:
            SAResult objesi
        """
        start_time = time.perf_counter()
        
        weights = weights or {
            'delay': 0.33,
            'reliability': 0.33,
            'resource': 0.34
        }
        
        # İstatistikleri sıfırla
        self.fitness_history = []
        self.temperature_history = []
        self.acceptance_history = []
        
        # Başlangıç çözümü oluştur
        current_path = self._generate_initial_solution(source, destination)
        if not current_path:
            try:
                current_path = nx.shortest_path(self.graph, source, destination)
            except nx.NetworkXNoPath:
                return SAResult(
                    path=[source, destination],
                    fitness=float('inf'),
                    iteration=0,
                    final_temperature=self.initial_temperature,
                    computation_time_ms=0
                )
        
        current_fitness = self._calculate_fitness(current_path, weights)
        
        best_path = current_path[:]
        best_fitness = current_fitness
        best_iteration = 0
        
        temperature = self.initial_temperature
        iteration = 0
        
        while temperature > self.final_temperature:
            for _ in range(self.iterations_per_temp):
                # Komşu çözüm oluştur
                neighbor_path = self._get_neighbor(current_path, source, destination)
                
                if not neighbor_path:
                    continue
                
                neighbor_fitness = self._calculate_fitness(neighbor_path, weights)
                
                # Kabul kriteri
                delta = neighbor_fitness - current_fitness
                
                if delta < 0:
                    # Daha iyi çözüm - kabul et
                    accept = True
                else:
                    # Daha kötü çözüm - olasılıkla kabul et
                    try:
                        acceptance_prob = math.exp(-delta / temperature)
                        accept = random.random() < acceptance_prob
                    except (OverflowError, ZeroDivisionError):
                        accept = False
                
                self.acceptance_history.append(accept)
                
                if accept:
                    current_path = neighbor_path
                    current_fitness = neighbor_fitness
                    
                    if current_fitness < best_fitness:
                        best_path = current_path[:]
                        best_fitness = current_fitness
                        best_iteration = iteration
                
                self.fitness_history.append(best_fitness)
                self.temperature_history.append(temperature)
                iteration += 1
            
            # Sıcaklığı düşür
            temperature *= self.cooling_rate
        
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        return SAResult(
            path=best_path,
            fitness=best_fitness,
            iteration=best_iteration,
            final_temperature=temperature,
            computation_time_ms=elapsed_time
        )
    
    def _generate_initial_solution(
        self,
        source: int,
        destination: int
    ) -> Optional[List[int]]:
        """
        Başlangıç çözümü oluşturur.
        
        Random walk ile bir yol bulur.
        """
        path = [source]
        current = source
        visited = {source}
        max_steps = 100
        
        while current != destination and len(path) < max_steps:
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
    
    def _get_neighbor(
        self,
        current_path: List[int],
        source: int,
        destination: int
    ) -> Optional[List[int]]:
        """
        Komşu çözüm oluşturur.
        
        Farklı neighborhood operatörleri:
        1. Node swap: Ara düğümü değiştir
        2. Segment replace: Yolun bir kısmını yeniden oluştur
        3. Shortcut: Yolu kısalt
        """
        if len(current_path) <= 2:
            return self._generate_initial_solution(source, destination)
        
        operator = random.choice(['swap', 'segment', 'shortcut'])
        
        if operator == 'swap':
            return self._neighbor_swap(current_path)
        elif operator == 'segment':
            return self._neighbor_segment(current_path, source, destination)
        else:
            return self._neighbor_shortcut(current_path)
    
    def _neighbor_swap(self, path: List[int]) -> Optional[List[int]]:
        """Bir ara düğümü alternatif ile değiştirir."""
        if len(path) <= 2:
            return None
        
        # Rastgele ara düğüm seç
        idx = random.randint(1, len(path) - 2)
        prev_node = path[idx - 1]
        next_node = path[idx + 1]
        current_node = path[idx]
        
        # Hem prev hem next'e bağlı alternatif düğüm bul
        candidates = set(self.graph.neighbors(prev_node)) & set(self.graph.neighbors(next_node))
        candidates.discard(current_node)
        candidates -= set(path)  # Döngü önle
        
        if not candidates:
            return None
        
        new_node = random.choice(list(candidates))
        new_path = path[:]
        new_path[idx] = new_node
        
        return new_path
    
    def _neighbor_segment(
        self,
        path: List[int],
        source: int,
        destination: int
    ) -> Optional[List[int]]:
        """Yolun bir segmentini yeniden oluşturur."""
        if len(path) <= 3:
            return self._generate_initial_solution(source, destination)
        
        # Rastgele iki nokta seç
        i = random.randint(0, len(path) - 3)
        j = random.randint(i + 2, len(path) - 1)
        
        start_node = path[i]
        end_node = path[j]
        
        # Bu iki nokta arasında yeni yol bul
        new_segment = self._find_alternative_segment(start_node, end_node, set(path) - set(path[i:j+1]))
        
        if not new_segment:
            return None
        
        new_path = path[:i] + new_segment + path[j+1:]
        
        # Döngü kontrolü
        if len(new_path) != len(set(new_path)):
            return None
        
        return new_path
    
    def _neighbor_shortcut(self, path: List[int]) -> Optional[List[int]]:
        """Yolu kısaltmaya çalışır."""
        if len(path) <= 3:
            return None
        
        # Rastgele iki non-adjacent düğüm seç
        i = random.randint(0, len(path) - 3)
        
        for j in range(i + 2, len(path)):
            if self.graph.has_edge(path[i], path[j]):
                # Shortcut bulduk
                new_path = path[:i+1] + path[j:]
                return new_path
        
        return None
    
    def _find_alternative_segment(
        self,
        start: int,
        end: int,
        forbidden: set
    ) -> Optional[List[int]]:
        """İki düğüm arasında alternatif yol bulur."""
        path = [start]
        current = start
        visited = {start} | forbidden
        max_steps = 20
        
        while current != end and len(path) < max_steps:
            neighbors = [n for n in self.graph.neighbors(current) if n not in visited]
            
            if not neighbors:
                return None
            
            if end in neighbors:
                path.append(end)
                return path
            
            next_node = random.choice(neighbors)
            path.append(next_node)
            visited.add(next_node)
            current = next_node
        
        return path if current == end else None
    
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
        if not self.acceptance_history:
            return {"iterations": 0}
        
        return {
            "iterations": len(self.fitness_history),
            "acceptance_rate": sum(self.acceptance_history) / len(self.acceptance_history),
            "initial_temp": self.temperature_history[0] if self.temperature_history else 0,
            "final_temp": self.temperature_history[-1] if self.temperature_history else 0,
            "best_fitness": min(self.fitness_history) if self.fitness_history else float('inf')
        }

