import logging
import os
import sys

exp_id = ""

class PrintLogger:
    def __init__(self, logging_system, exp_id):
        self.logging_system = logging_system  # Instance of LoggingSystem
        self.exp_id = exp_id  # Experiment ID

    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            self.logging_system.log_experiment_action(self.exp_id, message.strip())

    def flush(self):
        pass  # Required for compatibility with sys.stdout

import logging
import os
import sys

class LoggingSystem:
    def __init__(self, log_folder):
        self.log_folder = log_folder
        self.master_logger = None
        self.original_stdout = sys.stdout  # Save the original stdout for restoration

    def create_master_logger(self):
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

        master_log_file = os.path.join(self.log_folder, 'master.log')
        handler = logging.FileHandler(master_log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.master_logger = logging.getLogger('master_logger')
        if not self.master_logger.hasHandlers():
            self.master_logger.addHandler(handler)
            self.master_logger.setLevel(logging.INFO)

    def create_session_logger(self, exp_id):
        session_log_file = os.path.join(self.log_folder, f'{exp_id}.log')
        handler = logging.FileHandler(session_log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        session_logger = logging.getLogger(exp_id)
        if not session_logger.hasHandlers():
            session_logger.addHandler(handler)
            session_logger.setLevel(logging.INFO)

        return session_logger

    def log_experiment_action(self, exp_id, message):
        if self.master_logger is None:
            raise RuntimeError("Master logger is not initialized.")
        self.master_logger.info(f"{exp_id}: {message}")

        session_logger = self.create_session_logger(exp_id)
        session_logger.info(message)

    def setup_logging_for_experiment(self, exp_id):
        # Redirect sys.stdout to log to both master and session logs
        sys.stdout = PrintLogger(self, exp_id)

    def restore_stdout(self):
        # Restore original stdout
        sys.stdout = self.original_stdout