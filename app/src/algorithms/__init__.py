"""Optimization algorithms module."""
from .genetic_algorithm import GeneticAlgorithm
from .aco import AntColonyOptimization
from .pso import ParticleSwarmOptimization
from .simulated_annealing import SimulatedAnnealing
from .q_learning import QLearning

ALGORITHMS = {
    "ga": ("Genetic Algorithm", GeneticAlgorithm),
    "aco": ("Ant Colony Optimization", AntColonyOptimization),
    "pso": ("Particle Swarm Optimization", ParticleSwarmOptimization),
    "sa": ("Simulated Annealing", SimulatedAnnealing),
    "qlearning": ("Q-Learning", QLearning),
}

__all__ = [
    "GeneticAlgorithm", "AntColonyOptimization", "ParticleSwarmOptimization",
    "SimulatedAnnealing", "QLearning", "ALGORITHMS"
]
