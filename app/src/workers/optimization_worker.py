"""
Generic Optimization Worker - Background thread for any algorithm with progress tracking
"""
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, Any, Optional
import networkx as nx

from src.services.metrics_service import MetricsService
from src.ui.components.results_panel import OptimizationResult


class OptimizationWorker(QThread):
    """
    Generic worker thread for any optimization algorithm with live progress updates.
    
    This worker accepts any algorithm instance and calls its optimize() method
    with a progress callback for real-time convergence plot visualization.
    
    Emits:
        - finished: OptimizationResult when optimization completes
        - progress_data: (iteration, fitness) tuples for real-time plotting
        - error: str error message if optimization fails
    """
    
    finished = pyqtSignal(object)  # OptimizationResult
    progress_data = pyqtSignal(int, float)  # iteration, fitness
    error = pyqtSignal(str)
    
    def __init__(
        self,
        algorithm_instance: Any,
        algorithm_name: str,
        graph: nx.Graph,
        source: int,
        dest: int,
        weights: Dict
    ):
        """
        Initialize generic optimization worker.
        
        Args:
            algorithm_instance: Instantiated algorithm object (e.g., GeneticAlgorithm, AntColonyOptimization)
            algorithm_name: Display name for the algorithm (e.g., "Genetic Algorithm")
            graph: NetworkX graph
            source: Source node ID
            dest: Destination node ID
            weights: Metric weights dictionary
        """
        super().__init__()
        self.algorithm_instance = algorithm_instance
        self.algorithm_name = algorithm_name
        self.graph = graph
        self.source = source
        self.dest = dest
        self.weights = weights
    
    def run(self):
        """
        Execute optimization in background thread.
        
        Creates a progress callback that emits progress_data signal
        for real-time convergence plot updates.
        """
        try:
            # [LIVE CONVERGENCE PLOT] Progress callback helper
            # This function is called by the algorithm during optimization
            def on_progress(iteration: int, fitness: float):
                """Emit progress data signal for live plotting."""
                self.progress_data.emit(iteration, fitness)
            
            # Run optimization with progress callback
            # All algorithms should support progress_callback parameter
            result = self.algorithm_instance.optimize(
                source=self.source,
                destination=self.dest,
                weights=self.weights,
                progress_callback=on_progress
            )
            
            # Calculate metrics using MetricsService
            ms = MetricsService(self.graph)
            metrics = ms.calculate_all(
                result.path,
                self.weights['delay'],
                self.weights['reliability'],
                self.weights['resource']
            )
            
            # Create OptimizationResult
            opt_result = OptimizationResult(
                algorithm=self.algorithm_name,
                path=result.path,
                total_delay=metrics.total_delay,
                total_reliability=metrics.total_reliability,
                resource_cost=metrics.resource_cost,
                weighted_cost=metrics.weighted_cost,
                computation_time_ms=result.computation_time_ms
            )
            
            self.finished.emit(opt_result)
            
        except Exception as e:
            self.error.emit(str(e))

