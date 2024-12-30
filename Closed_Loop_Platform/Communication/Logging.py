import logging
import os
import sys

# Create log folder if it doesn't exist
log_folder = r"C:\Users\guazh\data"
exp_id = ""


# Function to redirect print statements to loggers
class PrintLogger:
    def __init__(self, exp_id):
        self.exp_id = exp_id

    def write(self, message):
        if message.strip():  # Prevent logging empty lines
            # Log to both the session log and master log
            log_experiment_action(self.exp_id, message.strip())

    def flush(self):
        pass  # No-op for flush (needed for compatibility)


class LoggingSystem:
    def __init__(self, log_folder):
        self.log_folder = log_folder
        self.master_logger = None

    def create_master_logger(self):
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

        # Master log file path (this file logs everything across all sessions)
        master_log_file = os.path.join(self.log_folder, 'master.log')

        # Set up the master log file handler
        master_handler = logging.FileHandler(master_log_file)
        master_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        master_handler.setFormatter(master_formatter)

        # Create master logger (only once)
        master_logger = logging.getLogger('master_logger')
        if not master_logger.hasHandlers():
            master_logger.setLevel(logging.INFO)
            master_logger.addHandler(master_handler)

        self.master_logger = master_logger

    # Function to create a session logger (specific to an experiment or session)
    def create_session_logger(self, exp_id):
        # Create a session log file specific to the experiment/session
        session_log_file = os.path.join(self.log_folder, f'{self.exp_id}.log')

        # Set up the session file handler
        session_handler = logging.FileHandler(session_log_file)

        # Note: Removing %(exp_id)s from formatter since it's not automatically available
        session_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        session_handler.setFormatter(session_formatter)

        # Create a session-specific logger
        session_logger = logging.getLogger(exp_id)
        if not session_logger.hasHandlers():  # To avoid adding multiple handlers
            session_logger.setLevel(logging.INFO)
            session_logger.addHandler(session_handler)

        return session_logger

    # Logging for both master and session
    def log_experiment_action(self, exp_id, message):
        # Log to the master log
        self.master_logger.info(f"{exp_id}: {message}")

        # Get or create the session-specific logger
        session_logger = self.create_session_logger(exp_id)

        # Log the message to the session-specific logger
        session_logger.info(message)

    # Example setup to use PrintLogger
    def setup_logging_for_experiment(self, exp_id):
        # Initialize the master logger
        self.create_master_logger()

        # Redirect print statements to the logger
        sys.stdout = PrintLogger(exp_id)


#%%
'''
# Example Usage
setup_logging_for_experiment('EXP0001')

# Now any print statements will be redirected to the logging system
print("Setting up master logger for EXP0001...")
print("Initializing experiment EXP0001...")
print("Magnetic stirrer activated.")
print("Pump operation started.")

# Another session
setup_logging_for_experiment('EXP0002')
print("Setting up master logger for EXP0002...")
print("Initializing experiment EXP0002...")
print("Magnetic stirrer activated for EXP0002.")
print("Pump operation started for EXP0002.")
'''