
from .gc_dataprocessing import *
from .DoEFormatting import *
from .DPAgent import *

def create_directory(path):
    """Create a directory if it doesn't already exist."""
    try:
        os.mkdir(path)
    except FileExistsError:
        print(f"{path} already exists.")
def generate_timestamp():
    """Generate a timestamp string."""
    datetime_str = datetime.now().isoformat(timespec='seconds')
    return datetime_str.replace(" ", "_").replace(":", "_")