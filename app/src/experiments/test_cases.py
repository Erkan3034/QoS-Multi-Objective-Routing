import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import networkx as nx

@dataclass
class TestCase:
    id: int
    source: int
    destination: int
    bandwidth_requirement: float
    weights: Dict[str, float]
    description: str

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "source": self.source, "destination": self.destination,
            "bandwidth_requirement": self.bandwidth_requirement,
            "weights": self.weights, "description": self.description
        }

@dataclass
class TestResult:
    test_case: TestCase
    algorithm_name: str
    success: bool
    execution_time_ms: float
    path: List[int] = field(default_factory=list)
    path_min_bandwidth: Optional[float] = None
    total_cost: Optional[float] = None
    failure_reason: Optional[str] = None

class TestCaseGenerator:
    def __init__(self, graph: nx.Graph, seed: int = 42):
        self.graph = graph
        self.nodes = list(graph.nodes())
        random.seed(seed)

    def generate_test_cases(self, n_cases: int = 25) -> List[TestCase]:
        """Arayüzün (UI) beklediği metodlardan biri."""
        return self.get_predefined_test_cases()[:n_cases]

    def get_predefined_test_cases(self) -> List[TestCase]:
        """Antigravity'nin fix dediği eksik metod burasıdır."""
        cases = []
        # Bant genişliği ve ağırlık varyasyonları
        bw_levels = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        
        for i in range(1, 26):
            s, d = random.sample(self.nodes, 2)
            bw = random.choice(bw_levels)
            cases.append(TestCase(
                id=i, source=s, destination=d, bandwidth_requirement=bw,
                weights={"delay": 0.33, "reliability": 0.33, "resource": 0.34},
                description=f"Senaryo {i}: {s}->{d} ({bw}Mbps)"
            ))
        return cases

class BandwidthConstraintChecker:
    def __init__(self, graph: nx.Graph):
        self.graph = graph

    def check_constraint(self, path: List[int], requirement: float) -> Tuple[bool, float, str]:
        if not path or len(path) < 2: return False, 0.0, "Yol bulunamadı"
        min_bw = float('inf')
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            if not self.graph.has_edge(u, v): return False, 0.0, "Bağlantı kopuk"
            min_bw = min(min_bw, self.graph.edges[u, v].get('bandwidth', 0))
        if min_bw < requirement: return False, min_bw, "Yetersiz Bant Genişliği"
        return True, min_bw, "Başarılı"