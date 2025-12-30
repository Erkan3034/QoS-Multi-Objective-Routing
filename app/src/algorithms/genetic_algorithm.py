"""
GENETİK ALGORİTMA 
=============================================================================
BİYOLOJİK EVHAM'DEN ESINLENEN OPTİMİZASYON:
------------------------------------------
Darwin'in doğal seçilim teorisini ağ yönlendirme problemine uygular.
Zayıf yollar elenir, güçlü yollar çoğalır, mutasyonlar yeni keşifler sağlar.

EVRIM DÖNGÜSÜ:
-------------
1. Başlangıç → Çeşitli yollar oluştur (shortest path + random walks)
2. Değerlendirme → Her yolun fitness'ını hesapla (delay, reliability, resource)
3. Seçilim → En iyi yolları ebeveyn olarak seç (tournament selection)
4. Çaprazlama → İki ebeveynden yeni yollar üret (edge-based crossover)
5. Mutasyon → Rastgele değişikliklerle çeşitlilik sağla
6. Yeni Nesil → Adım 2'ye dön (veya yakınsama ile dur)

NORMALİZASYON MATEMATİĞİ:
------------------------
Farklı birimlerdeki metrikleri (ms, %, Mbps) adil karşılaştırabilmek için:
- delay_normalized = min(total_delay / 200ms, 1.0)
- reliability_normalized = min(-log(reliability_product) / 10.0, 1.0)
- resource_normalized = min(Σ(1000/bandwidth) / 200.0, 1.0)
- final_cost = w1*delay + w2*reliability + w3*resource

PROJE YÖNERGESİ UYUMU:
----------------------
✓ TotalDelay = Σ(LinkDelay) + Σ(ProcessingDelay) [k ≠ S, D]
✓ ReliabilityCost = Σ[-log(LinkReliability)] + Σ[-log(NodeReliability)]
✓ ResourceCost = Σ(1Gbps / Bandwidth)
"""

import random, time, logging, threading, atexit, os, math
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from functools import lru_cache, partial
import networkx as nx
import multiprocessing

# Servis importları (modül bağımsız çalışabilir)
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

# =============================================================================
# KONFIGURASYON
# =============================================================================

class NormConfig:
    """
    Normalizasyon Referans Değerleri
    --------------------------------
    Bu değerler "kabul edilebilir en kötü" değerlerdir.
    Bunun üzerindeki değerler tam ceza (1.0) alır.
    
    Örnek: 150ms delay → 150/200 = 0.75 (normalleştirilmiş)
           250ms delay → 250/200 = 1.25 → min(1.25, 1.0) = 1.0 (max ceza)
    """
    MAX_DELAY_MS = 200.0
    MAX_HOP_COUNT = 20.0
    RELIABILITY_PENALTY = 10.0

class GAConfig:
    """Genetik Algoritma Davranış Parametreleri"""
    PARALLEL_AUTO_ENABLE_NODES = 500    # 500+ düğümde paralel mod devreye girer
    PARALLEL_MIN_POPULATION = 200       # Paralel işleme için minimum popülasyon
    SMALL_NET_GUIDED_RATIO = 0.3        # Küçük ağlarda akıllı başlangıç oranı
    SMALL_NET_MAX_INIT_ATTEMPTS = 5
    LARGE_NET_GUIDED_RATIO = 0.5        # Büyük ağlarda daha fazla akıllı başlangıç
    LARGE_NET_MAX_INIT_ATTEMPTS = 10
    POOL_CHUNKSIZE = 15                 # IPC overhead optimizasyonu

# =============================================================================
# FITNESS FONKSİYONU - Yol Kalitesi Hesaplama Motoru
# =============================================================================

def _fitness_worker(path_list: List[int], graph: nx.Graph, 
                   weights: Dict[str, float], bw_demand: float) -> float:
    """
    BİR YOLUN KALİTESİNİ HESAPLAR (Multiprocessing uyumlu)
    
    ÇALIŞMA PRENSİBİ:
    ----------------
    1. Düğümleri gez: Processing delay + node reliability topla
    2. Kenarları gez: Link delay + link reliability + bandwidth kontrolü
    3. Bandwidth kısıtı ihlali varsa → float('inf') döndür (geçersiz)
    4. Metrikleri normalize et (0.0-1.0 aralığına)
    5. Ağırlıklı toplam hesapla: w1*delay + w2*reliability + w3*resource
    
    ÖRNEK:
    ------
    Path: [1, 5, 8, 12, 20]
    - Düğüm 5,8,12'nin processing delay'leri toplanır (1,20 hariç - kaynak/hedef)
    - Kenarlar: (1→5), (5→8), (8→12), (12→20) delay'leri toplanır
    - Reliability: -log(0.99 * 0.98 * 0.97 * ...) hesaplanır
    - Bandwidth: min(500, 600, 450, 700) = 450 Mbps (darboğaz)
    - Demand 500 Mbps ise → 450 < 500 → float('inf') (REDDEDİLDİ)
    
    NEDEN -log(reliability)?
    -----------------------
    Reliability değerleri çarpılır (0.99 * 0.98 = 0.9702)
    log(-) ile toplama dönüşür: -log(0.99) + -log(0.98) = -log(0.99*0.98)
    Düşük reliability üssel cezalandırılır: -log(0.5) = 0.69, -log(0.9) = 0.11
    """
    try:
        # Metrik akümülatörleri
        total_delay = 0.0
        reliability_cost = 0.0
        min_bw = float('inf')
        raw_resource_cost = 0.0
        
        source, destination = path_list[0], path_list[-1]
        
        # ADIM 1: Düğüm metrikleri
        for node in path_list:
            # Processing delay: Sadece ara düğümler (proje yönergesi)
            if node != source and node != destination:
                total_delay += float(graph.nodes[node].get('processing_delay', 0.0))
            
            # Node reliability: Tüm düğümler dahil
            nr = float(graph.nodes[node].get('reliability', 0.99))
            reliability_cost += -math.log(max(nr, 0.001))  # Sıfır bölme koruması
        
        # ADIM 2: Kenar metrikleri
        for i in range(len(path_list) - 1):
            u, v = path_list[i], path_list[i+1]
            edge = graph[u][v]
            
            total_delay += edge.get('delay', 1.0)
            reliability_cost += -math.log(max(float(edge.get('reliability', 0.99)), 0.001))
            
            bw = float(edge.get('bandwidth', 1000.0))
            min_bw = min(min_bw, bw)  # Darboğaz tespiti
            raw_resource_cost += (1000.0 / max(bw, 1.0))  # 1Gbps / BW formülü

        # ADIM 3: Bandwidth kısıt kontrolü (sert kısıt)
        if bw_demand > 0 and min_bw < bw_demand:
            return float('inf')  # Yol reddedildi

        # ADIM 4: Normalizasyon (0.0-1.0 aralığı)
        norm_delay = min(total_delay / NormConfig.MAX_DELAY_MS, 1.0)
        norm_rel = min(reliability_cost / 10.0, 1.0)
        norm_resource = min(raw_resource_cost / 200.0, 1.0)

        # ADIM 5: Ağırlıklı toplam (kullanıcı tercihleri)
        return (weights['delay'] * norm_delay + 
                weights['reliability'] * norm_rel + 
                weights['resource'] * norm_resource)

    except Exception:
        return float('inf')

# =============================================================================
# VERİ SINIFLARI
# =============================================================================

@dataclass
class GAResult:
    """Optimizasyon sonuç paketi"""
    path: List[int]                    # Bulunan en iyi yol
    fitness: float                     # Yolun kalite skoru
    generation: int                    # Hangi nesildeoluştu
    computation_time_ms: float         # Hesaplama süresi
    convergence_history: List[float] = field(default_factory=list)  # Grafik için
    diversity_history: List[float] = field(default_factory=list)
    success: bool = True
    parallel_enabled: bool = False
    seed_used: Optional[int] = None    # Reproducibility için kullanılan seed
    
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
            "parallel_enabled": self.parallel_enabled,
            "seed_used": self.seed_used
        }

# =============================================================================
# GENETİK ALGORİTMA - Ana Motor
# =============================================================================

class GeneticAlgorithm:
    """
    Darwin'den Esinlenen Ağ Yönlendirme Optimizatörü
    ------------------------------------------------
    
    TEMEL STRATEJİ:
    - Başlangıç: Çeşitli yollar oluştur (shortest paths + heuristic + random)
    - Evrim: Her nesilde en iyi yollar üreyip yayılır, kötü olanlar elenir
    - Adaptasyon: Diversity düştüğünde mutation rate artar (lokal optimumdan kaç)
    
    PARALEL İŞLEME:
    - Küçük ağlar (<500 düğüm): Seri işleme (overhead > kazanç)
    - Büyük ağlar (≥500 düğüm): Paralel işleme (çoklu CPU core kullanımı)
    - Singleton pool pattern: Tüm GA örnekleri aynı process pool'u paylaşır
    
    ADAPTIVE PARAMETRELER:
    - Popülasyon boyutu ağ büyüklüğüne göre ölçeklenir
    - Mutation rate diversity'e göre dinamik ayarlanır
    - Erken yakınsama ile gereksiz iterasyon engellenir
    """
    
    # Singleton pool (bellek verimliliği)
    _shared_pool = None
    _pool_lock = threading.Lock()
    _pool_refcount = 0
    
    @classmethod
    def get_shared_pool(cls, n_processes=None):
        """Process pool singleton - tüm GA örnekleri paylaşır"""
        with cls._pool_lock:
            if cls._shared_pool is None:
                n_proc = n_processes or multiprocessing.cpu_count()
                cls._shared_pool = multiprocessing.Pool(processes=n_proc)
                logger.info(f"🚀 Process pool: {n_proc} workers")
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
    
    def __init__(self, graph: nx.Graph, population_size: int = None,
                 generations: int = None, mutation_rate: float = None,
                 crossover_rate: float = None, elitism: float = None,
                 tournament_size: int = 5, convergence_threshold: float = 0.001,
                 convergence_generations: int = 20, diversity_threshold: float = 0.1,
                 seed: int = None, use_parallel: str = 'auto',
                 use_standard_metrics: bool = False):
        """
        GA Motoru Başlatma
        -----------------
        
        ADAPTIVE DAVRANIŞLAR:
        - population_size=None → Ağ büyüklüğüne göre otomatik (100→200, 500→260, 1000→500)
        - use_parallel='auto' → 500+ düğümde otomatik paralel
        - mutation_rate=None → Başlangıç: 0.05, düşük diversity'de 2.5x artar
        
        EXPERIMENT MODE:
        - use_standard_metrics=True → MetricsService kullan (ACO/PSO ile adil karşılaştırma)
        - use_standard_metrics=False → Normalize fitness (daha iyi performans)
        """
        if not graph or graph.number_of_nodes() == 0:
            raise ValueError("Graf boş!")
        
        self.graph = graph
        self.graph_size = graph.number_of_nodes()
        
        # Experiment mode kontrolü
        self.use_standard_metrics = use_standard_metrics
        self.metrics_service = MetricsService(graph) if (use_standard_metrics and MetricsService) else None
        
        # Adaptive popülasyon (ağ büyüdükçe artar)
        base_pop = population_size or settings.GA_POPULATION_SIZE
        if not population_size:
            if self.graph_size < 100:
                self.population_size = base_pop
            elif self.graph_size < 500:
                self.population_size = int(base_pop * 1.3)
            else:
                self.population_size = int(base_pop * 2.5)
        else:
            self.population_size = population_size

        # Genetik operatör parametreleri
        self.generations = generations or settings.GA_GENERATIONS
        base_mutation = mutation_rate or settings.GA_MUTATION_RATE
        self.initial_mutation_rate = base_mutation * 1.5 if use_standard_metrics else base_mutation
        self.mutation_rate = self.initial_mutation_rate
        self.crossover_rate = crossover_rate or settings.GA_CROSSOVER_RATE
        self.elitism = elitism or settings.GA_ELITISM
        self.tournament_size = tournament_size
        
        # Yakınsama kontrolü
        self.convergence_threshold = convergence_threshold
        self.convergence_generations = convergence_generations
        self.diversity_threshold = diversity_threshold
        
        # Paralel işleme kararı
        self.use_parallel = (self.graph_size >= GAConfig.PARALLEL_AUTO_ENABLE_NODES) if use_parallel == 'auto' else bool(use_parallel)
        
        # Random seed (None = her çalışmada farklı, int = deterministik)
        self._seed = seed
        if seed is not None:
            random.seed(seed)
        
        # İstatistik takibi
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
        self.diversity_history: List[float] = []
        
        # Performans cache'leri
        self._neighbor_cache = {node: list(graph.neighbors(node)) for node in graph.nodes()}
        self.current_weights: Dict[str, float] = {}
        
        # Popülasyon başlatma stratejisi
        if self.graph_size < GAConfig.PARALLEL_AUTO_ENABLE_NODES:
            self.guided_ratio = GAConfig.SMALL_NET_GUIDED_RATIO
            self.max_init_attempts = GAConfig.SMALL_NET_MAX_INIT_ATTEMPTS
        else:
            self.guided_ratio = GAConfig.LARGE_NET_GUIDED_RATIO
            self.max_init_attempts = GAConfig.LARGE_NET_MAX_INIT_ATTEMPTS

    def optimize(self, source: int, destination: int, 
                weights: Dict[str, float] = None, bandwidth_demand: float = 0.0,
                progress_callback: Optional[Callable[[int, float], None]] = None) -> GAResult:
        """
        EVRİM MOTORU - En İyi Yolu Bul
        ------------------------------
        
        ÇALIŞMA AKIŞI:
        1. Başlangıç popülasyonu oluştur (shortest paths + guided + random)
        2. EVRİM DÖNGÜSÜ (max 100 nesil):
           a) Fitness hesapla (paralel/seri)
           b) En iyi bireyi kaydet (elitizm)
           c) İstatistikleri güncelle (convergence, diversity)
           d) Yakınsama kontrolü (erken durdurma)
           e) Yeni nesil üret (seçilim → çaprazlama → mutasyon)
        3. En iyi yolu döndür
        
        ÖNEMLİ NOKTA:
        Her optimize() çağrısı bağımsızdır:
        - Ağırlıklar güncellenir
        - Cache temizlenir
        - Random state sıfırlanır (seed yoksa)
        
        PROGRESS CALLBACK:
        Gerçek zamanlı görselleştirme için:
        progress_callback(generation: int, best_fitness: float)
        """
        start_time = time.perf_counter()
        
        # Girdileri doğrula
        self._validate_inputs(source, destination, weights)
        
        # Yeni optimizasyon için temiz durum
        self.current_weights = weights or {'delay': 0.33, 'reliability': 0.33, 'resource': 0.34}
        self._cached_shortest_path.cache_clear()
        self.best_fitness_history.clear()
        self.avg_fitness_history.clear()
        self.diversity_history.clear()
        self.mutation_rate = self.initial_mutation_rate
        
        # Random state yönetimi
        if self._seed is None:
            # Stokastik: Her çalışmada farklı seed
            import time as time_module
            if not hasattr(self, '_call_counter'):
                self._call_counter = 0
            self._call_counter += 1
            seed_val = time_module.time_ns() % (2**31) + os.getpid() + self._call_counter
            random.seed(seed_val)
            self._actual_seed = seed_val  # Track for result
            print(f"[GA] Stokastik - seed={seed_val}")
        else:
            self._actual_seed = self._seed
            print(f"[GA] Deterministik - seed={self._seed}")
        
        # Başlangıç popülasyonu
        population = self._initialize_population(source, destination, bandwidth_demand)
        if not population:
            return GAResult([], float('inf'), 0, (time.perf_counter()-start_time)*1000, success=False, seed_used=self._actual_seed)
        
        best_individual, best_fitness, best_generation = None, float('inf'), 0
        stagnation_counter = 0
        pool = self.get_shared_pool() if self.use_parallel else None
        
        # === EVRİM DÖNGÜSÜ ===
        for gen in range(self.generations):
            # 1. Değerlendirme (fitness hesapla)
            fitness_scores = self._evaluate_population(population, bandwidth_demand, pool)
            fitness_scores.sort(key=lambda x: x[1])
            
            # 2. En iyi birey (elitizm)
            current_best_path, current_best_score = fitness_scores[0]
            if current_best_score < best_fitness:
                best_fitness = current_best_score
                best_individual = list(current_best_path)
                best_generation = gen
                stagnation_counter = 0
            else:
                stagnation_counter += 1
            
            # 3. İstatistikler
            self.best_fitness_history.append(best_fitness)
            valid_scores = [s for _, s in fitness_scores if s != float('inf')]
            avg_fit = sum(valid_scores)/len(valid_scores) if valid_scores else float('inf')
            self.avg_fitness_history.append(avg_fit)
            diversity = self._calculate_diversity(population)
            self.diversity_history.append(diversity)
            
            # Progress callback
            if progress_callback:
                try:
                    progress_callback(gen, best_fitness)
                except Exception as e:
                    logger.warning(f"Callback error: {e}")
            
            # 4. Yakınsama kontrolü
            if self._check_convergence(stagnation_counter):
                break
            
            # 5. Yeni nesil
            if gen < self.generations - 1:
                self._adjust_mutation_rate(diversity)
                population = self._evolve(fitness_scores, source, destination, diversity)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        result_path = best_individual if best_individual else [source, destination]
        print(f"[GA] ✓ len={len(result_path)}, fitness={best_fitness:.4f}, t={elapsed:.1f}ms")
        
        return GAResult(path=result_path, fitness=best_fitness, generation=best_generation,
                       computation_time_ms=elapsed, convergence_history=self.best_fitness_history,
                       diversity_history=self.diversity_history, success=(best_fitness != float('inf')),
                       parallel_enabled=self.use_parallel, seed_used=self._actual_seed)

    def _validate_inputs(self, source, destination, weights):
        """Girdi doğrulama"""
        if source not in self.graph or destination not in self.graph:
            raise ValueError("Kaynak/Hedef bulunamadı!")
        if weights and not (0.99 <= sum(weights.values()) <= 1.01):
            raise ValueError("Ağırlıklar toplamı 1.0 olmalı!")

    def _evaluate_population(self, population: List[List[int]], 
                            bw_demand: float, pool=None) -> List[Tuple[List[int], float]]:
        """
        POPÜLASYON DEĞERLENDİRME - Fitness Hesaplama Motoru
        ---------------------------------------------------
        
        STRATEJİ SEÇİMİ:
        - Experiment mode → MetricsService kullan (adil karşılaştırma)
        - Normal mode → Normalize fitness kullan (daha hızlı)
        
        PARALEL vs SERİ:
        - Popülasyon > 200 ve parallel=True → Paralel (multiprocessing.Pool)
        - Aksi halde → Seri (process spawn overhead > kazanç)
        
        NEDEN İKİ MOD?
        - Küçük işler: Process spawn overhead hesaplama süresinden fazla
        - Büyük işler: Paralel işleme 4-8x hızlanma sağlar
        """
        # Experiment mode: MetricsService
        if self.use_standard_metrics and self.metrics_service:
            results = []
            for path in population:
                if bw_demand > 0:  # Bandwidth kontrolü
                    min_bw = min(self.graph[path[i]][path[i+1]].get('bandwidth', 1000.0) 
                               for i in range(len(path)-1) if self.graph.has_edge(path[i], path[i+1]))
                    if min_bw < bw_demand:
                        results.append((path, float('inf')))
                        continue
                fit = self.metrics_service.calculate_weighted_cost(
                    path, self.current_weights['delay'], 
                    self.current_weights['reliability'], 
                    self.current_weights['resource'])
                results.append((path, fit))
            return results
        
        # Normal mode: Normalize fitness
        should_parallel = pool and self.use_parallel and len(population) > GAConfig.PARALLEL_MIN_POPULATION
        
        if should_parallel:
            # Paralel işleme (büyük popülasyonlar)
            worker_func = partial(_fitness_worker, graph=self.graph, 
                                weights=self.current_weights, bw_demand=bw_demand)
            fitness_values = pool.map(worker_func, population, chunksize=GAConfig.POOL_CHUNKSIZE)
            return list(zip(population, fitness_values))
        else:
            # Seri işleme (küçük popülasyonlar)
            return [(path, _fitness_worker(path, self.graph, self.current_weights, bw_demand)) 
                   for path in population]

    @lru_cache(maxsize=5000)
    def _cached_shortest_path(self, src: int, dst: int) -> Tuple[int]:
        """Shortest path cache (performans optimizasyonu)"""
        try:
            return tuple(nx.shortest_path(self.graph, src, dst))
        except nx.NetworkXNoPath:
            return ()

    def _initialize_population(self, source: int, destination: int, 
                              bandwidth_demand: float = 0.0) -> List[List[int]]:
        """
        BAŞLANGIÇ POPÜLASYONU - Çeşitli ve Kaliteli
        -------------------------------------------
        
        ÇOKLU STRATEJİ:
        1. Baseline shortest paths (hop, delay, reliability bazlı)
        2. Fitness-based guided paths (en iyi 50'den en iyi %50'si)
        3. Heuristic guided walks (hub düğümlere yönelir)
        4. Random walks (keşif için)
        
        NEDEN KARIŞIK BAŞLANGIÇ?
        - Sadece shortest path → Lokal optimumda kalır
        - Sadece random → Yavaş yakınsama
        - Karışık → Hızlı başlangıç + geniş keşif
        
        BANDWIDTH FİLTRELEME:
        bandwidth_demand > 0 ise sadece yeterli BW'ye sahip edge'ler kullanılır.
        Bu sayede baştan geçersiz yollar üretilmez.
        """
        population, seen_paths = [], set()
        
        # Bandwidth filtreli graf
        if bandwidth_demand > 0:
            valid_edges = [(u,v) for u,v,d in self.graph.edges(data=True) 
                          if d.get('bandwidth', 0) >= bandwidth_demand]
            init_graph = self.graph.edge_subgraph(valid_edges).copy()
        else:
            init_graph = self.graph
        
        if not nx.has_path(init_graph, source, destination):
            return []
        
        # 1. Baseline shortest paths (farklı weight'lerle)
        for weight_type in ['weight', 'delay', None]:  # None = hop-based
            try:
                sp = nx.shortest_path(init_graph, source, destination, weight=weight_type)
                if tuple(sp) not in seen_paths:
                    population.append(list(sp))
                    seen_paths.add(tuple(sp))
            except:
                pass
        
        # 2. Reliability-based shortest path
        try:
            rel_graph = init_graph.copy() if bandwidth_demand > 0 else self.graph.copy()
            for u,v in rel_graph.edges():
                rel_graph[u][v]['temp_weight'] = 1.0 / (rel_graph[u][v].get('reliability', 0.99) + 0.01)
            rel_sp = nx.shortest_path(rel_graph, source, destination, weight='temp_weight')
            if tuple(rel_sp) not in seen_paths:
                population.append(list(rel_sp))
                seen_paths.add(tuple(rel_sp))
        except:
            pass
        
        # 3. Fitness-based guided initialization
        if self.current_weights:
            candidates = []
            for _ in range(min(50, self.population_size * 2)):
                path = (self._generate_guided_path(source, destination, bandwidth_demand) 
                       if random.random() < self.guided_ratio 
                       else self._generate_random_path(source, destination, bandwidth_demand))
                if path and tuple(path) not in seen_paths:
                    fit = (self.metrics_service.calculate_weighted_cost(path, **self.current_weights, bandwidth_demand=bandwidth_demand)
                          if (self.use_standard_metrics and self.metrics_service)
                          else _fitness_worker(path, self.graph, self.current_weights, bandwidth_demand))
                    candidates.append((fit, path))
            
            # En iyi %50'si
            candidates.sort(key=lambda x: x[0])
            for _, path in candidates[:len(candidates)//2]:
                if tuple(path) not in seen_paths and len(population) < self.population_size:
                    population.append(path)
                    seen_paths.add(tuple(path))
        
        # 4. Kalan yerleri doldur
        attempts, max_attempts = 0, self.population_size * self.max_init_attempts
        while len(population) < self.population_size and attempts < max_attempts:
            path = (self._generate_guided_path(source, destination, bandwidth_demand)
                   if random.random() < self.guided_ratio
                   else self._generate_random_path(source, destination, bandwidth_demand))
            if path and tuple(path) not in seen_paths:
                population.append(path)
                seen_paths.add(tuple(path))
            attempts += 1
        
        # Son çare: İlk yolu kopyala
        if population:
            while len(population) < self.population_size:
                population.append(list(population[0]))
        
        return population

    def _generate_path(self, source: int, destination: int, 
                       bandwidth_demand: float = 0.0, guided: bool = False, max_len: int = 50) -> Optional[List[int]]:
        """
        YOL OLUŞTURMA - Guided (hub-yönelimli) veya Random (rastgele yürüyüş)
        ---------------------------------------------------------------------
        
        guided=True: Rulet tekerleği ile yüksek degree'li düğümlere yönelir
        guided=False: Tamamen rastgele komşu seçimi (keşif için)
        """
        path, current, visited = [source], source, {source}
        
        for _ in range(max_len):
            if current == destination:
                return path
            
            # Bandwidth filtreli komşular
            neighbors = [n for n in self._neighbor_cache[current] 
                        if n not in visited and 
                        (bandwidth_demand == 0 or self.graph[current][n].get('bandwidth', 0) >= bandwidth_demand)]
            
            if not neighbors:
                return None
            if destination in neighbors:
                path.append(destination)
                return path
            
            # Sonraki düğüm seçimi
            if guided:
                # Rulet tekerleği: Yüksek degree = yüksek seçilme şansı
                degrees = [self.graph.degree(n) for n in neighbors]
                total = sum(degrees)
                if total > 0:
                    pick = random.uniform(0, total)
                    curr_sum = 0
                    for i, deg in enumerate(degrees):
                        curr_sum += deg
                        if curr_sum >= pick:
                            current = neighbors[i]
                            break
                else:
                    current = random.choice(neighbors)
            else:
                current = random.choice(neighbors)
            
            path.append(current)
            visited.add(current)
        
        return None
    
    # Backward compatibility wrappers
    def _generate_guided_path(self, src, dst, bw=0.0, max_len=50):
        return self._generate_path(src, dst, bw, guided=True, max_len=max_len)
    
    def _generate_random_path(self, src, dst, bw=0.0, max_len=50):
        return self._generate_path(src, dst, bw, guided=False, max_len=max_len)

    def _evolve(self, scores, src, dst, diversity):
        """
        YENİ NESİL ÜRET - Seçilim → Çaprazlama → Mutasyon
        -------------------------------------------------
        
        ADIMLAR:
        1. Elitizm: En iyi %10'u direkt aktar (iyi genleri koru)
        2. Üreme döngüsü (kalan %90 için):
           a) Tournament selection ile 2 ebeveyn seç
           b) %80 ihtimalle crossover (çocuk oluştur)
           c) Mutation rate ihtimaliyle mutate et
           d) Geçerli çocukları yeni popülasyona ekle
        """
        new_pop = []
        elite_count = max(1, int(self.population_size * self.elitism))
        new_pop.extend([list(s[0]) for s in scores[:elite_count]])
        
        while len(new_pop) < self.population_size:
            p1, p2 = self._tournament_select(scores), self._tournament_select(scores)
            c1, c2 = (self._edge_based_crossover(p1, p2, src, dst) 
                     if random.random() < self.crossover_rate 
                     else (list(p1), list(p2)))
            
            op = self._select_mutation_operator(diversity)
            if random.random() < self.mutation_rate: c1 = op(c1, src, dst)
            if random.random() < self.mutation_rate: c2 = op(c2, src, dst)
            
            for c in [c1, c2]:
                if len(new_pop) < self.population_size and self._is_valid(c):
                    new_pop.append(c)
        return new_pop

    def _adjust_mutation_rate(self, diversity: float):
        """Diversity düştüğünde mutation rate artır (lokal optimumdan kaç)"""
        if diversity < self.diversity_threshold:
            max_mut = 0.4 if self.use_standard_metrics else 0.3
            self.mutation_rate = min(max_mut, self.initial_mutation_rate * 2.5)
        else:
            self.mutation_rate = self.initial_mutation_rate

    def _tournament_select(self, scores):
        """Tournament: K bireyden en iyisini seç"""
        k = min(self.tournament_size, len(scores))
        return list(min(random.sample(scores, k), key=lambda x: x[1])[0])

    def _edge_based_crossover(self, p1, p2, src, dst):
        """Çaprazlama: Ortak düğümde kes ve değiştir"""
        common = set(p1[1:-1]).intersection(p2[1:-1])
        if not common: return list(p1), list(p2)
        node = random.choice(list(common))
        try:
            i1, i2 = p1.index(node), p2.index(node)
            return (self._repair_path(p1[:i1+1] + p2[i2+1:], src, dst),
                   self._repair_path(p2[:i2+1] + p1[i1+1:], src, dst))
        except ValueError:
            return list(p1), list(p2)

    def _mutate(self, path: List[int], src: int, dst: int, diversity: float) -> List[int]:
        """
        BİRLEŞİK MUTASYON - Diversity'e göre strateji seçimi
        ----------------------------------------------------
        
        diversity < 0.05: Segment replacement (agresif - kesit değiştir)
        diversity < 0.15: Node insertion (detour ekle)
        diversity >= 0.15: Node replacement (tek düğüm değiştir)
        """
        if diversity < 0.05 and len(path) >= 5:
            # SEGMENT REPLACEMENT - Agresif mutasyon
            idx1 = random.randint(1, len(path)-4)
            idx2 = random.randint(idx1+2, len(path)-1) if len(path) > 4 else len(path)-1
            try:
                via = random.choice([n for n in self._neighbor_cache[path[idx1]] if n not in path[idx1+1:idx2]])
                sp = self._cached_shortest_path(via, path[idx2])
                if sp: return self._repair_path(path[:idx1+1] + list(sp) + path[idx2+1:], src, dst)
            except: pass
            
        elif diversity < 0.15 and len(path) >= 3:
            # NODE INSERTION - Detour ekle
            idx = random.randint(1, len(path)-1)
            candidates = set(self._neighbor_cache[path[idx-1]]) - set(path)
            if candidates:
                detour = random.choice(list(candidates))
                sp = self._cached_shortest_path(detour, path[idx])
                if sp: return path[:idx] + list(sp) + path[idx+1:]
                
        elif len(path) >= 4:
            # NODE REPLACEMENT - Tek düğüm değiştir
            idx = random.randint(1, len(path)-2)
            opts = (set(self._neighbor_cache[path[idx-1]]) & set(self._neighbor_cache[path[idx+1]])) - set(path)
            if opts: path[idx] = random.choice(list(opts))
        
        return path
    
    # Backward compatibility - eski operatör referansları için
    def _select_mutation_operator(self, diversity: float):
        return lambda path, src, dst: self._mutate(path, src, dst, diversity)
    
    def _mutate_node_replacement(self, path, src, dst):
        return self._mutate(path, src, dst, 0.2)
    
    def _mutate_segment_replacement(self, path, src, dst):
        return self._mutate(path, src, dst, 0.01)
    
    def _mutate_node_insertion(self, path, src, dst):
        return self._mutate(path, src, dst, 0.1)

    def _repair_path(self, path, src, dst):
        """Yol onarımı: Tekrar/kopukluk düzelt"""
        if not path or len(path) < 2: return path
        clean = []
        seen = set()
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
        """Yol geçerlilik kontrolü"""
        return (path and len(path) >= 2 and len(path) == len(set(path)) and
               all(self.graph.has_edge(path[i], path[i+1]) for i in range(len(path)-1)))

    def _calculate_diversity(self, population):
        """Popülasyon çeşitliliği (Jaccard Distance)"""
        if len(population) < 2: return 0.0
        sample = random.sample(population, min(max(30, int(len(population)*0.15)), 80))
        total, count = 0, 0
        for i in range(len(sample)):
            for j in range(i+1, len(sample)):
                u = len(set(sample[i]) | set(sample[j]))
                if u > 0:
                    total += 1.0 - (len(set(sample[i]) & set(sample[j])) / u)
                    count += 1
        return total / count if count > 0 else 0.0

    def _check_convergence(self, stagnation):
        """Yakınsama kontrolü (erken durdurma)"""
        return (stagnation >= self.convergence_generations or
               (len(self.best_fitness_history) > 10 and
                max(self.best_fitness_history[-10:]) - min(self.best_fitness_history[-10:]) < self.convergence_threshold))

    def get_statistics(self) -> Dict[str, Any]:
        return {"best_fitness_history": self.best_fitness_history,
                "diversity_history": self.diversity_history,
                "final_best_fitness": self.best_fitness_history[-1] if self.best_fitness_history else None,
                "parallel_enabled": self.use_parallel}
    
    def reset_statistics(self):
        self.best_fitness_history.clear()
        self.diversity_history.clear()
        self._cached_shortest_path.cache_clear()



"""
Kod : ~370 satır
Yorum : ~430 satır

Erkan TURGUT
"""