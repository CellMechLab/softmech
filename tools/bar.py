import sys,os
import pandas as pd
import matplotlib.pyplot as plt
from PySide6.QtWidgets import QApplication, QFileDialog

def select_csv_file():
    app = QApplication(sys.argv)
    file_dialog = QFileDialog()
    file_dialog.setNameFilter("CSV files (*.csv)")
    if file_dialog.exec_():
        file_path = file_dialog.selectedFiles()[0]
        return file_path
    return None

def load_csv_data(file_path):
    data = pd.read_csv(file_path, comment='#',delimiter='\t')
    return data

def plot_data(data,name = ''):
    x = data.iloc[:, 0]*1e6
    y = data.iloc[:, 1]*1e9
    s = data.iloc[:, 2]*1e9
    plt.fill_between(x,y+s/2,y-s/2,alpha=0.5)
    plt.plot(x, y)
    #, fmt='o', ecolor='r', capsize=5
    plt.xlabel('Indentation [um]')
    plt.ylabel('Force [nN]')
    plt.xlim( (min(x),max(x)) )
    plt.title(f'Elasticity analysis {name}')
    plt.show()

if __name__ == "__main__":
    file_path = select_csv_file()
    if file_path:
        data = load_csv_data(file_path)
        file_name = os.path.basename(file_path)
        plot_data(data,file_name)
    else:
        print("No file selected.")