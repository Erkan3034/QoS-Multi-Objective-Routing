"""
=============================================================================
GRAF OLUŞTURMA VE YÖNETİM SERVİSİ
=============================================================================

MODÜL AÇIKLAMASI:
-----------------
Bu modül, ağ topolojilerinin oluşturulması ve yönetilmesinden sorumludur.
İki farklı veri kaynağı desteklenir:

1. CSV DOSYALARINDAN YÜKLEME:
   - NodeData.csv: Düğüm bilgileri (ID, işleme gecikmesi, güvenilirlik)
   - EdgeData.csv: Kenar bilgileri (kaynak, hedef, bant genişliği, gecikme, güvenilirlik)
   - DemandData.csv: Talep çiftleri (kaynak, hedef, talep miktarı Mbps)

2. RASTGELE GRAF OLUŞTURMA:
   - Erdős–Rényi G(n, p) modeli kullanılır
   - n: Düğüm sayısı
   - p: İki düğüm arasında kenar olma olasılığı
   - Grafın bağlı (connected) olması garanti edilir

AĞ MODELİ ÖZELLİKLERİ (Proje Yönergesine Uygun):
------------------------------------------------
DÜĞÜM ÖZELLİKLERİ:
  - processing_delay (s_ms): Düğümün işleme gecikmesi (milisaniye)
  - reliability (r_node): Düğümün güvenilirlik değeri (0.0 - 1.0)

KENAR ÖZELLİKLERİ:
  - bandwidth (capacity_mbps): Bant genişliği kapasitesi (Mbps)
  - delay (delay_ms): Link gecikmesi (milisaniye)
  - reliability (r_link): Link güvenilirlik değeri (0.0 - 1.0)

KULLANIM ÖRNEĞİ:
---------------
    # CSV'den yükleme
    service = GraphService(seed=42)
    graph = service.load_from_csv("data/graph_data")
    demands = service.get_demands()
    
    # Rastgele graf oluşturma
    service = GraphService(seed=42)
    graph = service.generate_graph(n_nodes=50, p=0.1)
"""

# =============================================================================
# KÜTÜPHANE İMPORTLARI
# =============================================================================
import os                              # Dosya sistemi işlemleri
import networkx as nx                  # Graf veri yapısı ve algoritmaları
import numpy as np                     # Rastgele sayı üretimi için
from typing import Optional, Dict, Any, List, Tuple  # Tip belirteçleri
from dataclasses import dataclass      # Veri sınıfları için dekoratör

# Proje konfigürasyonu (varsayılan değerler)
from src.core.config import settings


# =============================================================================
# TALEP ÇİFTİ VERİ SINIFI
# =============================================================================
@dataclass
class DemandPair:
    """
    Talep Çifti Veri Sınıfı
    
    Ağda bir kaynak-hedef çifti arasındaki trafik talebini temsil eder.
    CSV dosyasından yüklenen demand verileri bu sınıfta saklanır.
    
    Attributes:
        source (int): Kaynak düğüm ID'si
        destination (int): Hedef düğüm ID'si
        demand_mbps (int): Talep edilen bant genişliği (Megabit/saniye)
    
    Example:
        DemandPair(source=0, destination=249, demand_mbps=100)
        # 0 numaralı düğümden 249'a 100 Mbps trafik talebi
    """
    source: int          # Kaynak düğüm ID'si
    destination: int     # Hedef düğüm ID'si
    demand_mbps: int     # Talep miktarı (Mbps)


# =============================================================================
# GRAF SERVİSİ ANA SINIFI
# =============================================================================
class GraphService:
    """
    Graf Oluşturma ve Yönetim Servisi
    
    Bu sınıf, ağ topolojisinin oluşturulması, yüklenmesi ve yönetilmesinden
    sorumludur. Ana fonksiyonlar:
    
    1. CSV'den Graf Yükleme: load_from_csv()
    2. Rastgele Graf Oluşturma: generate_graph()
    3. Graf Bilgisi Sorgulama: get_graph_info(), has_path(), get_neighbors()
    4. Görselleştirme Desteği: get_node_positions()
    
    Attributes:
        seed (int): Rastgele sayı üreteci için seed (tekrarlanabilirlik)
        graph (nx.Graph): NetworkX graf objesi
        demands (List[DemandPair]): Talep çiftleri listesi
        _rng: NumPy rastgele sayı üreteci
        _data_source (str): Veri kaynağı ("generated" veya "csv")
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        GraphService constructor.
        
        Args:
            seed: Rastgele sayı üreteci seed değeri.
                  None ise settings'ten varsayılan değer alınır.
                  Aynı seed ile aynı graf oluşturulur (tekrarlanabilirlik).
        """
        # Seed değerini ayarla (tekrarlanabilir sonuçlar için önemli)
        self.seed = seed if seed is not None else settings.RANDOM_SEED
        
        # Graf ve talep verileri için başlangıç değerleri
        self.graph: Optional[nx.Graph] = None    # Henüz graf oluşturulmadı
        self.demands: List[DemandPair] = []      # Talep listesi boş
        
        # NumPy rastgele sayı üreteci (modern API)
        self._rng = np.random.default_rng(self.seed)
        
        # Veri kaynağı takibi
        self._data_source: str = "generated"  # "generated" veya "csv"
    # =========================================================================
    # CSV'DEN GRAF YÜKLEME METODLARI
    # =========================================================================
    
    def load_from_csv(self, data_dir: str) -> nx.Graph:
        """
        CSV dosyalarından graf yükler.
        
        Bu metod, proje yönergesinde belirtilen formatta hazırlanmış
        CSV dosyalarını okuyarak NetworkX graf objesi oluşturur.
        
        Beklenen dosyalar:
        - NodeData.csv: node_id;s_ms;r_node (düğüm verileri)
        - EdgeData.csv: src;dst;capacity_mbps;delay_ms;r_link (kenar verileri)
        - DemandData.csv: src;dst;demand_mbps (talep verileri)
        
        Args:
            data_dir: graph_data klasörünün yolu
            
        Returns:
            nx.Graph: Yüklenen NetworkX graf objesi
            
        Raises:
            FileNotFoundError: CSV dosyaları bulunamazsa
        """
        # CSV dosya yollarını oluştur
        node_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_NodeData.csv")
        edge_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_EdgeData.csv")
        demand_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_DemandData.csv")
        
        # Dosyaların varlığını kontrol et
        for f in [node_file, edge_file, demand_file]:
            if not os.path.exists(f):
                raise FileNotFoundError(f"CSV dosyası bulunamadı: {f}")
        
        # Boş NetworkX grafı oluştur (yönsüz graf)
        G = nx.Graph()
        
        # ADIM 1: Düğüm (Node) verilerini yükle
        # Her düğüm: processing_delay ve reliability özelliklerine sahip
        self._load_nodes_from_csv(G, node_file)
        
        # ADIM 2: Kenar (Edge) verilerini yükle
        # Her kenar: bandwidth, delay ve reliability özelliklerine sahip
        self._load_edges_from_csv(G, edge_file)
        
        # ADIM 3: Talep (Demand) verilerini yükle
        # Kaynak-hedef çiftleri ve bant genişliği talepleri
        self._load_demands_from_csv(demand_file)
        
        # Grafı sakla ve veri kaynağını işaretle
        self.graph = G
        self._data_source = "csv"
        return G
    
    def _parse_turkish_float(self, value: str) -> float:
        """
        Türkçe formatlı ondalık sayıları Python float'a çevirir.
        
        Türkçe'de ondalık ayırıcı virgül (,) kullanılır.
        Python'da nokta (.) kullanılır.
        
        Örnek: "0,95" -> 0.95
        
        Args:
            value: Türkçe formatlı sayı string'i ("0,95")
            
        Returns:
            float: Python float değeri (0.95)
        """
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
