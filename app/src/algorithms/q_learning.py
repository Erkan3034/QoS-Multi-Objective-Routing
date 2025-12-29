"""
Q-Learning Algoritması Implementasyonu

Bu modül pekiştirmeli öğrenme tabanlı
yol optimizasyonu sağlar.

Özellikler:
- Tabular Q-Learning
- ε-greedy exploration
- Experience-based learning
- Policy extraction
"""
import random
import time
import os
import math
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from src.services.metrics_service import MetricsService
from src.core.config import settings


@dataclass
class QLResult:
    """Q-Learning sonuç veri sınıfı."""
    path: List[int]
    total_reward: float
    episodes: int
    final_epsilon: float
    computation_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "total_reward": round(self.total_reward, 6),
            "episodes": self.episodes,
            "final_epsilon": round(self.final_epsilon, 6),
            "computation_time_ms": round(self.computation_time_ms, 2)
        }


class QLearning:
    """
    Q-Learning tabanlı yol optimizasyonu.
    
    State: Ajanın bulunduğu düğüm
    Action: Komşu düğüme gitme
    Reward: Hedefe ulaşıldığında yol maliyetine göre
    
    Attributes:
        graph: NetworkX graf objesi
        episodes: Eğitim episode sayısı
        learning_rate: Öğrenme hızı (α)
        discount_factor: İndirim faktörü (γ)
        epsilon_start: Başlangıç ε değeri
        epsilon_end: Bitiş ε değeri
        epsilon_decay: ε azalma oranı
    
    Example:
        >>> ql = QLearning(graph, episodes=5000)
        >>> result = ql.optimize(source=0, destination=249, weights={...})
        >>> print(f"Best path: {result.path}")
    """
    
    def __init__(
        self,
        graph: nx.Graph,
        episodes: int = None,
        learning_rate: float = None,
        discount_factor: float = None,
        epsilon_start: float = None,
        epsilon_end: float = None,
        epsilon_decay: float = None,
        seed: int = None
    ):
        """
        QLearning oluşturur.
        
        Args:
            graph: NetworkX graf objesi
            episodes: Eğitim episode sayısı
            learning_rate: Öğrenme hızı (α)
            discount_factor: İndirim faktörü (γ)
            epsilon_start: Başlangıç ε değeri
            epsilon_end: Bitiş ε değeri
            epsilon_decay: ε azalma oranı
            seed: Rastgele seed
        """
        self.graph = graph
        self.episodes = episodes or settings.QL_EPISODES
        self.learning_rate = learning_rate or settings.QL_LEARNING_RATE
        self.discount_factor = discount_factor or settings.QL_DISCOUNT_FACTOR
        self.epsilon_start = epsilon_start or settings.QL_EPSILON_START
        self.epsilon_end = epsilon_end or settings.QL_EPSILON_END
        self.epsilon_decay = epsilon_decay or settings.QL_EPSILON_DECAY
        
        # [FIX] Store seed for stochastic behavior check
        self._seed = seed
        if seed is not None:
            random.seed(seed)
        
        self.metrics_service = MetricsService(graph)
        
        # Q-table: state -> action -> Q-value
        self.q_table: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        
        # İstatistikler
        self.reward_history: List[float] = []
        self.epsilon_history: List[float] = []
    
    def optimize(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float] = None,
        bandwidth_demand: float = 0.0,
        progress_callback: Optional[callable] = None
    ) -> QLResult:
        """
        Optimal yolu bul.
        
        Args:
            source: Kaynak düğüm ID
            destination: Hedef düğüm ID
            weights: Metrik ağırlıkları {'delay', 'reliability', 'resource'}
            bandwidth_demand: İstenen bant genişliği (Mbps)
        
        Returns:
            QLResult objesi
        """
        start_time = time.perf_counter()
        
        weights = weights or {
            'delay': 0.33,
            'reliability': 0.33,
            'resource': 0.34
        }
        
        # [FIX] Reset random state if no seed was set to ensure stochastic behavior
        if not hasattr(self, '_seed') or self._seed is None:
            import time as time_module
            if not hasattr(self, '_call_counter'):
                self._call_counter = 0
            self._call_counter += 1
            seed_val = time_module.time_ns() % (2**31) + os.getpid() + self._call_counter
            random.seed(seed_val)
            print(f"[Q-Learning] Stokastik mod - seed={seed_val}, call={self._call_counter}")
        else:
            print(f"[Q-Learning] Deterministik mod - seed={self._seed}")
        
        # Q-table'ı sıfırla
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.reward_history = []
        self.epsilon_history = []
        
        epsilon = self.epsilon_start
        
        # Progress callback için ayar
        progress_every = max(1, self.episodes // 20)  # Her %5'te bir bildir
        
        # Eğitim döngüsü
        for episode in range(self.episodes):
            episode_reward = self._run_episode(source, destination, weights, epsilon, bandwidth_demand)
            self.reward_history.append(episode_reward)
            self.epsilon_history.append(epsilon)
            
            # Epsilon decay
            epsilon = max(self.epsilon_end, epsilon * self.epsilon_decay)
            
            # Progress callback - ilerleme bildir
            if progress_callback and (episode % progress_every == 0 or episode == self.episodes - 1):
                try:
                    # İki argüman: (iteration, best_value)
                    progress_callback(episode, episode_reward)
                except TypeError:
                    try:
                        # Dict formatı da dene
                        progress_callback({
                            'iteration': episode,
                            'total': self.episodes,
                            'epsilon': epsilon,
                            'reward': episode_reward
                        })
                    except Exception:
                        pass
        
        # En iyi yolu çıkar
        best_path = self._extract_best_path(source, destination, bandwidth_demand)
        
        if not best_path:
            # Fallback: Shortest path kullan
            try:
                # [FIX] Fallback respects bandwidth
                if bandwidth_demand > 0:
                    valid_edges = [
                        (u, v) for u, v, d in self.graph.edges(data=True) 
                        if d.get('bandwidth', 1000) >= bandwidth_demand
                    ]
                    temp_graph = self.graph.edge_subgraph(valid_edges)
                    best_path = nx.shortest_path(temp_graph, source, destination)
                else:
                    best_path = nx.shortest_path(self.graph, source, destination)
            except nx.NetworkXNoPath:
                best_path = [source, destination]
        
        # Toplam ödülü hesapla
        try:
            total_reward = 1000 / self.metrics_service.calculate_weighted_cost(
                best_path, weights['delay'], weights['reliability'], weights['resource'], bandwidth_demand
            )
        except Exception:
            total_reward = 0
        
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        print(f"[Q-Learning] Sonuç: path={best_path[:5]}...{best_path[-2:] if len(best_path)>5 else ''}, len={len(best_path)}, reward={total_reward:.4f}")
        
        return QLResult(
            path=best_path,
            total_reward=total_reward,
            episodes=self.episodes,
            final_epsilon=epsilon,
            computation_time_ms=elapsed_time
        )
    
    def _run_episode(
        self,
        source: int,
        destination: int,
        weights: Dict[str, float],
        epsilon: float,
        bandwidth_demand: float = 0.0
    ) -> float:
        """
        Tek bir eğitim episode'u çalıştırır.
        
        Returns:
            Episode toplam ödülü
        """
        state = source
        path = [source]
        visited = {source}
        total_reward = 0
        max_steps = 100
        step = 0
        
        while state != destination and step < max_steps:
            # Action seç (ε-greedy)
            action = self._choose_action(state, visited, epsilon, bandwidth_demand)
            
            if action is None:
                # Dead end
                break
            
            # Adımı at
            prev_state = state
            state = action
            path.append(state)
            visited.add(state)
            
            # Reward hesapla
            if state == destination:
                # Hedefe ulaşıldı - yol maliyetine göre ödül
                try:
                    cost = self.metrics_service.calculate_weighted_cost(
                        path, weights['delay'], weights['reliability'], weights['resource'], bandwidth_demand
                    )
                    reward = 1000 / cost  # Düşük maliyet = yüksek ödül
                except Exception:
                    reward = -100
            else:
                # Ara adım - küçük negatif ödül
                try:
                    edge_cost = self._calculate_step_cost(prev_state, state, weights)
                    reward = -edge_cost
                except Exception:
                    reward = -1
            
            total_reward += reward
            
            # Q-değerini güncelle
            self._update_q_value(prev_state, action, reward, state, destination)
            
            step += 1
        
        return total_reward
    
    def _choose_action(
        self,
        state: int,
        visited: set,
        epsilon: float,
        bandwidth_demand: float = 0.0
    ) -> Optional[int]:
        """
        ε-greedy politika ile action seçer.
        
        Returns:
            Seçilen komşu düğüm veya None
        """
        # Ziyaret edilmemiş komşuları al
        neighbors = list(self.graph.neighbors(state))
        
        # Filter by bandwidth
        if bandwidth_demand > 0:
            candidates = [n for n in neighbors if n not in visited and self.graph[state][n].get('bandwidth', 1000) >= bandwidth_demand]
        else:
            candidates = [n for n in neighbors if n not in visited]
        
        if not candidates:
            return None
        
        # ε-greedy seçim
        if random.random() < epsilon:
            # Rastgele keşif
            return random.choice(candidates)
        else:
            # En iyi Q-değerine sahip action
            q_values = [(n, self.q_table[state][n]) for n in candidates]
            q_values.sort(key=lambda x: x[1], reverse=True)
            return q_values[0][0]
    
    def _update_q_value(
        self,
        state: int,
        action: int,
        reward: float,
        next_state: int,
        destination: int
    ):
        """
        Q-değerini günceller.
        
        Q(s,a) ← Q(s,a) + α[R + γ·max_a' Q(s',a') - Q(s,a)]
        """
        current_q = self.q_table[state][action]
        
        # Next state'teki maksimum Q değeri
        if next_state == destination:
            max_next_q = 0
        else:
            next_actions = list(self.graph.neighbors(next_state))
            if next_actions:
                max_next_q = max(self.q_table[next_state][a] for a in next_actions)
            else:
                max_next_q = 0
        
        # TD güncellemesi
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
    
    def _calculate_step_cost(
        self,
        from_node: int,
        to_node: int,
        weights: Dict[str, float]
    ) -> float:
        """Tek adım maliyetini hesaplar.
        
        [PROJECT COMPLIANCE] Includes both edge and node reliability with -log formula.
        """
        edge = self.graph.edges[from_node, to_node]
        
        delay_cost = edge['delay'] / 100
        # [PROJECT COMPLIANCE] -log(LinkReliability) + -log(NodeReliability)
        edge_rel = max(edge['reliability'], 0.001)
        node_rel = max(self.graph.nodes[to_node].get('reliability', 0.99), 0.001)
        rel_cost = (-math.log(edge_rel) + -math.log(node_rel)) / 2  # Normalize per hop
        # [PROJECT COMPLIANCE] ResourceCost = 1Gbps / Bandwidth
        res_cost = (1000 / max(edge['bandwidth'], 1)) / 100
        
        return (
            weights['delay'] * delay_cost +
            weights['reliability'] * rel_cost +
            weights['resource'] * res_cost
        )
    
    def _extract_best_path(
        self,
        source: int,
        destination: int,
        bandwidth_demand: float = 0.0
    ) -> Optional[List[int]]:
        """
        Öğrenilen politikadan en iyi yolu çıkarır.
        
        Greedy olarak en yüksek Q değerini takip eder.
        """
        path = [source]
        state = source
        visited = {source}
        max_steps = 100
        
        while state != destination and len(path) < max_steps:
            # En iyi action'ı seç
            neighbors = list(self.graph.neighbors(state))
            
            # Filter by bandwidth
            if bandwidth_demand > 0:
                candidates = [n for n in neighbors if n not in visited and self.graph[state][n].get('bandwidth', 1000) >= bandwidth_demand]
            else:
                candidates = [n for n in neighbors if n not in visited]
            
            if not candidates:
                return None
            
            # Q değerlerine göre sırala
            q_values = [(n, self.q_table[state][n]) for n in candidates]
            q_values.sort(key=lambda x: x[1], reverse=True)
            
            next_state = q_values[0][0]
            path.append(next_state)
            visited.add(next_state)
            state = next_state
        
        return path if state == destination else None
    
    def get_q_table_stats(self) -> Dict[str, Any]:
        """Q-table istatistiklerini döndürür."""
        all_q_values = []
        for state_actions in self.q_table.values():
            all_q_values.extend(state_actions.values())
        
        if not all_q_values:
            return {"states": 0, "actions": 0}
        
        return {
            "states": len(self.q_table),
            "total_entries": len(all_q_values),
            "max_q": max(all_q_values),
            "min_q": min(all_q_values),
            "avg_q": sum(all_q_values) / len(all_q_values)
        }


