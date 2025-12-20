
import sys
import os

sys.path.insert(0, os.path.join(os.getcwd(), "app"))

print("1. Importing ExperimentRunner...")
try:
    from src.experiments.experiment_runner import ExperimentRunner
    print("SUCCESS: ExperimentRunner imported.")
except ImportError as e:
    print(f"FAILURE: ExperimentRunner import failed: {e}")
    sys.exit(1)

print("2. Checking src.experiments for TestResult...")
import src.experiments
if hasattr(src.experiments, 'TestResult'):
    print("SUCCESS: TestResult found in src.experiments.")
else:
    print("WARNING: TestResult NOT found in src.experiments (This might be okay if not used externally).")

print("3. Checking src.experiments.test_cases for TestResult...")
import src.experiments.test_cases
if hasattr(src.experiments.test_cases, 'TestResult'):
    print("SUCCESS: TestResult found in test_cases.")
else:
    print("FAILURE: TestResult missing from test_cases!")
