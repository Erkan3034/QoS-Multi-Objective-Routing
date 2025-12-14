"""
Genetik Algoritma (GA) Implementasyonu

Bu modül çok amaçlı rotalama problemi için 
Genetik Algoritma tabanlı optimizasyon sağlar.

Özellikler:
- Yol tabanlı kromozom kodlama
- Single-point crossover
- Random mutation
- Tournament selection
- Elitism
"""
import random
import time
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from ..services.metrics_service import MetricsService
from ..core.config import settings


@dataclass
class GAResult:
    """GA sonuç veri sınıfı."""
    path: List[int]
    fitness: float
    generation: int
    computation_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "fitness": round(self.fitness, 6),
            "generation": self.generation,
            "computation_time_ms": round(self.computation_time_ms, 2)
        }


class GeneticAlgorithm:
    """
    Genetik Algoritma optimizasyonu.
    
    250 düğümlü ağda kaynak-hedef arasındaki
    optimal yolu bulmak için evrimsel optimizasyon kullanır.
    
    Attributes:
        graph: NetworkX graf objesi
        population_size: Popülasyon büyüklüğü
        generations: Maksimum nesil sayısı
        mutation_rate: Mutasyon olasılığı
        crossover_rate: Çaprazlama olasılığı
        elitism: Elit bireylerin oranı
    
    Example:
        >>> ga = GeneticAlgorithm(graph, population_size=100)
        >>> result = ga.optimize(source=0, destination=249, weights={...})
        >>> print(f"Best path: {result.path}")
    """
    
    def __init__(
        self,
        graph: nx.Graph,
        population_size: int = None,
        generations: int = None,
        mutation_rate: float = None,
        crossover_rate: float = None,
        elitism: float = None,
        seed: int = None
    ):
        """
        GeneticAlgorithm oluşturur.
        
        Args:
            graph: NetworkX graf objesi
            population_size: Popülasyon büyüklüğü
            generations: Maksimum nesil sayısı
            mutation_rate: Mutasyon olasılığı (0-1)
            crossover_rate: Çaprazlama olasılığı (0-1)
            elitism: Elit bireylerin oranı (0-1)
            seed: Rastgele seed
        """
        self.graph = graph
        self.population_size = population_size or settings.GA_POPULATION_SIZE
        self.generations = generations or settings.GA_GENERATIONS
        self.mutation_rate = mutation_rate or settings.GA_MUTATION_RATE
        self.crossover_rate = crossover_rate or settings.GA_CROSSOVER_RATE
        self.elitism = elitism or settings.GA_ELITISM
        
        if seed is not None:
            random.seed(seed)
        
        self.metrics_service = MetricsService(graph)
        
        # İstatistikler
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
    
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None
    ) -> GAResult:
        """
        Optimal yolu bul.
        
        Args:
            source: Kaynak düğüm ID
            destination: Hedef düğüm ID
            weights: Metrik ağırlıkları {'delay', 'reliability', 'resource'}
        
        Returns:
            GAResult objesi
        """
        start_time = time.perf_counter()
        
        weights = weights or {
            'delay': 0.33,
            'reliability': 0.33,
            'resource': 0.34
        }
        
        # Popülasyonu başlat
        population = self._initialize_population(source, destination)
        
        if not population:
            raise ValueError(f"Could not generate initial population for {source} -> {destination}")
        
        best_individual = None
        best_fitness = float('inf')
        best_generation = 0
        
        for gen in range(self.generations):
            # Fitness değerlerini hesapla
            fitness_scores = []
            for individual in population:
                try:
                    fitness = self.metrics_service.calculate_weighted_cost(
                        individual,
                        weights['delay'],
                        weights['reliability'],
                        weights['resource']
                    )
                    fitness_scores.append((individual, fitness))
                except (ValueError, KeyError, IndexError):
                    fitness_scores.append((individual, float('inf')))
            
            # Fitness'a göre sırala
            fitness_scores.sort(key=lambda x: x[1])
            
            # En iyi bireyi güncelle
            if fitness_scores[0][1] < best_fitness:
                best_individual = fitness_scores[0][0]
                best_fitness = fitness_scores[0][1]
                best_generation = gen
            
            # İstatistikleri kaydet
            valid_scores = [f for _, f in fitness_scores if f != float('inf')]
            self.best_fitness_history.append(best_fitness)
            if valid_scores:
                self.avg_fitness_history.append(sum(valid_scores) / len(valid_scores))
            
            # Son nesil değilse evrim yap
            if gen < self.generations - 1:
                population = self._evolve(fitness_scores, source, destination)
        
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        return GAResult(
            path=best_individual or [source, destination],
            fitness=best_fitness,
            generation=best_generation,
            computation_time_ms=elapsed_time
        )
    
    def _initialize_population(self, source: int, destination: int) -> List[List[int]]:
        """
        Başlangıç popülasyonunu oluşturur.
        
        Her birey S'den D'ye geçerli bir yoldur.
        """
        population = []
        attempts_per_individual = 10

        for _ in range(self.population_size):
            for _ in range(attempts_per_individual):
                path = self._generate_random_path(source, destination)
                if path and path not in population:
                    population.append(path)
                    break
        
        return population
    
    def _generate_random_path(
        self,
        source: int,
        destination: int,
        max_length: int = 50
    ) -> Optional[List[int]]:
        """
        Rastgele geçerli yol oluşturur.
        
        Random walk ile source'tan destination'a gider.
        """
        path = [source]
        current = source
        visited = {source}
        
        while current != destination and len(path) < max_length:
            neighbors = [n for n in self.graph.neighbors(current) if n not in visited]
            
            if not neighbors:
                # Dead end - backtrack or return None
                return None
            
            # Hedefe doğru bias ekle (optional)
            if destination in neighbors:
                next_node = destination
            else:
                next_node = random.choice(neighbors)
            
            path.append(next_node)
            visited.add(next_node)
            current = next_node
        
        return path if current == destination else None
    
    def _evolve(
        self,
        fitness_scores: List[Tuple[List[int], float]],
        source: int,
        destination: int
    ) -> List[List[int]]:
        """
        Yeni nesil oluşturur.
        
        Selection, crossover ve mutation uygular.
        """
        new_population = []
        
        # Elitizm: En iyi bireyleri koru
        elite_count = int(self.population_size * self.elitism)
        elites = [ind for ind, _ in fitness_scores[:elite_count]]
        new_population.extend(elites)
        
        # Geri kalan bireyleri oluştur
        while len(new_population) < self.population_size:
            # Seçim (Tournament selection)
            parent1 = self._tournament_select(fitness_scores)
            parent2 = self._tournament_select(fitness_scores)
            
            # Çaprazlama
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1[:], parent2[:]
            
            # Mutasyon
            if random.random() < self.mutation_rate:
                child1 = self._mutate(child1)
            if random.random() < self.mutation_rate:
                child2 = self._mutate(child2)
            
            # Geçerli çocukları ekle
            for child in [child1, child2]:
                if child and self._is_valid_path(child) and len(new_population) < self.population_size:
                    new_population.append(child)
        
        return new_population
    
    def _tournament_select(
        self,
        fitness_scores: List[Tuple[List[int], float]],
        tournament_size: int = 5
    ) -> List[int]:
        """Tournament selection uygular."""
        tournament = random.sample(fitness_scores, min(tournament_size, len(fitness_scores)))
        tournament.sort(key=lambda x: x[1])
        return tournament[0][0][:]
    
    def _crossover(
        self,
        parent1: List[int],
        parent2: List[int]
    ) -> Tuple[List[int], List[int]]:
        """
        Single-point crossover uygular.
        
        İki ebeveynde ortak düğüm bulur ve o noktadan keser.
        """
        # Ortak düğümleri bul (source ve destination hariç)
        common_nodes = set(parent1[1:-1]) & set(parent2[1:-1])
        
        if not common_nodes:
            return parent1[:], parent2[:]
        
        # Rastgele bir ortak düğüm seç
        crossover_node = random.choice(list(common_nodes))
        
        # Crossover noktalarını bul
        idx1 = parent1.index(crossover_node)
        idx2 = parent2.index(crossover_node)
        
        # Çocukları oluştur
        child1 = parent1[:idx1] + parent2[idx2:]
        child2 = parent2[:idx2] + parent1[idx1:]
        
        # Döngü kontrolü
        if len(child1) != len(set(child1)):
            child1 = parent1[:]
        if len(child2) != len(set(child2)):
            child2 = parent2[:]
        
        return child1, child2
    
    def _mutate(
        self,
        individual: List[int]
    ) -> List[int]:
        """
        Mutasyon uygular.
        
        Rastgele bir düğümü komşusuyla değiştirir.
        """
        if len(individual) <= 2:
            return individual
        
        # Rastgele bir ara düğüm seç
        idx = random.randint(1, len(individual) - 2)
        current = individual[idx]
        prev_node = individual[idx - 1]
        next_node = individual[idx + 1]
        
        # Hem prev hem next'e bağlı bir komşu bul
        neighbors = set(self.graph.neighbors(prev_node)) & set(self.graph.neighbors(next_node))
        neighbors.discard(current)
        neighbors -= set(individual)  # Döngü önle
        
        if neighbors:
            new_node = random.choice(list(neighbors))
            mutated = individual[:]
            mutated[idx] = new_node
            return mutated
        
        return individual
    
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

