import sys
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QFileDialog

def select_csv_file():
    app = QApplication(sys.argv)
    file_dialog = QFileDialog()
    file_dialog.setNameFilter("CSV files (*.csv)")
    if file_dialog.exec_():
        file_path = file_dialog.selectedFiles()[0]
        return file_path
    return None

def load_csv_data(file_path):
    data = pd.read_csv(file_path, comment='#')
    return data

def plot_data(data):
    x = data.iloc[:, 0]
    y = data.iloc[:, 1]
    s = data.iloc[:, 2]

    plt.errorbar(x, y, yerr=s, fmt='o', ecolor='r', capsize=5)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('Error Plot')
    plt.show()

if __name__ == "__main__":
    file_path = select_csv_file()
    if file_path:
        data = load_csv_data(file_path)
        plot_data(data)
    else:
        print("No file selected.")