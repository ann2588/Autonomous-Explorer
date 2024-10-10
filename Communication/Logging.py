import logging
import os
import sys

# Create log folder if it doesn't exist
log_folder = r'/Users/Yi-An/Documents/000_Project/044_FAARM_PA-004/Data/Logfile'
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


def create_master_logger(log_folder):
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # Master log file path (this file logs everything across all sessions)
    master_log_file = os.path.join(log_folder, 'master.log')

    # Set up the master log file handler
    master_handler = logging.FileHandler(master_log_file)
    master_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    master_handler.setFormatter(master_formatter)

    # Create master logger (only once)
    master_logger = logging.getLogger('master_logger')
    if not master_logger.hasHandlers():
        master_logger.setLevel(logging.INFO)
        master_logger.addHandler(master_handler)

    return master_logger


# Function to create a session logger (specific to an experiment or session)
def create_session_logger(exp_id, log_folder):
    # Create a session log file specific to the experiment/session
    session_log_file = os.path.join(log_folder, f'{exp_id}.log')

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
def log_experiment_action(exp_id, message):
    # Log to the master log
    master_logger.info(f"{exp_id}: {message}")

    # Get or create the session-specific logger
    session_logger = create_session_logger(exp_id, log_folder)

    # Log the message to the session-specific logger
    session_logger.info(message)


#%%
# Example setup to use PrintLogger
def setup_logging_for_experiment(exp_id:str):
    # Initialize the master logger
    global master_logger, session_logger
    master_logger = create_master_logger(log_folder)
    session_logger = create_session_logger(exp_id, log_folder)

    # Redirect print statements to the logger
    sys.stdout = PrintLogger(exp_id)


#%%
# Example Usage
setup_logging_for_experiment('EXP0001')

# Now any print statements will be redirected to the logging system
print("Starting the experiment...")
print("Magnetic stirrer initialized.")
print("Pump activated.")

# Another session
setup_logging_for_experiment('EXP0002')
print("Starting the second experiment.")
print("Magnetic stirrer initialized SESSION 2.")
print("Pump activated SESSION 2.")