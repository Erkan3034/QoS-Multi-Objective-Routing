"""
Karınca Kolonisi Optimizasyonu (ACO) - QoS Yönlendirme
=====================================
ACO, doğadaki karıncaların yiyecek ararken bıraktıkları feromon izlerini 
takip etme davranışından esinlenmiş bir optimizasyon algoritmasıdır.

Temel Formüller:
- Olasılık: P(i,j) = [τ(i,j)^α · η(i,j)^β] / Σ[τ(i,k)^α · η(i,k)^β]
  * τ(i,j): i'den j'ye feromon miktarı (geçmiş deneyim)
  * η(i,j): sezgisel değer (anlık çekicilik, genelde 1/maliyet)
  * α: feromon önem derecesi (yüksek = geçmişe güven)
  * β: sezgisel önem derecesi (yüksek = açgözlü seçim)

- Feromon Güncelleme: τ(i,j) ← (1-ρ)·τ(i,j) + Σ[Δτ_k(i,j)]
  * ρ: buharlaşma oranı (eskiyi unutma hızı)
  * Δτ_k: k. karıncanın bıraktığı feromon (genelde Q/maliyet)
"""

import random, time, math, os
import numpy as np
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from collections import defaultdict
from src.services.metrics_service import MetricsService


@dataclass
class ACOResult:
    """
    ACO algoritması sonuç yapısı
    
    Attributes:
        path: Bulunan en iyi yol (düğüm ID'leri listesi)
        fitness: Yolun toplam maliyeti (düşük = iyi)
        iteration: En iyi çözümün bulunduğu iterasyon numarası
        computation_time_ms: Hesaplama süresi (milisaniye)
        convergence_data: Yakınsama verileri (her iterasyondaki en iyi fitness)
        seed_used: Tekrarlanabilirlik için kullanılan rastgelelik seed'i
    """
    path: List[int]
    fitness: float
    iteration: int
    computation_time_ms: float
    convergence_data: Optional[Dict] = None
    seed_used: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Sonuçları sözlük formatına dönüştür (API/JSON için)"""
        return {
            "path": self.path,
            "fitness": round(self.fitness, 6),
            "iteration": self.iteration,
            "computation_time_ms": round(self.computation_time_ms, 2),
            "seed_used": self.seed_used
        }


class OptimizedACO:
    """
    Gelişmiş Karınca Kolonisi Optimizasyonu
    ========================================
    1. Adaptif α/β: Zamanla keşif→sömürü dengesi değişir
    2. Rank-based feromon: En iyi N karınca daha fazla feromon bırakır
    3. ε-greedy: Bazen rastgele seçim yaparak yerel optimumdan kaçınır
    4. Min-max feromon: Feromon değerleri sınırlanır (stabilite)
    5. Erken durdurma: Yakınsama/durgunluk tespiti ile gereksiz hesap önlenir
    """
    #===================1. Başlangıç Ayarları===================
    def __init__(
        self,
        graph: nx.Graph,
        n_ants: int = 50,              # Karınca sayısı (paralel çözüm adayı)
        n_iterations: int = 100,       # Maksimum iterasyon sayısı
        alpha_range: Tuple[float, float] = (0.8, 2.0),   # α aralığı [min, max]
        beta_range: Tuple[float, float] = (2.0, 5.0),    # β aralığı [max, min]
        evaporation_rate: float = 0.1, # ρ: feromon buharlaşma oranı
        q: float = 100.0,              # Q: feromon deposit sabiti
        epsilon: float = 0.1,          # ε: rastgele seçim olasılığı
        seed: int = None               # Rastgelelik seed'i (tekrarlanabilirlik)
    ):
        # Graf ve metrik servisi
        self.graph = graph
        self.metrics = MetricsService(graph)
        # Graf boyutuna göre karınca/iterasyon sayısı adaptasyonu(hesap maliyetini düşürmek için sayılar azaltılır) 
        graph_size = len(graph.nodes())
        if graph_size > 200:
            self.n_ants = min(n_ants, 20)
            self.n_iter = min(n_iterations, 30)
        elif graph_size > 100:
            self.n_ants = min(n_ants, 30)
            self.n_iter = min(n_iterations, 50)
        else:
            self.n_ants = n_ants
            self.n_iter = n_iterations
    
        # Parametre aralıkları ve başlangıç değerleri
        self.a_range = alpha_range      # α: feromon ağırlığı aralığı
        self.b_range = beta_range       # β: sezgisel ağırlığı aralığı
        self.alpha = sum(alpha_range) / 2   # Başlangıç α (orta nokta)
        self.beta = sum(beta_range) / 2     # Başlangıç β (orta nokta)
        self.rho = evaporation_rate     # Feromon buharlaşma oranı
        self.q = q                      # Feromon deposit miktarı sabiti
        self.eps = epsilon              # ε-greedy rastgelelik oranı
        self._seed = seed               # Kullanıcı tanımlı seed
        self._actual_seed = None        # Gerçekte kullanılan seed
        # Feromon matrisi (lazy initialization ile bellek tasarrufu)(# defaultdict kullanımı: yeni kenarlar otomatik 1.0 ile başlar)
        self.pheromone: Dict[Tuple[int, int], float] = defaultdict(lambda: 1.0)
        # Feromon sınırları (min-max ACO)
        # Çok düşük/yüksek feromon değerleri algoritmanın takılmasına sebep olabilir
        self.tau_min = 0.01   # Minimum feromon (unutma sınırı)
        self.tau_max = 10.0   # Maksimum feromon (aşırı pekiştirme önleme)
        
        # Yakınsama takibi
        self.best_hist = []   # Her iterasyondaki en iyi fitness deperlerini yakalar
        self.stag = 0         # Stagnasyon sayacı (kaç iterasyon gelişme yok)
    
    #===================2. Optimizasyon Fonksiyonu===================
    def optimize(
        self,
        source: int,                    # Başlangıç düğümü
        destination: int,               # Hedef düğümü
        weights: Dict[str, float] = None,  # Maliyet ağırlıkları
        bandwidth_demand: float = 0.0,  # Minimum bandwidth gereksinimi (Mbps)
        progress_callback: Callable = None  # İlerleme bildirimi için callback
    ) -> ACOResult:
        """
        Ana optimizasyon döngüsü
        Args:
            source: Başlangıç düğümü ID'si
            destination: Hedef düğümü ID'si
            weights: Maliyet bileşenleri ağırlıkları (delay, reliability, resource)
            bandwidth_demand: Minimum bandwidth gereksinimi
            progress_callback: İlerleme güncellemeleri için fonksiyon
            
        Returns: ACOResult: En iyi yol ve optimizasyon metrikleri
        """
        # Başlangıç zamanı ve varsayılan ağırlıklar
        t0 = time.perf_counter()
        weights = weights or {
            'delay': 0.33,        # Gecikme ağırlığı
            'reliability': 0.33,  # Güvenilirlik ağırlığı
            'resource': 0.34      # Kaynak (bandwidth) ağırlığı
        }
        
        # Rastgelelik seed'ini ayarla (tekrarlanabilirlik için)
        if self._seed:
            self._actual_seed = self._seed
        else:
            # ❗❗Seed verilmemişse: zaman + process ID kombinasyonu kullan
            self._actual_seed = (time.time_ns() + os.getpid()) % (2**32 - 1)
        random.seed(self._actual_seed)
        np.random.seed(self._actual_seed)
        
        # State'i sıfırla (her optimizasyon bağımsız başlar)
        self.pheromone.clear()
        self.best_hist = []
        self.stag = 0
        self.alpha = sum(self.a_range) / 2
        self.beta = sum(self.b_range) / 2
        self.rho = 0.1
        
        # Global en iyi çözüm takibi
        best_path = None
        best_fit = float('inf')  # Başlangıç: sonsuz kötü
        best_iter = 0
        
        # =============== Ana ACO döngüsü ===============
        for it in range(self.n_iter):
            # =============== Adaptif parametre güncellemesi ===============
            # İlerleme oranı: 0 (başlangıç) → 1 (son)
            progress = it / self.n_iter
            # α (feromon etkisi): Zamanla artırılır
            # Başlangıçta keşif (düşük α), sonda sömürü (yüksek α)
            self.alpha = self.a_range[0] + (self.a_range[1] - self.a_range[0]) * progress
            # β (sezgisel etki): Zamanla azaltılır
            # Başlangıçta açgözlü seçim (yüksek β), sonda feromon takibi (düşük β)
            self.beta = self.b_range[1] - (self.b_range[1] - self.b_range[0]) * progress
            # Stagnasyon tespiti: 10 iterasyon gelişme yoksa buharlaşmayı artır
            # Daha fazla unutma → farklı bölgeleri keşfetmeye zorla
            if self.stag > 10:
                self.rho = min(0.3, self.rho * 1.1)
                self.stag = 0
            
            # =============== Tüm karıncaları çalıştır (paralel yol inşası) ===============
            paths = []   # Bu iterasyonda bulunan tüm yollar
            fits = []    # Yolların fitness değerleri
            
            for _ in range(self.n_ants):
                # Her karınca bağımsız bir yol inşa eder
                path = self._build_path(source, destination, weights, bandwidth_demand)
                
                if path:  # Geçerli yol bulunduysa
                    paths.append(path)
                    # Yolun maliyetini hesapla
                    fitness = self.metrics.calculate_weighted_cost(
                        path,
                        weights['delay'],
                        weights['reliability'],
                        weights['resource'],
                        bandwidth_demand
                    )
                    fits.append(fitness)
            
            # =============== Global en iyi çözümü güncelle ===============
            if fits:  # En az bir geçerli yol bulunduysa
                idx = int(np.argmin(fits))  # En düşük maliyetli yol
                
                if fits[idx] < best_fit:
                    # Yeni rekor! Global en iyiyi güncelle
                    best_fit = fits[idx]
                    best_path = paths[idx]
                    best_iter = it
                    self.stag = 0  # Stagnasyon sayacını sıfırla
                else:
                    # Gelişme yok, stagnasyon arttır
                    self.stag += 1
            
            # Yakınsama geçmişine ekle
            self.best_hist.append(best_fit)
            
            # =============== Feromon güncelleme ===============
            self._update_pheromones(paths, fits, best_path, best_fit)
            
            # =============== İlerleme callback'i (opsiyonel) =======================================
            if progress_callback and it % 3 == 0:
                try:
                    progress_callback(it, best_fit)
                except:
                    pass  # Callback hatası algoritma durdurmaz
            
            # =============== Erken durdurma koşulları =============================================
            # 1) Yakınsama: Son 3 iterasyon neredeyse aynı sonucu veriyorsa dur
            if len(self.best_hist) > 3:
                recent_range = max(self.best_hist[-3:]) - min(self.best_hist[-3:])
                if recent_range < 0.001:  # Çok küçük değişim
                    break
            
            # 2) Stagnasyon: 5+ iterasyon gelişme yoksa dur
            if self.stag > 5:
                break
        
        # =============== Fallback: ACO hiç çözüm bulamadıysa =============================================
        if not best_path:
            try:
                # En kısa yolu kullan (Dijkstra)
                best_path = nx.shortest_path(self.graph, source, destination)
            except:
                # Graf bağlantısız, sadece kaynak ve hedefi döndür
                best_path = [source, destination]
            
            try:
                # Fallback yolun maliyetini hesapla
                best_fit = self.metrics.calculate_weighted_cost(
                    best_path,
                    weights['delay'],
                    weights['reliability'],
                    weights['resource'],
                    bandwidth_demand
                )
            except:
                best_fit = float('inf')
        
        # Sonuç nesnesini oluştur ve döndür
        return ACOResult(
            path=best_path,
            fitness=best_fit,
            iteration=best_iter,
            computation_time_ms=(time.perf_counter() - t0) * 1000,
            convergence_data={"best_fitness": self.best_hist},
            seed_used=self._actual_seed
        )
    
    # ------------------------------------------------------------------
    # Yol inşası (ε-greedy strateji)
    # ------------------------------------------------------------------
    def _build_path(
        self,
        src: int,
        dst: int,
        w: Dict,
        bw: float
    ) -> Optional[List[int]]:
        """
        Tek karınca için yol inşası (ε-greedy strateji)
        
        Karınca, kaynak düğümden başlayarak her adımda komşularından birini seçer.
        Seçim, feromon ve sezgisel değerlere göre olasılıksal yapılır.

        [Başlangıç] → [Komşu Seç] → [Komşu Seç] → ... → [Hedef]
        Args:
            src: Başlangıç düğümü
            dst: Hedef düğümü
            w: Maliyet ağırlıkları
            bw: Minimum bandwidth gereksinimi
            
        Returns:
            Bulunan yol (düğüm listesi) veya None (yol bulunamadıysa)
        """
        path = [src]           # Yol başlangıçta sadece kaynak düğümü içerir
        cur = src              # Şu anki düğüm
        visited = {src}        # Ziyaret edilen düğümler (döngü önleme)
        
        # Maksimum 100 adım (sonsuz döngü önleme)
        for _ in range(100):
            # Hedefe ulaştıysak başarı
            if cur == dst:
                return path
            # ------------------------------------------------------------------
            # Geçerli komşuları filtrele
            # ------------------------------------------------------------------
            candidates = [
                n for n in self.graph.neighbors(cur)
                if n not in visited  # Daha önce ziyaret edilmemiş
                and (bw <= 0 or self.graph[cur][n].get('bandwidth', 1000) >= bw)  # Bandwidth yeterli
            ]
            
            if not candidates:
                # Çıkmaz sokak, yol bulunamadı
                return None
            
            # Hedef komşu listesindeyse direkt oraya git
            if dst in candidates:
                return path + [dst]
            
            # ------------------------------------------------------------------
            # ε-greedy seçim stratejisi
            # ------------------------------------------------------------------
            if random.random() < self.eps:
                # ε olasılıkla: Rastgele seçim (keşif)
                nxt = random.choice(candidates)
            else:
                # (1-ε) olasılıkla: Feromon-sezgisel tabanlı seçim (sömürü)
                
                # Her komşu için skor hesapla: P(i,j) ∝ τ^α · η^β
                scores = [
                    (self.pheromone[(cur, c)] ** self.alpha) *  # Feromon etkisi
                    (self._eta(cur, c, w) ** self.beta)         # Sezgisel etki
                    for c in candidates
                ]
                
                # Skorları normalize et (olasılık dağılımı)
                tot = sum(scores)
                if tot > 0:
                    probs = [s / tot for s in scores]
                else:
                    # Tüm skorlar 0 ise uniform dağılım
                    probs = [1 / len(candidates)] * len(candidates)
                
                # Rulet tekerleği seçimi (roulette wheel selection(Yüksek skorlu komşuların daha yüksek olasılıkla seçilmesi))
                r = random.random()
                cum = 0.0
                for c, p in zip(candidates, probs):
                    cum += p
                    if r <= cum:
                        nxt = c
                        break
                else:
                    # Yuvarlama hatası, son adayı seç
                    nxt = candidates[-1]
            
            # Seçilen düğümü yola ekle
            path.append(nxt)
            visited.add(nxt)
            cur = nxt
        
        # 100 adımda hedefe ulaşılamadı
        return None
    

    # ------------------------------------------------------------------
    # Sezgisel değer hesaplama
    # ------------------------------------------------------------------
    def _eta(self, u: int, v: int, w: Dict) -> float:
        """
        Sezgisel değer hesaplama: η(u,v)
        
        Sezgisel değer, bir kenarın "çekiciliğini" temsil eder.
        Genelde 1/maliyet şeklinde hesaplanır: düşük maliyet = yüksek çekicilik
        
        Args:
            u: Başlangıç düğümü
            v: Hedef düğümü
            w: Maliyet ağırlıkları
            
        Returns:
            Sezgisel değer (0.001 ile 1 arası)
        """
        edge = self.graph.edges[u, v]
        
        # Ağırlıklı toplam maliyet hesapla
        cost = (
            # Gecikme maliyeti (normalize edilmiş)
            w['delay'] * edge['delay'] / 100 +
            
            # Güvenilirlik maliyeti (log-olasılık: yüksek güvenilirlik = düşük maliyet)
            w['reliability'] * (
                -math.log(max(edge['reliability'], 0.01)) -
                math.log(max(self.graph.nodes[v].get('reliability', 0.99), 0.01))
            ) +
            
            # Kaynak maliyeti (düşük bandwidth = yüksek maliyet)
            w['resource'] * (1000 / max(edge['bandwidth'], 1)) / 100
        )
        
        # η = 1 / (1 + maliyet), minimum 0.001
        return max(1 / (1 + cost), 0.001)
    
    def _update_pheromones(
        self,
        paths: List,
        fits: List,
        best: List,
        best_f: float
    ):
        """
        Feromon güncelleme (3 aşamalı)
        
        1. Buharlaşma: Eski feromon azalır (unutma)
        2. Rank-based deposit: En iyi N karınca feromon bırakır
        3. Global-best bonus: En iyi yola ekstra feromon
        4. Min-max sınırlama: Feromon değerlerini sınırla
        
        Args:
            paths: Bu iterasyonda bulunan tüm yollar
            fits: Yolların fitness değerleri
            best: Global en iyi yol
            best_f: Global en iyi fitness
        """
        # ----------------------------------------------------------------------
        # 1) Buharlaşma (sadece kullanılan kenarlar)
        # ----------------------------------------------------------------------
        # Kullanılan tüm kenarları topla
        edges = set()
        for p in paths:
            for i in range(len(p) - 1):
                # Yönsüz graf için her iki yönü de ekle
                edges.add((p[i], p[i+1]))
                edges.add((p[i+1], p[i]))
        
        # Her kenardaki feromonu (1-ρ) ile çarp (buharlaşma)
        for e in edges:
            if e in self.pheromone:
                self.pheromone[e] *= (1 - self.rho)
        
        # ----------------------------------------------------------------------
        # 2) Rank-based deposit (en iyi 10 karınca)
        # ----------------------------------------------------------------------
        if paths and fits:
            # Fitness'a göre sırala, en iyi 10'u al
            for rank, idx in enumerate(np.argsort(fits)[:10]):
                if fits[idx] == float('inf'):
                    continue  # Geçersiz çözümleri atla
                
                # Rank'e göre ağırlıklı feromon: daha iyi rank = daha fazla feromon
                # deposit = (N - rank) * Q / fitness
                deposit = (len(fits) - rank) * self.q / fits[idx]
                
                # Yoldaki her kenara feromon bırak
                for i in range(len(paths[idx]) - 1):
                    self.pheromone[(paths[idx][i], paths[idx][i+1])] += deposit
                    self.pheromone[(paths[idx][i+1], paths[idx][i])] += deposit
        
        # ----------------------------------------------------------------------
        # 3) Global-best bonus (3x ağırlık)
        # ----------------------------------------------------------------------
        if best and best_f != float('inf'):
            # En iyi yola ekstra feromon bırak (pekiştirme 3 kat)
            deposit = 3 * self.q / best_f
            
            for i in range(len(best) - 1):
                self.pheromone[(best[i], best[i+1])] += deposit
                self.pheromone[(best[i+1], best[i])] += deposit
        
        # ----------------------------------------------------------------------
        # 4) Min-max sınırları uygula
        # ----------------------------------------------------------------------
        # Feromon değerlerini [tau_min, tau_max] aralığında tut
        # Bu, algoritmanın çok dar bölgelere takılmasını önler
        for e in self.pheromone:
            self.pheromone[e] = max(
                self.tau_min,
                min(self.tau_max, self.pheromone[e])
            )


# Geriye uyumluluk için alias
AntColonyOptimization = OptimizedACO

"""
Yorum : ~280 satır
Kod : ~254 satır

"""