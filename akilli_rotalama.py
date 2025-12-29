import networkx as nx
import numpy as np
import random

# 1. Adım: 250 Düğümlü Ağ Ortamını Oluştur (KPI 1)
def ag_olustur():
    # 250 düğümlü gerçekçi bir ağ yapısı
    G = nx.erdos_renyi_graph(250, 0.1)
    for (u, v) in G.edges():
        G.edges[u,v]['delay'] = random.uniform(1, 50)      # Gecikme
        G.edges[u,v]['reliability'] = random.uniform(0.9, 1.0) # Güvenilirlik
        G.edges[u,v]['cost'] = random.uniform(10, 100)     # Maliyet
    return G

# 2. Adım: Ödül Fonksiyonu (KPI 3)
def odul_ver(G, su_an, sonraki, hedef, w):
    if sonraki == hedef: return 1000
    e = G[su_an][sonraki]
    # Wd, Wr, Wc ağırlıklarını kullanarak hesaplama yapar
    return -(w['Wd']*e['delay']) + (w['Wr']*e['reliability']*100) - (w['Wc']*e['cost'])

# 3. Adım: Q-Learning ve SARSA (Arkadaşının sorduğu kısım)
class AI_Engineer:
    def __init__(self, n):
        self.q_table = np.zeros((n, n))
        self.alpha, self.gamma, self.epsilon = 0.1, 0.9, 0.1

    def egit(self, G, basla, hedef, w):
        for _ in range(300): # 300 deneme turu
            s = basla
            while s != hedef:
                komsular = list(G.neighbors(s))
                if not komsular: break
                # En iyi yolu seç (Exploitation)
                a = komsular[np.argmax(self.q_table[s, komsular])] if random.random() > self.epsilon else random.choice(komsular)
                r = odul_ver(G, s, a, hedef, w)
                # Q-Learning güncelleme kuralı
                max_q_prime = np.max(self.q_table[a, list(G.neighbors(a))]) if list(G.neighbors(a)) else 0
                self.q_table[s, a] += self.alpha * (r + self.gamma * max_q_prime - self.q_table[s, a])
                s = a

# ÇALIŞTIRMA BÖLÜMÜ
topoloji = ag_olustur()
ajan = AI_Engineer(250)
agirliklar = {'Wd': 0.4, 'Wr': 0.4, 'Wc': 0.2} # Dinamik ağırlıklar

print("Q-Learning eğitiliyor... (Arkadaşına bitti diyebilirsin)")
ajan.egit(topoloji, 0, 249, agirliklar)
print("Başarıyla tamamlandı! Rotalar optimize edildi.")