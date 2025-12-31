import time
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from src.algorithms.genetic_algorithm import GeneticAlgorithm
from src.algorithms.aco import AntColonyOptimization
from src.algorithms.pso import ParticleSwarmOptimization
from src.algorithms.simulated_annealing import SimulatedAnnealing
from src.algorithms.q_learning import QLearning
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
    
    def _get_weight_profile_name(self, weights: Dict) -> str:
        """Ağırlıklara göre profil adını belirle."""
        d = weights.get('delay', 0)
        r = weights.get('reliability', 0)
        res = weights.get('resource', 0)
        
        if d >= 0.6:
            return "Gecikme"
        elif r >= 0.6:
            return "Güvenilirlik"
        elif res >= 0.6:
            return "Kaynak"
        else:
            return "Dengeli"

    def run_experiments(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """
        Kapsamlı Deney Motoru
        ---------------------
        Her senaryo için tüm algoritmaların detaylı karşılaştırmasını üretir.
        
        Returns:
            - comparison_table: Algoritma bazlı özet istatistikler
            - scenario_results: Senaryo bazlı detaylı karşılaştırma
            - failure_report: Başarısız testlerin gerekçeleri
        """
        start_total = time.time()
        
        algorithms = ["GA", "ACO", "PSO", "SA", "QL"]
        total_steps = len(algorithms) * len(test_cases)
        current_step = 0
        
        # === Data aggregation structures ===
        comparison_table = []
        failure_details = []
        total_failures = 0
        
        # YENİ: Senaryo bazlı detaylı sonuçlar
        scenario_results = {}
        
        # Her senaryo için boş yapı oluştur
        for case in test_cases:
            scenario_key = f"scenario_{case.id}"
            
            # Ağırlık profilini belirle
            profile_name = self._get_weight_profile_name(case.weights)
            
            scenario_results[scenario_key] = {
                "id": case.id,
                "source": case.source,
                "destination": case.destination,
                "bandwidth": case.bandwidth_requirement,
                "weights": case.weights,
                "profile_name": profile_name,
                "algorithms": {}
            }
        
        # === Run experiments for each algorithm ===
        for alg_name in algorithms:
            alg_total_cost = 0.0
            alg_total_time = 0.0
            alg_success_count = 0
            alg_bw_satisfaction_count = 0
            best_cost_for_alg = float('inf')
            best_seed_for_alg = None
            
            total_runs_for_alg = len(test_cases) * self.n_repeats
            
            for case in test_cases:
                scenario_key = f"scenario_{case.id}"
                case_runs = []
                case_costs = []
                case_times = []
                case_failures = []
                
                for repeat_idx in range(self.n_repeats):
                    res = self._execute_single_run(alg_name, case)
                    case_runs.append(res)
                    case_times.append(res['time'])
                    
                    # Track failures
                    if not res['success']:
                        total_failures += 1
                        fail_info = {
                            "algorithm": alg_name,
                            "test_case_id": case.id,
                            "repeat": repeat_idx + 1,
                            "source": case.source,
                            "destination": case.destination,
                            "bandwidth_requirement": case.bandwidth_requirement,
                            "failure_reason": res.get("failure_reason", "Bilinmeyen Hata"),
                            "details": f"Süre: {res['time']:.2f}ms",
                            "seed_used": res.get("seed_used")
                        }
                        failure_details.append(fail_info)
                        case_failures.append(fail_info)
                    else:
                        case_costs.append(res['weighted_cost'])
                        if res['weighted_cost'] < best_cost_for_alg:
                            best_cost_for_alg = res['weighted_cost']
                            best_seed_for_alg = res.get('seed_used')
                
                # === Senaryo bazlı istatistikler ===
                n_success = len(case_costs)
                n_total = self.n_repeats
                
                if n_success > 0:
                    avg_cost = float(np.mean(case_costs))
                    std_cost = float(np.std(case_costs)) if n_success > 1 else 0.0
                    min_cost = float(np.min(case_costs))
                    max_cost = float(np.max(case_costs))
                    best_seed_case = case_runs[case_costs.index(min_cost)].get('seed_used')
                else:
                    avg_cost = float('inf')
                    std_cost = 0.0
                    min_cost = float('inf')
                    max_cost = float('inf')
                    best_seed_case = None
                
                avg_time = float(np.mean(case_times))
                
                # Senaryo sonucuna algoritma verisi ekle
                scenario_results[scenario_key]["algorithms"][alg_name] = {
                    "all_costs": [round(c, 6) for c in case_costs],
                    "avg_cost": round(avg_cost, 6) if avg_cost != float('inf') else None,
                    "std_cost": round(std_cost, 6),
                    "min_cost": round(min_cost, 6) if min_cost != float('inf') else None,
                    "max_cost": round(max_cost, 6) if max_cost != float('inf') else None,
                    "all_times_ms": [round(t, 2) for t in case_times],
                    "avg_time_ms": round(avg_time, 2),
                    "success_count": n_success,
                    "failure_count": n_total - n_success,
                    "success_rate": n_success / n_total,
                    "best_seed": best_seed_case,
                    "failures": case_failures
                }
                
                # === Algoritma toplam istatistikleri ===
                alg_success_count += n_success
                alg_bw_satisfaction_count += n_success
                
                if n_success > 0:
                    alg_total_cost += sum(case_costs)
                alg_total_time += sum(case_times)

                current_step += 1
                
                if self.progress_callback and (current_step % 5 == 0 or current_step == total_steps):
                     msg = f"{alg_name} - Senaryo {case.id}/{len(test_cases)}"
                     self.progress_callback(current_step, total_steps, msg)

            # === Algoritma özet istatistikleri ===
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
                "best_cost": best_cost_for_alg if best_cost_for_alg != float('inf') else 0.0,
                "best_seed": best_seed_for_alg
            })

        end_total = time.time()
        
        # Sort comparison table by overall_avg_cost
        comparison_table.sort(key=lambda x: x['overall_avg_cost'])
        
        # === RANKING HESAPLA: Her senaryoda hangi algoritma kazandı? ===
        ranking_summary = {alg: {"1st": 0, "2nd": 0, "3rd": 0, "4th": 0, "5th": 0} for alg in algorithms}
        
        for scenario_key, scenario in scenario_results.items():
            # Bu senaryodaki algoritmaları ortalama maliyete göre sırala
            algo_costs = []
            for algo_name, algo_data in scenario.get("algorithms", {}).items():
                avg_cost = algo_data.get("avg_cost")
                if avg_cost is not None:
                    algo_costs.append((algo_name, avg_cost))
            
            # Maliyete göre sırala (en düşük en iyi)
            algo_costs.sort(key=lambda x: x[1])
            
            # Sıralamaya göre puan ver
            for rank, (algo_name, _) in enumerate(algo_costs):
                rank_key = ["1st", "2nd", "3rd", "4th", "5th"][min(rank, 4)]
                ranking_summary[algo_name][rank_key] += 1
        
        # Toplam kazanma sayısı (1. olma) ekle
        for algo_name in ranking_summary:
            ranking_summary[algo_name]["total_wins"] = ranking_summary[algo_name]["1st"]

        return {
            "timestamp": datetime.now().isoformat(),
            "n_test_cases": len(test_cases),
            "n_repeats": self.n_repeats,
            "total_time_sec": round(end_total - start_total, 2),
            "comparison_table": comparison_table,
            "scenario_results": scenario_results,
            "ranking_summary": ranking_summary,  # YENİ: Algoritma sıralaması
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
                alg = GeneticAlgorithm(self.graph, seed=None)  # Stokastik: her çalışmada farklı
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "ACO":
                alg = AntColonyOptimization(self.graph, seed=None)
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "PSO":
                alg = ParticleSwarmOptimization(self.graph, seed=None)
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "SA":
                alg = SimulatedAnnealing(self.graph, seed=None)
                result = alg.optimize(**run_args)
                path = result.path
                
            elif alg_name == "QL":
                alg = QLearning(self.graph, seed=None)
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
                "failure_reason": reason if not is_valid else None,
                "seed_used": getattr(result, 'seed_used', None)
            }
            
        except Exception as e:
            end_ms = (time.time() - start) * 1000
            return {
                "success": False,
                "time": end_ms,
                "weighted_cost": float('inf'),
                "failure_reason": f"Exception: {str(e)}",
                "seed_used": None
            }