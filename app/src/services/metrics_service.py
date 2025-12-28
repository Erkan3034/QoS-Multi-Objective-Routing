"""
=============================================================================
METRİK HESAPLAMA SERVİSİ
=============================================================================

MODÜL AÇIKLAMASI:
-----------------
Bu modül, ağ yollarının QoS (Quality of Service) metriklerini hesaplar.
Tüm algoritmalar ve UI bu servisi kullanarak yol kalitesini değerlendirir.

HESAPLANAN METRİKLER:
---------------------
1. TOPLAM GECİKME (TotalDelay):
   - Formül: Σ(LinkDelay) + Σ(ProcessingDelay)
   - Not: ProcessingDelay sadece ARA düğümler için (S ve D hariç)
   - Birim: Milisaniye (ms)

2. GÜVENİLİRLİK MALİYETİ (ReliabilityCost):
   - Formül: Σ[-log(LinkReliability)] + Σ[-log(NodeReliability)]
   - Neden -log?: Çarpma işlemini toplama çevirir, düşük güvenilirliği cezalandırır
   - Örnek: rel=0.99 → -log(0.99)≈0.01, rel=0.5 → -log(0.5)≈0.69

3. KAYNAK MALİYETİ (ResourceCost):
   - Formül: Σ(1Gbps / Bandwidth)
   - OSPF-benzeri maliyet: Düşük bant genişliği = Yüksek maliyet
   - Örnek: 1000Mbps → cost=1, 100Mbps → cost=10

NORMALİZASYON:
--------------
Tüm metrikler 0.0-1.0 arasına normalize edilir:
- MAX_DELAY_MS = 200ms (bunun üzeri 1.0)
- MAX_RELIABILITY_COST = 10.0 (bunun üzeri 1.0)
- MAX_RESOURCE_COST = 200 (20 hop × 10 maliyet)

PROJE UYUMLULUĞU:
-----------------
[PROJECT COMPLIANCE] Proje yönergesindeki formüller birebir uygulanmaktadır.
"""

# =============================================================================
# KÜTÜPHANE İMPORTLARI
# =============================================================================
from dataclasses import dataclass      # Veri sınıfları için dekoratör
from typing import List, Optional, Tuple, Dict  # Tip belirteçleri
from functools import lru_cache        # Önbellekleme için dekoratör
import math                            # Logaritma hesaplaması için
import networkx as nx                  # Graf veri yapısı


# =============================================================================
# NORMALİZASYON SABİTLERİ
# =============================================================================
# Bu sabitler tüm algoritmalarda standart olarak kullanılır.
# Farklı birimlerdeki metriklerin adil karşılaştırılmasını sağlar.
class NormConfig:
    """
    Normalizasyon Konfigürasyonu
    
    Bu referans değerler, metrikleri 0.0-1.0 arasına normalize etmek için kullanılır.
    Değerler bu referansları aştığında 1.0 (maksimum ceza) olarak kabul edilir.
    """
    # Gecikme normalizasyonu: 200ms üzeri maksimum ceza
    MAX_DELAY_MS = 200.0
    
    # Hop sayısı referansı (kullanılmıyor, bilgi amaçlı)
    MAX_HOP_COUNT = 20.0
    
    # Güvenilirlik maliyeti normalizasyonu:
    # 20 hop × 0.95 güvenilirlik = 40 element × -log(0.95) ≈ 2.0
    # Düşük güvenilirlik: -log(0.001) ≈ 6.9 per element
    # Makul maksimum: 10.0
    MAX_RELIABILITY_COST = 10.0


# =============================================================================
# YOL METRİKLERİ VERİ SINIFI
# =============================================================================
@dataclass
class PathMetrics:
    """
    Yol Metrikleri Veri Sınıfı
    
    Bir yolun tüm QoS metriklerini tek bir objede toplar.
    
    Attributes:
        total_delay (float): Toplam gecikme (ms) - ham değer
        total_reliability (float): Toplam güvenilirlik (0.0-1.0) - çarpım sonucu
        resource_cost (float): Normalize kaynak maliyeti (0.0-1.0)
        weighted_cost (float): Ağırlıklı toplam maliyet (0.0-1.0)
        min_bandwidth (float): Yoldaki minimum bant genişliği (darboğaz)
        reliability_cost (float): Ham -log güvenilirlik maliyeti
    """
    total_delay: float           # Toplam gecikme (ms)
    total_reliability: float     # Çarpımsal güvenilirlik (0.0-1.0)
    resource_cost: float         # Normalize kaynak maliyeti
    weighted_cost: float         # Ağırlıklı toplam (fitness değeri)
    min_bandwidth: float = float('inf')  # Darboğaz bant genişliği
    reliability_cost: float = 0.0        # Ham -log maliyeti


# =============================================================================
# METRİK SERVİSİ ANA SINIFI
# =============================================================================
class MetricsService:
    """
    Metrik Hesaplama Servisi
    
    Bir NetworkX graf üzerinde yol metriklerini hesaplar.
    Tüm optimizasyon algoritmaları bu servisi ortak kullanır.
    
    Ana Fonksiyonlar:
    1. calculate_all(): Tüm metrikleri hesapla, PathMetrics döndür
    2. calculate_weighted_cost(): Sadece ağırlıklı maliyeti hesapla
    3. calculate_weighted_cost_cached(): Önbellekli versiyon (performans)
    
    [PROJECT COMPLIANCE] Proje yönergesindeki -log formülü kullanılır.
    """

    def __init__(self, graph: nx.Graph):
        """
        MetricsService constructor.
        
        Args:
            graph: Metriklerin hesaplanacağı NetworkX graf objesi
        """
        self.graph = graph  # Graf referansını sakla
    # =========================================================================
    # ÖNBELLEKLİ MALİYET HESAPLAMA
    # =========================================================================
    
    @lru_cache(maxsize=10000)
    def calculate_weighted_cost_cached(
        self, 
        path_tuple: tuple, 
        delay_w: float, 
        reliability_w: float, 
        resource_w: float,
        bw_demand: float = 0.0
    ) -> float:
        """
        Önbellekli ağırlıklı maliyet hesaplama.
        
        Aynı yol ve ağırlıklarla tekrarlanan sorgular için önbellekleme yapar.
        Bu, algoritma iterasyonlarında performansı önemli ölçüde artırır.
        
        Not: lru_cache hashable parametreler gerektirir, bu yüzden
        path list yerine tuple olarak alınır.
        
        Args:
            path_tuple: Düğüm ID'leri tuple'i (hashable olmalı)
            delay_w: Gecikme ağırlığı (0.0-1.0)
            reliability_w: Güvenilirlik ağırlığı (0.0-1.0)
            resource_w: Kaynak ağırlığı (0.0-1.0)
            bw_demand: Bant genişliği talebi (Mbps)
            
        Returns:
            float: Ağırlıklı maliyet (0.0-1.0) veya inf (geçersiz yol)
        """
        return self.calculate_weighted_cost(list(path_tuple), delay_w, reliability_w, resource_w, bw_demand)

    # =========================================================================
    # ANA METRİK HESAPLAMA METODU
    # =========================================================================
    
    def calculate_all(self, path: List[int], delay_w: float, reliability_w: float, resource_w: float) -> PathMetrics:
        """
        Bir yolun tüm QoS metriklerini hesaplar.
        
        Bu metod, yol üzerindeki tüm düğüm ve kenarları dolaşarak
        proje yönergesindeki formüllere göre metrikleri hesaplar.
        
        HESAPLAMA ADIMLARI:
        1. Düğüm metrikleri: ProcessingDelay (S,D hariç), NodeReliability (tümü)
        2. Kenar metrikleri: LinkDelay, LinkReliability, Bandwidth
        3. Normalizasyon: Tüm metrikleri 0.0-1.0 arasına sıkıştır
        4. Ağırlıklı toplam: Kullanıcı ağırlıklarıyla birleştir
        
        [PROJECT COMPLIANCE] 
        - ProcessingDelay: Sadece ara düğümler (S ve D hariç)
        - ReliabilityCost: Tüm düğümler dahil, -log formülü
        
        Args:
            path: Düğüm ID listesi [kaynak, ..., hedef]
            delay_w: Gecikme ağırlığı (0.0-1.0)
            reliability_w: Güvenilirlik ağırlığı (0.0-1.0)
            resource_w: Kaynak ağırlığı (0.0-1.0)
            
        Returns:
            PathMetrics: Tüm metrikleri içeren veri objesi
        """
        # GEÇERSİZ YOL KONTROLÜ
        # En az 2 düğüm olmalı (kaynak ve hedef)
        if not path or len(path) < 2:
            return PathMetrics(0.0, 0.0, 0.0, float('inf'), 0.0, 0.0)

        # METRİK DEĞİŞKENLERİNİ BAŞLAT
        total_delay = 0.0          # Toplam gecikme (ms)
        total_reliability = 1.0    # Çarpımsal güvenilirlik
        reliability_cost = 0.0     # -log toplamı
        min_bw = float('inf')      # Darboğaz bant genişliği
        
        # [PROJECT COMPLIANCE] Kaynak ve Hedef düğümleri belirle
        source = path[0]           # İlk düğüm = Kaynak (S)
        destination = path[-1]     # Son düğüm = Hedef (D)
        
        # ==================== DÜĞÜM METRİKLERİ ====================
        for node in path:
            # [PROJECT COMPLIANCE] ProcessingDelay: Sadece ARA düğümler
            # Kaynak ve Hedef düğümlerin işleme gecikmesi hesaplanmaz
            if node != source and node != destination:
                pd = self.graph.nodes[node].get('processing_delay', 0.0)
                total_delay += float(pd)
            
            # [PROJECT COMPLIANCE] NodeReliability: TÜM düğümler dahil
            # Güvenilirlik çarpımsal (P(A∩B) = P(A) × P(B))
            nr = float(self.graph.nodes[node].get('reliability', 1.0))
            total_reliability *= nr
            # -log dönüşümü: çarpımı toplama çevirir
            reliability_cost += -math.log(max(nr, 0.001))  # 0'a bölme önleme

        # ==================== KENAR METRİKLERİ ====================
        for u, v in zip(path[:-1], path[1:]):
            # Kenar varlığını kontrol et
            if self.graph.has_edge(u, v):
                edge = self.graph.edges[u, v]
                
                # Link Delay (gecikme)
                edelay = edge.get('delay', 0.0)
                total_delay += float(edelay)
                
                # Link Reliability (güvenilirlik)
                ereliability = float(edge.get('reliability', 1.0))
                total_reliability *= ereliability
                reliability_cost += -math.log(max(ereliability, 0.001))
                
                # Bandwidth (bant genişliği) - darboğazı bul
                bandwidth = edge.get('bandwidth', 1000.0)
                min_bw = min(min_bw, float(bandwidth))
            else:
                # Kenar yoksa yol geçersiz
                return PathMetrics(0.0, 0.0, 0.0, float('inf'), 0.0, 0.0)

        # --- NORMALIZED SCORING (The "Fair" Calculation) ---
        
        # 1. Normalize Delay
        norm_delay = min(total_delay / NormConfig.MAX_DELAY_MS, 1.0)
        
        # 2. Normalize Reliability Cost (using -log formula)
        # [PROJECT COMPLIANCE] This replaces the old (1-rel)*10 formula
        norm_rel = min(reliability_cost / NormConfig.MAX_RELIABILITY_COST, 1.0)
        
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
            resource_cost=norm_resource,  # Storing normalized resource cost
            weighted_cost=weighted_cost,
            min_bandwidth=min_bw,
            reliability_cost=reliability_cost  # [PROJECT COMPLIANCE] Raw -log cost
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
