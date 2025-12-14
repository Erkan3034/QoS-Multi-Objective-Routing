"""
SARSA (State-Action-Reward-State-Action) Algoritması

Bu modül pekiştirmeli öğrenme tabanlı
yol optimizasyonu sağlar.

Özellikler:
- On-policy TD learning
- ε-greedy exploration
- Experience-based learning
- Q-Learning'den farkı: sonraki aksiyonu da kullanır

Referans: Rummery & Niranjan, "On-Line Q-Learning Using Connectionist Systems"
"""
import random
import time
import math
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

from src.services.metrics_service import MetricsService
from src.core.config import settings


@dataclass
class SARSAResult:
    """SARSA sonuç veri sınıfı."""
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


class SARSA:
    """
    SARSA algoritması ile yol optimizasyonu.
    
    Q-Learning'den farkı:
    - On-policy: Ajan gerçekte yaptığı aksiyonu kullanarak öğrenir
    - Q(s,a) güncellenmesinde next_action da seçilir
    
    Güncelleme kuralı:
    Q(s,a) ← Q(s,a) + α[R + γ·Q(s',a') - Q(s,a)]
    
    Attributes:
        graph: NetworkX graf objesi
        episodes: Eğitim episode sayısı
        learning_rate: Öğrenme hızı (α)
        discount_factor: İndirim faktörü (γ)
        epsilon_start: Başlangıç ε değeri
        epsilon_end: Bitiş ε değeri
        epsilon_decay: ε azalma oranı
    
    Example:
        >>> sarsa = SARSA(graph, episodes=5000)
        >>> result = sarsa.optimize(source=0, destination=249, weights={...})
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
        SARSA oluşturur.
        
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
        self.episodes = episodes or getattr(settings, 'QL_EPISODES', 1000)
        self.learning_rate = learning_rate or getattr(settings, 'QL_LEARNING_RATE', 0.1)
        self.discount_factor = discount_factor or getattr(settings, 'QL_DISCOUNT_FACTOR', 0.95)
        self.epsilon_start = epsilon_start or getattr(settings, 'QL_EPSILON_START', 1.0)
        self.epsilon_end = epsilon_end or getattr(settings, 'QL_EPSILON_END', 0.01)
        self.epsilon_decay = epsilon_decay or getattr(settings, 'QL_EPSILON_DECAY', 0.995)
        
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
        weights: Dict[str, float] = None
    ) -> SARSAResult:
        """
        Optimal yolu bul.
        
        Args:
            source: Kaynak düğüm ID
            destination: Hedef düğüm ID
            weights: Metrik ağırlıkları {'delay', 'reliability', 'resource'}
        
        Returns:
            SARSAResult objesi
        """
        start_time = time.perf_counter()
        
        weights = weights or {
            'delay': 0.33,
            'reliability': 0.33,
            'resource': 0.34
        }
        
        # Q-table'ı sıfırla
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.reward_history = []
        self.epsilon_history = []
        
        epsilon = self.epsilon_start
        
        # Eğitim döngüsü
        for episode in range(self.episodes):
            episode_reward = self._run_episode(source, destination, weights, epsilon)
            self.reward_history.append(episode_reward)
            self.epsilon_history.append(epsilon)
            
            # Epsilon decay
            epsilon = max(self.epsilon_end, epsilon * self.epsilon_decay)
        
        # En iyi yolu çıkar
        best_path = self._extract_best_path(source, destination)
        
        if not best_path:
            # Fallback: Shortest path kullan
            try:
                best_path = nx.shortest_path(self.graph, source, destination)
            except nx.NetworkXNoPath:
                best_path = [source, destination]
        
        # Toplam ödülü hesapla
        try:
            total_reward = 1000 / self.metrics_service.calculate_weighted_cost(
                best_path, weights['delay'], weights['reliability'], weights['resource']
            )
        except Exception:
            total_reward = 0
        
        elapsed_time = (time.perf_counter() - start_time) * 1000
        
        return SARSAResult(
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
        epsilon: float
    ) -> float:
        """
        Tek bir SARSA eğitim episode'u çalıştırır.
        
        SARSA'nın Q-Learning'den farkı burada:
        - Sonraki aksiyon da ε-greedy ile seçilir
        - Bu aksiyon Q-değeri güncellemesinde kullanılır
        
        Returns:
            Episode toplam ödülü
        """
        state = source
        path = [source]
        visited = {source}
        total_reward = 0
        max_steps = 100
        step = 0
        
        # İlk aksiyonu seç
        action = self._choose_action(state, visited, epsilon)
        
        if action is None:
            return -1000
        
        while state != destination and step < max_steps:
            if action is None:
                break
            
            # Adımı at
            prev_state = state
            state = action
            path.append(state)
            visited.add(state)
            
            # Reward hesapla
            if state == destination:
                # Hedefe ulaşıldı
                try:
                    cost = self.metrics_service.calculate_weighted_cost(
                        path, weights['delay'], weights['reliability'], weights['resource']
                    )
                    reward = 1000 / cost
                except Exception:
                    reward = -100
                next_action = None  # Terminal state
            else:
                # Ara adım
                try:
                    edge_cost = self._calculate_step_cost(prev_state, state, weights)
                    reward = -edge_cost
                except Exception:
                    reward = -1
                
                # SARSA: Sonraki aksiyonu ε-greedy ile seç
                next_action = self._choose_action(state, visited, epsilon)
            
            total_reward += reward
            
            # Q-değerini SARSA kuralıyla güncelle
            self._update_q_value_sarsa(prev_state, action, reward, state, next_action, destination)
            
            # Sonraki iterasyona geç
            action = next_action
            step += 1
        
        return total_reward
    
    def _choose_action(
        self,
        state: int,
        visited: set,
        epsilon: float
    ) -> Optional[int]:
        """
        ε-greedy politika ile action seçer.
        
        Returns:
            Seçilen komşu düğüm veya None
        """
        # Ziyaret edilmemiş komşuları al
        neighbors = [n for n in self.graph.neighbors(state) if n not in visited]
        
        if not neighbors:
            return None
        
        # ε-greedy seçim
        if random.random() < epsilon:
            # Rastgele keşif
            return random.choice(neighbors)
        else:
            # En iyi Q-değerine sahip action
            q_values = [(n, self.q_table[state][n]) for n in neighbors]
            q_values.sort(key=lambda x: x[1], reverse=True)
            return q_values[0][0]
    
    def _update_q_value_sarsa(
        self,
        state: int,
        action: int,
        reward: float,
        next_state: int,
        next_action: Optional[int],
        destination: int
    ):
        """
        Q-değerini SARSA kuralıyla günceller.
        
        Q(s,a) ← Q(s,a) + α[R + γ·Q(s',a') - Q(s,a)]
        
        Q-Learning'den farkı: max yerine gerçek a' kullanılır
        """
        current_q = self.q_table[state][action]
        
        # Next state'teki Q değeri (SARSA: gerçek next_action kullan)
        if next_state == destination or next_action is None:
            next_q = 0
        else:
            next_q = self.q_table[next_state][next_action]
        
        # TD güncellemesi
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * next_q - current_q
        )
        
        self.q_table[state][action] = new_q
    
    def _calculate_step_cost(
        self,
        from_node: int,
        to_node: int,
        weights: Dict[str, float]
    ) -> float:
        """Tek adım maliyetini hesaplar."""
        edge = self.graph.edges[from_node, to_node]
        
        delay_cost = edge['delay'] / 100
        rel_cost = -math.log(edge['reliability'])
        res_cost = 1000 / edge['bandwidth'] / 50
        
        return (
            weights['delay'] * delay_cost +
            weights['reliability'] * rel_cost +
            weights['resource'] * res_cost
        )
    
    def _extract_best_path(
        self,
        source: int,
        destination: int
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
            neighbors = [n for n in self.graph.neighbors(state) if n not in visited]
            
            if not neighbors:
                return None
            
            # Q değerlerine göre sırala
            q_values = [(n, self.q_table[state][n]) for n in neighbors]
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

