
import logging
import sys

# Create logger
logger = logging.getLogger("qos_routing")
logger.setLevel(logging.INFO)

# Create console handler and set level to debug
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add formatter to ch
ch.setFormatter(formatter)

# Add ch to logger
if not logger.handlers:
    logger.addHandler(ch)

__all__ = ["logger"]
