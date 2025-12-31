"""
Uygulama Konfigürasyonu
"""
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Uygulama ayarları."""
    
    # Genel Ayarlar
    APP_NAME: str = "QoS Routing Optimizer"
    DEBUG: bool = True
    
    # Graf Ayarları (Erdős–Rényi modeli)
    DEFAULT_NODE_COUNT: int = 250
    DEFAULT_CONNECTION_PROB: float = 0.4
    RANDOM_SEED: int = 42
    
    # Düğüm Özellikleri Aralıkları
    PROCESSING_DELAY_MIN: float = 0.5
    PROCESSING_DELAY_MAX: float = 2.0
    NODE_RELIABILITY_MIN: float = 0.95
    NODE_RELIABILITY_MAX: float = 0.999
    
    # Bağlantı Özellikleri Aralıkları
    BANDWIDTH_MIN: float = 100.0
    BANDWIDTH_MAX: float = 1000.0
    LINK_DELAY_MIN: float = 3.0
    LINK_DELAY_MAX: float = 15.0
    LINK_RELIABILITY_MIN: float = 0.95
    LINK_RELIABILITY_MAX: float = 0.999
    
    # Genetic Algorithm
    # [OPTIMIZED] Experiment mode için daha agresif parametreler
    GA_POPULATION_SIZE: int = 150  # 100 -> 150 (daha fazla çeşitlilik)
    GA_GENERATIONS: int = 500
    GA_MUTATION_RATE: float = 0.12  # 0.1 -> 0.12 (daha fazla keşif)
    GA_CROSSOVER_RATE: float = 0.8
    GA_ELITISM: float = 0.08  # 0.1 -> 0.08 (daha az elitizm, daha fazla çeşitlilik)
    
    # Ant Colony Optimization
    ACO_N_ANTS: int = 50
    ACO_N_ITERATIONS: int = 100
    ACO_ALPHA: float = 1.0
    ACO_BETA: float = 2.0
    ACO_EVAPORATION_RATE: float = 0.5
    ACO_Q: float = 100.0
    
    # Particle Swarm Optimization
    PSO_N_PARTICLES: int = 30 
    PSO_N_ITERATIONS: int = 100
    PSO_W: float = 0.7
    PSO_C1: float = 1.5
    PSO_C2: float = 1.5
    
    # Simulated Annealing
    SA_INITIAL_TEMPERATURE: float = 1000.0
    SA_FINAL_TEMPERATURE: float = 0.01
    SA_COOLING_RATE: float = 0.995
    SA_ITERATIONS_PER_TEMP: int = 10
    
    # Q-Learning
    QL_EPISODES: int = 5000
    QL_LEARNING_RATE: float = 0.1
    QL_DISCOUNT_FACTOR: float = 0.95
    QL_EPSILON_START: float = 1.0
    QL_EPSILON_END: float = 0.01
    QL_EPSILON_DECAY: float = 0.995
    

    # Experiments
    EXPERIMENT_N_REPEATS: int = 5
    EXPERIMENT_TIMEOUT_SEC: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

