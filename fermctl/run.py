"""Entry point for the fermentation controller.

Starts the Flask API server. The controller loop starts when a
fermentation run is initiated via the API or dashboard.

Usage:
    python3 run.py                  # Normal mode (requires Pi hardware)
    FERMCTL_SIMULATE=1 python3 run.py  # Simulation mode (no hardware needed)
"""

import logging
import signal
import sys
import os

# Add parent to path so fermctl package is importable
sys.path.insert(0, os.path.dirname(__file__))

from fermctl import config
from fermctl.api import app, controller
from fermctl.relay import cleanup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fermctl")


def shutdown_handler(signum, frame):
    """Graceful shutdown — stop any active run and clean up GPIO."""
    logger.info("Shutdown signal received")
    if controller.is_running:
        controller.stop_run()
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)


if __name__ == "__main__":
    if config.SIMULATE:
        logger.info("Running in SIMULATION mode (no hardware)")
    else:
        logger.info("Running in HARDWARE mode")

    logger.info("Starting FermCtl API on %s:%d", config.API_HOST, config.API_PORT)
    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=False,  # debug=True would spawn a second process
        use_reloader=False,
    )
