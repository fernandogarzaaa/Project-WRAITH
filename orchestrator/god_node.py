import datetime
import logging
import os
import subprocess
import sys
import time

# Configure logging
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GOD_NODE - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, 'god_node.log'))
    ]
)
logger = logging.getLogger("GodNode")

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLTERGEIST_PATH = os.path.join(PROJECT_ROOT, "poltergeist", "scraper_swarm.py")
SOMNUS_PATH = os.path.join(PROJECT_ROOT, "somnus", "evolution_loop.py")

def _hour_from_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "")
    try:
        value = int(raw) if raw.strip() else default
    except ValueError:
        logger.warning(f"Ignoring invalid {name}={raw!r}; using {default}")
        return default
    if not 0 <= value <= 23:
        logger.warning(f"Ignoring out-of-range {name}={value}; using {default}")
        return default
    return value


class WraithOrchestrator:
    def __init__(self):
        self.current_mode = None
        self.active_process: subprocess.Popen | None = None
        self.log_file = None
        # A job that exits cleanly (return code 0) is finished for this mode
        # and is not restarted until the next mode transition.
        self.mode_job_done = False
        # Night window in the machine's LOCAL time (it used to be UTC, which on
        # a UTC+8 machine ran the "nightly" job at 10:00-16:00).
        self.night_start = _hour_from_env("WRAITH_NIGHT_START", 2)
        self.night_end = _hour_from_env("WRAITH_NIGHT_END", 8)

    def is_night_mode(self, now: datetime.datetime | None = None):
        """Night Mode is [WRAITH_NIGHT_START, WRAITH_NIGHT_END) local time,
        02:00-08:00 by default. A window that crosses midnight (e.g. 22 -> 6)
        is supported."""
        try:
            hour = (now or datetime.datetime.now()).hour
            start, end = self.night_start, self.night_end
            if start == end:
                return False
            if start < end:
                return start <= hour < end
            return hour >= start or hour < end
        except Exception as e:  # noqa: BLE001 - daemon must survive unexpected errors
            logger.error(f"Error checking time: {e}")
            return False

    def start_process(self, name, script_path):
        if not os.path.exists(script_path):
            logger.error(f"Script not found: {script_path}. Critical failure.")
            return
        
        logger.info(f"Starting {name}...")
        try:
            log_path = os.path.join(LOG_DIR, f"{name.split()[0].lower()}_output.log")
            if self.log_file and not self.log_file.closed:
                self.log_file.close()
            self.log_file = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 - handle kept open for daemon lifetime
            
            self.active_process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=self.log_file,
                stderr=subprocess.STDOUT
            )
            logger.info(f"{name} started with PID {self.active_process.pid}. Logs redirected to {log_path}")
        except Exception as e:  # noqa: BLE001 - daemon must survive unexpected errors
            logger.error(f"Failed to start {name}: {e}")
            self.active_process = None

    def stop_process(self):
        try:
            if self.active_process:
                logger.info(f"Stopping active process (PID {self.active_process.pid})...")
                try:
                    self.active_process.terminate()
                    self.active_process.wait(timeout=10)
                    logger.info("Process terminated gracefully.")
                except subprocess.TimeoutExpired:
                    logger.warning("Process did not terminate gracefully, sending SIGKILL...")
                    self.active_process.kill()
                    self.active_process.wait()
                    logger.info("Process forcefully killed.")
                except Exception as e:  # noqa: BLE001 - daemon must survive unexpected errors
                    logger.error(f"Error while stopping process: {e}")
        except Exception as e:  # noqa: BLE001 - daemon must survive unexpected errors
            logger.error(f"Fatal error in stop_process: {e}")
        finally:
            self.active_process = None
            try:
                if self.log_file and not self.log_file.closed:
                    self.log_file.close()
            except Exception as e:  # noqa: BLE001 - daemon must survive unexpected errors
                logger.debug("log file close failed: %s", e)
            self.log_file = None

    def check_process_health(self) -> bool:
        """Returns True if process is healthy (running), False if dead or none."""
        if self.active_process is None:
            return False
            
        try:
            return_code = self.active_process.poll()
            if return_code is not None:
                if return_code == 0:
                    logger.info(f"{self.current_mode} job finished cleanly; idle until the next mode.")
                    self.mode_job_done = True
                else:
                    logger.warning(f"Active process ({self.current_mode}) died with return code {return_code}.")
                self.stop_process() # Ensure cleanup
                return False
            return True
        except Exception as e:  # noqa: BLE001 - daemon must survive unexpected errors
            logger.error(f"Health check failed: {e}")
            self.stop_process()
            return False

    def run(self):
        logger.info("WRAITH Ecosystem GOD_NODE initialized.")
        logger.info(
            f"Schedule (local time): Night Mode ({self.night_start:02d}:00-{self.night_end:02d}:00) -> Somnus"
            " | Day Mode (rest of the day) -> Poltergeist"
        )
        
        while True:
            try:
                night = self.is_night_mode()
                target_mode = "NIGHT" if night else "DAY"
                
                if self.current_mode != target_mode:
                    logger.info(f"Mode transition triggered: {self.current_mode} -> {target_mode}")
                    self.stop_process()
                    self.current_mode = target_mode
                    self.mode_job_done = False
                    
                    if target_mode == "DAY":
                        self.start_process("Poltergeist (Day Mode)", POLTERGEIST_PATH)
                    else:
                        self.start_process("Somnus (Night Mode)", SOMNUS_PATH)
                elif not self.mode_job_done:
                    if not self.check_process_health() and not self.mode_job_done:
                        logger.warning(f"Restarting dead {self.current_mode} process...")
                        if self.current_mode == "DAY":
                            self.start_process("Poltergeist (Day Mode)", POLTERGEIST_PATH)
                        else:
                            self.start_process("Somnus (Night Mode)", SOMNUS_PATH)

                # Polling interval
                time.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("GOD_NODE shutting down gracefully...")
                self.stop_process()
                break
            except Exception as e:  # noqa: BLE001 - daemon must survive unexpected errors
                logger.error(f"Critical error in main orchestrator loop: {e}")
                time.sleep(30)

if __name__ == "__main__":
    try:
        orchestrator = WraithOrchestrator()
        orchestrator.run()
    except Exception as e:  # noqa: BLE001 - daemon must survive unexpected errors
        logger.error(f"Fatal crash: {e}")
        sys.exit(1)
