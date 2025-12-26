"""Metrics service: compute path metrics and weighted cost.

Provides a simple implementation used by algorithms and the UI.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
from functools import lru_cache
import networkx as nx

# ---------------------------------------------------------------------------
# NORMALIZATION CONSTANTS (Standardized across all algorithms)
# ---------------------------------------------------------------------------
class NormConfig:
    MAX_DELAY_MS = 200.0        # 200ms reference for normalization
    MAX_HOP_COUNT = 20.0        # 20 hops reference
    RELIABILITY_PENALTY = 10.0  # Penalty multiplier for unreliability

@dataclass
class PathMetrics:
    total_delay: float
    total_reliability: float
    resource_cost: float
    weighted_cost: float
    min_bandwidth: float = float('inf')  # Track minimum bandwidth for constraints


class MetricsService:
    """Compute metrics for a given path on a NetworkX graph.
    """

    def __init__(self, graph: nx.Graph):
        self.graph = graph

    @lru_cache(maxsize=10000)
    def calculate_weighted_cost_cached(
        self, 
        path_tuple: tuple, 
        delay_w: float, 
        reliability_w: float, 
        resource_w: float,
        bw_demand: float = 0.0
    ) -> float:
        """Cached wrapper for cost calculation.
        
        Args:
            path_tuple: Tuple of node IDs (must be hashable for caching)
            ...
        """
        return self.calculate_weighted_cost(list(path_tuple), delay_w, reliability_w, resource_w, bw_demand)

    def calculate_all(self, path: List[int], delay_w: float, reliability_w: float, resource_w: float) -> PathMetrics:
        """Calculate metrics for `path` and return a PathMetrics instance.
        """
        if not path or len(path) < 2:
            return PathMetrics(0.0, 0.0, 0.0, float('inf'), 0.0)

        total_delay = 0.0
        total_reliability = 1.0
        min_bw = float('inf')
        
        # Calculate raw metrics
        # Nodes
        for node in path:
            pd = self.graph.nodes[node].get('processing_delay', 0.0)
            total_delay += float(pd)
            nr = self.graph.nodes[node].get('reliability', 1.0)
            total_reliability *= float(nr)

        # Edges
        for u, v in zip(path[:-1], path[1:]):
            if self.graph.has_edge(u, v):
                edge = self.graph.edges[u, v]
                edelay = edge.get('delay', 0.0)
                ereliability = edge.get('reliability', 1.0)
                bandwidth = edge.get('bandwidth', 1000.0)

                total_delay += float(edelay)
                total_reliability *= float(ereliability)
                min_bw = min(min_bw, float(bandwidth))
            else:
                return PathMetrics(0.0, 0.0, 0.0, float('inf'), 0.0)

        # --- NORMALIZED SCORING (The "Fair" Calculation) ---
        
        # 1. Normalize Delay
        norm_delay = min(total_delay / NormConfig.MAX_DELAY_MS, 1.0)
        
        # 2. Normalize Reliability (Penalty based)
        unreliability = 1.0 - total_reliability
        norm_rel = min(unreliability * NormConfig.RELIABILITY_PENALTY, 1.0)
        
        # 3. Normalize Resource (Bandwidth based Cost)
        # Project Requirement: Resource Cost = Sum(1Gbps / Bandwidth)
        # This penalizes low bandwidth links (High Cost) and favors high bandwidth (Low Cost)
        # Using 1000.0 (1Gbps) as reference.
        # Max expected cost per link is 10 (100Mbps), min is 1 (1000Mbps).
        # We normalize by assuming a max path length (e.g., 20) and min bandwidth (100Mbps).
        # Max theoretical raw cost approx: 20 hops * (1000/100) = 200.
        
        # Calculate raw resource cost based on bandwidth
        raw_resource_cost = 0.0
        for u, v in zip(path[:-1], path[1:]):
            if self.graph.has_edge(u, v):
                bw = float(self.graph.edges[u, v].get('bandwidth', 1000.0))
                # Avoid division by zero
                bw = max(bw, 1.0)
                # Cost = Reference / Bandwidth (Standard OSPF-like cost)
                raw_resource_cost += (1000.0 / bw)
        
        # Normalize: Divide by a reasonable max cost to keep it in [0, 1] range
        # Reference Max: 20 hops of lowest bandwidth (100Mbps -> cost 10) = 200
        norm_resource = min(raw_resource_cost / 200.0, 1.0)

        # Weighted Sum
        weighted_cost = (
            delay_w * norm_delay +
            reliability_w * norm_rel +
            resource_w * norm_resource
        )

        return PathMetrics(
            total_delay=total_delay,
            total_reliability=total_reliability,
            resource_cost=norm_resource, # Storing normalized resource cost
            weighted_cost=weighted_cost,
            min_bandwidth=min_bw
        )

    def calculate_weighted_cost(
        self, 
        path: List[int], 
        delay_w: float, 
        reliability_w: float, 
        resource_w: float,
        bw_demand: float = 0.0
    ) -> float:
        """Returns weighted cost. Returns infinity if bandwidth constraint is violated."""
        
        # Fast fail for invalid paths
        if not path or len(path) < 2:
            return float('inf')
            
        metrics = self.calculate_all(path, delay_w, reliability_w, resource_w)
        
        # HARD CONSTRAINT: Bandwidth
        if bw_demand > 0 and metrics.min_bandwidth < bw_demand:
            return float('inf')
            
        return metrics.weighted_cost

__all__ = ["MetricsService", "PathMetrics", "NormConfig"]
