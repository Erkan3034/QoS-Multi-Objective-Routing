"""
Scalability Analysis Module

Bu modül, algoritmaların farklı ağ boyutlarındaki performansını analiz eder.
>1000 düğüm desteği için optimize edilmiştir.

Özellikler:
- 100'den 2000+ düğüme ölçeklenebilirlik testi
- Hafıza ve CPU kullanım analizi
- Karşılaştırmalı performans grafikleri
"""

import time
import gc
import tracemalloc
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import networkx as nx
import random

from src.services.graph_service import GraphService
from src.services.metrics_service import MetricsService
from src.algorithms import ALGORITHMS


@dataclass
class ScalabilityDataPoint:
    """Tek bir ölçeklenebilirlik veri noktası."""
    node_count: int
    edge_count: int
    algorithm: str
    avg_time_ms: float
    std_time_ms: float
    min_time_ms: float
    max_time_ms: float
    success_rate: float
    avg_cost: float
    memory_mb: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "algorithm": self.algorithm,
            "avg_time_ms": self.avg_time_ms,
            "std_time_ms": self.std_time_ms,
            "min_time_ms": self.min_time_ms,
            "max_time_ms": self.max_time_ms,
            "success_rate": self.success_rate,
            "avg_cost": self.avg_cost,
            "memory_mb": self.memory_mb
        }


@dataclass
class ScalabilityReport:
    """Kapsamlı ölçeklenebilirlik raporu."""
    data_points: List[ScalabilityDataPoint]
    node_sizes: List[int]
    algorithms: List[str]
    total_time_sec: float
    
    # Analiz sonuçları
    fastest_algorithm: str = ""
    most_scalable: str = ""  # En az zaman artışı gösteren
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "data_points": [dp.to_dict() for dp in self.data_points],
            "node_sizes": self.node_sizes,
            "algorithms": self.algorithms,
            "total_time_sec": self.total_time_sec,
            "fastest_algorithm": self.fastest_algorithm,
            "most_scalable": self.most_scalable,
            "recommendations": self.recommendations
        }
    
    def get_time_by_algorithm(self, algorithm: str) -> List[float]:
        """Algoritma için tüm node boyutlarındaki süreleri döndür."""
        return [dp.avg_time_ms for dp in self.data_points 
                if dp.algorithm == algorithm]
    
    def get_time_by_nodes(self, node_count: int) -> Dict[str, float]:
        """Belirli node sayısı için tüm algoritma sürelerini döndür."""
        return {dp.algorithm: dp.avg_time_ms for dp in self.data_points 
                if dp.node_count == node_count}


class ScalabilityAnalyzer:
    """
    Gelişmiş Ölçeklenebilirlik Analiz Aracı
    
    Özellikleri:
    - Çoklu düğüm boyutu desteği (100-2000+)
    - Hafıza profiling
    - İstatistiksel analiz
    - Ölçeklenebilirlik önerileri
    """
    
    def __init__(
        self,
        node_sizes: List[int] = None,
        n_repeats: int = 3,
        n_test_cases: int = 5,
        algorithms: List[str] = None,
        progress_callback: Callable[[int, int, str], None] = None
    ):
        """
        Args:
            node_sizes: Test edilecek düğüm sayıları [100, 250, 500, 1000, ...]
            n_repeats: Her test için tekrar sayısı
            n_test_cases: Her boyut için test sayısı
            algorithms: Test edilecek algoritmalar (default: hepsi)
            progress_callback: (current, total, message) -> None
        """
        self.node_sizes = node_sizes or [100, 250, 500, 750, 1000, 1500, 2000]
        self.n_repeats = n_repeats
        self.n_test_cases = n_test_cases
        self.algorithms = algorithms or list(ALGORITHMS.keys())
        self.progress_callback = progress_callback
    
    def run_analysis(self) -> ScalabilityReport:
        """
        Tam ölçeklenebilirlik analizi çalıştır.
        
        Returns:
            ScalabilityReport
        """
        start_time = time.time()
        data_points = []
        
        total_steps = len(self.node_sizes) * len(self.algorithms)
        current_step = 0
        
        for n_nodes in self.node_sizes:
            # Graf oluştur
            self._emit_progress(current_step, total_steps, 
                               f"Graf oluşturuluyor ({n_nodes} düğüm)...")
            
            graph, edge_count = self._create_test_graph(n_nodes)
            
            for algo_key in self.algorithms:
                current_step += 1
                algo_name = ALGORITHMS[algo_key][0]
                
                self._emit_progress(current_step, total_steps,
                                   f"{n_nodes} düğüm - {algo_name}")
                
                # Algoritma testi
                dp = self._test_algorithm(graph, algo_key, n_nodes, edge_count)
                data_points.append(dp)
                
                # Hafıza temizle
                gc.collect()
        
        total_time = time.time() - start_time
        
        # Rapor oluştur
        report = ScalabilityReport(
            data_points=data_points,
            node_sizes=self.node_sizes,
            algorithms=[ALGORITHMS[k][0] for k in self.algorithms],
            total_time_sec=total_time
        )
        
        # Analizi tamamla
        self._analyze_results(report)
        
        return report
    
    def _create_test_graph(self, n_nodes: int) -> tuple:
        """Test için graf oluştur."""
        # Seyreklik ayarla - büyük graflarda daha seyrek
        if n_nodes <= 250:
            p = 0.15
        elif n_nodes <= 500:
            p = 0.08
        elif n_nodes <= 1000:
            p = 0.04
        else:
            p = 0.02  # >1000 düğüm için çok seyrek
        
        service = GraphService(seed=42)  # Reproducibility
        graph = service.generate_graph(n_nodes=n_nodes, p=p)
        edge_count = graph.number_of_edges()
        
        return graph, edge_count
    
    def _test_algorithm(
        self, 
        graph: nx.Graph, 
        algo_key: str,
        n_nodes: int,
        edge_count: int
    ) -> ScalabilityDataPoint:
        """Tek algoritma için test çalıştır."""
        algo_name, AlgoClass = ALGORITHMS[algo_key]
        times = []
        costs = []
        successes = 0
        memory_peak = 0.0
        
        nodes = list(graph.nodes())
        
        for _ in range(self.n_test_cases):
            # Rastgele kaynak-hedef çifti
            source, dest = random.sample(nodes, 2)
            
            for _ in range(self.n_repeats):
                try:
                    # Hafıza izleme başlat
                    tracemalloc.start()
                    
                    start = time.time()
                    algo = AlgoClass(graph=graph, seed=None)
                    result = algo.optimize(
                        source=source,
                        destination=dest,
                        weights={'delay': 0.33, 'reliability': 0.33, 'resource': 0.34}
                    )
                    elapsed_ms = (time.time() - start) * 1000
                    
                    # Hafıza kullanımı
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc.stop()
                    memory_peak = max(memory_peak, peak / (1024 * 1024))  # MB
                    
                    times.append(elapsed_ms)
                    
                    if hasattr(result, 'path') and result.path:
                        successes += 1
                        if hasattr(result, 'fitness'):
                            costs.append(result.fitness)
                        elif hasattr(result, 'weighted_cost'):
                            costs.append(result.weighted_cost)
                            
                except Exception as e:
                    tracemalloc.stop()
                    times.append(0)
        
        # İstatistikler
        import numpy as np
        times_arr = np.array([t for t in times if t > 0]) if times else np.array([0])
        
        total_runs = self.n_test_cases * self.n_repeats
        
        return ScalabilityDataPoint(
            node_count=n_nodes,
            edge_count=edge_count,
            algorithm=algo_name,
            avg_time_ms=float(np.mean(times_arr)) if len(times_arr) > 0 else 0,
            std_time_ms=float(np.std(times_arr)) if len(times_arr) > 0 else 0,
            min_time_ms=float(np.min(times_arr)) if len(times_arr) > 0 else 0,
            max_time_ms=float(np.max(times_arr)) if len(times_arr) > 0 else 0,
            success_rate=successes / total_runs if total_runs > 0 else 0,
            avg_cost=float(np.mean(costs)) if costs else 0,
            memory_mb=memory_peak
        )
    
    def _analyze_results(self, report: ScalabilityReport) -> None:
        """Sonuçları analiz et ve öneriler oluştur."""
        if not report.data_points:
            return
        
        # En hızlı algoritma (ortalama)
        algo_avg_times = {}
        for algo in report.algorithms:
            times = report.get_time_by_algorithm(algo)
            if times:
                algo_avg_times[algo] = sum(times) / len(times)
        
        if algo_avg_times:
            report.fastest_algorithm = min(algo_avg_times, key=algo_avg_times.get)
        
        # En ölçeklenebilir (zaman artış oranı en düşük)
        scaling_factors = {}
        for algo in report.algorithms:
            times = report.get_time_by_algorithm(algo)
            if len(times) >= 2 and times[0] > 0:
                # Son / İlk oranı
                scaling_factors[algo] = times[-1] / times[0]
        
        if scaling_factors:
            report.most_scalable = min(scaling_factors, key=scaling_factors.get)
        
        # Öneriler
        report.recommendations = []
        
        if report.fastest_algorithm:
            report.recommendations.append(
                f"🏆 En hızlı algoritma: {report.fastest_algorithm}"
            )
        
        if report.most_scalable:
            report.recommendations.append(
                f"📈 En iyi ölçeklenebilirlik: {report.most_scalable}"
            )
        
        # Büyük ağ önerisi
        large_node_data = [dp for dp in report.data_points 
                          if dp.node_count >= 1000 and dp.success_rate > 0.8]
        if large_node_data:
            best_large = min(large_node_data, key=lambda x: x.avg_time_ms)
            report.recommendations.append(
                f"🔷 1000+ düğüm için önerilen: {best_large.algorithm}"
            )
    
    def _emit_progress(self, current: int, total: int, message: str):
        """Progress callback çağır."""
        if self.progress_callback:
            self.progress_callback(current, total, message)


__all__ = ["ScalabilityAnalyzer", "ScalabilityReport", "ScalabilityDataPoint"]
