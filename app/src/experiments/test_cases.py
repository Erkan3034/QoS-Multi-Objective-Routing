"""
Test Case Generator

PDF Gereksinimleri:
- 20+ farklı (S, D, B) kombinasyonu
- S: Kaynak düğüm
- D: Hedef düğüm  
- B: Talep edilen bant genişliği
- Başarısız/uygunsuz örnekler gerekçeleriyle raporlanmalı
"""
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import networkx as nx


@dataclass
class TestCase:
    """
    Tek bir test case.
    
    PDF Gereksinimi: (S, D, B) üçlüsü
    """
    id: int
    source: int                    # S: Kaynak düğüm
    destination: int               # D: Hedef düğüm
    bandwidth_requirement: float   # B: Talep edilen bant genişliği (Mbps)
    weights: Dict[str, float]
    description: str
    
    def to_dict(self) -> Dict:
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
    Test sonucu - başarılı veya başarısız.
    
    PDF Gereksinimi: Başarısız örnekler gerekçeleriyle raporlanmalı
    """
    test_case: TestCase
    success: bool
    failure_reason: Optional[str] = None
    path: List[int] = field(default_factory=list)
    path_min_bandwidth: Optional[float] = None
    metrics: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        result = {
            "test_case_id": self.test_case.id,
            "source": self.test_case.source,
            "destination": self.test_case.destination,
            "bandwidth_requirement": self.test_case.bandwidth_requirement,
            "success": self.success,
        }
        
        if self.success:
            result["path"] = self.path
            result["path_min_bandwidth"] = self.path_min_bandwidth
            result["metrics"] = self.metrics
        else:
            result["failure_reason"] = self.failure_reason
            
        return result


# Bant genişliği gereksinimleri (Mbps)
BANDWIDTH_REQUIREMENTS = [
    100,   # Düşük - çoğu yol karşılar
    200,   # Orta-düşük
    300,   # Orta
    400,   # Orta-yüksek
    500,   # Yüksek - bazı yollar karşılamayabilir
    600,   # Çok yüksek
    700,   # Kritik
    800,   # Çok kritik
    900,   # Neredeyse maksimum
    1000,  # Maksimum - sadece en iyi bağlantılar
]


class TestCaseGenerator:
    """
    Test case üretici.
    
    PDF Gereksinimi:
    - 20+ farklı (S, D, B) test senaryosu
    - Farklı mesafelerde S-D çiftleri
    - Farklı bant genişliği gereksinimleri
    - Farklı ağırlık kombinasyonları
    """
    
    # Önceden tanımlanmış ağırlık senaryoları
    WEIGHT_SCENARIOS = [
        {"delay": 1.0, "reliability": 0.0, "resource": 0.0, "name": "Sadece Gecikme"},
        {"delay": 0.0, "reliability": 1.0, "resource": 0.0, "name": "Sadece Güvenilirlik"},
        {"delay": 0.0, "reliability": 0.0, "resource": 1.0, "name": "Sadece Kaynak"},
        {"delay": 0.5, "reliability": 0.5, "resource": 0.0, "name": "Gecikme + Güvenilirlik"},
        {"delay": 0.5, "reliability": 0.0, "resource": 0.5, "name": "Gecikme + Kaynak"},
        {"delay": 0.0, "reliability": 0.5, "resource": 0.5, "name": "Güvenilirlik + Kaynak"},
        {"delay": 0.33, "reliability": 0.33, "resource": 0.34, "name": "Eşit Ağırlık"},
        {"delay": 0.6, "reliability": 0.2, "resource": 0.2, "name": "Gecikme Öncelikli"},
        {"delay": 0.2, "reliability": 0.6, "resource": 0.2, "name": "Güvenilirlik Öncelikli"},
        {"delay": 0.2, "reliability": 0.2, "resource": 0.6, "name": "Kaynak Öncelikli"},
    ]
    
    def __init__(self, graph: nx.Graph, seed: int = 42):
        """
        TestCaseGenerator oluşturur.
        
        Args:
            graph: NetworkX graf objesi
            seed: Rastgele seed
        """
        self.graph = graph
        self.n_nodes = graph.number_of_nodes()
        random.seed(seed)
    
    def generate_test_cases(self, n_cases: int = 25) -> List[TestCase]:
        """
        Test case'leri üretir.
        
        PDF Gereksinimi: En az 20 farklı (S, D, B) örneği
        
        Args:
            n_cases: Üretilecek test sayısı (minimum 20)
        
        Returns:
            TestCase listesi
        """
        n_cases = max(n_cases, 20)  # PDF: en az 20
        test_cases = []
        
        # S-D çiftleri oluştur
        sd_pairs = self._generate_sd_pairs(n_cases)
        
        for i, (source, dest) in enumerate(sd_pairs):
            # Her S-D çifti için ağırlık senaryosu ve B değeri seç
            scenario = self.WEIGHT_SCENARIOS[i % len(self.WEIGHT_SCENARIOS)]
            bandwidth_req = BANDWIDTH_REQUIREMENTS[i % len(BANDWIDTH_REQUIREMENTS)]
            
            test_cases.append(TestCase(
                id=i + 1,
                source=source,
                destination=dest,
                bandwidth_requirement=bandwidth_req,
                weights={
                    "delay": scenario["delay"],
                    "reliability": scenario["reliability"],
                    "resource": scenario["resource"]
                },
                description=f"S={source} -> D={dest}, B={bandwidth_req}Mbps, {scenario['name']}"
            ))
        
        return test_cases
    
    def _generate_sd_pairs(self, n_pairs: int) -> List[Tuple[int, int]]:
        """
        Kaynak-Hedef çiftleri oluşturur.
        
        Farklı mesafelerde çiftler seçer:
        - Kısa mesafe (hop < 3)
        - Orta mesafe (3 <= hop <= 5)
        - Uzun mesafe (hop > 5)
        """
        pairs = []
        nodes = list(self.graph.nodes())
        
        short_pairs = []
        medium_pairs = []
        long_pairs = []
        
        attempts = 0
        max_attempts = 1000
        
        while len(pairs) < n_pairs and attempts < max_attempts:
            source = random.choice(nodes)
            dest = random.choice(nodes)
            
            if source == dest or (source, dest) in pairs:
                attempts += 1
                continue
            
            try:
                path_length = nx.shortest_path_length(self.graph, source, dest)
                
                if path_length < 3 and len(short_pairs) < n_pairs // 3:
                    short_pairs.append((source, dest))
                    pairs.append((source, dest))
                elif 3 <= path_length <= 5 and len(medium_pairs) < n_pairs // 3:
                    medium_pairs.append((source, dest))
                    pairs.append((source, dest))
                elif path_length > 5 and len(long_pairs) < n_pairs // 3:
                    long_pairs.append((source, dest))
                    pairs.append((source, dest))
                elif len(pairs) < n_pairs:
                    pairs.append((source, dest))
            
            except nx.NetworkXNoPath:
                pass
            
            attempts += 1
        
        # Eğer yeterli çift bulunamazsa rastgele tamamla
        while len(pairs) < n_pairs:
            source = random.choice(nodes)
            dest = random.choice(nodes)
            if source != dest and (source, dest) not in pairs:
                pairs.append((source, dest))
        
        return pairs[:n_pairs]
    
    def check_bandwidth_constraint(
        self, 
        path: List[int], 
        bandwidth_requirement: float
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Yolun bant genişliği kısıtını karşılayıp karşılamadığını kontrol eder.
        
        Args:
            path: Düğüm listesi
            bandwidth_requirement: Gereken minimum bant genişliği (Mbps)
        
        Returns:
            (karşılar_mı, yol_min_bandwidth, hata_nedeni)
        """
        if len(path) < 2:
            return False, 0, "Geçersiz yol: En az 2 düğüm gerekli"
        
        min_bandwidth = float('inf')
        bottleneck_edge = None
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            
            if not self.graph.has_edge(u, v):
                return False, 0, f"Geçersiz yol: {u}-{v} arasında bağlantı yok"
            
            edge_bandwidth = self.graph.edges[u, v]['bandwidth']
            
            if edge_bandwidth < min_bandwidth:
                min_bandwidth = edge_bandwidth
                bottleneck_edge = (u, v)
        
        if min_bandwidth >= bandwidth_requirement:
            return True, min_bandwidth, None
        else:
            return False, min_bandwidth, (
                f"Bant genişliği yetersiz: Yolun minimum bant genişliği {min_bandwidth:.1f} Mbps, "
                f"gereken {bandwidth_requirement:.1f} Mbps. Darboğaz: {bottleneck_edge[0]}-{bottleneck_edge[1]}"
            )
    
    def get_predefined_test_cases(self) -> List[TestCase]:
        """
        PDF için önceden tanımlanmış 25 test senaryosu.
        
        Farklı (S, D, B) kombinasyonları içerir.
        """
        n = self.n_nodes
        
        predefined = [
            # === DÜŞÜK BANT GENİŞLİĞİ (100-200 Mbps) - Çoğu yol karşılar ===
            TestCase(1, 0, n-1, 100, 
                    {"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                    "İlk->Son, B=100Mbps, Eşit ağırlık"),
            TestCase(2, 0, n//2, 150,
                    {"delay": 0.6, "reliability": 0.2, "resource": 0.2},
                    "İlk->Orta, B=150Mbps, Gecikme öncelikli"),
            TestCase(3, n//4, 3*n//4, 200,
                    {"delay": 0.2, "reliability": 0.6, "resource": 0.2},
                    "Çeyrek arası, B=200Mbps, Güvenilirlik öncelikli"),
            TestCase(4, 10, 240, 100,
                    {"delay": 0.2, "reliability": 0.2, "resource": 0.6},
                    "10->240, B=100Mbps, Kaynak öncelikli"),
            TestCase(5, 50, 200, 150,
                    {"delay": 1.0, "reliability": 0.0, "resource": 0.0},
                    "50->200, B=150Mbps, Sadece gecikme"),
            
            # === ORTA BANT GENİŞLİĞİ (300-500 Mbps) ===
            TestCase(6, 0, n-1, 300,
                    {"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                    "İlk->Son, B=300Mbps, Eşit ağırlık"),
            TestCase(7, 25, 225, 400,
                    {"delay": 0.0, "reliability": 1.0, "resource": 0.0},
                    "25->225, B=400Mbps, Sadece güvenilirlik"),
            TestCase(8, 100, 150, 350,
                    {"delay": 0.5, "reliability": 0.5, "resource": 0.0},
                    "100->150, B=350Mbps, Gecikme+Güvenilirlik"),
            TestCase(9, 75, 175, 450,
                    {"delay": 0.0, "reliability": 0.0, "resource": 1.0},
                    "75->175, B=450Mbps, Sadece kaynak"),
            TestCase(10, 30, 220, 500,
                    {"delay": 0.4, "reliability": 0.4, "resource": 0.2},
                    "30->220, B=500Mbps, Gecikme+Güvenilirlik ağırlıklı"),
            
            # === YÜKSEK BANT GENİŞLİĞİ (600-800 Mbps) - Bazı yollar başarısız olabilir ===
            TestCase(11, 0, n-1, 600,
                    {"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                    "İlk->Son, B=600Mbps, Eşit ağırlık"),
            TestCase(12, 5, 245, 650,
                    {"delay": 0.6, "reliability": 0.2, "resource": 0.2},
                    "5->245, B=650Mbps, Gecikme öncelikli"),
            TestCase(13, n//2-25, n//2+25, 700,
                    {"delay": 0.2, "reliability": 0.6, "resource": 0.2},
                    "Orta bölge, B=700Mbps, Güvenilirlik öncelikli"),
            TestCase(14, 60, 190, 750,
                    {"delay": 0.5, "reliability": 0.0, "resource": 0.5},
                    "60->190, B=750Mbps, Gecikme+Kaynak"),
            TestCase(15, 80, 170, 800,
                    {"delay": 0.0, "reliability": 0.5, "resource": 0.5},
                    "80->170, B=800Mbps, Güvenilirlik+Kaynak"),
            
            # === ÇOK YÜKSEK BANT GENİŞLİĞİ (850-1000 Mbps) - Çoğu yol başarısız olabilir ===
            TestCase(16, 0, n-1, 850,
                    {"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                    "İlk->Son, B=850Mbps, Eşit ağırlık"),
            TestCase(17, 0, 100, 900,
                    {"delay": 1.0, "reliability": 0.0, "resource": 0.0},
                    "0->100, B=900Mbps, Sadece gecikme"),
            TestCase(18, 100, n-1, 950,
                    {"delay": 0.0, "reliability": 1.0, "resource": 0.0},
                    "100->Son, B=950Mbps, Sadece güvenilirlik"),
            TestCase(19, n//4, n//2, 1000,
                    {"delay": 0.0, "reliability": 0.0, "resource": 1.0},
                    "Çeyrek->Yarı, B=1000Mbps, Sadece kaynak"),
            TestCase(20, 0, n//4, 1000,
                    {"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                    "İlk->Çeyrek, B=1000Mbps, Eşit ağırlık"),
            
            # === EK SENARYOLAR (Kenar durumlar) ===
            TestCase(21, 0, 1, 100,
                    {"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                    "Komşu düğümler, B=100Mbps (baseline)"),
            TestCase(22, 0, 1, 1000,
                    {"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                    "Komşu düğümler, B=1000Mbps (stres testi)"),
            TestCase(23, n//2, n//2+1, 500,
                    {"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                    "Orta komşular, B=500Mbps"),
            TestCase(24, 1, n-2, 300,
                    {"delay": 0.4, "reliability": 0.3, "resource": 0.3},
                    "İkinci->Sondan ikinci, B=300Mbps"),
            TestCase(25, n//3, 2*n//3, 700,
                    {"delay": 0.3, "reliability": 0.3, "resource": 0.4},
                    "Üçte bir noktaları, B=700Mbps"),
        ]
        
        return predefined


class BandwidthConstraintChecker:
    """
    Bant genişliği kısıtı kontrol sınıfı.
    
    PDF Gereksinimi: Yolun B (talep edilen bant genişliği) değerini
    karşılayıp karşılamadığını kontrol eder.
    """
    
    def __init__(self, graph: nx.Graph):
        self.graph = graph
    
    def get_path_min_bandwidth(self, path: List[int]) -> float:
        """Yoldaki minimum bant genişliğini hesaplar."""
        if len(path) < 2:
            return 0
        
        min_bw = float('inf')
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if self.graph.has_edge(u, v):
                min_bw = min(min_bw, self.graph.edges[u, v]['bandwidth'])
            else:
                return 0
        
        return min_bw if min_bw != float('inf') else 0
    
    def check_constraint(
        self, 
        path: List[int], 
        bandwidth_requirement: float
    ) -> Tuple[bool, str]:
        """
        Yolun bant genişliği kısıtını kontrol eder.
        
        Returns:
            (başarılı_mı, açıklama)
        """
        min_bw = self.get_path_min_bandwidth(path)
        
        if min_bw == 0:
            return False, "Geçersiz yol"
        
        if min_bw >= bandwidth_requirement:
            return True, f"Yeterli bant genişliği: {min_bw:.1f} >= {bandwidth_requirement:.1f} Mbps"
        else:
            return False, f"Yetersiz bant genişliği: {min_bw:.1f} < {bandwidth_requirement:.1f} Mbps"
    
    def find_bottleneck(self, path: List[int]) -> Optional[Tuple[int, int, float]]:
        """Yoldaki darboğaz bağlantıyı bulur."""
        if len(path) < 2:
            return None
        
        min_bw = float('inf')
        bottleneck = None
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if self.graph.has_edge(u, v):
                bw = self.graph.edges[u, v]['bandwidth']
                if bw < min_bw:
                    min_bw = bw
                    bottleneck = (u, v, bw)
        
        return bottleneck

