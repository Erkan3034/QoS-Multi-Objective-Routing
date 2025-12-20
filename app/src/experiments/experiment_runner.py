"""
Experiment Runner

PDF Gereksinimleri:
- En az 20 farklı (S, D, B) örneği
- En az 2 farklı algoritma kıyaslama
- En az 5 tekrar: ortalama, std, min, max raporu
- Başarısız/uygunsuz örnekler gerekçeleriyle raporlanmalı
- Çalışma süresi (zorunlu)
- Ölçeklenebilirlik analizi (opsiyonel)
"""
import time
import statistics
from typing import List, Dict, Any, Optional, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime
import networkx as nx

from src.core.config import Settings
from src.core.logger import logger
from src.services.metrics_service import MetricsService
from src.algorithms.genetic_algorithm import GeneticAlgorithm
from src.algorithms.aco import AntColonyOptimization
from src.algorithms.pso import ParticleSwarmOptimization
from src.algorithms.simulated_annealing import SimulatedAnnealing
from src.algorithms.q_learning import QLearning
from src.algorithms.sarsa import SARSA
from src.experiments.test_cases import TestCase, BandwidthConstraintChecker
from src.core.config import settings


# =========================================================================
# FAILURE REASONS - Başarısızlık Nedenleri
# =========================================================================

class FailureReason:
    """Standart başarısızlık nedenleri."""
    NO_PATH = "Kaynak ve hedef arasında yol bulunamadı"
    BANDWIDTH_INSUFFICIENT = "Bant genişliği yetersiz"
    TIMEOUT = "Algoritma zaman aşımına uğradı"
    INVALID_SOURCE = "Geçersiz kaynak düğüm"
    INVALID_DESTINATION = "Geçersiz hedef düğüm"
    SAME_NODE = "Kaynak ve hedef aynı düğüm"
    ALGORITHM_ERROR = "Algoritma hatası"


# =========================================================================
# RESULT DATA CLASSES
# =========================================================================

@dataclass
class AlgorithmResult:
    """Tek bir algoritma çalıştırma sonucu."""
    algorithm_name: str
    path: List[int]
    weighted_cost: float
    total_delay: float
    total_reliability: float
    resource_cost: float
    computation_time_ms: float
    success: bool
    bandwidth_satisfied: bool = True
    path_min_bandwidth: float = 0.0
    required_bandwidth: float = 0.0
    error: Optional[str] = None
    failure_reason: Optional[str] = None


@dataclass
class FailedTestCase:
    """
    Başarısız test case raporu.
    
    PDF Gereksinimi: Başarısız/uygunsuz örnekler gerekçeleriyle raporlanmalı
    """
    test_case_id: int
    source: int
    destination: int
    bandwidth_requirement: float
    algorithm_name: str
    failure_reason: str
    details: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "test_case_id": self.test_case_id,
            "source": self.source,
            "destination": self.destination,
            "bandwidth_requirement": self.bandwidth_requirement,
            "algorithm": self.algorithm_name,
            "failure_reason": self.failure_reason,
            "details": self.details
        }


@dataclass
class RepeatResult:
    """
    Tekrarlı deney sonucu.
    
    PDF Gereksinimi: En az 5 tekrar yapılıp ortalama, std, min, max raporu
    """
    test_case_id: int
    algorithm_name: str
    source: int
    destination: int
    bandwidth_requirement: float
    results: List[AlgorithmResult]
    
    # İstatistiklerr
    avg_cost: float = 0.0
    std_cost: float = 0.0
    min_cost: float = 0.0
    max_cost: float = 0.0
    avg_time_ms: float = 0.0
    success_rate: float = 0.0
    bandwidth_satisfaction_rate: float = 0.0
    
    # Başarısızlık detayları
    failures: List[FailedTestCase] = field(default_factory=list)
    
    def calculate_stats(self):
        """İstatistikleri hesaplar."""
        successful = [r for r in self.results if r.success]
        bandwidth_ok = [r for r in successful if r.bandwidth_satisfied]
        
        if successful:
            costs = [r.weighted_cost for r in successful]
            times = [r.computation_time_ms for r in successful]
            
            self.avg_cost = statistics.mean(costs)
            self.std_cost = statistics.stdev(costs) if len(costs) > 1 else 0.0
            self.min_cost = min(costs)
            self.max_cost = max(costs)
            self.avg_time_ms = statistics.mean(times)
            self.success_rate = len(successful) / len(self.results)
            self.bandwidth_satisfaction_rate = len(bandwidth_ok) / len(self.results)
        else:
            self.success_rate = 0.0
            self.bandwidth_satisfaction_rate = 0.0
        
        # Başarısız sonuçları kaydet
        for r in self.results:
            if not r.success or not r.bandwidth_satisfied:
                reason = r.failure_reason or (
                    FailureReason.BANDWIDTH_INSUFFICIENT if not r.bandwidth_satisfied 
                    else FailureReason.ALGORITHM_ERROR
                )
                details = None
                if not r.bandwidth_satisfied:
                    details = f"Min bandwidth: {r.path_min_bandwidth:.1f} Mbps < Required: {r.required_bandwidth:.1f} Mbps"
                
                self.failures.append(FailedTestCase(
                    test_case_id=self.test_case_id,
                    source=self.source,
                    destination=self.destination,
                    bandwidth_requirement=self.bandwidth_requirement,
                    algorithm_name=self.algorithm_name,
                    failure_reason=reason,
                    details=details
                ))
    
    def to_dict(self) -> Dict:
        return {
            "test_case_id": self.test_case_id,
            "algorithm": self.algorithm_name,
            "source": self.source,
            "destination": self.destination,
            "bandwidth_requirement": self.bandwidth_requirement,
            "n_runs": len(self.results),
            "success_rate": round(self.success_rate, 2),
            "bandwidth_satisfaction_rate": round(self.bandwidth_satisfaction_rate, 2),
            "avg_cost": round(self.avg_cost, 6),
            "std_cost": round(self.std_cost, 6),
            "min_cost": round(self.min_cost, 6),
            "max_cost": round(self.max_cost, 6),
            "avg_time_ms": round(self.avg_time_ms, 2),
            "failures": [f.to_dict() for f in self.failures]
        }


@dataclass
class FailureReport:
    """
    Tüm başarısız testlerin raporu.
    
    PDF Gereksinimi: Başarısız/uygunsuz örnekler gerekçeleriyle raporlanmalı
    """
    failed_cases: List[FailedTestCase] = field(default_factory=list)
    
    def add_failures(self, failures: List[FailedTestCase]):
        self.failed_cases.extend(failures)
    
    def get_summary(self) -> Dict:
        """Başarısızlık özeti."""
        by_reason = {}
        by_algorithm = {}
        
        for f in self.failed_cases:
            # Nedene göre grupla
            if f.failure_reason not in by_reason:
                by_reason[f.failure_reason] = 0
            by_reason[f.failure_reason] += 1
            
            # Algoritmaya göre grupla
            if f.algorithm_name not in by_algorithm:
                by_algorithm[f.algorithm_name] = 0
            by_algorithm[f.algorithm_name] += 1
        
        return {
            "total_failures": len(self.failed_cases),
            "by_reason": by_reason,
            "by_algorithm": by_algorithm,
            "details": [f.to_dict() for f in self.failed_cases]
        }


@dataclass
class ScalabilityResult:
    """
    Ölçeklenebilirlik analizi sonucu.
    
    PDF Gereksinimi: Ölçeklenebilirlik analizi (opsiyonel)
    """
    node_counts: List[int]
    algorithm_times: Dict[str, List[float]]  # algorithm -> [time per node count]
    
    def to_dict(self) -> Dict:
        return {
            "node_counts": self.node_counts,
            "algorithm_times": {
                algo: [round(t, 2) for t in times]
                for algo, times in self.algorithm_times.items()
            }
        }


@dataclass
class ExperimentResult:
    """
    Tam deney sonucu.
    
    PDF Gereksinimleri:
    - 20+ test case
    - 2+ algoritma karşılaştırma
    - 5+ tekrar
    - Çalışma süresi
    - Başarısızlık raporu
    """
    test_cases: List[TestCase]
    algorithm_results: Dict[str, List[RepeatResult]]  # algorithm -> [results per test]
    total_time_sec: float
    failure_report: FailureReport
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    scalability_result: Optional[ScalabilityResult] = None
    
    def get_comparison_table(self) -> List[Dict]:
        """
        Karşılaştırma tablosu oluşturur.
        
        PDF Gereksinimi: En az 2 farklı algoritma kıyaslama
        """
        table = []
        
        for algo_name, results in self.algorithm_results.items():
            successful_results = [r for r in results if r.success_rate > 0]
            
            if successful_results:
                avg_costs = [r.avg_cost for r in successful_results]
                avg_times = [r.avg_time_ms for r in successful_results]
                success_rates = [r.success_rate for r in results]
                bw_rates = [r.bandwidth_satisfaction_rate for r in results]
                
                table.append({
                    "algorithm": algo_name,
                    "n_tests": len(results),
                    "success_rate": round(statistics.mean(success_rates), 2),
                    "bandwidth_satisfaction_rate": round(statistics.mean(bw_rates), 2),
                    "overall_avg_cost": round(statistics.mean(avg_costs), 6),
                    "overall_std_cost": round(statistics.stdev(avg_costs), 6) if len(avg_costs) > 1 else 0,
                    "overall_avg_time_ms": round(statistics.mean(avg_times), 2),
                    "best_cost": round(min(r.min_cost for r in successful_results), 6),
                    "worst_cost": round(max(r.max_cost for r in successful_results), 6)
                })
            else:
                table.append({
                    "algorithm": algo_name,
                    "n_tests": len(results),
                    "success_rate": 0.0,
                    "bandwidth_satisfaction_rate": 0.0,
                    "overall_avg_cost": float('inf'),
                    "overall_std_cost": 0,
                    "overall_avg_time_ms": 0,
                    "best_cost": float('inf'),
                    "worst_cost": float('inf')
                })
        
        # Ortalama maliyete göre sırala
        table.sort(key=lambda x: x.get("overall_avg_cost", float('inf')))
        
        return table
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "n_test_cases": len(self.test_cases),
            "n_algorithms": len(self.algorithm_results),
            "total_time_sec": round(self.total_time_sec, 2),
            "comparison_table": self.get_comparison_table(),
            "failure_report": self.failure_report.get_summary(),
            "detailed_results": {
                algo: [r.to_dict() for r in results]
                for algo, results in self.algorithm_results.items()
            },
            "scalability": self.scalability_result.to_dict() if self.scalability_result else None
        }


# =========================================================================
# EXPERIMENT RUNNER
# =========================================================================

class ExperimentRunner:
    """
    Deney çalıştırıcı.
    
    PDF Gereksinimleri:
    - En az 20 farklı (S, D, B) örneği
    - En az 2 farklı algoritma kıyaslama
    - En az 5 tekrar
    - Başarısız örnekler gerekçeleriyle raporlanmalı
    - Çalışma süresi (zorunlu)
    """
    
    ALGORITHMS = {
        "GeneticAlgorithm": GeneticAlgorithm,
        "AntColonyOptimization": AntColonyOptimization,
        "ParticleSwarmOptimization": ParticleSwarmOptimization,
        "SimulatedAnnealing": SimulatedAnnealing,
        "QLearning": QLearning,
        "SARSA": SARSA
    }
    
    def __init__(
        self,
        graph: nx.Graph,
        n_repeats: int = None,
        timeout_sec: int = None,
        algorithms: List[str] = None,
        progress_callback: Callable[[int, int, str], None] = None
    ):
        """
        ExperimentRunner oluşturur.
        
        Args:
            graph: NetworkX graf objesi
            n_repeats: Her test için tekrar sayısı (varsayılan: 5, PDF gereksinimi)
            timeout_sec: Algoritma timeout (saniye)
            algorithms: Çalıştırılacak algoritmalar (varsayılan: tümü, PDF: en az 2)
            progress_callback: İlerleme callback'i (current, total, message)
        """
        self.graph = graph
        self.n_repeats = n_repeats or settings.EXPERIMENT_N_REPEATS
        self.timeout_sec = timeout_sec or settings.EXPERIMENT_TIMEOUT_SEC
        self.metrics_service = MetricsService(graph)
        self.bandwidth_checker = BandwidthConstraintChecker(graph)
        self.progress_callback = progress_callback
        
        # Kullanılacak algoritmalar (PDF: en az 2)
        if algorithms:
            self.algorithms = {k: v for k, v in self.ALGORITHMS.items() if k in algorithms}
        else:
            self.algorithms = self.ALGORITHMS
    
    def _report_progress(self, current: int, total: int, message: str):
        """İlerleme raporla."""
        if self.progress_callback:
            self.progress_callback(current, total, message)
    
    def run_experiments(self, test_cases: List[TestCase]) -> ExperimentResult:
        """
        Tüm deneyleri çalıştırır.
        
        PDF Gereksinimleri:
        - 20+ farklı test case
        - 5+ tekrar
        - Başarısızlık raporlaması
        - Çalışma süresi
        
        Args:
            test_cases: Test case listesi (en az 20)
        
        Returns:
            ExperimentResult objesi
        """
        start_time = time.time()
        failure_report = FailureReport()
        
        algorithm_results: Dict[str, List[RepeatResult]] = {
            name: [] for name in self.algorithms
        }
        
        total_steps = len(test_cases) * len(self.algorithms)
        current_step = 0
        
        print(f"\n{'='*60}")
        print(f"DENEY BAŞLIYOR")
        print(f"Test sayısı: {len(test_cases)}")
        print(f"Algoritma sayısı: {len(self.algorithms)}")
        print(f"Tekrar sayısı: {self.n_repeats}")
        print(f"{'='*60}\n")
        
        for i, test_case in enumerate(test_cases):
            print(f"Test {i+1}/{len(test_cases)}: {test_case.description}")
            
            for algo_name, AlgoClass in self.algorithms.items():
                current_step += 1
                self._report_progress(
                    current_step, 
                    total_steps,
                    f"Test {i+1}/{len(test_cases)} - {algo_name}"
                )
                
                repeat_result = self._run_repeated_test(
                    test_case, algo_name, AlgoClass
                )
                algorithm_results[algo_name].append(repeat_result)
                
                # Başarısızlıkları rapora ekle
                failure_report.add_failures(repeat_result.failures)
        
        total_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"DENEY TAMAMLANDI")
        print(f"Toplam süre: {total_time:.2f} saniye")
        print(f"Başarısız test sayısı: {len(failure_report.failed_cases)}")
        print(f"{'='*60}\n")
        
        return ExperimentResult(
            test_cases=test_cases,
            algorithm_results=algorithm_results,
            total_time_sec=total_time,
            failure_report=failure_report
        )
    
    def _run_repeated_test(
        self,
        test_case: TestCase,
        algo_name: str,
        AlgoClass: Type
    ) -> RepeatResult:
        """
        Tek test case için tekrarlı deney çalıştırır.
        
        PDF Gereksinimi: En az 5 tekrar
        """
        results = []
        
        for i in range(self.n_repeats):
            result = self._run_single_test(test_case, algo_name, AlgoClass, seed=i)
            results.append(result)
        
        repeat_result = RepeatResult(
            test_case_id=test_case.id,
            algorithm_name=algo_name,
            source=test_case.source,
            destination=test_case.destination,
            bandwidth_requirement=test_case.bandwidth_requirement,
            results=results
        )
        repeat_result.calculate_stats()
        
        return repeat_result
    
    def _run_single_test(
        self,
        test_case: TestCase,
        algo_name: str,
        AlgoClass: Type,
        seed: int = None
    ) -> AlgorithmResult:
        """
        Tek bir test çalıştırır.
        
        B (bandwidth) kısıtını kontrol eder.
        """
        # Ön kontroller
        if test_case.source == test_case.destination:
            return AlgorithmResult(
                algorithm_name=algo_name,
                path=[],
                weighted_cost=float('inf'),
                total_delay=0,
                total_reliability=0,
                resource_cost=0,
                computation_time_ms=0,
                success=False,
                failure_reason=FailureReason.SAME_NODE
            )
        
        if test_case.source not in self.graph.nodes():
            return AlgorithmResult(
                algorithm_name=algo_name,
                path=[],
                weighted_cost=float('inf'),
                total_delay=0,
                total_reliability=0,
                resource_cost=0,
                computation_time_ms=0,
                success=False,
                failure_reason=FailureReason.INVALID_SOURCE
            )
        
        if test_case.destination not in self.graph.nodes():
            return AlgorithmResult(
                algorithm_name=algo_name,
                path=[],
                weighted_cost=float('inf'),
                total_delay=0,
                total_reliability=0,
                resource_cost=0,
                computation_time_ms=0,
                success=False,
                failure_reason=FailureReason.INVALID_DESTINATION
            )
        
        try:
            # Algoritma oluştur
            # [FAIR COMPARISON] GA ve ACO için standard metrics kullan
            # Bu sayede tüm algoritmalar aynı fitness fonksiyonunu kullanır
            algo_kwargs = {"graph": self.graph, "seed": seed}
            if algo_name == "GeneticAlgorithm":
                algo_kwargs["use_standard_metrics"] = True
            elif algo_name == "AntColonyOptimization":
                # ACO zaten MetricsService kullanıyor, değişiklik gerekmez
                pass
            
            algo = AlgoClass(**algo_kwargs)
            
            # Optimizasyonu çalıştır
            start_time = time.perf_counter()
            result = algo.optimize(
                source=test_case.source,
                destination=test_case.destination,
                weights=test_case.weights
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Yol bulunamadı
            if not result.path or len(result.path) < 2:
                return AlgorithmResult(
                    algorithm_name=algo_name,
                    path=[],
                    weighted_cost=float('inf'),
                    total_delay=0,
                    total_reliability=0,
                    resource_cost=0,
                    computation_time_ms=elapsed_ms,
                    success=False,
                    failure_reason=FailureReason.NO_PATH
                )
            
            # Bant genişliği kontrolü (B kısıtı)
            path_min_bandwidth = self.bandwidth_checker.get_path_min_bandwidth(result.path)
            bandwidth_satisfied = path_min_bandwidth >= test_case.bandwidth_requirement
            
            # Metrikleri hesapla
            metrics = self.metrics_service.calculate_all(
                result.path,
                test_case.weights['delay'],
                test_case.weights['reliability'],
                test_case.weights['resource']
            )
            
            return AlgorithmResult(
                algorithm_name=algo_name,
                path=result.path,
                weighted_cost=metrics.weighted_cost,
                total_delay=metrics.total_delay,
                total_reliability=metrics.total_reliability,
                resource_cost=metrics.resource_cost,
                computation_time_ms=elapsed_ms,
                success=True,
                bandwidth_satisfied=bandwidth_satisfied,
                path_min_bandwidth=path_min_bandwidth,
                required_bandwidth=test_case.bandwidth_requirement,
                failure_reason=None if bandwidth_satisfied else FailureReason.BANDWIDTH_INSUFFICIENT
            )
        
        except Exception as e:
            return AlgorithmResult(
                algorithm_name=algo_name,
                path=[],
                weighted_cost=float('inf'),
                total_delay=0,
                total_reliability=0,
                resource_cost=0,
                computation_time_ms=0,
                success=False,
                failure_reason=f"{FailureReason.ALGORITHM_ERROR}: {str(e)}"
            )
    
    def run_quick_comparison(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None,
        bandwidth_requirement: float = 100.0
    ) -> Dict[str, Any]:
        """
        Hızlı karşılaştırma yapar (tek test, tekrarsız).
        
        Args:
            source: Kaynak düğüm (S)
            destination: Hedef düğüm (D)
            weights: Ağırlıklar
            bandwidth_requirement: Bant genişliği gereksinimi (B)
        
        Returns:
            Karşılaştırma sonucu
        """
        weights = weights or {"delay": 0.33, "reliability": 0.33, "resource": 0.34}
        
        test_case = TestCase(
            id=1,
            source=source,
            destination=destination,
            bandwidth_requirement=bandwidth_requirement,
            weights=weights,
            description="Quick comparison"
        )
        
        results = {}
        failures = []
        
        for algo_name, AlgoClass in self.algorithms.items():
            result = self._run_single_test(test_case, algo_name, AlgoClass)
            results[algo_name] = {
                "path": result.path,
                "weighted_cost": result.weighted_cost,
                "computation_time_ms": result.computation_time_ms,
                "success": result.success,
                "bandwidth_satisfied": result.bandwidth_satisfied,
                "path_min_bandwidth": result.path_min_bandwidth
            }
            
            if not result.success or not result.bandwidth_satisfied:
                failures.append({
                    "algorithm": algo_name,
                    "failure_reason": result.failure_reason
                })
        
        # En iyi algoritmayı bul (hem başarılı hem bandwidth'i karşılayan)
        valid_results = {k: v for k, v in results.items() 
                        if v["success"] and v["bandwidth_satisfied"]}
        best_algo = min(valid_results, key=lambda k: valid_results[k]["weighted_cost"]) if valid_results else None
        
        return {
            "source": source,
            "destination": destination,
            "bandwidth_requirement": bandwidth_requirement,
            "weights": weights,
            "results": results,
            "best_algorithm": best_algo,
            "best_cost": results[best_algo]["weighted_cost"] if best_algo else None,
            "failures": failures
        }
    
    @staticmethod
    def run_scalability_analysis(
        node_counts: List[int] = None,
        connection_prob: float = 0.4,
        seed: int = 42,
        progress_callback: Callable[[int, int, str], None] = None
    ) -> ScalabilityResult:
        """
        Ölçeklenebilirlik analizi çalıştırır.
        
        PDF Gereksinimi: Ölçeklenebilirlik analizi (opsiyonel)
        
        Args:
            node_counts: Test edilecek düğüm sayıları
            connection_prob: Bağlantı olasılığı
            seed: Rastgele seed
            progress_callback: İlerleme callback'i
        
        Returns:
            ScalabilityResult objesi
        """
        from src.services.graph_service import GraphService
        
        if node_counts is None:
            node_counts = [50, 100, 150, 200, 250]
        
        # Sadece hızlı algoritmalar kullan (RL algoritmalar çok yavaş)
        fast_algorithms = {
            "GeneticAlgorithm": GeneticAlgorithm,
            "AntColonyOptimization": AntColonyOptimization,
            "ParticleSwarmOptimization": ParticleSwarmOptimization,
            "SimulatedAnnealing": SimulatedAnnealing,
        }
        
        algorithm_times: Dict[str, List[float]] = {
            name: [] for name in fast_algorithms
        }
        
        total_steps = len(node_counts) * len(fast_algorithms)
        current_step = 0
        
        print(f"\n{'='*60}")
        print("ÖLÇEKLENEBİLİRLİK ANALİZİ")
        print(f"Düğüm sayıları: {node_counts}")
        print(f"{'='*60}\n")
        
        for n in node_counts:
            print(f"Test: n={n} düğüm...")
            
            # Graf oluştur
            graph_service = GraphService(seed=seed)
            graph = graph_service.generate_graph(n, connection_prob)
            
            # Test için weights
            weights = {"delay": 0.33, "reliability": 0.33, "resource": 0.34}
            
            for algo_name, AlgoClass in fast_algorithms.items():
                current_step += 1
                if progress_callback:
                    progress_callback(current_step, total_steps, f"n={n} - {algo_name}")
                
                try:
                    algo = AlgoClass(graph=graph, seed=seed)
                    
                    start_time = time.perf_counter()
                    algo.optimize(
                        source=0,
                        destination=n-1,
                        weights=weights
                    )
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    
                    algorithm_times[algo_name].append(elapsed_ms)
                    print(f"  {algo_name}: {elapsed_ms:.2f} ms")
                except Exception as e:
                    algorithm_times[algo_name].append(-1)  # Hata durumunda -1
                    print(f"  {algo_name}: HATA - {str(e)}")
        
        return ScalabilityResult(
            node_counts=node_counts,
            algorithm_times=algorithm_times
        )

