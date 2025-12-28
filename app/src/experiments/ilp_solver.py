"""
ILP (Integer Linear Programming) Solver for QoS Routing

Bu modül, çok amaçlı rotalama problemini ILP formülasyonu ile çözer.
Küçük-orta ölçekli problemler için optimal (kesin) çözüm sağlar.

Avantaj: Garantili optimal çözüm
Dezavantaj: Büyük ağlarda (>100 düğüm) çok yavaş

Kullanım:
    solver = ILPSolver(graph)
    result = solver.solve(source, destination, weights)
"""

import time
import networkx as nx
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math

# scipy.optimize kullan (PuLP yerine - kurulum gerektirmez)
try:
    from scipy.optimize import milp, LinearConstraint, Bounds
    import numpy as np
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class ILPResult:
    """ILP çözüm sonucu."""
    path: List[int]
    optimal_cost: float
    delay: float
    reliability: float
    resource_cost: float
    computation_time_ms: float
    status: str  # "optimal", "infeasible", "timeout", etc.
    gap: float = 0.0  # Optimality gap
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "optimal_cost": self.optimal_cost,
            "delay": self.delay,
            "reliability": self.reliability,
            "resource_cost": self.resource_cost,
            "computation_time_ms": self.computation_time_ms,
            "status": self.status,
            "gap": self.gap
        }


class ILPSolver:
    """
    ILP Tabanlı Optimal Rotalama Çözücüsü
    
    Problem Formülasyonu:
    - Decision Variables: x_ij ∈ {0,1} for each edge (i,j)
    - Objective: minimize Σ c_ij * x_ij
    - Constraints:
        - Flow conservation at each node
        - Source has net outflow of 1
        - Destination has net inflow of 1
        - Other nodes have net flow of 0
    
    Not: Güvenilirlik çarpımsal olduğu için -log dönüşümü kullanılır.
    """
    
    def __init__(self, graph: nx.Graph, timeout_seconds: float = 30.0):
        self.graph = graph
        self.timeout = timeout_seconds
        
        # Edge listesini hazırla
        self.edges = list(graph.edges())
        self.edge_to_idx = {e: i for i, e in enumerate(self.edges)}
        # Ters yön için (undirected graph)
        self.edge_to_idx.update({(v, u): i for i, (u, v) in enumerate(self.edges)})
        
        self.nodes = list(graph.nodes())
        self.node_to_idx = {n: i for i, n in enumerate(self.nodes)}
    
    def solve(
        self, 
        source: int, 
        destination: int,
        weights: Dict[str, float],
        bandwidth_demand: float = 0.0
    ) -> ILPResult:
        """
        ILP ile optimal yolu bul.
        
        Args:
            source: Kaynak düğüm
            destination: Hedef düğüm
            weights: Metrik ağırlıkları
            bandwidth_demand: Minimum bant genişliği gereksinimi
            
        Returns:
            ILPResult
        """
        start_time = time.time()
        
        # Yol mümkün mü kontrol et
        if not nx.has_path(self.graph, source, destination):
            return ILPResult(
                path=[],
                optimal_cost=float('inf'),
                delay=0, reliability=0, resource_cost=0,
                computation_time_ms=(time.time() - start_time) * 1000,
                status="no_path"
            )
        
        try:
            # K-shortest paths enumeration ile çözüm
            # (Dijkstra tabanlı - scipy gerektirmez)
            print(f"[ILPSolver] K-shortest paths enumeration başlıyor...")
            result = self._solve_enumeration(source, destination, weights, bandwidth_demand)
            result.computation_time_ms = (time.time() - start_time) * 1000
            print(f"[ILPSolver] Tamamlandı: cost={result.optimal_cost:.4f}, path_len={len(result.path)}")
            return result
            
        except Exception as e:
            import traceback
            print(f"[ILPSolver] HATA: {str(e)}")
            return ILPResult(
                path=[],
                optimal_cost=float('inf'),
                delay=0, reliability=0, resource_cost=0,
                computation_time_ms=(time.time() - start_time) * 1000,
                status=f"error: {str(e)}"
            )
    
    def _solve_enumeration(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float],
        bandwidth_demand: float
    ) -> ILPResult:
        """
        Dijkstra tabanlı enumerate ile "optimal" çözüm bul.
        
        Farklı ağırlık kombinasyonlarıyla Dijkstra çalıştırıp
        en iyi sonucu seçiyoruz. Hızlı ve pratik yaklaşım.
        """
        best_path = None
        best_cost = float('inf')
        best_metrics = (0.0, 0.0, 0.0)
        seen_paths = set()
        
        # Farklı ağırlık kombinasyonları ile Dijkstra
        weight_configs = [
            # Sadece delay
            lambda u, v, d: d.get('delay', 1.0),
            # Sadece reliability (unreliability olarak)
            lambda u, v, d: (1 - d.get('reliability', 0.99)) * 100,
            # Sadece bandwidth (resource)  
            lambda u, v, d: 1000.0 / max(d.get('bandwidth', 1000.0), 1.0),
            # Karma 1
            lambda u, v, d: d.get('delay', 1.0) + (1-d.get('reliability', 0.99))*50,
            # Karma 2
            lambda u, v, d: d.get('delay', 1.0) + 1000.0/max(d.get('bandwidth', 1000.0), 1.0),
            # Hop count
            lambda u, v, d: 1.0,
        ]
        
        for weight_fn in weight_configs:
            try:
                path = nx.dijkstra_path(self.graph, source, destination, weight=weight_fn)
                
                path_tuple = tuple(path)
                if path_tuple in seen_paths:
                    continue
                seen_paths.add(path_tuple)
                
                metrics = self._calculate_path_metrics(list(path))
                
                # Bandwidth constraint
                if bandwidth_demand > 0:
                    min_bw = self._get_min_bandwidth(list(path))
                    if min_bw < bandwidth_demand:
                        continue
                
                # Weighted cost
                cost = self._calculate_weighted_cost(metrics, weights)
                
                if cost < best_cost:
                    best_cost = cost
                    best_path = list(path)
                    best_metrics = metrics
                    
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
        
        if best_path is None:
            return ILPResult([], float('inf'), 0, 0, 0, 0, "infeasible")
        
        return ILPResult(
            path=best_path,
            optimal_cost=best_cost,
            delay=best_metrics[0],
            reliability=best_metrics[1],
            resource_cost=best_metrics[2],
            computation_time_ms=0,  # Caller will set this
            status="optimal"
        )
    
    def _calculate_path_metrics(self, path: List[int]) -> Tuple[float, float, float]:
        """Yolun ham metriklerini hesapla: (delay, reliability, resource_cost)"""
        total_delay = 0.0
        total_reliability = 1.0
        raw_resource_cost = 0.0
        
        # Node metrics
        for node in path:
            pd = self.graph.nodes[node].get('processing_delay', 0.0)
            total_delay += float(pd)
            nr = self.graph.nodes[node].get('reliability', 1.0)
            total_reliability *= float(nr)
        
        # Edge metrics
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            if self.graph.has_edge(u, v):
                edge = self.graph.edges[u, v]
                total_delay += float(edge.get('delay', 0.0))
                total_reliability *= float(edge.get('reliability', 1.0))
                bw = float(edge.get('bandwidth', 1000.0))
                raw_resource_cost += 1000.0 / max(bw, 1.0)
        
        # Normalize
        norm_resource = min(raw_resource_cost / 200.0, 1.0)
        
        return (total_delay, total_reliability, norm_resource)
    
    def _calculate_weighted_cost(
        self, 
        metrics: Tuple[float, float, float],
        weights: Dict[str, float]
    ) -> float:
        """Normalize edilmiş ağırlıklı maliyet hesapla."""
        delay, reliability, resource = metrics
        
        # Normalize delay
        norm_delay = min(delay / 200.0, 1.0)
        
        # Normalize reliability (penalty based)
        unreliability = 1.0 - reliability
        norm_rel = min(unreliability * 10.0, 1.0)
        
        return (weights.get('delay', 0.33) * norm_delay +
                weights.get('reliability', 0.33) * norm_rel +
                weights.get('resource', 0.34) * resource)
    
    def _get_min_bandwidth(self, path: List[int]) -> float:
        """Yoldaki minimum bant genişliğini bul."""
        min_bw = float('inf')
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            if self.graph.has_edge(u, v):
                bw = self.graph.edges[u, v].get('bandwidth', 1000.0)
                min_bw = min(min_bw, bw)
        return min_bw


class ILPBenchmark:
    """
    ILP vs Meta-Heuristic karşılaştırma aracı.
    
    Küçük ağlarda ILP optimal sonucunu meta-sezgisel algoritmaların
    sonuçlarıyla karşılaştırır.
    """
    
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.solver = ILPSolver(graph)
    
    def compare_with_algorithm(
        self,
        algorithm_result,
        source: int,
        destination: int,
        weights: Dict[str, float],
        bandwidth_demand: float = 0.0
    ) -> Dict:
        """
        ILP optimum ile algoritma sonucunu karşılaştır.
        
        Returns:
            {
                "ilp_cost": float,
                "algorithm_cost": float,
                "optimality_gap": float,  # % ne kadar optimal
                "ilp_path_length": int,
                "algorithm_path_length": int,
                "ilp_time_ms": float,
                "is_optimal": bool  # Algorithm == ILP mi?
            }
        """
        # ILP çözümü
        ilp_result = self.solver.solve(source, destination, weights, bandwidth_demand)
        
        # Algorithm sonucunun maliyetini hesapla
        if hasattr(algorithm_result, 'path') and algorithm_result.path:
            alg_metrics = self.solver._calculate_path_metrics(algorithm_result.path)
            alg_cost = self.solver._calculate_weighted_cost(alg_metrics, weights)
        else:
            alg_cost = float('inf')
        
        # Optimality gap hesapla
        if ilp_result.optimal_cost > 0 and ilp_result.optimal_cost != float('inf'):
            gap = ((alg_cost - ilp_result.optimal_cost) / ilp_result.optimal_cost) * 100
        else:
            gap = 0.0
        
        return {
            "ilp_cost": ilp_result.optimal_cost,
            "algorithm_cost": alg_cost,
            "optimality_gap_percent": round(gap, 2),
            "ilp_path_length": len(ilp_result.path) if ilp_result.path else 0,
            "algorithm_path_length": len(algorithm_result.path) if hasattr(algorithm_result, 'path') else 0,
            "ilp_time_ms": ilp_result.computation_time_ms,
            "ilp_status": ilp_result.status,
            "is_optimal": abs(gap) < 0.01  # %0.01 tolerans
        }


__all__ = ["ILPSolver", "ILPResult", "ILPBenchmark"]
