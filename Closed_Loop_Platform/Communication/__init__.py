

from .Logging import *
from .Client import *

# Path to the server script
server_script = os.path.abspath("/Users/Yi-An/Software/PycharmProjects/CO2Optimizer/Closed_Loop_Platform/Communication/Server.py")

def start_server_in_new_terminal(script_path):
    """Starts the given script in a new terminal window."""
    try:
        if os.name == "nt":  # For Windows
            subprocess.Popen(
                ["start", "cmd", "/k", f"python {script_path}"],
                shell=True,
            )
        elif os.name == "posix":  # For Linux/Mac
            terminal_emulator = "xterm"  # Replace with your preferred terminal emulator
            subprocess.Popen([terminal_emulator, "-e", f"python {script_path}"])
        print(f"Successfully started server: {script_path}")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

def ask_user_confirmation():
    """Asks the user if the server is running and connected to the GC."""
    while True:
        response = input("Is the server terminal running and connected to GC? (Y/N): ").strip().upper()
        if response == "Y":
            print("Server is confirmed to be running and connected to GC.")
            return True
        elif response == "N":
            print("Please ensure the server terminal is running and connected to GC, then try again.")
        else:
            print("Invalid input. Please enter 'Y' or 'N'.")

def check_experiment_preconditions():
    """Ask the user a series of questions to confirm preconditions before proceeding."""
    checks = [
        "Is the current platform connected to the server? (Y/N): ",
        "Is FID turned on to high sensitivity? (Y/N): ",
        "Is TCD turned on to high sensitivity? (Y/N): ",
        "Are all the solutions filled? (Y/N): ",
        "Is the gas (N2 and CO2) ready? (Y/N): ",
    ]
    
    for question in checks:
        while True:
            response = input(question).strip().upper()
            if response == "Y":
                break  # Proceed to the next question
            elif response == "N":
                print("Please resolve this issue before continuing.")
            else:
                print("Invalid input. Please enter 'Y' or 'N'.")

    print("All preconditions confirmed. Proceeding with the experiment.")

def open_terminal_to_view_log(log_file_path):
    """Opens a new terminal window to tail a log file."""
    try:
        if os.name == "nt":  # For Windows
            # Use start cmd to open a new console and tail the log file
            subprocess.Popen(
                ["start", "cmd", "/k", f"tail -f {log_file_path}"],
                shell=True,
            )
        elif os.name == "posix":  # For Linux/Mac
            # Replace 'xterm' with your preferred terminal emulator
            terminal_emulator = "xterm"  # Options: 'gnome-terminal', 'konsole', etc.
            subprocess.Popen(
                [terminal_emulator, "-e", f"tail -f {log_file_path}"],
            )
        print(f"Opened terminal for log file: {log_file_path}")
    except Exception as e:
        print(f"Error opening terminal for log file {log_file_path}: {e}")
