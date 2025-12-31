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
    =======================
    
    Ağda bir kaynak-hedef çifti arasındaki trafik talebini temsil eder.
    CSV dosyasından yüklenen demand verileri bu sınıfta saklanır.
    
    PROJE YÖNERGESİ:
    ----------------
    DemandData.csv dosyasındaki her satır bir talep çiftini temsil eder.
    Optimizasyon algoritmaları bu talepleri karşılayacak rotalar bulmalıdır.
    
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
    ==================================
    
    Bu sınıf, ağ topolojisinin oluşturulması, yüklenmesi ve yönetilmesinden
    sorumludur.
    
    ANA FONKSİYONLAR:
    -----------------
    1. load_from_csv(): CSV dosyalarından graf yükler
    2. generate_graph(): Rastgele Erdős–Rényi grafı oluşturur
    3. get_graph_info(): Graf istatistiklerini döndürür
    4. get_node_positions(): Görselleştirme için düğüm pozisyonları
    5. has_path(): İki düğüm arasında yol varlığını kontrol eder
    
    TEKRARLANABILIRLIK (Reproducibility):
    -------------------------------------
    Aynı seed değeri ile aynı graf elde edilir:
    - service1 = GraphService(seed=42)
    - service2 = GraphService(seed=42)
    - service1.generate_graph(50, 0.1) == service2.generate_graph(50, 0.1)
    
    Attributes:
        seed (int): Rastgele sayı üreteci için seed (tekrarlanabilirlik)
        graph (nx.Graph): NetworkX graf objesi
        demands (List[DemandPair]): Talep çiftleri listesi
        _rng: NumPy rastgele sayı üreteci
        _data_source (str): Veri kaynağı ("generated" veya "csv")
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        GraphService Constructor
        ========================
        
        Servisi başlatır ve rastgele sayı üretecini hazırlar.
        
        Args:
            seed: Rastgele sayı üreteci seed değeri.
                  None ise settings'ten varsayılan değer alınır.
                  Aynı seed ile aynı graf oluşturulur (tekrarlanabilirlik).
        
        Example:
            # Deterministik (aynı sonuç her seferinde)
            service = GraphService(seed=42)
            
            # Stokastik (her seferinde farklı)
            service = GraphService(seed=None)
        """
        # ----------------------------------------------------------------
        # Seed değerini ayarla (tekrarlanabilir sonuçlar için önemli)
        # ----------------------------------------------------------------
        self.seed = seed if seed is not None else settings.RANDOM_SEED
        
        # ----------------------------------------------------------------
        # Graf ve talep verileri için başlangıç değerleri
        # ----------------------------------------------------------------
        self.graph: Optional[nx.Graph] = None    # Henüz graf oluşturulmadı
        self.demands: List[DemandPair] = []      # Talep listesi boş
        
        # ----------------------------------------------------------------
        # NumPy rastgele sayı üreteci (modern API)
        # ----------------------------------------------------------------
        # np.random.default_rng() kullanımı önerilir çünkü:
        # 1. Thread-safe (paralel işlemlerde güvenli)
        # 2. Daha iyi istatistiksel özellikler
        # 3. Deterministic (aynı seed = aynı sonuç)
        self._rng = np.random.default_rng(self.seed)
        
        # ----------------------------------------------------------------
        # Veri kaynağı takibi
        # ----------------------------------------------------------------
        # "generated": Rastgele oluşturuldu
        # "csv": CSV dosyalarından yüklendi
        self._data_source: str = "generated"


    # =================================================================================================================
    # CSV'DEN GRAF YÜKLEME METODLARI
    # =================================================================================================================
    
    def load_from_csv(self, data_dir: str) -> nx.Graph:
        """
        CSV Dosyalarından Graf Yükleme
        ==============================
        
        Bu metod, proje yönergesinde belirtilen formatta hazırlanmış
        CSV dosyalarını okuyarak NetworkX graf objesi oluşturur.
        
        BEKLENEN DOSYALAR:
        ------------------
        1. BSM307_317_Guz2025_TermProject_NodeData.csv
           Format: node_id; s_ms ;r_node
           Örnek:  0;1.5;0,99
           
        2. BSM307_317_Guz2025_TermProject_EdgeData.csv
           Format: src;dst;capacity_mbps;delay_ms;r_link
           Örnek:  0;1;500;5.2;0,98
           
        3. BSM307_317_Guz2025_TermProject_DemandData.csv
           Format: src;dst;demand_mbps
           Örnek:  0;249;100
        
        YÜKLEME ADMLARI:
        ----------------
        1. Dosya varlığını kontrol et
        2. Düğümleri yükle (processing_delay, reliability)
        3. Kenarları yükle (bandwidth, delay, reliability)
        4. Talepleri yükle (source, destination, demand_mbps)
        
        Args:
            data_dir: graph_data klasörünün yolu
            
        Returns:
            nx.Graph: Yüklenen NetworkX graf objesi
            
        Raises:
            FileNotFoundError: CSV dosyaları bulunamazsa
            
        Example:
            service = GraphService()
            graph = service.load_from_csv("./graph_data")
            print(f"Yüklenen düğüm sayısı: {graph.number_of_nodes()}")
        """
        # ----------------------------------------------------------------
        # CSV dosya yollarını oluştur
        # ----------------------------------------------------------------
        node_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_NodeData.csv")
        edge_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_EdgeData.csv")
        demand_file = os.path.join(data_dir, "BSM307_317_Guz2025_TermProject_DemandData.csv")
        
        # ----------------------------------------------------------------
        # Dosyaların varlığını kontrol et
        # ----------------------------------------------------------------
        for f in [node_file, edge_file, demand_file]:
            if not os.path.exists(f):
                raise FileNotFoundError(f"CSV dosyası bulunamadı: {f}")
        
        # ----------------------------------------------------------------
        # Boş NetworkX grafı oluştur (yönsüz graf)
        # ----------------------------------------------------------------
        # nx.Graph(): Yönsüz graf (edge A-B ve B-A aynı)
        # nx.DiGraph(): Yönlü graf (edge A->B ve B->A farklı)
        # Bu projede yönsüz graf kullanılıyor.
        G = nx.Graph()
        
        # ----------------------------------------------------------------
        # ADIM 1: Düğüm (Node) verilerini yükle
        # ----------------------------------------------------------------
        # Her düğüm: processing_delay ve reliability özelliklerine sahip
        self._load_nodes_from_csv(G, node_file)
        
        # ----------------------------------------------------------------
        # ADIM 2: Kenar (Edge) verilerini yükle
        # ----------------------------------------------------------------
        # Her kenar: bandwidth, delay ve reliability özelliklerine sahip
        self._load_edges_from_csv(G, edge_file)
        
        # ----------------------------------------------------------------
        # ADIM 3: Talep (Demand) verilerini yükle
        # ----------------------------------------------------------------
        # Kaynak-hedef çiftleri ve bant genişliği talepleri
        self._load_demands_from_csv(demand_file)
        
        # ----------------------------------------------------------------
        # Grafı sakla ve veri kaynağını işaretle
        # ----------------------------------------------------------------
        self.graph = G
        self._data_source = "csv"
        return G
    
    def _parse_turkish_float(self, value: str) -> float:
        """
        Türkçe Ondalık Sayı Dönüştürücü

        Args:
            value: Türkçe formatlı sayı string'i ("0,95")
            
        Returns:
            float: Python float değeri (0.95)
        """
        return float(value.replace(',', '.'))
    
    def _load_nodes_from_csv(self, G: nx.Graph, filepath: str) -> None:
        """
        Düğüm Verilerini CSV'den Yükle
        ==============================
        
        NodeData.csv dosyasından düğüm bilgilerini okur ve grafa ekler.
        
        CSV FORMAT:
        -----------
        Başlık: node_id;s_ms;r_node
        Veri:   0;1.5;0,99
        
        - node_id: Düğüm ID'si (integer)
        - s_ms: İşleme gecikmesi - processing_delay (float, ms)
        - r_node: Düğüm güvenilirliği - reliability (float, 0.0-1.0)
        
        Args:
            G: Düğümlerin ekleneceği NetworkX grafı
            filepath: NodeData.csv dosya yolu
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # İlk satır başlık: node_id;s_ms;r_node (atla)
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue  # Boş satırları atla
            
            parts = line.split(';')
            if len(parts) >= 3:
                node_id = int(parts[0])
                
                # s_ms -> processing_delay (Türkçe format)
                processing_delay = self._parse_turkish_float(parts[1])
                
                # r_node -> reliability (Türkçe format)
                reliability = self._parse_turkish_float(parts[2])
                
                # Düğümü grafa ekle
                G.add_node(node_id, 
                          processing_delay=processing_delay,
                          reliability=reliability)
    
    def _load_edges_from_csv(self, G: nx.Graph, filepath: str) -> None:
        """
        Kenar Verilerini CSV'den Yükle
        
        EdgeData.csv dosyasından kenar bilgilerini okur ve grafa ekler.
        
        CSV FORMAT:
        -----------
        Başlık: src;dst;capacity_mbps;delay_ms;r_link
        Veri:   0;1;500;5.2;0,98
        
        - src: Kaynak düğüm ID'si
        - dst: Hedef düğüm ID'si
        - capacity_mbps: Bant genişliği kapasitesi (Mbps)
        - delay_ms: Link gecikmesi (ms)
        - r_link: Link güvenilirliği (0.0-1.0)
        
        YÖNSÜZ GRAF:
        ------------
        nx.Graph() yönsüz olduğu için edge(0,1) = edge(1,0)
        Tek satır yeterli, iki yön ayrı yazılmaz.
        
        Args:
            G: Kenarların ekleneceği NetworkX grafı
            filepath: EdgeData.csv dosya yolu
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # İlk satır başlık (atla)
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(';')
            if len(parts) >= 5:
                src = int(parts[0])
                dst = int(parts[1])
                bandwidth = float(parts[2])      # capacity_mbps
                delay = float(parts[3])          # delay_ms
                reliability = self._parse_turkish_float(parts[4])  # r_link
                
                # Kenarı grafa ekle (özelliklerle birlikte)
                G.add_edge(src, dst,
                          bandwidth=bandwidth,
                          delay=delay,
                          reliability=reliability)
    
    def _load_demands_from_csv(self, filepath: str) -> None:
        """
        Talep Verilerini CSV'den Yükle
        ==============================
        
        DemandData.csv dosyasından kaynak-hedef talep çiftlerini okur.
        
        CSV FORMAT:
        -----------
        Başlık: src;dst;demand_mbps
        Veri:   0;249;100
        
        - src: Kaynak düğüm ID'si
        - dst: Hedef düğüm ID'si
        - demand_mbps: İstenen bant genişliği (Mbps)
        
        KULLANIM:
        ---------
        Bu talepler UI'da dropdown olarak gösterilir.
        Kullanıcı bir talep seçtiğinde optimizasyon o talep için çalışır.
        
        Args:
            filepath: DemandData.csv dosya yolu
        """
        self.demands = []  # Önceki talepleri temizle
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # İlk satır başlık (atla)
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(';')
            if len(parts) >= 3:
                src = int(parts[0])
                dst = int(parts[1])
                demand = int(parts[2])
                
                # DemandPair nesnesi oluştur ve listeye ekle
                self.demands.append(DemandPair(
                    source=src,
                    destination=dst,
                    demand_mbps=demand
                ))
    
    def get_demands(self) -> List[DemandPair]:
        """Yüklenen talep çiftlerini döndürür."""
        return self.demands
    
    def get_demand_pairs_for_ui(self) -> List[Tuple[int, int, int]]:
        """
        UI İçin Talep Çiftleri
        ======================
        
        Talep listesini UI bileşenlerinin kullanabileceği
        basit tuple formatına dönüştürür.
        
        Returns:
            List[Tuple[int, int, int]]: [(source, destination, demand_mbps), ...]
            
        Example:
            [(0, 249, 100), (10, 200, 50), ...]
        """
        return [(d.source, d.destination, d.demand_mbps) for d in self.demands]


    # ==================================================================================================================
    # RASTGELE GRAF OLUŞTURMA METODLARI
    # ==================================================================================================================
    
    def generate_graph(self, n_nodes: int = None, p: float = None) -> nx.Graph:
        """
        Rastgele Graf Oluşturma (Erdos–Renyi Modeli)
        ============================================
        
        Erdős–Rényi G(n, p) modeli ile rastgele graf oluşturur.
        
        ERDŐS–RÉNYI MODELİ:
        -------------------
        - n düğüm oluşturulur
        - Her düğüm çifti arasında p olasılıkla kenar eklenir
        - Beklenen kenar sayısı: n*(n-1)*p/2
        
        BAĞLILILIK GARANTİSİ:
        ---------------------
        Graf bağlı değilse (disconnected components varsa):
        1. Maksimum 100 deneme yapılır (farklı seed'lerle)
        2. Hâlâ bağlı değilse, bileşenler arası kenar eklenir
        
        Bu garanti sayesinde her zaman S'den D'ye yol vardır.
        
        Args:
            n_nodes: Düğüm sayısı (varsayılan: settings.DEFAULT_NODE_COUNT)
            p: Kenar olasılığı (varsayılan: settings.DEFAULT_CONNECTION_PROB)
            
        Returns:
            nx.Graph: Oluşturulan NetworkX graf objesi
            
        Raises:
            ValueError: n_nodes < 2 veya p ∉ (0, 1]
            
        Example:
            service = GraphService(seed=42)
            graph = service.generate_graph(n_nodes=100, p=0.05)
            print(f"Kenar sayısı: {graph.number_of_edges()}")
        """
        # ----------------------------------------------------------------
        # Varsayılan değerleri ayarla
        # ----------------------------------------------------------------
        n_nodes = n_nodes or settings.DEFAULT_NODE_COUNT
        p = p or settings.DEFAULT_CONNECTION_PROB
        
        # ----------------------------------------------------------------
        # Parametre doğrulama
        # ----------------------------------------------------------------
        if n_nodes < 2:
            raise ValueError("Node miktari en az 2 olmalidir.")
        if not 0 < p <= 1:
            raise ValueError("Baglanti olasiliği 0 ve 1 arasında olmalidir.")
        
        # ----------------------------------------------------------------
        # BAĞLI GRAF OLUŞTURMA DÖNGÜSÜ
        # ----------------------------------------------------------------
        # Düşük p değerlerinde graf bağlı olmayabilir.
        # Bu döngü bağlı graf bulana kadar farklı seed'ler dener.
        attempt = 0
        max_attempts = 100
        
        while attempt < max_attempts:
            # Erdős–Rényi graf oluştur
            G = nx.erdos_renyi_graph(n_nodes, p, seed=self.seed + attempt)
            
            # Bağlılık kontrolü
            if nx.is_connected(G):
                break  # Bağlı graf bulundu!
            
            attempt += 1
        else:
            # ----------------------------------------------------------------
            # FALLBACK: Bileşenleri manuel olarak bağla
            # ----------------------------------------------------------------
            # 100 denemede bağlı graf bulunamadıysa, bileşenler arasına
            # kenar ekleyerek zorla bağlı hale getir.
            G = nx.erdos_renyi_graph(n_nodes, p, seed=self.seed)
            components = list(nx.connected_components(G))
            
            # Her bileşen çiftini bağla
            for i in range(len(components) - 1):
                node1 = list(components[i])[0]
                node2 = list(components[i + 1])[0]
                G.add_edge(node1, node2)
        
        # ----------------------------------------------------------------
        # Düğüm ve kenar özelliklerini ata
        # ----------------------------------------------------------------
        self._assign_node_attributes(G)
        self._assign_edge_attributes(G)
        
        # ----------------------------------------------------------------
        # Grafı sakla ve döndür
        # ----------------------------------------------------------------
        self.graph = G
        self._data_source = "generated"
        self.demands = []  # Rastgele graf için demand yok
        return G
    
    def _assign_node_attributes(self, G: nx.Graph) -> None:
        """
        Düğüm Özelliklerini Ata
        =======================
        
        Rastgele oluşturulan grafa düğüm özellikleri ekler.
        
        ATANAN ÖZELLİKLER:
        ------------------
        1. processing_delay: Rastgele [PROCESSING_DELAY_MIN, PROCESSING_DELAY_MAX]
           Varsayılan: [0.5, 2.0] ms
           
        2. reliability: Rastgele [NODE_RELIABILITY_MIN, NODE_RELIABILITY_MAX]
           Varsayılan: [0.95, 0.999]
        
        Args:
            G: Özelliklerin ekleneceği NetworkX grafı
        """
        for node in G.nodes():
            # İşleme gecikmesi (ms) - uniform dağılım
            G.nodes[node]['processing_delay'] = self._rng.uniform(
                settings.PROCESSING_DELAY_MIN, 
                settings.PROCESSING_DELAY_MAX
            )
            
            # Düğüm güvenilirliği (0.0-1.0) - uniform dağılım
            G.nodes[node]['reliability'] = self._rng.uniform(
                settings.NODE_RELIABILITY_MIN, 
                settings.NODE_RELIABILITY_MAX
            )
    
    def _assign_edge_attributes(self, G: nx.Graph) -> None:
        """
        Kenar Özelliklerini Ata
        =======================
        
        Rastgele oluşturulan grafa kenar özellikleri ekler.
        
        ATANAN ÖZELLİKLER:
        ------------------
        1. bandwidth: Rastgele [BANDWIDTH_MIN, BANDWIDTH_MAX]
           Varsayılan: [100, 1000] Mbps
           
        2. delay: Rastgele [LINK_DELAY_MIN, LINK_DELAY_MAX]
           Varsayılan: [3, 15] ms
           
        3. reliability: Rastgele [LINK_RELIABILITY_MIN, LINK_RELIABILITY_MAX]
           Varsayılan: [0.95, 0.999]
        
        Args:
            G: Özelliklerin ekleneceği NetworkX grafı
        """
        for u, v in G.edges():
            # Bant genişliği (Mbps)
            G.edges[u, v]['bandwidth'] = self._rng.uniform(
                settings.BANDWIDTH_MIN, 
                settings.BANDWIDTH_MAX
            )
            
            # Link gecikmesi (ms)
            G.edges[u, v]['delay'] = self._rng.uniform(
                settings.LINK_DELAY_MIN, 
                settings.LINK_DELAY_MAX
            )
            
            # Link güvenilirliği
            G.edges[u, v]['reliability'] = self._rng.uniform(
                settings.LINK_RELIABILITY_MIN, 
                settings.LINK_RELIABILITY_MAX
            )


    # =========================================================================
    # GRAF BİLGİ SORGULAMA METODLARI
    # =========================================================================
    
    def get_graph_info(self) -> Dict[str, Any]:
        """
        Graf Bilgilerini Döndür
        =======================
        
        Mevcut grafın istatistiklerini ve meta bilgilerini döndürür.
        
        DÖNDÜRÜLEN BİLGİLER:
        --------------------
        - node_count: Düğüm sayısı
        - edge_count: Kenar sayısı
        - is_connected: Bağlılık durumu
        - average_degree: Ortalama düğüm derecesi
        - data_source: "generated" veya "csv"
        - seed: Sadece generated için
        - demand_count: Sadece csv için
        
        Returns:
            Dict: Graf istatistikleri
            
        Example:
            info = service.get_graph_info()
            print(f"Düğüm: {info['node_count']}, Kenar: {info['edge_count']}")
        """
        if self.graph is None:
            return {"error": "No graph generated yet"}
        
        # Temel istatistikler
        info = {
            "node_count": self.graph.number_of_nodes(),
            "edge_count": self.graph.number_of_edges(),
            "is_connected": nx.is_connected(self.graph),
            "average_degree": sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            "data_source": self._data_source
        }
        
        # Veri kaynağına göre ek bilgiler
        if self._data_source == "generated":
            info["seed"] = self.seed
        else:
            info["demand_count"] = len(self.demands)
        
        return info
    
    def get_node_positions(self, dim: int = 2) -> Dict[int, tuple]:
        """
        Düğüm Pozisyonlarını Hesapla
        ============================
        
        Graf görselleştirmesi için düğüm koordinatlarını hesaplar.
        Spring layout (yay-tabanlı yerleşim) algoritması kullanılır.
        
        SPRING LAYOUT:
        --------------
        - Düğümler birbirini iter (repulsion)
        - Kenarlar bağlı düğümleri çeker (attraction)
        - Sonuç: Estetik ve okunabilir graf çizimi
        
        Args:
            dim: Boyut sayısı (2 veya 3)
                 2: 2D görselleştirme için
                 3: 3D görselleştirme için
        
        Returns:
            Dict[int, tuple]: {node_id: (x, y) veya (x, y, z)}
            
        Example:
            pos_2d = service.get_node_positions(dim=2)
            pos_3d = service.get_node_positions(dim=3)
        """
        if self.graph is None:
            return {}
        
        # k parametresi: ideal düğüm-düğüm mesafesi
        # Düğüm sayısı arttıkça k küçülür (daha sıkı yerleşim)
        k = 2 / np.sqrt(self.graph.number_of_nodes())
        
        return nx.spring_layout(
            self.graph, 
            seed=self.seed,  # Tekrarlanabilir pozisyonlar
            k=k, 
            dim=dim
        )
    
    def has_path(self, source: int, destination: int) -> bool:
        """
        Yol Varlığı Kontrolü
        ====================
        
        İki düğüm arasında yol olup olmadığını kontrol eder.
        
        Args:
            source: Kaynak düğüm ID'si
            destination: Hedef düğüm ID'si
            
        Returns:
            bool: Yol varsa True, yoksa False
            
        Example:
            if service.has_path(0, 249):
                # Optimizasyon çalıştırılabilir
            else:
                print("Hedef ulaşılamaz!")
        """
        if self.graph is None:
            return False
        return nx.has_path(self.graph, source, destination)
    
    def get_neighbors(self, node: int) -> List[int]:
        """
        Komşu Düğümleri Getir
        =====================
        
        Belirtilen düğümün doğrudan bağlı olduğu komşularını döndürür.
        
        Args:
            node: Düğüm ID'si
            
        Returns:
            List[int]: Komşu düğüm ID'leri listesi
            
        Example:
            neighbors = service.get_neighbors(0)
            print(f"0 numaralı düğümün {len(neighbors)} komşusu var")
        """
        if self.graph is None:
            return []
        return list(self.graph.neighbors(node))
    
    def is_from_csv(self) -> bool:
        """
        CSV Kaynağı Kontrolü
        ====================
        
        Grafın CSV dosyalarından yüklenip yüklenmediğini döndürür.
        
        Returns:
            bool: CSV'den yüklendiyse True, rastgele oluşturulduysa False
            
        Kullanım:
            if service.is_from_csv():
                demands = service.get_demands()  # CSV'de demand var
        """
        return self._data_source == "csv"
