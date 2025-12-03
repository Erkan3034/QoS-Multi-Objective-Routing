"""
Graf Oluşturma ve Yönetim Servisi

Bu modül Erdős–Rényi modeli kullanarak rastgele ağ topolojileri oluşturur.
"""
import networkx as nx
import numpy as np
from typing import Optional, Dict, Any, List

from src.core.config import settings


class GraphService:
    """Graf oluşturma ve yönetim servisi."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else settings.RANDOM_SEED
        self.graph: Optional[nx.Graph] = None
        self._rng = np.random.default_rng(self.seed)
    
    def generate_graph(self, n_nodes: int = None, p: float = None) -> nx.Graph:
        """Erdős–Rényi G(n, p) modeli ile bağlı graf oluşturur."""
        n_nodes = n_nodes or settings.DEFAULT_NODE_COUNT
        p = p or settings.DEFAULT_CONNECTION_PROB
        
        if n_nodes < 2:
            raise ValueError("Node count must be at least 2")
        if not 0 < p <= 1:
            raise ValueError("Connection probability must be between 0 and 1")
        
        attempt = 0
        max_attempts = 100
        
        while attempt < max_attempts:
            G = nx.erdos_renyi_graph(n_nodes, p, seed=self.seed + attempt)
            if nx.is_connected(G):
                break
            attempt += 1
        else:
            G = nx.erdos_renyi_graph(n_nodes, p, seed=self.seed)
            components = list(nx.connected_components(G))
            for i in range(len(components) - 1):
                node1 = list(components[i])[0]
                node2 = list(components[i + 1])[0]
                G.add_edge(node1, node2)
        
        self._assign_node_attributes(G)
        self._assign_edge_attributes(G)
        self.graph = G
        return G
    
    def _assign_node_attributes(self, G: nx.Graph) -> None:
        for node in G.nodes():
            G.nodes[node]['processing_delay'] = self._rng.uniform(
                settings.PROCESSING_DELAY_MIN, settings.PROCESSING_DELAY_MAX
            )
            G.nodes[node]['reliability'] = self._rng.uniform(
                settings.NODE_RELIABILITY_MIN, settings.NODE_RELIABILITY_MAX
            )
    
    def _assign_edge_attributes(self, G: nx.Graph) -> None:
        for u, v in G.edges():
            G.edges[u, v]['bandwidth'] = self._rng.uniform(
                settings.BANDWIDTH_MIN, settings.BANDWIDTH_MAX
            )
            G.edges[u, v]['delay'] = self._rng.uniform(
                settings.LINK_DELAY_MIN, settings.LINK_DELAY_MAX
            )
            G.edges[u, v]['reliability'] = self._rng.uniform(
                settings.LINK_RELIABILITY_MIN, settings.LINK_RELIABILITY_MAX
            )
    
    def get_graph_info(self) -> Dict[str, Any]:
        if self.graph is None:
            return {"error": "No graph generated yet"}
        
        return {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "is_connected": nx.is_connected(self.graph),
            "average_degree": sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            "seed": self.seed
        }
    
    def get_node_positions(self) -> Dict[int, tuple]:
        """Graf düğümlerinin pozisyonlarını hesaplar (görselleştirme için)."""
        if self.graph is None:
            return {}
        return nx.spring_layout(self.graph, seed=self.seed, k=2/np.sqrt(self.graph.number_of_nodes()))
    
    def has_path(self, source: int, destination: int) -> bool:
        if self.graph is None:
            return False
        return nx.has_path(self.graph, source, destination)
    
    def get_neighbors(self, node: int) -> List[int]:
        if self.graph is None:
            return []
        return list(self.graph.neighbors(node))

