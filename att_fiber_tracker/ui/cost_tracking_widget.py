import os
import json
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QHBoxLayout, QComboBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from datetime import datetime, timedelta
import csv
from PySide6.QtWidgets import QFileDialog

logger = logging.getLogger(__name__)

class CostTrackingWidget(QWidget):
    """Widget for tracking and displaying API costs"""
    
    def __init__(self):
        super().__init__()
        self.cost_tracker = None  # Will be set from main app
        self.setup_ui()
        self.load_cost_data()
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(60000)  # Refresh every minute
    
    def setup_ui(self):
        """Setup the cost tracking UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("📊 API Cost Tracker")
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Period selector
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Today", "This Week", "This Month", "All Time"])
        self.period_combo.currentIndexChanged.connect(self.refresh_data)
        period_layout.addWidget(self.period_combo)
        period_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        period_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("📤 Export CSV")
        export_btn.clicked.connect(self.export_to_csv)
        period_layout.addWidget(export_btn)
        layout.addLayout(period_layout)
        
        # Summary cards
        summary_layout = QHBoxLayout()
        self.total_cost_label = self.create_summary_card("Total Cost", "$0.00")
        self.google_vision_cost = self.create_summary_card("Google Vision", "$0.00")
        self.google_maps_cost = self.create_summary_card("Google Maps", "$0.00")
        self.openai_cost = self.create_summary_card("OpenAI", "$0.00")
        self.xai_cost = self.create_summary_card("xAI", "$0.00")
        summary_layout.addWidget(self.total_cost_label)
        summary_layout.addWidget(self.google_vision_cost)
        summary_layout.addWidget(self.google_maps_cost)
        summary_layout.addWidget(self.openai_cost)
        summary_layout.addWidget(self.xai_cost)
        layout.addLayout(summary_layout)
        
        # Detailed table
        self.cost_table = QTableWidget()
        self.cost_table.setColumnCount(5)
        self.cost_table.setHorizontalHeaderLabels(["API", "Requests", "Cost", "Date", "Details"])
        self.cost_table.horizontalHeader().setStretchLastSection(True)
        self.cost_table.setAlternatingRowColors(True)
        self.cost_table.setSortingEnabled(True)
        layout.addWidget(self.cost_table)
    
    def create_summary_card(self, title, value):
        """Create a summary card label"""
        card = QLabel(f"{title}\n{value}")
        card.setAlignment(Qt.AlignCenter)
        card.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            margin: 5px;
        """)
        card.setFont(QFont("Arial", 12))
        return card
    
    def load_cost_data(self):
        """Load cost data from tracker"""
        if not self.cost_tracker:
            return
        
        try:
            self.all_cost_data = self.cost_tracker.get_all_usage()
            self.refresh_data()
        except Exception as e:
            logger.error(f"Error loading cost data: {e}")
    
    def refresh_data(self):
        """Refresh displayed data based on selected period"""
        if not hasattr(self, 'all_cost_data'):
            return
        
        period = self.period_combo.currentText()
        now = datetime.now()
        
        if period == "Today":
            start_date = now.replace(hour=0, minute=0, second=0)
        elif period == "This Week":
            start_date = now - timedelta(days=now.weekday())
        elif period == "This Month":
            start_date = now.replace(day=1)
        elif period == "All Time":
            start_date = datetime.min
        
        filtered_data = [entry for entry in self.all_cost_data if datetime.fromisoformat(entry['timestamp']) >= start_date]
        
        # Calculate summaries
        summaries = {
            'total': 0.0,
            'google_vision': 0.0,
            'google_maps': 0.0,
            'openai': 0.0,
            'xai': 0.0
        }
        
        for entry in filtered_data:
            summaries[entry['api']] += entry['cost']
            summaries['total'] += entry['cost']
        
        self.total_cost_label.setText(f"Total Cost\n${summaries['total']:.2f}")
        self.google_vision_cost.setText(f"Google Vision\n${summaries['google_vision']:.2f}")
        self.google_maps_cost.setText(f"Google Maps\n${summaries['google_maps']:.2f}")
        self.openai_cost.setText(f"OpenAI\n${summaries['openai']:.2f}")
        self.xai_cost.setText(f"xAI\n${summaries['xai']:.2f}")
        
        # Update table
        self.cost_table.setRowCount(len(filtered_data))
        for row, entry in enumerate(filtered_data):
            self.cost_table.setItem(row, 0, QTableWidgetItem(entry['api'].replace('_', ' ').title()))
            self.cost_table.setItem(row, 1, QTableWidgetItem(str(entry['requests'])))
            self.cost_table.setItem(row, 2, QTableWidgetItem(f"${entry['cost']:.4f}"))
            self.cost_table.setItem(row, 3, QTableWidgetItem(datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d %H:%M")))
            self.cost_table.setItem(row, 4, QTableWidgetItem(entry.get('details', '')))
        
        self.cost_table.sortItems(3, Qt.DescendingOrder)
    
    def export_to_csv(self):
        """Export cost data to CSV"""
        if not hasattr(self, 'all_cost_data') or not self.all_cost_data:
            QMessageBox.warning(self, "No Data", "No cost data available to export.")
            return
        
        filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "api_costs.csv", "CSV Files (*.csv)")
        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['timestamp', 'api', 'requests', 'cost', 'details'])
                    writer.writeheader()
                    writer.writerows(self.all_cost_data)
                QMessageBox.information(self, "Export Successful", f"Data exported to {filename}")
            except Exception as e:
                QMessageBox.error(self, "Export Error", f"Failed to export: {e}")
    
    def set_cost_tracker(self, cost_tracker):
        """Set the cost tracker instance from main app"""
        self.cost_tracker = cost_tracker
        self.load_cost_data() 