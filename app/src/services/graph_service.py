"""
Graf Oluşturma ve Yönetim Servisi

Bu modülde Erdős–Rényi modeli kullanarak rastgele ağ topolojileri oluşturuyoruz
ve CSV dosyalarından graf verisi yüklüyoruz.
"""
import os
import networkx as nx
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from src.core.config import settings


@dataclass
class DemandPair:
    """Talep çifti veri sınıfı."""
    source: int
    destination: int
    demand_mbps: int


class GraphService:
    """Graf oluşturma ve yönetim servisi. 
    Burada graf oluşturma, graf verisi yükleme, graf bağlantılılık kontrolü, 
    graf düğümlerinin pozisyonlarını hesaplamak gibi işlemler yapılıyor."""
    
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else settings.RANDOM_SEED
        self.graph: Optional[nx.Graph] = None
        self.demands: List[DemandPair] = []
        self._rng = np.random.default_rng(self.seed)
        self._data_source: str = "generated"  # "generated" veya "csv"
    
    def load_from_csv(self, data_dir: str) -> nx.Graph:
        """
        CSV dosyalarından graf yükler.
        
        Args:
            data_dir: graph_data klasörünün yolu
            
        Returns:
            Yüklenen NetworkX graf
        """
        node_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_NodeData.csv")
        edge_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_EdgeData.csv")
        demand_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_DemandData.csv")
        
        # Dosyaların varlığını kontrol et
        for f in [node_file, edge_file, demand_file]:
            if not os.path.exists(f):
                raise FileNotFoundError(f"CSV dosyası bulunamadı: {f}")
        
        # Yeni graf oluştur
        G = nx.Graph()
        
        # Node verilerini yükle
        self._load_nodes_from_csv(G, node_file)
        
        # Edge verilerini yükle
        self._load_edges_from_csv(G, edge_file)
        
        # Demand verilerini yükle
        self._load_demands_from_csv(demand_file)
        
        self.graph = G
        self._data_source = "csv"
        return G
    
    def _parse_turkish_float(self, value: str) -> float:
        """Türkçe formatlı sayıları parse eder (virgül -> nokta)."""
        return float(value.replace(',', '.'))
    
    def _load_nodes_from_csv(self, G: nx.Graph, filepath: str) -> None:
        """Node verilerini CSV'den yükler."""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # İlk satır başlık: node_id;s_ms;r_node
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(';')
            if len(parts) >= 3:
                node_id = int(parts[0])
                processing_delay = self._parse_turkish_float(parts[1])  # s_ms -> processing_delay
                reliability = self._parse_turkish_float(parts[2])  # r_node -> reliability
                
                G.add_node(node_id, 
                          processing_delay=processing_delay,
                          reliability=reliability)
    
    def _load_edges_from_csv(self, G: nx.Graph, filepath: str) -> None:
        """Edge verilerini CSV'den yükler."""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # İlk satır başlık: src;dst;capacity_mbps;delay_ms;r_link
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(';')
            if len(parts) >= 5:
                src = int(parts[0])
                dst = int(parts[1])
                bandwidth = float(parts[2])  # capacity_mbps -> bandwidth
                delay = float(parts[3])  # delay_ms -> delay
                reliability = self._parse_turkish_float(parts[4])  # r_link -> reliability
                
                G.add_edge(src, dst,
                          bandwidth=bandwidth,
                          delay=delay,
                          reliability=reliability)
    
    def _load_demands_from_csv(self, filepath: str) -> None:
        """Demand verilerini CSV'den yükler."""
        self.demands = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # İlk satır başlık: src;dst;demand_mbps
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(';')
            if len(parts) >= 3:
                src = int(parts[0])
                dst = int(parts[1])
                demand = int(parts[2])
                
                self.demands.append(DemandPair(
                    source=src,
                    destination=dst,
                    demand_mbps=demand
                ))
    
    def get_demands(self) -> List[DemandPair]:
        """Yüklenen talep çiftlerini döndürür."""
        return self.demands
    
    def get_demand_pairs_for_ui(self) -> List[Tuple[int, int, int]]:
        """UI için talep çiftlerini tuple listesi olarak döndürür."""
        return [(d.source, d.destination, d.demand_mbps) for d in self.demands]
    
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
        self._data_source = "generated"
        self.demands = []  # Rastgele graf için demand yok
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
        
        info = {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "is_connected": nx.is_connected(self.graph),
            "average_degree": sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            "data_source": self._data_source
        }
        
        if self._data_source == "generated":
            info["seed"] = self.seed
        else:
            info["demand_count"] = len(self.demands)
        
        return info
    
    def get_node_positions(self, dim: int = 2) -> Dict[int, tuple]:
        """Graf düğümlerinin pozisyonlarını hesaplar (görselleştirme için).
        Args:
            dim: 2 veya 3 (boyut sayısı)
        """
        if self.graph is None:
            return {}
        # 3D layout için dim=3
        return nx.spring_layout(self.graph, seed=self.seed, k=2/np.sqrt(self.graph.number_of_nodes()), dim=dim)
    
    def has_path(self, source: int, destination: int) -> bool:
        if self.graph is None:
            return False
        return nx.has_path(self.graph, source, destination)
    
    def get_neighbors(self, node: int) -> List[int]:
        if self.graph is None:
            return []
        return list(self.graph.neighbors(node))
    
    def is_from_csv(self) -> bool:
        """Grafın CSV'den yüklenip yüklenmediğini döndürür."""
        return self._data_source == "csv"
