from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog
from PySide6.QtCore import Signal
import csv
import os

class ADTResultsWidget(QWidget):
    csv_loaded = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Load button
        self.load_adt_csv_btn = QPushButton("Load ADT Results CSV")
        self.load_adt_csv_btn.clicked.connect(self.load_adt_results_csv)
        layout.addWidget(self.load_adt_csv_btn)
        
        # Results table
        self.adt_results_table = QTableWidget()
        self.adt_results_table.setColumnCount(7)
        self.adt_results_table.setHorizontalHeaderLabels([
            "Address", "City", "State", "Zip", "Confidence", "Image Path", "Feedback"
        ])
        self.adt_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.adt_results_table)
        
        self.setLayout(layout)

    def load_adt_results_csv(self):
        # Look for CSV files in the data directory first
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'consolidated')
        if os.path.exists(data_dir):
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select ADT Results CSV", 
                data_dir, 
                "CSV Files (*.csv)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select ADT Results CSV", 
                "", 
                "CSV Files (*.csv)"
            )
            
        if not file_path:
            return
            
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
            self.adt_results_table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                self.adt_results_table.setItem(row_idx, 0, QTableWidgetItem(row.get('address', '')))
                self.adt_results_table.setItem(row_idx, 1, QTableWidgetItem(row.get('city', '')))
                self.adt_results_table.setItem(row_idx, 2, QTableWidgetItem(row.get('state', '')))
                self.adt_results_table.setItem(row_idx, 3, QTableWidgetItem(row.get('zip', '')))
                self.adt_results_table.setItem(row_idx, 4, QTableWidgetItem(row.get('confidence', '')))
                self.adt_results_table.setItem(row_idx, 5, QTableWidgetItem(row.get('image_path', '')))
                self.adt_results_table.setItem(row_idx, 6, QTableWidgetItem(row.get('feedback', '')))
                
            self.csv_loaded.emit(file_path)
        except Exception as e:
            print(f"Error loading CSV: {e}") 