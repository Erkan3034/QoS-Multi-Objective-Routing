"""Metrics service: compute path metrics and weighted cost.

Provides a simple implementation used by algorithms and the UI.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PathMetrics:
    total_delay: float
    total_reliability: float
    resource_cost: float
    weighted_cost: float


class MetricsService:
    """Compute metrics for a given path on a NetworkX graph.

    This implementation is intentionally simple but consistent with
    the attributes assigned by `GraphService` (node 'processing_delay',
    node 'reliability', edge 'delay', edge 'reliability', edge 'bandwidth').
    """

    def __init__(self, graph):
        self.graph = graph

    def calculate_all(self, path: List[int], delay_w: float, reliability_w: float, resource_w: float) -> PathMetrics:
        """Calculate metrics for `path` and return a PathMetrics instance.

        Args:
            path: list of node ids representing the path
            delay_w, reliability_w, resource_w: weights (not used for normalization here)
        """
        if not path or len(path) < 2:
            return PathMetrics(0.0, 0.0, 0.0, float('inf'))

        total_delay = 0.0
        total_reliability = 1.0
        resource_cost = 0.0

        # Sum node processing delays (include all nodes on path)
        for node in path:
            pd = self.graph.nodes[node].get('processing_delay', 0.0)
            total_delay += float(pd)
            nr = self.graph.nodes[node].get('reliability', 1.0)
            total_reliability *= float(nr)

        # Sum edge delays and resource costs, multiply reliabilities
        for u, v in zip(path[:-1], path[1:]):
            if self.graph.has_edge(u, v):
                edge = self.graph.edges[u, v]
                edelay = edge.get('delay', 0.0)
                ereliability = edge.get('reliability', 1.0)
                bandwidth = edge.get('bandwidth', 1.0)

                total_delay += float(edelay)
                total_reliability *= float(ereliability)
                # resource cost: lower bandwidth => higher cost
                try:
                    resource_cost += 1.0 / float(bandwidth) if bandwidth else float('inf')
                except Exception:
                    resource_cost += float('inf')
            else:
                # invalid edge, mark as very bad
                total_delay += 1e6
                total_reliability *= 0.0
                resource_cost += 1e6

        # Weighted cost (simple linear combination)
        weighted_cost = (
            delay_w * total_delay
            + reliability_w * (1.0 - total_reliability)
            + resource_w * resource_cost
        )

        return PathMetrics(
            total_delay=total_delay,
            total_reliability=total_reliability,
            resource_cost=resource_cost,
            weighted_cost=weighted_cost
        )

    def calculate_weighted_cost(self, path: List[int], delay_w: float, reliability_w: float, resource_w: float) -> float:
        """Convenience wrapper to return only weighted cost value."""
        pm = self.calculate_all(path, delay_w, reliability_w, resource_w)
        return pm.weighted_cost

__all__ = ["MetricsService", "PathMetrics"]
