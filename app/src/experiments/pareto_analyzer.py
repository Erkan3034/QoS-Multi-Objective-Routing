"""
Pareto Optimality Analysis Module

Bu modül çok amaçlı optimizasyonda Pareto optimal çözümleri bulmak için kullanılır.

Pareto Optimalite Nedir?
- Bir çözüm Pareto Optimal ise, o çözümün hedeflerinden herhangi birini 
  iyileştirmek için diğer hedeflerden en az birini feda etmek zorunda kalırsınız.
- Pareto Sınırı (Pareto Frontier): Tüm Pareto optimal çözümlerin kümesi.

Kullanım:
    analyzer = ParetoAnalyzer(graph)
    pareto_front = analyzer.find_pareto_frontier(source, dest, n_solutions=50)
"""

import time
import random
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import networkx as nx

from src.services.metrics_service import MetricsService


@dataclass
class ParetoSolution:
    """Pareto çözüm veri sınıfı."""
    path: List[int]
    delay: float
    reliability: float
    resource_cost: float
    is_dominated: bool = False
    domination_count: int = 0  # Bu çözümü kaç çözüm domine ediyor
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "delay": self.delay,
            "reliability": self.reliability,
            "resource_cost": self.resource_cost,
            "is_dominated": self.is_dominated,
            "domination_count": self.domination_count
        }


@dataclass
class ParetoAnalysisResult:
    """Pareto analiz sonucu."""
    pareto_frontier: List[ParetoSolution]
    all_solutions: List[ParetoSolution]
    computation_time_ms: float
    
    # İstatistikler
    total_solutions: int = 0
    pareto_count: int = 0
    dominated_count: int = 0
    
    # Metrik aralıkları
    delay_range: Tuple[float, float] = (0.0, 0.0)
    reliability_range: Tuple[float, float] = (0.0, 0.0)
    resource_range: Tuple[float, float] = (0.0, 0.0)
    
    def to_dict(self) -> Dict:
        return {
            "pareto_frontier": [s.to_dict() for s in self.pareto_frontier],
            "total_solutions": self.total_solutions,
            "pareto_count": self.pareto_count,
            "dominated_count": self.dominated_count,
            "computation_time_ms": self.computation_time_ms,
            "delay_range": self.delay_range,
            "reliability_range": self.reliability_range,
            "resource_range": self.resource_range
        }


class ParetoAnalyzer:
    """
    Pareto Optimality Analyzer
    
    Üç metrik için Pareto sınırı bulur:
    - Delay (minimizasyon)
    - Reliability (maksimizasyon) -> 1-reliability minimizasyon
    - Resource Cost (minimizasyon)
    """
    
    def __init__(self, graph: nx.Graph, seed: int = None):
        self.graph = graph
        self.metrics_service = MetricsService(graph)
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
    
    def dominates(self, sol1: ParetoSolution, sol2: ParetoSolution) -> bool:
        """
        sol1, sol2'yi domine ediyor mu kontrol et.
        
        Dominasyon kuralı:
        - sol1 tüm metriklerde sol2'ye eşit veya daha iyi
        - sol1 en az bir metrikte sol2'den kesinlikle daha iyi
        
        Not: Reliability için daha YÜKSEK daha iyi, 
             Delay ve Resource için daha DÜŞÜK daha iyi.
        """
        # Delay: düşük daha iyi
        delay_better_or_equal = sol1.delay <= sol2.delay
        delay_strictly_better = sol1.delay < sol2.delay
        
        # Reliability: yüksek daha iyi
        rel_better_or_equal = sol1.reliability >= sol2.reliability
        rel_strictly_better = sol1.reliability > sol2.reliability
        
        # Resource: düşük daha iyi
        res_better_or_equal = sol1.resource_cost <= sol2.resource_cost
        res_strictly_better = sol1.resource_cost < sol2.resource_cost
        
        # Tüm metriklerde eşit veya daha iyi?
        all_better_or_equal = (delay_better_or_equal and 
                               rel_better_or_equal and 
                               res_better_or_equal)
        
        # En az bir metrikte kesinlikle daha iyi?
        at_least_one_better = (delay_strictly_better or 
                               rel_strictly_better or 
                               res_strictly_better)
        
        return all_better_or_equal and at_least_one_better
    
    def find_pareto_frontier(
        self, 
        source: int, 
        destination: int,
        n_solutions: int = 100,
        max_path_length: int = 30
    ) -> ParetoAnalysisResult:
        """
        Pareto sınırını bul.
        
        Yöntem:
        1. Farklı ağırlık kombinasyonlarıyla çok sayıda çözüm üret
        2. Tüm çözümleri Pareto dominasyon açısından karşılaştır
        3. Domine edilmeyen çözümleri (Pareto sınırı) döndür
        
        Args:
            source: Kaynak düğüm
            destination: Hedef düğüm
            n_solutions: Üretilecek çözüm sayısı
            max_path_length: Maksimum yol uzunluğu
            
        Returns:
            ParetoAnalysisResult
        """
        start_time = time.time()
        
        # 1. Çeşitli yollar üret
        all_solutions = self._generate_diverse_solutions(
            source, destination, n_solutions, max_path_length
        )
        
        if not all_solutions:
            return ParetoAnalysisResult(
                pareto_frontier=[],
                all_solutions=[],
                computation_time_ms=0,
                total_solutions=0
            )
        
        # 2. Dominasyon analizi yap
        self._analyze_domination(all_solutions)
        
        # 3. Pareto sınırını çıkar (domine edilmeyenler)
        pareto_frontier = [s for s in all_solutions if not s.is_dominated]
        dominated = [s for s in all_solutions if s.is_dominated]
        
        # 4. İstatistikleri hesapla
        delays = [s.delay for s in all_solutions]
        rels = [s.reliability for s in all_solutions]
        ress = [s.resource_cost for s in all_solutions]
        
        end_time = time.time()
        
        return ParetoAnalysisResult(
            pareto_frontier=pareto_frontier,
            all_solutions=all_solutions,
            computation_time_ms=(end_time - start_time) * 1000,
            total_solutions=len(all_solutions),
            pareto_count=len(pareto_frontier),
            dominated_count=len(dominated),
            delay_range=(min(delays), max(delays)),
            reliability_range=(min(rels), max(rels)),
            resource_range=(min(ress), max(ress))
        )
    
    def _generate_diverse_solutions(
        self, 
        source: int, 
        destination: int,
        n_solutions: int,
        max_path_length: int
    ) -> List[ParetoSolution]:
        """
        Çeşitli yollar üret.
        
        Üretim stratejileri:
        1. En kısa yol (her metrik için tek başına)
        2. Rastgele ağırlıklarla çözümler
        3. K-en kısa yol varyasyonları
        """
        solutions = []
        seen_paths = set()
        
        print(f"[ParetoAnalyzer] Çözüm üretimi başlıyor (n={n_solutions})")
        
        # Strateji 1: Tek metrik optimizasyonları
        single_weights = [
            {'delay': 1.0, 'reliability': 0.0, 'resource': 0.0},  # Sadece gecikme
            {'delay': 0.0, 'reliability': 1.0, 'resource': 0.0},  # Sadece güvenilirlik
            {'delay': 0.0, 'reliability': 0.0, 'resource': 1.0},  # Sadece kaynak
        ]
        
        print("[ParetoAnalyzer] Strateji 1: Tek metrik optimizasyonları")
        for i, weights in enumerate(single_weights):
            path = self._find_weighted_path(source, destination, weights)
            if path and tuple(path) not in seen_paths:
                seen_paths.add(tuple(path))
                sol = self._path_to_solution(path)
                if sol:
                    solutions.append(sol)
        print(f"[ParetoAnalyzer] Strateji 1 tamamlandı: {len(solutions)} çözüm")
        
        # Strateji 2: Rastgele ağırlık kombinasyonları (daha az iterasyon)
        # n_solutions'ı sınırla - çok fazla olmasın
        random_count = min(n_solutions - 3, 20)  # Max 20 rastgele deneme
        print(f"[ParetoAnalyzer] Strateji 2: {random_count} rastgele ağırlık kombinasyonu")
        
        for i in range(random_count):
            # Dirichlet dağılımı kullanarak ağırlık toplamı 1 olsun
            w = np.random.dirichlet([1, 1, 1])
            weights = {'delay': w[0], 'reliability': w[1], 'resource': w[2]}
            
            path = self._find_weighted_path(source, destination, weights)
            if path and tuple(path) not in seen_paths:
                seen_paths.add(tuple(path))
                sol = self._path_to_solution(path)
                if sol:
                    solutions.append(sol)
        
        print(f"[ParetoAnalyzer] Strateji 2 tamamlandı: {len(solutions)} toplam çözüm")
        
        # Strateji 3: Basit alternatif yollar (k-shortest çok yavaş, BFS kullan)
        print("[ParetoAnalyzer] Strateji 3: Alternatif yollar aranıyor...")
        try:
            # Sadece bir tane daha alternatif yol dene - BFS ile
            # Bu çok daha hızlı
            if nx.has_path(self.graph, source, destination):
                # BFS ile en kısa yolu bul (hop count)
                bfs_path = nx.shortest_path(self.graph, source, destination)
                if tuple(bfs_path) not in seen_paths:
                    seen_paths.add(tuple(bfs_path))
                    sol = self._path_to_solution(list(bfs_path))
                    if sol:
                        solutions.append(sol)
                        
            print(f"[ParetoAnalyzer] Strateji 3 tamamlandı: {len(solutions)} toplam çözüm")
        except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
            print(f"[ParetoAnalyzer] Strateji 3 hatası: {e}")
        
        print(f"[ParetoAnalyzer] Toplam {len(solutions)} benzersiz çözüm üretildi")
        return solutions
    
    def _find_weighted_path(
        self, 
        source: int, 
        destination: int, 
        weights: Dict[str, float]
    ) -> Optional[List[int]]:
        """Ağırlıklı maliyet fonksiyonu ile en kısa yolu bul."""
        try:
            # Edge maliyetlerini hesapla
            def edge_cost(u, v, data):
                edge = self.graph.edges[u, v]
                delay = edge.get('delay', 1.0)
                rel = edge.get('reliability', 0.99)
                bw = edge.get('bandwidth', 1000.0)
                
                # Normalize ve ağırlıkla
                delay_cost = delay / 200.0  # Normalize
                rel_cost = (1 - rel) * 10.0  # Unreliability penalty
                res_cost = (1000.0 / bw) / 200.0  # Normalize
                
                return (weights['delay'] * delay_cost + 
                        weights['reliability'] * rel_cost + 
                        weights['resource'] * res_cost)
            
            path = nx.dijkstra_path(self.graph, source, destination, weight=edge_cost)
            return path
            
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    def _path_to_solution(self, path: List[int]) -> Optional[ParetoSolution]:
        """Yolu ParetoSolution'a dönüştür."""
        if not path or len(path) < 2:
            return None
        
        # MetricsService kullanarak metrikleri hesapla
        metrics = self.metrics_service.calculate_all(path, 0.33, 0.33, 0.34)
        
        return ParetoSolution(
            path=path,
            delay=metrics.total_delay,
            reliability=metrics.total_reliability,
            resource_cost=metrics.resource_cost
        )
    
    def _analyze_domination(self, solutions: List[ParetoSolution]) -> None:
        """
        Tüm çözümler için dominasyon analizi yap.
        In-place güncelleme yapar.
        """
        n = len(solutions)
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                # i, j'yi domine ediyor mu?
                if self.dominates(solutions[i], solutions[j]):
                    solutions[j].is_dominated = True
                    solutions[j].domination_count += 1


# Export
__all__ = ["ParetoAnalyzer", "ParetoSolution", "ParetoAnalysisResult"]
