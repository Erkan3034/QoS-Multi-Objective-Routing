"""
Test Senaryoları Modülü
=======================
Bu modül, toplu deney özelliği için test senaryolarını oluşturur ve yönetir.

AMAÇ:
-----
- Algoritmaların performansını karşılaştırmak için standart test setleri oluşturmak
- Her senaryo: Kaynak (S), Hedef (D), Bant Genişliği (B) içerir
- Tekrarlanabilirlik için seed kullanılır

KULLANIM:
---------
generator = TestCaseGenerator(graph, seed=42)
test_cases = generator.get_predefined_test_cases()  # 25 senaryo döner
"""

import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import networkx as nx


# =============================================================================
# VERİ SINIFLARI
# =============================================================================

@dataclass
class TestCase:
    """
    Tek bir test senaryosunu temsil eder.
    
    Örnek:
        TestCase(id=1, source=5, destination=20, bandwidth_requirement=500, ...)
        → "Düğüm 5'ten 20'ye 500 Mbps bant genişliği gerektiren yol bul"
    """
    id: int                        # Senaryo numarası (1, 2, ..., 25)
    source: int                    # Kaynak düğüm (S)
    destination: int               # Hedef düğüm (D)
    bandwidth_requirement: float   # Gereken minimum bant genişliği (Mbps)
    weights: Dict[str, float]      # Optimizasyon ağırlıkları {delay, reliability, resource}
    description: str               # İnsan okunabilir açıklama

    def to_dict(self) -> Dict:
        """JSON/CSV export için dictionary'e dönüştür."""
        return {
            "id": self.id, 
            "source": self.source, 
            "destination": self.destination,
            "bandwidth_requirement": self.bandwidth_requirement,
            "weights": self.weights, 
            "description": self.description
        }


@dataclass
class TestResult:
    """
    Bir test senaryosunun çalıştırılma sonucunu tutar.
    
    Başarılı: success=True, path=[5, 8, 12, 20], total_cost=0.42
    Başarısız: success=False, failure_reason="Yetersiz Bant Genişliği"
    """
    test_case: TestCase                         # Hangi senaryo için
    algorithm_name: str                         # Hangi algoritma kullanıldı
    success: bool                               # Yol bulundu mu?
    execution_time_ms: float                    # Hesaplama süresi (ms)
    path: List[int] = field(default_factory=list)  # Bulunan yol [S, ..., D]
    path_min_bandwidth: Optional[float] = None  # Yoldaki en düşük BW (darboğaz)
    total_cost: Optional[float] = None          # Toplam maliyet (başarılıysa)
    failure_reason: Optional[str] = None        # Başarısızlık sebebi


# =============================================================================
# TEST SENARYO ÜRETİCİ
# =============================================================================

class TestCaseGenerator:
    """
    Test Senaryosu Oluşturucu
    -------------------------
    Graf üzerinde rastgele (S, D, B) kombinasyonları üretir.
    
    Neden seed kullanıyoruz?
    - seed=42 → Her çalışmada AYNI 25 senaryo üretilir (tekrarlanabilirlik)
    - Farklı seed → Farklı senaryolar
    
    Örnek:
        generator = TestCaseGenerator(graph, seed=42)
        cases = generator.get_predefined_test_cases()
        # Her zaman aynı 25 senaryo döner
    """
    
    def __init__(self, graph: nx.Graph, seed: int = 42):
        """
        Args:
            graph: Test edilecek NetworkX graf objesi
            seed: Rastgelelik tohumu (tekrarlanabilirlik için sabit tut)
        """
        self.graph = graph
        self.nodes = list(graph.nodes())
        random.seed(seed)  # Determinizm: Aynı seed = aynı senaryolar

    def generate_test_cases(self, n_cases: int = 25) -> List[TestCase]:
        """
        Belirtilen sayıda test senaryosu üret.
        
        UI (arayüz) tarafından çağrılır.
        
        Args:
            n_cases: Üretilecek senaryo sayısı (varsayılan: 25)
        
        Returns:
            İlk n_cases adet test senaryosu listesi
        """
        return self.get_predefined_test_cases()[:n_cases]

    def get_predefined_test_cases(self) -> List[TestCase]:
        """
        25 adet standart test senaryosu üret.
        
        SENARYO ÜRETİM MATRİSİ:
        -----------------------
        - Kaynak (S): Graf düğümlerinden rastgele seçilir
        - Hedef (D): S'den farklı, rastgele seçilir
        - Bant Genişliği (B): 100, 200, ..., 1000 Mbps arasından rastgele
        - Ağırlıklar: 4 FARKLI PROFİL (döngüsel olarak atanır)
        
        AĞIRLIK PROFİLLERİ:
        -------------------
        1. Gecikme Odaklı: delay=0.7, reliability=0.2, resource=0.1
        2. Güvenilirlik Odaklı: delay=0.2, reliability=0.7, resource=0.1
        3. Kaynak Odaklı: delay=0.2, reliability=0.1, resource=0.7
        4. Dengeli: delay=0.33, reliability=0.33, resource=0.34
        """
        cases = []
        
        # 10 farklı bant genişliği seviyesi (100 Mbps adımlarla)
        bw_levels = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        
        # 4 farklı ağırlık profili
        weight_profiles = [
            {"name": "Gecikme", "delay": 0.7, "reliability": 0.2, "resource": 0.1},
            {"name": "Güvenilirlik", "delay": 0.2, "reliability": 0.7, "resource": 0.1},
            {"name": "Kaynak", "delay": 0.2, "reliability": 0.1, "resource": 0.7},
            {"name": "Dengeli", "delay": 0.33, "reliability": 0.33, "resource": 0.34},
        ]
        
        for i in range(1, 26):  # 25 senaryo üret
            # Rastgele kaynak ve hedef seç (farklı olmalı)
            s, d = random.sample(self.nodes, 2)
            
            # Rastgele bant genişliği gereksinimi seç
            bw = random.choice(bw_levels)
            
            # Döngüsel olarak ağırlık profili seç (1-4, 5-8, 9-12, ...)
            profile = weight_profiles[(i - 1) % 4]
            weights = {
                "delay": profile["delay"],
                "reliability": profile["reliability"],
                "resource": profile["resource"]
            }
            
            # Test senaryosu oluştur
            cases.append(TestCase(
                id=i,
                source=s,
                destination=d,
                bandwidth_requirement=bw,
                weights=weights,
                description=f"Senaryo {i}: {s}->{d} ({bw}Mbps) [{profile['name']}]"
            ))
        
        return cases


# =============================================================================
# BANT GENİŞLİĞİ KISIT DENETLEYİCİ
# =============================================================================

class BandwidthConstraintChecker:
    """
    Bant Genişliği Kısıt Denetleyicisi
    ----------------------------------
    Bulunan yolun bant genişliği gereksinimini karşılayıp karşılamadığını kontrol eder.
    
    ÇALIŞMA PRENSİBİ:
    1. Yoldaki her kenarın bant genişliğini kontrol et
    2. En düşük değeri bul (darboğaz)
    3. Darboğaz >= gereksinim ise BAŞARILI, değilse BAŞARISIZ
    
    Örnek:
        Yol: [5, 8, 12, 20]
        Kenar BW'leri: (5→8)=500, (8→12)=400, (12→20)=600
        Darboğaz: 400 Mbps
        Gereksinim: 500 Mbps
        Sonuç: BAŞARISIZ (400 < 500)
    """
    
    def __init__(self, graph: nx.Graph):
        """
        Args:
            graph: Bant genişliği bilgisi içeren NetworkX graf
        """
        self.graph = graph

    def check_constraint(self, path: List[int], requirement: float) -> Tuple[bool, float, str]:
        """
        Yolun bant genişliği kısıtını karşılayıp karşılamadığını kontrol et.
        
        Args:
            path: Kontrol edilecek yol [kaynak, ..., hedef]
            requirement: Gereken minimum bant genişliği (Mbps)
        
        Returns:
            Tuple[bool, float, str]:
                - bool: Kısıt karşılandı mı?
                - float: Yoldaki minimum (darboğaz) bant genişliği
                - str: Sonuç mesajı
        
        Olası Sonuçlar:
            (True, 600.0, "Başarılı") → Yol uygun
            (False, 400.0, "Yetersiz Bant Genişliği") → Darboğaz < gereksinim
            (False, 0.0, "Yol bulunamadı") → Boş yol
            (False, 0.0, "Bağlantı kopuk") → Yolda olmayan kenar var
        """
        # Boş veya tek düğümlü yol geçersiz
        if not path or len(path) < 2:
            return False, 0.0, "Yol bulunamadı"
        
        # Yoldaki minimum bant genişliğini bul (darboğaz)
        min_bw = float('inf')
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            
            # Kenar var mı kontrol et
            if not self.graph.has_edge(u, v):
                return False, 0.0, "Bağlantı kopuk"
            
            # Bu kenarın bant genişliğini al
            edge_bw = self.graph.edges[u, v].get('bandwidth', 0)
            min_bw = min(min_bw, edge_bw)
        
        # Darboğaz kontrolü
        if min_bw < requirement:
            return False, min_bw, "Yetersiz Bant Genişliği"
        
        return True, min_bw, "Başarılı"
