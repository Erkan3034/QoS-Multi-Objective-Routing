"""
Genetic Algorithm for Multi-Objective QoS Routing (v2.4 - Normalized & Optimized)

Değişiklik Logu (Network Engineering Team):
- [CRITICAL] Fitness Fonksiyonu Normalize Edildi: 'Dominant Metric' problemi çözüldü.
  Artık Delay (ms) ve Reliability (%) birbiriyle matematiksel olarak adil yarışıyor.
- [PERF] Singleton Pool ve Adaptive Scaling korundu.
- [DOC] Geliştirici notları eklendi.

Yazar: Network Engineering Lead
"""

import random
import time
import logging
import threading
import atexit
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from functools import lru_cache, partial
import networkx as nx
import multiprocessing
import os

# Servis Import Kontrolü
try:
    from ..services.metrics_service import MetricsService
    from ..core.config import settings
except ImportError:
    MetricsService = None
    class Settings:
        GA_POPULATION_SIZE = 200
        GA_GENERATIONS = 100
        GA_MUTATION_RATE = 0.05
        GA_CROSSOVER_RATE = 0.8
        GA_ELITISM = 0.1
    settings = Settings()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NORMALIZATION CONSTANTS (MÜHENDİSLİK REFERANS DEĞERLERİ)
# ---------------------------------------------------------------------------
# Arkadaşlar, burası önemli. Farklı birimleri (ms, %, hop) toplayabilmek için
# her birini 0.0 ile 1.0 arasına sıkıştırmamız lazım.
# Bu değerler, ağımızdaki "Kabul Edilebilir En Kötü" değerlerdir.
# ---------------------------------------------------------------------------
class NormConfig:
    MAX_DELAY_MS = 200.0        # 200ms üzeri bizim için "1.0" yani tam ceza puanıdır.
    MAX_HOP_COUNT = 20.0        # 20 hop üzeri çok verimsizdir.
    RELIABILITY_PENALTY = 10.0  # Paket kaybını (Hata) 10 kat cezalandırıyoruz ki Delay'in altında ezilmesin.

class GAConfig:
    """Genetik Algoritma Konfigürasyonu"""
    PARALLEL_AUTO_ENABLE_NODES = 500
    PARALLEL_MIN_POPULATION = 200
    SMALL_NET_GUIDED_RATIO = 0.3
    SMALL_NET_MAX_INIT_ATTEMPTS = 5
    LARGE_NET_GUIDED_RATIO = 0.5
    LARGE_NET_MAX_INIT_ATTEMPTS = 10
    POOL_CHUNKSIZE = 15

# ---------------------------------------------------------------------------
# FITNESS WORKER (CORE LOGIC)
# ---------------------------------------------------------------------------
def _fitness_worker(path_list: List[int], graph: nx.Graph, weights: Dict[str, float], bw_demand: float) -> float:
    """
    Burası algoritmanın kalbi. Eskiden ham değerleri topluyorduk, bu yüzden
    Delay (örn: 50ms) Reliability'i (örn: 0.01) eziyordu.
    
    Şimdi 'Elma ile Armut'u kıyaslayabilmek için Normalizasyon yapıyoruz.
    """
    try:
        total_delay = 0.0
        total_rel = 1.0
        min_bw = float('inf')
        
        # 1. Ham Verileri Topla
        for i in range(len(path_list) - 1):
            u, v = path_list[i], path_list[i+1]
            edge_data = graph[u][v]
            
            total_delay += edge_data.get('delay', 1.0)
            total_rel *= edge_data.get('reliability', 0.99)
            min_bw = min(min_bw, edge_data.get('bandwidth', 1000.0))

        # 2. Hard Constraint: Bant Genişliği
        # Eğer boru hattı darsa (bandwidth yetersizse), o yolun hiçbir değeri yoktur.
        if bw_demand > 0 and min_bw < bw_demand:
            return float('inf')

        # 3. NORMALİZASYON (Adil Puanlama)
        # ---------------------------------------------------------
        
        # Gecikme Skoru: 50ms / 200ms = 0.25 puan
        norm_delay = min(total_delay / NormConfig.MAX_DELAY_MS, 1.0)
        
        # Güvenilirlik Skoru: (1 - 0.99) = 0.01 Hata.
        # Bunu 10 ile çarpıyoruz (0.1 puan) ki Delay'in yanında sinek gibi kalmasın.
        # Güvenilirlik bizim için kritik!
        unreliability = 1.0 - total_rel
        norm_rel = min(unreliability * NormConfig.RELIABILITY_PENALTY, 1.0)
        
        # Kaynak Skoru: 5 Hop / 20 Hop = 0.25 puan
        norm_resource = min(len(path_list) / NormConfig.MAX_HOP_COUNT, 1.0)

        # 4. Ağırlıklı Toplam Maliyet
        # Artık kullanıcı %50 Güvenilirlik seçerse, algoritma gerçekten onu dinler.
        cost = (weights['delay'] * norm_delay) + \
               (weights['reliability'] * norm_rel) + \
               (weights['resource'] * norm_resource)
               
        return cost

    except Exception:
        return float('inf')

# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------
@dataclass
class GAResult:
    path: List[int]
    fitness: float
    generation: int
    computation_time_ms: float
    convergence_history: List[float] = field(default_factory=list)
    diversity_history: List[float] = field(default_factory=list)
    success: bool = True
    parallel_enabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "fitness": round(self.fitness, 6),
            "generation": self.generation,
            "computation_time_ms": round(self.computation_time_ms, 2),
            "convergence_history": [round(f, 4) for f in self.convergence_history],
            "diversity_history": [round(d, 4) for d in self.diversity_history],
            "success": self.success,
            "path_length": len(self.path),
            "parallel_enabled": self.parallel_enabled
        }

# ---------------------------------------------------------------------------
# GENETIC ALGORITHM CLASS
# ---------------------------------------------------------------------------
class GeneticAlgorithm:
    # Singleton Pool Pattern (Bellek Tasarrufu İçin)
    _shared_pool = None
    _pool_lock = threading.Lock()
    _pool_refcount = 0
    
    @classmethod
    def get_shared_pool(cls, n_processes=None):
        with cls._pool_lock:
            if cls._shared_pool is None:
                n_proc = n_processes or multiprocessing.cpu_count()
                cls._shared_pool = multiprocessing.Pool(processes=n_proc)
                logger.info(f"🚀 [System] Process pool initialized with {n_proc} workers.")
                atexit.register(cls._shutdown_pool)
            cls._pool_refcount += 1
            return cls._shared_pool
    
    @classmethod
    def _shutdown_pool(cls):
        with cls._pool_lock:
            if cls._shared_pool is not None:
                cls._shared_pool.close()
                cls._shared_pool.join()
                cls._shared_pool = None
    
    def __init__(
        self,
        graph: nx.Graph,
        population_size: int = None,
        generations: int = None,
        mutation_rate: float = None,
        crossover_rate: float = None,
        elitism: float = None,
        tournament_size: int = 5,
        convergence_threshold: float = 0.001,
        convergence_generations: int = 20,
        diversity_threshold: float = 0.1,
        seed: int = None,
        use_parallel: str = 'auto',
        use_standard_metrics: bool = False
    ):
        if not graph or graph.number_of_nodes() == 0:
            raise ValueError("Graf verisi boş, yönlendirme yapılamaz.")
        
        self.graph = graph
        self.graph_size = graph.number_of_nodes()
        
        # [EXPERIMENT MODE] Diğer algoritmalarla adil karşılaştırma için
        # Eğer True ise, MetricsService kullanılır (ACO, PSO ile aynı)
        # Eğer False ise, normalize edilmiş fitness kullanılır (daha iyi performans)
        self.use_standard_metrics = use_standard_metrics
        if self.use_standard_metrics and MetricsService:
            self.metrics_service = MetricsService(graph)
        else:
            self.metrics_service = None
        
        # Adaptive Parametreler
        base_pop = population_size or settings.GA_POPULATION_SIZE
        if not population_size:
            # Ağ büyüdükçe popülasyonu artırıyoruz ki çözüm uzayını tarayabilelim
            if self.graph_size < 100: self.population_size = base_pop
            elif self.graph_size < 500: self.population_size = int(base_pop * 1.3)
            else: self.population_size = int(base_pop * 2.5)
        else:
            self.population_size = population_size

        self.generations = generations or settings.GA_GENERATIONS
        # [IMPROVEMENT] Experiment mode'da daha agresif mutation
        # Standard metrics kullanıldığında, daha fazla keşif yap
        base_mutation = mutation_rate or settings.GA_MUTATION_RATE
        if self.use_standard_metrics:
            # Experiment mode: Daha agresif mutation (daha fazla keşif)
            self.initial_mutation_rate = base_mutation * 1.5  # 0.1 -> 0.15
        else:
            self.initial_mutation_rate = base_mutation
        self.mutation_rate = self.initial_mutation_rate
        self.crossover_rate = crossover_rate or settings.GA_CROSSOVER_RATE
        self.elitism = elitism or settings.GA_ELITISM
        self.tournament_size = tournament_size
        
        self.convergence_threshold = convergence_threshold
        self.convergence_generations = convergence_generations
        self.diversity_threshold = diversity_threshold
        
        # Auto-Parallel Decision
        if use_parallel == 'auto':
            self.use_parallel = (self.graph_size >= GAConfig.PARALLEL_AUTO_ENABLE_NODES)
        else:
            self.use_parallel = bool(use_parallel)
        
        # [FIX] Store seed for reference
        # If seed is None, random will use system time (non-deterministic, different each run)
        # If seed is set, results will be deterministic (useful for experiments)
        self._seed = seed
        if seed is not None:
            random.seed(seed)
        
        # İstatistikler
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
        self.diversity_history: List[float] = []
        
        # Caching & Optimization
        self._neighbor_cache = {node: list(graph.neighbors(node)) for node in graph.nodes()}
        self.current_weights: Dict[str, float] = {}
        
        # Init Strategy
        if self.graph_size < GAConfig.PARALLEL_AUTO_ENABLE_NODES:
            self.guided_ratio = GAConfig.SMALL_NET_GUIDED_RATIO
            self.max_init_attempts = GAConfig.SMALL_NET_MAX_INIT_ATTEMPTS
        else:
            self.guided_ratio = GAConfig.LARGE_NET_GUIDED_RATIO
            self.max_init_attempts = GAConfig.LARGE_NET_MAX_INIT_ATTEMPTS

    def optimize(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None,
        bandwidth_demand: float = 0.0,
        # [LIVE CONVERGENCE PLOT] Progress callback for real-time visualization
        progress_callback: Optional[Callable[[int, float], None]] = None
    ) -> GAResult:
        start_time = time.perf_counter()
        
        self._validate_inputs(source, destination, weights)
        
        # [FIX] Always update weights FIRST to ensure new optimization uses new weights
        # This is critical: weights affect fitness calculation throughout the algorithm
        self.current_weights = weights or {'delay': 0.33, 'reliability': 0.33, 'resource': 0.34}
        
        # [FIX] Always clear cache to force fresh calculation with new weights
        # Weights affect fitness, so cached paths may not be optimal with new weights
        self._cached_shortest_path.cache_clear()
        
        # [FIX] Reset statistics to ensure clean state for new optimization
        self.best_fitness_history.clear()
        self.avg_fitness_history.clear()
        self.diversity_history.clear()
        
        # [FIX] Reset mutation rate to initial value for fresh start
        self.mutation_rate = self.initial_mutation_rate
        
        # [FIX] Reset random state if no seed was set to ensure stochastic behavior
        # This ensures different results even with same weights (exploration)
        # If seed was set in __init__, it will remain deterministic (for experiments)
        if not hasattr(self, '_seed') or self._seed is None:
            # [FIX] Use nanoseconds + process ID + call counter for truly random seed
            # time_ns() provides nanosecond precision for uniqueness
            import time as time_module
            if not hasattr(self, '_call_counter'):
                self._call_counter = 0
            self._call_counter += 1
            seed_val = time_module.time_ns() % (2**31) + os.getpid() + self._call_counter
            random.seed(seed_val)
            print(f"[GA] Stokastik mod - seed={seed_val}, call={self._call_counter}")
        else:
            print(f"[GA] Deterministik mod - seed={self._seed}")
        
        population = self._initialize_population(source, destination, bandwidth_demand)
        
        if not population:
            return GAResult([], float('inf'), 0, (time.perf_counter()-start_time)*1000, success=False)
        
        best_individual = None
        best_fitness = float('inf')
        best_generation = 0
        stagnation_counter = 0
        
        # Lazy Pool Initialization
        pool = None
        if self.use_parallel:
            pool = self.get_shared_pool()
        
        # --- EVRİM DÖNGÜSÜ ---
        for gen in range(self.generations):
            # 1. Değerlendirme
            fitness_scores = self._evaluate_population(population, bandwidth_demand, pool)
            fitness_scores.sort(key=lambda x: x[1])
            
            # 2. Elitizm
            current_best_path, current_best_score = fitness_scores[0]
            
            if current_best_score < best_fitness:
                best_fitness = current_best_score
                best_individual = list(current_best_path)
                best_generation = gen
                stagnation_counter = 0
            else:
                stagnation_counter += 1
            
            # 3. İstatistik Kaydı
            self.best_fitness_history.append(best_fitness)
            valid_scores = [s for _, s in fitness_scores if s != float('inf')]
            avg_fit = sum(valid_scores)/len(valid_scores) if valid_scores else float('inf')
            self.avg_fitness_history.append(avg_fit)
            
            diversity = self._calculate_diversity(population)
            self.diversity_history.append(diversity)
            
            # [LIVE CONVERGENCE PLOT] Progress callback for real-time visualization
            if progress_callback:
                try:
                    progress_callback(gen, best_fitness)
                except Exception as e:
                    # Don't let callback errors break the optimization
                    logger.warning(f"Progress callback error: {e}")
            
            # 4. Erken Yakınsama Kontrolü
            if self._check_convergence(stagnation_counter):
                break
            
            # 5. Yeni Nesil Üretimi
            if gen < self.generations - 1:
                self._adjust_mutation_rate(diversity)
                population = self._evolve(fitness_scores, source, destination, diversity)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        
        result_path = best_individual if best_individual else [source, destination]
        print(f"[GA] Sonuç: path={result_path[:5]}...{result_path[-2:] if len(result_path)>5 else ''}, len={len(result_path)}, fitness={best_fitness:.4f}")
        
        return GAResult(
            path=result_path,
            fitness=best_fitness,
            generation=best_generation,
            computation_time_ms=elapsed,
            convergence_history=self.best_fitness_history,
            diversity_history=self.diversity_history,
            success=(best_fitness != float('inf')),
            parallel_enabled=self.use_parallel
        )

    def _validate_inputs(self, source, destination, weights):
        if source not in self.graph or destination not in self.graph:
            raise ValueError("Kaynak veya Hedef düğüm grafikte bulunamadı.")
        # Ağırlık toplamı kontrolü (Hata payı ile)
        if weights and not (0.99 <= sum(weights.values()) <= 1.01):
            raise ValueError("Ağırlıklar toplamı 1.0 olmalıdır.")

    def _evaluate_population(
        self, 
        population: List[List[int]], 
        bw_demand: float, 
        pool=None
    ) -> List[Tuple[List[int], float]]:
        # [EXPERIMENT MODE] Eğer standard metrics kullanılıyorsa, MetricsService ile hesapla
        if self.use_standard_metrics and self.metrics_service:
            results = []
            for path in population:
                # Bandwidth kontrolü
                if bw_demand > 0:
                    min_bw = float('inf')
                    for i in range(len(path) - 1):
                        u, v = path[i], path[i+1]
                        if self.graph.has_edge(u, v):
                            min_bw = min(min_bw, self.graph[u][v].get('bandwidth', 1000.0))
                    if min_bw < bw_demand:
                        results.append((path, float('inf')))
                        continue
                
                # MetricsService ile hesapla (ACO, PSO ile aynı)
                fit = self.metrics_service.calculate_weighted_cost(
                    path,
                    self.current_weights['delay'],
                    self.current_weights['reliability'],
                    self.current_weights['resource']
                )
                results.append((path, fit))
            return results
        
        # Normalize edilmiş fitness kullan (varsayılan, daha iyi performans)
        # Threshold Logic: Çok küçük popülasyonlar için process spawn etmeye değmez.
        should_use_parallel = (
            pool is not None and 
            self.use_parallel and
            len(population) > GAConfig.PARALLEL_MIN_POPULATION
        )
        
        if should_use_parallel:
            worker_func = partial(
                _fitness_worker, 
                graph=self.graph, 
                weights=self.current_weights, 
                bw_demand=bw_demand
            )
            # Chunksize performansı artırır (IPC overhead'i düşürür)
            fitness_values = pool.map(
                worker_func, 
                population, 
                chunksize=GAConfig.POOL_CHUNKSIZE
            )
            return list(zip(population, fitness_values))
        else:
            # Serial Execution (Küçük yükler için çok daha hızlı)
            results = []
            for path in population:
                fit = _fitness_worker(path, self.graph, self.current_weights, bw_demand)
                results.append((path, fit))
            return results

    @lru_cache(maxsize=5000)
    def _cached_shortest_path(self, src: int, dst: int) -> Tuple[int]:
        try:
            return tuple(nx.shortest_path(self.graph, src, dst))
        except nx.NetworkXNoPath:
            return ()

    def _initialize_population(self, source: int, destination: int, bandwidth_demand: float = 0.0) -> List[List[int]]:
        """
        [IMPROVED] Daha iyi başlangıç popülasyonu oluşturur.
        
        İyileştirmeler:
        1. Multiple shortest path variations (k-weighted shortest paths)
        2. Fitness-based guided initialization (daha iyi yollar)
        3. Daha fazla çeşitlilik
        4. [NEW] Bandwidth constraint filtering
        """
        population = []
        seen_paths = set()
        
        # [FIX] Create a filtered subgraph meeting bandwidth demand for initialization
        if bandwidth_demand > 0:
            valid_edges = [
                (u, v) for u, v, d in self.graph.edges(data=True)
                if d.get('bandwidth', 0) >= bandwidth_demand
            ]
            init_graph = self.graph.edge_subgraph(valid_edges).copy()
        else:
            init_graph = self.graph
            
        # Check connectivity on filtered graph
        if not nx.has_path(init_graph, source, destination):
            return []
        
        # Baseline: En Kısa Yol (on filtered graph)
        try:
            sp = nx.shortest_path(init_graph, source, destination, weight='weight') # Default unweighted or 'weight'
            if sp:
                population.append(list(sp))
                seen_paths.add(tuple(sp))
        except nx.NetworkXNoPath:
            pass
        
        # [IMPROVEMENT 1] K-weighted shortest paths ekle (çeşitlilik için)
        # Farklı edge weight kombinasyonlarıyla shortest path'ler bul
        try:
            # Delay-based shortest path
            delay_sp = nx.shortest_path(init_graph, source, destination, weight='delay')
            if tuple(delay_sp) not in seen_paths:
                population.append(list(delay_sp))
                seen_paths.add(tuple(delay_sp))
        except:
            pass
        
        try:
            # Reliability-based (inverse) shortest path
            # Yüksek reliability'li edge'leri tercih et
            # Note: We need to modify weights on the filtered graph copy
            if bandwidth_demand > 0:
                 # Already a copy
                 rel_graph = init_graph 
            else:
                 rel_graph = self.graph.copy()
                 
            for u, v in rel_graph.edges():
                rel = rel_graph[u][v].get('reliability', 0.99)
                rel_graph[u][v]['temp_weight'] = 1.0 / (rel + 0.01)  # Inverse
                
            rel_sp = nx.shortest_path(rel_graph, source, destination, weight='temp_weight')
            if tuple(rel_sp) not in seen_paths:
                population.append(list(rel_sp))
                seen_paths.add(tuple(rel_sp))
        except:
            pass
        
        # [IMPROVEMENT 2] Fitness-based guided initialization
        # Önce birkaç guided path oluştur, en iyilerini seç
        # [FIX] Use fitness-based initialization even in normal mode if weights are available
        # This ensures that weight changes affect the initial population
        if hasattr(self, 'current_weights') and self.current_weights:
            # Use MetricsService if available, otherwise use internal fitness
            use_metrics_service = (self.use_standard_metrics and self.metrics_service)
            candidate_paths = []
            max_candidates = min(50, self.population_size * 2)
            
            for _ in range(max_candidates):
                if random.random() < self.guided_ratio:
                    path = self._generate_guided_path(source, destination, bandwidth_demand)
                else:
                    path = self._generate_random_path(source, destination, bandwidth_demand)
                
                if path and tuple(path) not in seen_paths:
                    # [FIX] Calculate fitness using current weights (critical for weight changes)
                    if use_metrics_service:
                        # Use MetricsService for standard metrics
                        fitness = self.metrics_service.calculate_weighted_cost(
                            path,
                            self.current_weights.get('delay', 0.33),
                            self.current_weights.get('reliability', 0.33),
                            self.current_weights.get('resource', 0.34),
                            bandwidth_demand # Pass constraint
                        )
                    else:
                        # Use internal fitness worker for normalized metrics
                        fitness = _fitness_worker(
                            path, 
                            self.graph, 
                            self.current_weights, 
                            bandwidth_demand # Pass constraint
                        )
                    candidate_paths.append((fitness, path))
            
            # En iyi %50'sini seç
            candidate_paths.sort(key=lambda x: x[0])
            for _, path in candidate_paths[:len(candidate_paths)//2]:
                pt = tuple(path)
                if pt not in seen_paths and len(population) < self.population_size:
                    population.append(path)
                    seen_paths.add(pt)
        
        # Karışık Strateji: Guided (Akıllı) + Random (Çeşitlilik)
        attempts = 0
        max_attempts = self.population_size * self.max_init_attempts
        
        while len(population) < self.population_size and attempts < max_attempts:
            if random.random() < self.guided_ratio:
                path = self._generate_guided_path(source, destination, bandwidth_demand)
            else:
                path = self._generate_random_path(source, destination, bandwidth_demand)
            
            if path:
                pt = tuple(path)
                if pt not in seen_paths:
                    population.append(path)
                    seen_paths.add(pt)
            attempts += 1
            
        # Popülasyon dolmadıysa (küçük ağlarda veya kısıtlı ağlarda olur), shortest path ile doldur
        # Ama sadece geçerli SP varsa.
        if population:
            # En az bir yol varsa, çeşitlilik için onu kopyalayabiliriz veya SP'yi tekrar ekleyebiliriz.
            # En iyi yol (ilk bulunan SP) ile dolduralım.
            fill_path = population[0]
            while len(population) < self.population_size:
                population.append(list(fill_path))
        
        return population

    def _generate_guided_path(self, source: int, destination: int, bandwidth_demand: float = 0.0, max_len: int = 50) -> Optional[List[int]]:
        """Heuristic Path Generation: Degree Centrality kullanarak 'Hub' düğümlere yönelir."""
        path = [source]
        current = source
        visited = {source}
        
        for _ in range(max_len):
            if current == destination: return path
            
            # Filter neighbors
            neighbors = []
            for n in self._neighbor_cache[current]:
                if n in visited: continue
                # Check bandwidth constraint
                if bandwidth_demand > 0:
                     bw = self.graph[current][n].get('bandwidth', 0)
                     if bw < bandwidth_demand: continue
                neighbors.append(n)

            if not neighbors: return None
            
            if destination in neighbors:
                path.append(destination)
                return path
            
            # Hub Selection (Rulet Tekerleği)
            degrees = [self.graph.degree(n) for n in neighbors]
            total = sum(degrees)
            if total > 0:
                pick = random.uniform(0, total)
                curr_sum = 0
                next_node = neighbors[0]
                for i, deg in enumerate(degrees):
                    curr_sum += deg
                    if curr_sum >= pick:
                        next_node = neighbors[i]
                        break
            else:
                next_node = random.choice(neighbors)
            
            path.append(next_node)
            visited.add(next_node)
            current = next_node
        return None

    def _generate_random_path(self, source: int, destination: int, bandwidth_demand: float = 0.0, max_len: int = 50) -> Optional[List[int]]:
        """Saf Rastgele Yürüyüş (Keşif/Exploration için)"""
        path = [source]
        current = source
        visited = {source}
        for _ in range(max_len):
            if current == destination: return path
            
            # Filter neighbors
            neighbors = []
            for n in self._neighbor_cache[current]:
                if n in visited: continue
                # Check bandwidth constraint
                if bandwidth_demand > 0:
                     bw = self.graph[current][n].get('bandwidth', 0)
                     if bw < bandwidth_demand: continue
                neighbors.append(n)
                
            if not neighbors: return None
            
            if destination in neighbors:
                path.append(destination)
                return path
            current = random.choice(neighbors)
            path.append(current)
            visited.add(current)
        return None

    def _evolve(self, scores, src, dst, diversity):
        new_pop = []
        # Elitizm
        elite_count = max(1, int(self.population_size * self.elitism))
        new_pop.extend([list(s[0]) for s in scores[:elite_count]])
        
        while len(new_pop) < self.population_size:
            p1 = self._tournament_select(scores)
            p2 = self._tournament_select(scores)
            
            if random.random() < self.crossover_rate:
                c1, c2 = self._edge_based_crossover(p1, p2, src, dst)
            else:
                c1, c2 = list(p1), list(p2)
            
            op = self._select_mutation_operator(diversity)
            if random.random() < self.mutation_rate: c1 = op(c1, src, dst)
            if random.random() < self.mutation_rate: c2 = op(c2, src, dst)
            
            for c in [c1, c2]:
                if len(new_pop) < self.population_size and self._is_valid(c):
                    new_pop.append(c)
        return new_pop

    def _select_mutation_operator(self, diversity: float):
        if diversity < 0.05: return self._mutate_segment_replacement
        elif diversity < 0.15: return self._mutate_node_insertion
        else: return self._mutate_node_replacement

    def _adjust_mutation_rate(self, diversity: float):
        """
        [IMPROVED] Daha agresif mutation rate ayarlama.
        
        Experiment mode'da daha fazla keşif yapmak için mutation rate'i artır.
        """
        if diversity < self.diversity_threshold:
            # Çeşitlilik azaldıysa mutation'ı artır
            max_mutation = 0.4 if self.use_standard_metrics else 0.3
            self.mutation_rate = min(max_mutation, self.initial_mutation_rate * 2.5)
        else:
            self.mutation_rate = self.initial_mutation_rate

    def _tournament_select(self, scores):
        k = min(self.tournament_size, len(scores))
        return list(min(random.sample(scores, k), key=lambda x: x[1])[0])

    def _edge_based_crossover(self, p1, p2, src, dst):
        common = set(p1[1:-1]).intersection(p2[1:-1])
        if not common: return list(p1), list(p2)
        node = random.choice(list(common))
        try:
            i1, i2 = p1.index(node), p2.index(node)
            c1 = self._repair_path(p1[:i1+1] + p2[i2+1:], src, dst)
            c2 = self._repair_path(p2[:i2+1] + p1[i1+1:], src, dst)
            return c1, c2
        except ValueError:
            return list(p1), list(p2)

    def _mutate_node_replacement(self, path, src, dst):
        if len(path) < 4: return path
        idx = random.randint(1, len(path)-2)
        opts = (set(self._neighbor_cache[path[idx-1]]) & set(self._neighbor_cache[path[idx+1]])) - set(path)
        if opts: path[idx] = random.choice(list(opts))
        return path

    def _mutate_segment_replacement(self, path, src, dst):
        if len(path) < 5: return path
        idx1 = random.randint(1, len(path) - 4)
        idx2 = random.randint(idx1 + 2, len(path) - 1)
        n1, n2 = path[idx1], path[idx2]
        try:
            n1_neighbors = [n for n in self._neighbor_cache[n1] if n not in path[idx1+1:idx2]]
            if not n1_neighbors: return path
            via = random.choice(n1_neighbors)
            sp = self._cached_shortest_path(via, n2)
            if sp: return self._repair_path(path[:idx1+1] + list(sp) + path[idx2+1:], src, dst)
        except Exception: pass
        return path

    def _mutate_node_insertion(self, path, src, dst):
        if len(path) < 3: return path
        idx = random.randint(1, len(path)-1)
        candidates = set(self._neighbor_cache[path[idx-1]]) - set(path)
        if candidates:
            detour = random.choice(list(candidates))
            sp = self._cached_shortest_path(detour, path[idx])
            if sp: return path[:idx] + list(sp) + path[idx+1:]
        return path

    def _repair_path(self, path, src, dst):
        if not path or len(path) < 2: return path
        seen = set()
        clean = []
        for x in path:
            if x not in seen:
                clean.append(x)
                seen.add(x)
        repaired = [clean[0]]
        for i in range(1, len(clean)):
            if self.graph.has_edge(repaired[-1], clean[i]):
                repaired.append(clean[i])
            else:
                sp = self._cached_shortest_path(repaired[-1], clean[i])
                if sp: repaired.extend(list(sp)[1:])
        if repaired[-1] != dst:
            sp = self._cached_shortest_path(repaired[-1], dst)
            if sp: repaired.extend(list(sp)[1:])
        return repaired if repaired[-1] == dst else []

    def _is_valid(self, path):
        if not path or len(path) < 2: return False
        if len(path) != len(set(path)): return False
        for i in range(len(path)-1):
            if not self.graph.has_edge(path[i], path[i+1]): return False
        return True

    def _calculate_diversity(self, population):
        if len(population) < 2: return 0.0
        sample_size = min(max(30, int(len(population)*0.15)), 80)
        sample = random.sample(population, sample_size)
        total, count = 0, 0
        for i in range(len(sample)):
            for j in range(i+1, len(sample)):
                u = len(set(sample[i]) | set(sample[j]))
                if u > 0:
                    total += 1.0 - (len(set(sample[i]) & set(sample[j])) / u)
                    count += 1
        return total / count if count > 0 else 0.0

    def _check_convergence(self, stagnation):
        if stagnation >= self.convergence_generations: return True
        if len(self.best_fitness_history) > 10:
            recent = self.best_fitness_history[-10:]
            if max(recent) - min(recent) < self.convergence_threshold: return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "best_fitness_history": self.best_fitness_history,
            "diversity_history": self.diversity_history,
            "final_best_fitness": self.best_fitness_history[-1] if self.best_fitness_history else None,
            "parallel_enabled": self.use_parallel
        }
    
    def reset_statistics(self):
        self.best_fitness_history.clear()
        self.diversity_history.clear()
        self._cached_shortest_path.cache_clear()