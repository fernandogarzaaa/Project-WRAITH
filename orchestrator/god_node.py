import time
import datetime
import subprocess
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GOD_NODE - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'god_node.log'))
    ]
)

# Paths relative to orchestrator
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLTERGEIST_PATH = os.path.join(BASE_DIR, "poltergeist", "scraper_swarm.py")
SOMNUS_PATH = os.path.join(BASE_DIR, "somnus", "evolution_loop.py")

class WraithOrchestrator:
    def __init__(self):
        self.current_mode = None
        self.active_process = None

    def is_night_mode(self):
        """Night Mode is from 02:00 to 08:00 (exclusive of 08:00)"""
        hour = datetime.datetime.now().hour
        return 2 <= hour < 8

    def start_process(self, name, script_path):
        if not os.path.exists(script_path):
            logging.warning(f"Script not found: {script_path}. Ensure it exists for actual execution.")
        
        logging.info(f"Starting {name}...")
        try:
            # Start the sub-process
            self.active_process = subprocess.Popen([sys.executable, script_path])
            logging.info(f"{name} started with PID {self.active_process.pid}")
        except Exception as e:
            logging.error(f"Failed to start {name}: {e}")

    def stop_process(self):
        if self.active_process:
            logging.info(f"Stopping active process (PID {self.active_process.pid})...")
            self.active_process.terminate()
            try:
                self.active_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logging.warning("Process did not terminate gracefully, killing...")
                self.active_process.kill()
            self.active_process = None
            logging.info("Process stopped.")

    def run(self):
        logging.info("WRAITH Ecosystem GOD_NODE initialized.")
        logging.info("Schedule: Day Mode (08:00-02:00) -> Poltergeist | Night Mode (02:00-08:00) -> Somnus")
        
        while True:
            try:
                night = self.is_night_mode()
                target_mode = "NIGHT" if night else "DAY"
                
                if self.current_mode != target_mode:
                    logging.info(f"Mode transition: {self.current_mode} -> {target_mode}")
                    self.stop_process()
                    
                    self.current_mode = target_mode
                    if target_mode == "DAY":
                        self.start_process("Poltergeist (Day Mode)", POLTERGEIST_PATH)
                    else:
                        self.start_process("Somnus (Night Mode)", SOMNUS_PATH)
                else:
                    # Check if process is still alive, restart if dead
                    if self.active_process and self.active_process.poll() is not None:
                        logging.warning(f"Active process ({self.current_mode}) died unexpectedly. Restarting...")
                        if self.current_mode == "DAY":
                            self.start_process("Poltergeist (Day Mode)", POLTERGEIST_PATH)
                        else:
                            self.start_process("Somnus (Night Mode)", SOMNUS_PATH)

                # Sleep before next check (check every 60 seconds)
                time.sleep(60)
                
            except KeyboardInterrupt:
                logging.info("GOD_NODE shutting down gracefully...")
                self.stop_process()
                break
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(60)

if __name__ == "__main__":
    orchestrator = WraithOrchestrator()
    orchestrator.run()
