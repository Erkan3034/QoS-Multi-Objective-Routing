
import sys
import os

# App path setup
sys.path.insert(0, os.path.join(os.getcwd(), "app"))

print("Attempting to import src.experiments package...")
try:
    import src.experiments
    print("SUCCESS: src.experiments imported.")
    print(f"Exports: {dir(src.experiments)}")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
except Exception as e:
    print(f"FAILURE: Exception: {e}")
