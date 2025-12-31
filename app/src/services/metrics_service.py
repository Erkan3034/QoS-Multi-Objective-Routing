"""
METRİK HESAPLAMA SERVİSİ
========================
Ağ yollarının QoS metriklerini hesaplar.

FORMÜLLER:
----------
1. TotalDelay = Σ(LinkDelay) + Σ(ProcessingDelay), k ≠ S,D
2. ReliabilityCost = Σ[-log(LinkRel)] + Σ[-log(NodeRel)]
3. ResourceCost = Σ(1Gbps / Bandwidth)
4. WeightedCost = w₁×Delay + w₂×Reliability + w₃×Resource
"""

from dataclasses import dataclass
from typing import List, Dict
from functools import lru_cache
import math
import networkx as nx


# Normalizasyon sabitleri
class NormConfig:
    """0.0-1.0 arasına normalize etmek için referans maksimum değerler."""
    MAX_DELAY_MS = 200.0         # 200ms üzeri → 1.0
    MAX_HOP_COUNT = 20.0         # Referans hop sayısı
    MAX_RELIABILITY_COST = 10.0  # 40 × -log(0.95) ≈ 2, güvenlik payı=10


@dataclass 
class PathMetrics:
    """Yol metrikleri veri sınıfı."""
    total_delay: float           # Toplam gecikme (ms)
    total_reliability: float     # Çarpımsal güvenilirlik (0-1)
    resource_cost: float         # Normalize kaynak maliyeti (0-1)
    weighted_cost: float         # Ağırlıklı toplam (fitness)
    min_bandwidth: float = float('inf')  # Darboğaz (Mbps)
    reliability_cost: float = 0.0        # Ham -log maliyeti


class MetricsService:
    """
    Metrik Hesaplama Servisi
    
    Kullanım:
        service = MetricsService(graph)
        metrics = service.calculate_all(path, 0.33, 0.33, 0.34)
        cost = service.calculate_weighted_cost(path, 0.33, 0.33, 0.34)
    """

    def __init__(self, graph: nx.Graph):
        """Graf referansını sakla."""
        self.graph = graph

    @lru_cache(maxsize=10000)
    def calculate_weighted_cost_cached(
        self, path_tuple: tuple, 
        delay_w: float, reliability_w: float, resource_w: float,
        bw_demand: float = 0.0
    ) -> float:
        """Önbellekli ağırlıklı maliyet hesaplama (performans için)."""
        return self.calculate_weighted_cost(
            list(path_tuple), delay_w, reliability_w, resource_w, bw_demand
        )

    def calculate_all(
        self, path: List[int], 
        delay_w: float, reliability_w: float, resource_w: float
    ) -> PathMetrics:
        """
        Tüm QoS metriklerini hesaplar.
        
        Args:
            path: Düğüm ID listesi [kaynak, ..., hedef]
            delay_w, reliability_w, resource_w: Metrik ağırlıkları (toplam=1)
        
        Returns:
            PathMetrics: Tüm metrikleri içeren veri objesi
        """
        # Geçersiz yol kontrolü
        if not path or len(path) < 2:
            return PathMetrics(0.0, 0.0, 0.0, float('inf'), 0.0, 0.0)

        # Değişken başlatma
        total_delay = 0.0
        total_reliability = 1.0
        reliability_cost = 0.0
        min_bw = float('inf')
        
        source, destination = path[0], path[-1]
        
        # === DÜĞÜM METRİKLERİ ===
        for node in path:
            # ProcessingDelay: Sadece ARA düğümler (S,D hariç)
            if node != source and node != destination:
                pd = self.graph.nodes[node].get('processing_delay', 0.0)
                total_delay += float(pd)
            
            # NodeReliability: TÜM düğümler
            nr = float(self.graph.nodes[node].get('reliability', 1.0))
            total_reliability *= nr
            reliability_cost += -math.log(max(nr, 0.001))

        # === KENAR METRİKLERİ ===
        for u, v in zip(path[:-1], path[1:]):
            if not self.graph.has_edge(u, v):
                return PathMetrics(0.0, 0.0, 0.0, float('inf'), 0.0, 0.0)
            
            edge = self.graph.edges[u, v]
            
            # Link Delay
            total_delay += float(edge.get('delay', 0.0))
            
            # Link Reliability
            ereliability = float(edge.get('reliability', 1.0))
            total_reliability *= ereliability
            reliability_cost += -math.log(max(ereliability, 0.001))
            
            # Bandwidth (darboğaz)
            min_bw = min(min_bw, float(edge.get('bandwidth', 1000.0)))

        # === NORMALİZASYON ===
        norm_delay = min(total_delay / NormConfig.MAX_DELAY_MS, 1.0)
        norm_rel = min(reliability_cost / NormConfig.MAX_RELIABILITY_COST, 1.0)
        
        # Kaynak maliyeti: OSPF benzeri (Cost = 1Gbps / BW)
        raw_resource = sum(
            1000.0 / max(float(self.graph.edges[u, v].get('bandwidth', 1000.0)), 1.0)
            for u, v in zip(path[:-1], path[1:])
            if self.graph.has_edge(u, v)
        )
        norm_resource = min(raw_resource / 200.0, 1.0)

        # Ağırlıklı toplam
        weighted_cost = (
            delay_w * norm_delay +
            reliability_w * norm_rel +
            resource_w * norm_resource
        )

        return PathMetrics(
            total_delay=total_delay,
            total_reliability=total_reliability,
            resource_cost=norm_resource,
            weighted_cost=weighted_cost,
            min_bandwidth=min_bw,
            reliability_cost=reliability_cost
        )

    def calculate_weighted_cost(
        self, path: List[int], 
        delay_w: float, reliability_w: float, resource_w: float,
        bw_demand: float = 0.0
    ) -> float:
        """
        Ağırlıklı maliyet hesapla.
        
        Args:
            bw_demand: Bandwidth kısıtı (Mbps), 0=kısıt yok
            
        Returns:
            float: Maliyet (0-1) veya inf (geçersiz/kısıt ihlali)
        """
        if not path or len(path) < 2:
            return float('inf')
            
        metrics = self.calculate_all(path, delay_w, reliability_w, resource_w)
        
        # Bandwidth sert kısıt kontrolü
        if bw_demand > 0 and metrics.min_bandwidth < bw_demand:
            return float('inf')
            
        return metrics.weighted_cost


__all__ = ["MetricsService", "PathMetrics", "NormConfig"]
