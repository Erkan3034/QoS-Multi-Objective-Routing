# Optimization Implementation Plan

This document outlines the steps to optimize the QoS Multi-Objective Routing application. The goal is to standardize metric normalization, implement caching for performance, and enforce bandwidth constraints across all algorithms.

## 1. Centralize Normalization Logic
**Current State:** `GeneticAlgorithm` has its own sophisticated normalization logic, while `MetricsService` (used by other algorithms) uses simple linear combination. This leads to unbalanced scoring where Delay or Reliability might dominate the other.
**Goal:** Move `NormConfig` and normalization logic into `MetricsService` so all algorithms share the same "Fair Scoring" mechanism.

### Actions:
- [ ] Update `app/src/services/metrics_service.py`:
    - Define `NormConfig` constants (Max Delay, Max Hop, Reliability Penalty).
    - Update `calculate_weighted_cost` to use normalization.
    - Ensure backwards compatibility or update all callers.

## 2. Implement Caching Layer
**Current State:** Path metrics are recalculated every time, even for identical paths.
**Goal:** Reduce CPU load by caching calculation results.

### Actions:
- [ ] Update `app/src/services/metrics_service.py`:
    - Add `functools.lru_cache` or a custom dictionary-based cache to `calculate_weighted_cost`.
    - implementation details: Cache key should be `(tuple(path), weights_tuple)`.

## 3. Enforce Bandwidth Constraints Globally
**Current State:** GA checks bandwidth during path finding. Other algorithms might check it only *after* finding a path (Post-Processing), leading to "Failed" results.
**Goal:** All algorithms must treat Bandwidth as a "Hard Constraint" during the search.

### Actions:
- [ ] Review and Update Algorithms:
    - [ ] `aco.py`
    - [ ] `pso.py`
    - [ ] `simulated_annealing.py`
    - [ ] `q_learning.py`
    - [ ] `sarsa.py`
- **Change:** In their cost/fitness calculation, check:
  ```python
  if min_path_bandwidth < required_bandwidth:
      return infinity
  ```

## 4. Align Genetic Algorithm
**Current State:** GA uses its own internal worker for performance.
**Goal:** Ensure GA aligns with the new system.
- If `MetricsService` becomes efficient enough (with caching), GA can optionally use it, or at least share the `NormConfig` constants to ensure scoring is identical across the board.

## Execution Sequence
1. Modify `MetricsService` (Normalization + Caching).
2. Validate `MetricsService` changes.
3. Update `ACO`, `PSO`, `SA` to use the updated `MetricsService` or enforce BW constraints directly.
4. Update `RL` algorithms (`Q-Learning`, `SARSA`).
5. Verify GA compatibility.
