

from .Logging import *
from .Client import *


# Path to the server script
server_script = os.path.abspath(r"C:\Users\guazh\PycharmProjects\CO2Platform\Closed_Loop_Platform\Communication\Server.py")


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
    """Opens a PowerShell window to tail a log file using Start-Process."""
    try:
        # PowerShell command to open a new window and tail the log file
        command = f"Start-Process powershell -ArgumentList '-NoExit', '-Command \"Get-Content \\\"{log_file_path}\\\" -Wait\"'"

        # Execute the command
        subprocess.Popen(["powershell", "-Command", command], shell=True)
        print(f"Opened PowerShell window for log file: {log_file_path}")
    except Exception as e:
        print(f"Error opening PowerShell window for log file {log_file_path}: {e}")

def ask_user_restartPeakSimple():
    """Asks the user if the server is running and connected to the GC."""
    while True:
        response = input("Please restart the Peaksimple client (Y/N): ").strip().upper()
        if response == "Y":
            print("Server connecting to Peaksimple and GC...")
            return True
        elif response == "N":
            print("Please ensure the Peaksimple Client has been restarted and connected to GC, then try again.")
        else:
            print("Invalid input. Please enter 'Y' or 'N'.")

def find_and_kill_process(program_name):
    """Find and kill a process by its name."""
    import psutil
    import signal
    for process in psutil.process_iter(['pid', 'name']):
        if program_name.lower() in process.info['name'].lower():
            try:
                os.kill(process.info['pid'], signal.SIGTERM)
                print(f"Terminated process: {program_name} (PID: {process.info['pid']})")
                return True
            except Exception as e:
                print(f"Error terminating process {program_name}: {e}")
                return False
    print(f"No process found with name: {program_name}")
    return False

def restart_program(program_path):
    """Restart a program by killing it and starting it again."""
    program_name = os.path.basename(program_path)

    # Step 1: Kill the program if it's running
    if find_and_kill_process(program_name):
        time.sleep(2)  # Wait for the process to terminate

    # Step 2: Start the program
    try:
        subprocess.Popen([program_path], shell=True)
        print(f"Restarted program: {program_name}")
    except Exception as e:
        print(f"Error restarting program: {e}")