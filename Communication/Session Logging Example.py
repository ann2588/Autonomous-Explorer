import logging
import logging.handlers
import os
import time

# Create log folder if it doesn't exist
log_folder = r'/path/to/log/folder'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Master log file path (this file logs everything across all sessions)
master_log_file = os.path.join(log_folder, 'master.log')

# Set up the master log file handler
master_handler = logging.FileHandler(master_log_file)
master_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
master_handler.setFormatter(master_formatter)

# Create master logger
master_logger = logging.getLogger('master_logger')
master_logger.setLevel(logging.INFO)
master_logger.addHandler(master_handler)


# Function to create a session logger (specific to an experiment or session)
def create_session_logger(exp_id):
    # Create a session log file specific to the experiment/session
    session_log_file = os.path.join(log_folder, f'{exp_id}.log')

    # Set up the session file handler
    session_handler = logging.FileHandler(session_log_file)
    session_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [Session: %(exp_id)s] %(message)s')
    session_handler.setFormatter(session_formatter)

    # Create a session-specific logger
    session_logger = logging.getLogger(exp_id)
    session_logger.setLevel(logging.INFO)
    session_logger.addHandler(session_handler)

    return session_logger


# Logging for both master and session
def log_experiment_action(exp_id, message):
    # Log to the master log
    master_logger.info(f"Experiment {exp_id}: {message}")

    # Get or create the session-specific logger
    session_logger = create_session_logger(exp_id)

    # Log the message to the session-specific logger
    session_logger.info(message, extra={'exp_id': exp_id})


# Example usage
experiment_id = "EXP0001"  # Example experiment ID

#% Usage example #@@TODO Use this message for all the printed function
# Log an action for the specific session (experiment)
log_experiment_action(experiment_id, "Started experiment.")
log_experiment_action(experiment_id, "Processed data.")
log_experiment_action(experiment_id, "Completed experiment.")

# You can log more experiments by changing the experiment ID
log_experiment_action("EXP0002", "Started experiment.")
log_experiment_action("EXP0002", "Finished preliminary tests.")



from logging.handlers import RotatingFileHandler

def create_session_logger(exp_id):
    session_log_file = os.path.join(log_folder, f'{exp_id}.log')

    # Use RotatingFileHandler to rotate the log file based on size
    session_handler = RotatingFileHandler(session_log_file, maxBytes=5000, backupCount=5)
    session_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [Session: %(exp_id)s] %(message)s')
    session_handler.setFormatter(session_formatter)

    session_logger = logging.getLogger(exp_id)
    session_logger.setLevel(logging.INFO)
    session_logger.addHandler(session_handler)

    return session_logger