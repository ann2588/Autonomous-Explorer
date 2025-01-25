import matplotlib.pyplot as plt
import os

def plotxy(size, x, y, title:str, xlabel:str, ylabel:str, path:str, filename:str):
    """
    Plot the catalysis current over time.
    """
    plt.figure(figsize=(size ,size))  # Set the figure size
    plt.plot(x, y, linestyle='-', color='b')  # Plot the data
    plt.title(title)  # Set the title
    plt.xlabel(xlabel)  # Set the x-axis label
    plt.ylabel(ylabel)  # Set the y-axis label
    plt.tight_layout()
    plt.savefig(os.path.join(path, f'{filename}.png'), dpi=600)  # Save the plot
    plt.show()  # Show the plot
    plt.close()