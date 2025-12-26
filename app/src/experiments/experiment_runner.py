import time
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from src.algorithms.genetic_algorithm import GeneticAlgorithm
from src.algorithms.aco import AntColonyOptimization
from src.algorithms.pso import ParticleSwarmOptimization
from src.algorithms.simulated_annealing import SimulatedAnnealing
from src.algorithms.q_learning import QLearning
from src.algorithms.sarsa import SARSA
from src.experiments.test_cases import TestCase, BandwidthConstraintChecker
from src.services.metrics_service import MetricsService

# Arayüz için gerekli tip tanımı
ExperimentResult = Dict[str, Any]

class ExperimentRunner:
    def __init__(self, graph, n_repeats=5, iterations=100, progress_callback=None):
        self.graph = graph
        self.iterations = iterations
        self.n_repeats = n_repeats
        self.progress_callback = progress_callback
        self.checker = BandwidthConstraintChecker(graph)
        self.metrics_service = MetricsService(graph)

    def run_experiments(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Arayüz tarafından çağrılan ana deney metodu."""
        start_total = time.time()
        
        algorithms = ["GA", "ACO", "PSO", "SA", "QL", "SARSA"]
        total_steps = len(algorithms) * len(test_cases)
        current_step = 0
        
        # Data aggregation structures
        comparison_table = []
        failure_details = []
        total_failures = 0
        
        # Run experiments for each algorithm
        for alg_name in algorithms:
            alg_total_cost = 0.0
            alg_total_time = 0.0
            alg_success_count = 0
            alg_bw_satisfaction_count = 0
            best_cost_for_alg = float('inf')
            
            total_runs_for_alg = len(test_cases) * self.n_repeats
            
            for case in test_cases:
                case_runs = []
                for _ in range(self.n_repeats):
                    res = self._execute_single_run(alg_name, case)
                    case_runs.append(res)
                    
                    # Track global failures
                    if not res['success']:
                        total_failures += 1
                        failure_details.append({
                            "algorithm": alg_name,
                            "test_case_id": case.id,
                            "source": case.source,
                            "destination": case.destination,
                            "bandwidth_requirement": case.bandwidth_requirement,
                            "failure_reason": res.get("failure_reason", "Bilinmeyen Hata"),
                            "details": f"Süre: {res['time']:.2f}ms"
                        })
                    else:
                        if res['weighted_cost'] < best_cost_for_alg:
                            best_cost_for_alg = res['weighted_cost']

                # Case stats (for this algorithm)
                successful_runs = [r for r in case_runs if r['success']]
                alg_success_count += len(successful_runs)
                
                # Bandwidth satisfaction (implied by success in check_constraint)
                alg_bw_satisfaction_count += len(successful_runs) 
                
                # Sum costs and times
                if successful_runs:
                    alg_total_cost += sum(r['weighted_cost'] for r in successful_runs)
                    alg_total_time += sum(r['time'] for r in list(case_runs))
                else:
                    alg_total_time += sum(r['time'] for r in case_runs)

                current_step += 1
                
                # [OPTIMIZATION] Update progress only once per test case per algorithm
                # to prevent UI freezing due to signal flooding.
                if self.progress_callback and (current_step % 5 == 0 or current_step == total_steps):
                     msg = f"{alg_name} - Senaryo {case.id}/{len(test_cases)}"
                     self.progress_callback(current_step, total_steps, msg)

            # Calculate algorithm averages
            n_samples = len(test_cases) * self.n_repeats
            success_n = alg_success_count
            
            avg_cost = alg_total_cost / success_n if success_n > 0 else float('inf')
            avg_time = alg_total_time / n_samples if n_samples > 0 else 0.0
            success_rate = success_n / n_samples if n_samples > 0 else 0.0
            bw_sat_rate = alg_bw_satisfaction_count / n_samples if n_samples > 0 else 0.0
            
            comparison_table.append({
                "algorithm": alg_name,
                "success_rate": success_rate,
                "bandwidth_satisfaction_rate": bw_sat_rate,
                "overall_avg_cost": avg_cost,
                "overall_avg_time_ms": avg_time,
                "best_cost": best_cost_for_alg if best_cost_for_alg != float('inf') else 0.0
            })

        end_total = time.time()
        
        # Sort comparison table by overall_avg_cost (lower is better)
        comparison_table.sort(key=lambda x: x['overall_avg_cost'])

        return {
            "timestamp": datetime.now().isoformat(),
            "n_test_cases": len(test_cases),
            "total_time_sec": round(end_total - start_total, 2),
            "comparison_table": comparison_table,
            "failure_report": {
                "total_failures": total_failures,
                "details": failure_details
            }
        }

    def _execute_single_run(self, alg_name: str, case: TestCase) -> Dict:
        start = time.time()
        path = []
        
        try:
            # Common arguments for all algorithms
            # All algorithms now support bandwidth_demand thanks to recent updates
            run_args = {
                "source": case.source,
                "destination": case.destination,
                "weights": case.weights,
                "bandwidth_demand": case.bandwidth_requirement
            }

            if alg_name == "GA":
                alg = GeneticAlgorithm(self.graph)
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "ACO":
                alg = AntColonyOptimization(self.graph)
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "PSO":
                alg = ParticleSwarmOptimization(self.graph)
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "SA":
                alg = SimulatedAnnealing(self.graph)
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "QL":
                alg = QLearning(self.graph)
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "SARSA":
                alg = SARSA(self.graph)
                result = alg.optimize(**run_args)
                path = result.path
            
            else:
                raise ValueError(f"Unknown algorithm: {alg_name}")
            
            end_ms = (time.time() - start) * 1000
            
            # Check constraints
            is_valid, min_bw, reason = self.checker.check_constraint(path, case.bandwidth_requirement)
            
            # Calculate cost if valid
            weighted_cost = 0.0
            if is_valid:
                weighted_cost = self.metrics_service.calculate_weighted_cost(
                    path, 
                    case.weights['delay'], 
                    case.weights['reliability'], 
                    case.weights['resource']
                )
            
            return {
                "success": is_valid, 
                "time": end_ms,
                "weighted_cost": weighted_cost,
                "failure_reason": reason if not is_valid else None
            }
            
        except Exception as e:
            end_ms = (time.time() - start) * 1000
            return {
                "success": False,
                "time": end_ms,
                "weighted_cost": float('inf'),
                "failure_reason": f"Exception: {str(e)}"
            }