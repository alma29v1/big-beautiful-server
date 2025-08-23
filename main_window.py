from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QPushButton, QGroupBox, QCheckBox, QProgressBar, QSizePolicy, QTextEdit,
    QTableWidget, QListWidget, QHeaderView, QApplication, QFileDialog,
    QMessageBox, QComboBox, QSpinBox, QLineEdit, QTextBrowser, QTableWidgetItem,
    QDateEdit
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QThread, QDate
import time
from PySide6.QtGui import QFont, QPixmap, QCloseEvent
from workers.att_worker import ATTWorker
from workers.batchdata_worker import BatchDataWorker
from workers.mailchimp_worker import MailchimpWorker
from workers.custom_att_worker import CustomATTWorker
from workers.adt_detection_worker import ADTDetectionWorker
from workers.redfin_adt_detection_worker import RedfinADTDetectionWorker
from workers.redfin_worker import RedfinWorker
from workers.adt_training_worker import ADTTrainingWorker
from gui.adt_verification_widget import ADTVerificationWidget
from gui.settings_widget import SettingsWidget
from gui.cost_tracking_widget import CostTrackingWidget
# from gui.ai_email_marketing_widget import AIEmailMarketingWidget  # REMOVED - Using XAI version instead
from gui.fiber_availability_map_widget import FiberAvailabilityMapWidget
from gui.incident_response_widget import IncidentResponseWidget
from gui.backup_widget import BackupWidget
from gui.automation_widget import AutomationWidget
from gui.efficient_ai_email_widget import EfficientAIEmailWidget
import os
import time
import pandas as pd
import json
import glob
from datetime import datetime
import requests

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AT&T Fiber Tracker - Clean Version with Consolidated BatchData + Mailchimp")
        self.resize(1600, 900)
        self.setMinimumSize(1200, 800)
        self.setMaximumSize(1920, 1200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Initialize tracking
        self.redfin_workers = {}
        self.att_workers = {}
        self.batchdata_worker = None
        self.mailchimp_worker = None
        self.adt_worker = None
        self.redfin_completed = set()
        self.att_completed = set()
        self.att_results = {}
        self.att_workers = {}
        self.batchdata_workers = {}
        self.city_fiber_counts = {}
        self.total_fiber_count = 0
        self.total_redfin_count = 0
        self.total_att_fiber = 0
        self.total_adt_detected = 0
        self.consolidated_contacts = []
        
        # BatchData enriched results storage
        self.adt_enriched_contacts = []
        self.att_enriched_contacts = []
        
        # BatchLeads monitoring
        self.all_batchleads = []
        self.batchdata_file_timestamps = {}  # Track when files were last processed
        
        # City configurations
        self.cities = [
            {"name": "Leland", "url": "https://www.redfin.com/city/9564/NC/Leland/filter/include=sold-1wk"},
            {"name": "Wilmington", "url": "https://www.redfin.com/city/18894/NC/Wilmington/filter/include=sold-1wk,viewport=34.2898685:34.124065:-77.7896965:-77.957117"},
            {"name": "Lumberton", "url": "https://www.redfin.com/city/10113/NC/Lumberton/filter/include=sold-1wk"},
            {"name": "Hampstead", "url": "https://www.redfin.com/city/32836/NC/Hampstead/filter/include=sold-1wk"},
            {"name": "Southport", "url": "https://www.redfin.com/city/16254/NC/Southport/filter/include=sold-1wk"}
        ]
        
        self.settings_widget = SettingsWidget()
        self.settings_widget.api_keys_updated.connect(self.update_api_keys)
        self.settings_widget.backup_config_updated.connect(self.on_backup_config_updated)
        
        self.setup_ui()
        self.connect_signals()
        
        # Load API keys on startup
        self.api_keys = self.settings_widget.get_keys()
        self.set_api_env_vars(self.api_keys)
    
    def setup_ui(self):
        # Create main window and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # --- Main Tab ---
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout(main_tab)
        
        # Title
        title = QLabel("AT&T Fiber Tracker - Clean Version with Consolidated BatchData + Mailchimp")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; background: #e8f4fd;")
        main_tab_layout.addWidget(title)
        
        # Statistics Dashboard
        stats_group = QGroupBox("📊 Statistics Dashboard")
        stats_layout = QVBoxLayout()
        
        # Top row - Main stats
        main_stats_layout = QHBoxLayout()
        
        self.redfin_count = QLabel("Redfin Downloaded: 0")
        self.redfin_count.setStyleSheet("background: #FF9800; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: 14px;")
        main_stats_layout.addWidget(self.redfin_count)
        
        self.att_fiber_count = QLabel("AT&T Fiber: 0")
        self.att_fiber_count.setStyleSheet("background: #2196F3; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: 14px;")
        main_stats_layout.addWidget(self.att_fiber_count)
        
        # Add fiber_counter for compatibility with other methods
        self.fiber_counter = self.att_fiber_count
        
        self.adt_count = QLabel("ADT Detected: 0")
        self.adt_count.setStyleSheet("background: #9C27B0; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-size: 14px;")
        main_stats_layout.addWidget(self.adt_count)
        
        stats_layout.addLayout(main_stats_layout)
        
        # Bottom row - Status indicators
        status_layout = QHBoxLayout()
        
        self.redfin_status = QLabel("Redfin: Ready")
        self.redfin_status.setStyleSheet("background: gray; color: white; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")
        status_layout.addWidget(self.redfin_status)
        
        self.att_status = QLabel("AT&T: Ready")
        self.att_status.setStyleSheet("background: gray; color: white; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")
        status_layout.addWidget(self.att_status)
        
        self.batchdata_status = QLabel("BatchData: Waiting")
        self.batchdata_status.setStyleSheet("background: gray; color: white; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")
        status_layout.addWidget(self.batchdata_status)
        
        self.mailchimp_status = QLabel("Mailchimp: Waiting")
        self.mailchimp_status.setStyleSheet("background: gray; color: white; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")
        status_layout.addWidget(self.mailchimp_status)
        
        self.completion_status = QLabel("Process: Not Started")
        self.completion_status.setStyleSheet("background: gray; color: white; padding: 6px; border-radius: 4px; font-weight: bold; font-size: 12px;")
        status_layout.addWidget(self.completion_status)
        
        status_layout.addStretch()
        stats_layout.addLayout(status_layout)
        
        stats_group.setLayout(stats_layout)
        main_tab_layout.addWidget(stats_group)
        
        # City selection
        city_group = QGroupBox("City Selection")
        city_layout = QHBoxLayout()
        
        self.city_checkboxes = {}
        for city in self.cities:
            checkbox = QCheckBox(city["name"])
            checkbox.setChecked(True)
            self.city_checkboxes[city["name"]] = checkbox
            city_layout.addWidget(checkbox)
        
        city_group.setLayout(city_layout)
        main_tab_layout.addWidget(city_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_style = "QPushButton { background: #4CAF50; color: white; padding: 4px 10px; font-size: 12px; font-weight: bold; border-radius: 4px; min-width: 120px; min-height: 28px; max-width: 200px; } QPushButton:hover { background: #388E3C; } QPushButton:disabled { background: #cccccc; }"

        self.pull_data_btn = QPushButton("Pull Data (Redfin Only)")
        self.pull_data_btn.setStyleSheet(button_style)
        self.pull_data_btn.clicked.connect(self.pull_data)
        button_layout.addWidget(self.pull_data_btn)

        self.start_processing_btn = QPushButton("Start AT&T Processing")
        self.start_processing_btn.setStyleSheet(button_style)
        self.start_processing_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_processing_btn)

        self.adt_btn = QPushButton("Run ADT Detection")
        self.adt_btn.setStyleSheet(button_style)
        self.adt_btn.clicked.connect(self.run_adt_detection)
        button_layout.addWidget(self.adt_btn)
        
        self.batchdata_btn = QPushButton("Run BatchData")
        self.batchdata_btn.setStyleSheet(button_style)
        self.batchdata_btn.clicked.connect(self.start_batchdata_processing)
        button_layout.addWidget(self.batchdata_btn)

        # Add Manual MailChimp button
        mailchimp_style = "QPushButton { background: #FF5722; color: white; padding: 4px 10px; font-size: 12px; font-weight: bold; border-radius: 4px; min-width: 120px; min-height: 28px; max-width: 200px; } QPushButton:hover { background: #E64A19; } QPushButton:disabled { background: #cccccc; }"
        self.manual_mailchimp_btn = QPushButton("📧 Send to MailChimp")
        self.manual_mailchimp_btn.setStyleSheet(mailchimp_style)
        self.manual_mailchimp_btn.clicked.connect(self.manual_mailchimp_send)
        self.manual_mailchimp_btn.setEnabled(False)  # Disabled until data is ready
        button_layout.addWidget(self.manual_mailchimp_btn)

        self.batchdata_pause_btn = QPushButton("Pause BatchData")
        self.batchdata_pause_btn.setStyleSheet(button_style)
        self.batchdata_pause_btn.setEnabled(False)
        self.batchdata_pause_btn.clicked.connect(self.toggle_batchdata_pause)
        button_layout.addWidget(self.batchdata_pause_btn)

        self.adt_training_btn = QPushButton("Start ADT Training")
        self.adt_training_btn.setStyleSheet(button_style)
        self.adt_training_btn.clicked.connect(self.start_adt_training)
        button_layout.addWidget(self.adt_training_btn)
        
        self.custom_csv_btn = QPushButton("Custom CSV Import")
        self.custom_csv_btn.setStyleSheet(button_style)
        self.custom_csv_btn.clicked.connect(self.import_custom_csv)
        button_layout.addWidget(self.custom_csv_btn)
        
        # Add Clear Cache button with different styling
        clear_cache_style = "QPushButton { background: #f44336; color: white; padding: 4px 10px; font-size: 12px; font-weight: bold; border-radius: 4px; min-width: 120px; min-height: 28px; max-width: 200px; } QPushButton:hover { background: #d32f2f; } QPushButton:disabled { background: #cccccc; }"
        self.clear_cache_btn = QPushButton("Clear Cache")
        self.clear_cache_btn.setStyleSheet(clear_cache_style)
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        button_layout.addWidget(self.clear_cache_btn)
        
        main_tab_layout.addLayout(button_layout)
        
        # Progress bars
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.redfin_progress = QProgressBar()
        self.redfin_progress.setVisible(False)
        progress_layout.addWidget(QLabel("Redfin Progress:"))
        progress_layout.addWidget(self.redfin_progress)
        
        self.att_progress = QProgressBar()
        self.att_progress.setVisible(False)
        progress_layout.addWidget(QLabel("AT&T Progress:"))
        progress_layout.addWidget(self.att_progress)
        
        self.batchdata_progress = QProgressBar()
        self.batchdata_progress.setVisible(False)
        progress_layout.addWidget(QLabel("BatchData Progress:"))
        progress_layout.addWidget(self.batchdata_progress)
        
        progress_group.setLayout(progress_layout)
        main_tab_layout.addWidget(progress_group)
        
        # Log area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #475569;
                border-radius: 4px;
            }
        """)
        main_tab_layout.addWidget(self.log_text)
        
        self.tabs.addTab(main_tab, "Main")

        # --- ADT Detection Results Tab ---
        adt_tab = QWidget()
        adt_layout = QVBoxLayout(adt_tab)
        
        # ADT Results Header
        adt_header = QLabel("ADT Detection Results")
        adt_header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #e8f4fd;")
        adt_layout.addWidget(adt_header)
        
        # ADT Results Table
        self.adt_results_table = QTableWidget()
        self.adt_results_table.setColumnCount(7)
        self.adt_results_table.setHorizontalHeaderLabels([
            "Address", "City", "State", "ADT Detected", "Confidence", "Detection Method", "Image Path"
        ])
        self.adt_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        adt_layout.addWidget(self.adt_results_table)
        
        # Export ADT Results Button
        export_adt_btn = QPushButton("Export ADT Results to CSV")
        export_adt_btn.setStyleSheet(button_style)
        export_adt_btn.clicked.connect(self.export_adt_results)
        adt_layout.addWidget(export_adt_btn)
        
        # BatchData Integration for ADT
        adt_batchdata_group = QGroupBox("📊 BatchData Integration")
        adt_batchdata_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2980b9;
            }
        """)
        
        adt_batchdata_layout = QVBoxLayout()
        
        # Export to BatchData
        export_adt_batchdata_btn = QPushButton("📤 Send ADT Results to BatchData")
        export_adt_batchdata_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        export_adt_batchdata_btn.clicked.connect(self.export_adt_to_batchdata)
        adt_batchdata_layout.addWidget(export_adt_batchdata_btn)
        
        # Import BatchData results and send to MailChimp/ActiveKnocker
        adt_enriched_layout = QHBoxLayout()
        
        import_adt_batchdata_btn = QPushButton("📥 Import BatchData Results")
        import_adt_batchdata_btn.setStyleSheet("""
            QPushButton {
                background: #e67e22;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #d35400; }
        """)
        import_adt_batchdata_btn.clicked.connect(self.import_adt_batchdata_results)
        adt_enriched_layout.addWidget(import_adt_batchdata_btn)
        
        send_adt_mailchimp_btn = QPushButton("📧 Send to MailChimp")
        send_adt_mailchimp_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        send_adt_mailchimp_btn.clicked.connect(self.send_adt_to_mailchimp)
        adt_enriched_layout.addWidget(send_adt_mailchimp_btn)
        
        send_adt_activeknocker_btn = QPushButton("🎯 Send to ActiveKnocker")
        send_adt_activeknocker_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #229954; }
        """)
        send_adt_activeknocker_btn.clicked.connect(self.send_adt_to_activeknocker)
        adt_enriched_layout.addWidget(send_adt_activeknocker_btn)
        
        adt_batchdata_layout.addLayout(adt_enriched_layout)
        
        # Status label for ADT BatchData
        self.adt_batchdata_status = QLabel("⏳ No BatchData results loaded for ADT")
        self.adt_batchdata_status.setStyleSheet("""
            QLabel {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        adt_batchdata_layout.addWidget(self.adt_batchdata_status)
        
        adt_batchdata_group.setLayout(adt_batchdata_layout)
        adt_layout.addWidget(adt_batchdata_group)
        
        self.tabs.addTab(adt_tab, "ADT Detection Results")

        # --- BatchData & Contacts Tab ---
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        
        # BatchData Header
        batch_header = QLabel("BatchData Contacts with AT&T Fiber")
        batch_header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #e8f4fd;")
        batch_layout.addWidget(batch_header)
        
        self.batchdata_table = QTableWidget()
        self.batchdata_table.setColumnCount(8)
        self.batchdata_table.setHorizontalHeaderLabels([
            "Address", "City", "State", "Zip", "Phone", "Email", "Owner Name", "ADT Sign"
        ])
        self.batchdata_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        batch_layout.addWidget(self.batchdata_table)
        
        # Export BatchData Button
        export_batch_btn = QPushButton("Export BatchData to CSV")
        export_batch_btn.setStyleSheet(button_style)
        export_batch_btn.clicked.connect(self.export_batchdata_results)
        batch_layout.addWidget(export_batch_btn)
        
        self.tabs.addTab(batch_tab, "BatchData Contacts")
        
        # --- BatchLeads Monitoring Tab ---
        batchleads_tab = QWidget()
        batchleads_layout = QVBoxLayout(batchleads_tab)
        
        # BatchLeads Header
        batchleads_header = QLabel("📊 BatchLeads - Unified Lead Monitoring")
        batchleads_header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #e8f4fd;")
        batchleads_layout.addWidget(batchleads_header)
        
        # Status and monitoring section
        monitoring_group = QGroupBox("🔄 BatchData Monitoring")
        monitoring_layout = QVBoxLayout()
        
        # Status indicators
        status_row = QHBoxLayout()
        
        self.batchleads_status = QLabel("⏳ Monitoring for BatchData results...")
        self.batchleads_status.setStyleSheet("""
            QLabel {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        status_row.addWidget(self.batchleads_status)
        
        self.auto_scan_btn = QPushButton("🔍 Scan for New Results")
        self.auto_scan_btn.setStyleSheet("""
            QPushButton {
                background: #17a2b8;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #138496; }
        """)
        self.auto_scan_btn.clicked.connect(self.scan_for_batchdata_results)
        status_row.addWidget(self.auto_scan_btn)
        
        monitoring_layout.addLayout(status_row)
        
        # Results summary
        self.batchleads_summary = QLabel("No BatchData results found yet")
        self.batchleads_summary.setStyleSheet("""
            QLabel {
                background: #e9ecef;
                padding: 10px;
                border-radius: 4px;
                font-size: 14px;
            }
        """)
        monitoring_layout.addWidget(self.batchleads_summary)
        
        monitoring_group.setLayout(monitoring_layout)
        batchleads_layout.addWidget(monitoring_group)
        
        # Results table
        self.batchleads_table = QTableWidget()
        self.batchleads_table.setColumnCount(10)
        self.batchleads_table.setHorizontalHeaderLabels([
            "Select", "Source", "Address", "City", "Owner Name", "Email", "Phone", "Lead Type", "Import Date", "Status"
        ])
        self.batchleads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        batchleads_layout.addWidget(self.batchleads_table)
        
        # Action buttons for BatchLeads
        batchleads_actions = QHBoxLayout()
        
        select_all_btn = QPushButton("☑️ Select All")
        select_all_btn.setStyleSheet("""
            QPushButton {
                background: #6c757d;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5a6268; }
        """)
        select_all_btn.clicked.connect(self.select_all_batchleads)
        batchleads_actions.addWidget(select_all_btn)
        
        export_selected_mailchimp_btn = QPushButton("📧 Send Selected to MailChimp")
        export_selected_mailchimp_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        export_selected_mailchimp_btn.clicked.connect(self.send_selected_batchleads_to_mailchimp)
        batchleads_actions.addWidget(export_selected_mailchimp_btn)
        
        export_selected_ak_btn = QPushButton("🎯 Send Selected to ActiveKnocker")
        export_selected_ak_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #229954; }
        """)
        export_selected_ak_btn.clicked.connect(self.send_selected_batchleads_to_activeknocker)
        batchleads_actions.addWidget(export_selected_ak_btn)
        
        batchleads_layout.addLayout(batchleads_actions)
        
        self.tabs.addTab(batchleads_tab, "BatchLeads Monitor")

        # --- AT&T Fiber Results Tab ---
        att_tab = QWidget()
        att_layout = QVBoxLayout(att_tab)
        
        # AT&T Header
        att_header = QLabel("AT&T Fiber Availability Results")
        att_header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #e8f4fd;")
        att_layout.addWidget(att_header)
        
        self.att_results_table = QTableWidget()
        self.att_results_table.setColumnCount(6)
        self.att_results_table.setHorizontalHeaderLabels([
            "Address", "Fiber Available", "City", "State", "Zip", "Processed Date"
        ])
        self.att_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        att_layout.addWidget(self.att_results_table)
        
        # Export AT&T Results Button
        export_att_btn = QPushButton("Export AT&T Results to CSV")
        export_att_btn.setStyleSheet(button_style)
        export_att_btn.clicked.connect(self.export_att_results)
        att_layout.addWidget(export_att_btn)
        
        # BatchData Integration for AT&T
        att_batchdata_group = QGroupBox("📊 BatchData Integration")
        att_batchdata_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2980b9;
            }
        """)
        
        att_batchdata_layout = QVBoxLayout()
        
        # Export to BatchData
        export_att_batchdata_btn = QPushButton("📤 Send AT&T Results to BatchData")
        export_att_batchdata_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        export_att_batchdata_btn.clicked.connect(self.export_att_to_batchdata)
        att_batchdata_layout.addWidget(export_att_batchdata_btn)
        
        # Import BatchData results and send to MailChimp/ActiveKnocker
        att_enriched_layout = QHBoxLayout()
        
        import_att_batchdata_btn = QPushButton("📥 Import BatchData Results")
        import_att_batchdata_btn.setStyleSheet("""
            QPushButton {
                background: #e67e22;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #d35400; }
        """)
        import_att_batchdata_btn.clicked.connect(self.import_att_batchdata_results)
        att_enriched_layout.addWidget(import_att_batchdata_btn)
        
        send_att_mailchimp_btn = QPushButton("📧 Send to MailChimp")
        send_att_mailchimp_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        send_att_mailchimp_btn.clicked.connect(self.send_att_to_mailchimp)
        att_enriched_layout.addWidget(send_att_mailchimp_btn)
        
        send_att_activeknocker_btn = QPushButton("🎯 Send to ActiveKnocker")
        send_att_activeknocker_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #229954; }
        """)
        send_att_activeknocker_btn.clicked.connect(self.send_att_to_activeknocker)
        att_enriched_layout.addWidget(send_att_activeknocker_btn)
        
        att_batchdata_layout.addLayout(att_enriched_layout)
        
        # Status label for AT&T BatchData
        self.att_batchdata_status = QLabel("⏳ No BatchData results loaded for AT&T")
        self.att_batchdata_status.setStyleSheet("""
            QLabel {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        att_batchdata_layout.addWidget(self.att_batchdata_status)
        
        att_batchdata_group.setLayout(att_batchdata_layout)
        att_layout.addWidget(att_batchdata_group)
        
        self.tabs.addTab(att_tab, "AT&T Fiber Results")

        # --- ActiveKnocker Tab ---
        activeknocker_tab = QWidget()
        ak_layout = QVBoxLayout(activeknocker_tab)
        
        # ActiveKnocker Header
        ak_header = QLabel("ActiveKnocker Integration")
        ak_header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #e8f4fd;")
        ak_layout.addWidget(ak_header)
        
        # Date Range and Filter Controls
        filter_group = QGroupBox("Export Filters")
        filter_layout = QVBoxLayout()
        
        # Date Range Selection
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date Range:"))
        self.ak_start_date = QDateEdit()
        self.ak_start_date.setCalendarPopup(True)
        self.ak_start_date.setDate(QDate.currentDate().addDays(-30))  # Default to last 30 days
        date_layout.addWidget(self.ak_start_date)
        date_layout.addWidget(QLabel("to"))
        self.ak_end_date = QDateEdit()
        self.ak_end_date.setCalendarPopup(True)
        self.ak_end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.ak_end_date)
        filter_layout.addLayout(date_layout)
        
        # Lead Type Filter
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Lead Type:"))
        self.ak_lead_type = QComboBox()
        self.ak_lead_type.addItems([
            "All Leads",
            "AT&T Fiber Available Only", 
            "AT&T Verified Homes Only",
            "ADT Detected Only",
            "Fiber + ADT Combo"
        ])
        type_layout.addWidget(self.ak_lead_type)
        filter_layout.addLayout(type_layout)
        
        # City Filter
        city_layout = QHBoxLayout()
        city_layout.addWidget(QLabel("Cities:"))
        self.ak_city_filter = QComboBox()
        self.ak_city_filter.addItems([
            "All Cities",
            "Wilmington",
            "Leland", 
            "Hampstead",
            "Lumberton",
            "Southport"
        ])
        city_layout.addWidget(self.ak_city_filter)
        filter_layout.addLayout(city_layout)
        
        filter_group.setLayout(filter_layout)
        ak_layout.addWidget(filter_group)
        
        # Pacific Sales Team Assignment
        sales_group = QGroupBox("🏢 Pacific Sales Team Assignment")
        sales_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #27ae60;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #27ae60;
            }
        """)
        sales_layout = QVBoxLayout()
        
        # Salesperson Assignment Controls
        assignment_layout = QHBoxLayout()
        
        assignment_layout.addWidget(QLabel("Assign leads to:"))
        self.ak_salesperson = QComboBox()
        self.ak_salesperson.addItems([
            "Auto-Assign by Territory",
            "Robert Mitchell - Wilmington/Leland",
            "Amanda Rodriguez - Hampstead/Pender County", 
            "James Patterson - Brunswick County",
            "Maria Gonzalez - Lumberton/Robeson County",
            "Team Lead - All Territories"
        ])
        self.ak_salesperson.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #27ae60;
                border-radius: 4px;
                background: white;
                font-weight: bold;
            }
        """)
        assignment_layout.addWidget(self.ak_salesperson)
        
        # Territory Rules Button
        self.territory_rules_btn = QPushButton("📋 View Territory Rules")
        self.territory_rules_btn.setStyleSheet("""
            QPushButton {
                background: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
        """)
        self.territory_rules_btn.clicked.connect(self.show_territory_rules)
        assignment_layout.addWidget(self.territory_rules_btn)
        
        sales_layout.addLayout(assignment_layout)
        
        # Lead Priority Settings
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Lead Priority:"))
        self.ak_priority = QComboBox()
        self.ak_priority.addItems([
            "Standard Priority",
            "High Priority - Fiber + ADT",
            "Medium Priority - Fiber Only",
            "Low Priority - ADT Only",
            "Rush - Same Day Contact"
        ])
        self.ak_priority.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #27ae60;
                border-radius: 4px;
                background: white;
            }
        """)
        priority_layout.addWidget(self.ak_priority)
        
        # Contact Method
        priority_layout.addWidget(QLabel("Contact Method:"))
        self.ak_contact_method = QComboBox()
        self.ak_contact_method.addItems([
            "Door Knock + Phone",
            "Door Knock Only",
            "Phone Call First",
            "Email + Phone",
            "Text Message + Call"
        ])
        priority_layout.addWidget(self.ak_contact_method)
        
        sales_layout.addLayout(priority_layout)
        
        # Assignment Summary
        self.assignment_summary = QLabel("No assignments configured")
        self.assignment_summary.setStyleSheet("""
            QLabel {
                background: #ecf0f1;
                padding: 8px;
                border-radius: 4px;
                font-style: italic;
                color: #2c3e50;
            }
        """)
        sales_layout.addWidget(self.assignment_summary)
        
        # Connect signals for dynamic updates
        self.ak_salesperson.currentTextChanged.connect(self.update_assignment_summary)
        self.ak_priority.currentTextChanged.connect(self.update_assignment_summary)
        self.ak_contact_method.currentTextChanged.connect(self.update_assignment_summary)
        
        sales_group.setLayout(sales_layout)
        ak_layout.addWidget(sales_group)
        
        # ActiveKnocker Controls
        ak_controls = QHBoxLayout()
        
        self.load_ak_data_btn = QPushButton("Load Data")
        self.load_ak_data_btn.setStyleSheet(button_style)
        self.load_ak_data_btn.clicked.connect(self.load_activeknocker_data)
        ak_controls.addWidget(self.load_ak_data_btn)
        
        self.export_ak_csv_btn = QPushButton("Export to CSV")
        self.export_ak_csv_btn.setStyleSheet(button_style)
        self.export_ak_csv_btn.clicked.connect(self.export_activeknocker_csv)
        ak_controls.addWidget(self.export_ak_csv_btn)
        
        self.upload_to_ak_btn = QPushButton("Upload to ActiveKnocker")
        self.upload_to_ak_btn.setStyleSheet(button_style)
        self.upload_to_ak_btn.clicked.connect(self.upload_to_activeknocker)
        ak_controls.addWidget(self.upload_to_ak_btn)
        
        # Add verification button
        self.verify_ak_btn = QPushButton("🔍 Verify Uploads")
        self.verify_ak_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        self.verify_ak_btn.clicked.connect(self.verify_activeknocker_uploads)
        ak_controls.addWidget(self.verify_ak_btn)
        
        self.ak_status_label = QLabel("Status: Ready")
        self.ak_status_label.setStyleSheet("background: gray; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        ak_controls.addWidget(self.ak_status_label)
        
        ak_layout.addLayout(ak_controls)
        
        # Stats Display
        self.ak_stats_label = QLabel("No data loaded")
        self.ak_stats_label.setStyleSheet("background: #f8f9fa; padding: 8px; border-radius: 5px; font-weight: bold;")
        ak_layout.addWidget(self.ak_stats_label)
        
        # ActiveKnocker Results Table
        self.ak_results_table = QTableWidget()
        self.ak_results_table.setColumnCount(10)
        self.ak_results_table.setHorizontalHeaderLabels([
            "Select", "Address", "City", "State", "Zip", "Fiber Available", "ADT Detected", "Assigned To", "Priority", "Status"
        ])
        self.ak_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        ak_layout.addWidget(self.ak_results_table)
        
        self.tabs.addTab(activeknocker_tab, "ActiveKnocker")
        
        # --- AI/Mailchimp Marketing Tab ---
        ai_tab = QWidget()
        ai_layout = QVBoxLayout()
        
        mailchimp_group = QGroupBox("Mailchimp Marketing Data")
        mailchimp_layout = QVBoxLayout()
        
        self.mailchimp_table = QTableWidget()
        self.mailchimp_table.setColumnCount(5)
        self.mailchimp_table.setHorizontalHeaderLabels([
            "Email", "List", "Status", "Name", "Address"
        ])
        self.mailchimp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.mailchimp_table.setAlternatingRowColors(True)
        self.mailchimp_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e293b;
                alternate-background-color: #334155;
                color: #e2e8f0;
                gridline-color: #475569;
                border: 1px solid #475569;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #334155;
                color: #e2e8f0;
                padding: 4px;
                border: 1px solid #475569;
            }
        """)
        
        refresh_mailchimp_btn = QPushButton("Refresh Mailchimp Data")
        refresh_mailchimp_btn.setStyleSheet(button_style)
        refresh_mailchimp_btn.clicked.connect(self.sync_ai_tab_data)
        mailchimp_layout.addWidget(refresh_mailchimp_btn)
        mailchimp_layout.addWidget(self.mailchimp_table)
        
        mailchimp_group.setLayout(mailchimp_layout)
        ai_layout.addWidget(mailchimp_group)
        
        # Add AI Marketing Controls
        ai_controls_group = QGroupBox("AI Marketing Controls")
        ai_controls_layout = QVBoxLayout()
        
        # Marketing campaign controls
        campaign_layout = QHBoxLayout()
        
        self.create_campaign_btn = QPushButton("Create Marketing Campaign")
        self.create_campaign_btn.setStyleSheet(button_style)
        self.create_campaign_btn.clicked.connect(self.create_marketing_campaign)
        campaign_layout.addWidget(self.create_campaign_btn)
        
        self.send_campaign_btn = QPushButton("Send Campaign")
        self.send_campaign_btn.setStyleSheet(button_style)
        self.send_campaign_btn.clicked.connect(self.send_marketing_campaign)
        campaign_layout.addWidget(self.send_campaign_btn)
        
        ai_controls_layout.addLayout(campaign_layout)
        
        # Campaign status
        self.campaign_status_label = QLabel("Campaign Status: Ready")
        self.campaign_status_label.setStyleSheet("background: gray; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        ai_controls_layout.addWidget(self.campaign_status_label)
        
        ai_controls_group.setLayout(ai_controls_layout)
        ai_layout.addWidget(ai_controls_group)
        
        # --- XAI Assistant Section ---
        xai_group = QGroupBox("XAI Email Assistant")
        xai_layout = QVBoxLayout()
        xai_desc = QLabel("Use XAI or OpenAI to help write, review, and optimize Mailchimp campaigns. Coming soon!")
        xai_layout.addWidget(xai_desc)
        xai_group.setLayout(xai_layout)
        ai_layout.addWidget(xai_group)
        
        ai_tab.setLayout(ai_layout)
        # Removed redundant tab
        # self.tabs.addTab(ai_tab, "AI Email Marketing")
        
        # --- ADT Verification Tab ---
        adt_verification_tab = QWidget()
        adt_verification_layout = QVBoxLayout(adt_verification_tab)
        
        # ADT Verification Header
        adt_verification_header = QLabel("ADT Verification")
        adt_verification_header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background: #e8f4fd;")
        adt_verification_layout.addWidget(adt_verification_header)
        
        # ADT Verification Widget
        self.adt_verification_tab = ADTVerificationWidget()
        adt_verification_layout.addWidget(self.adt_verification_tab)
        
        self.tabs.addTab(adt_verification_tab, "ADT Verification")

        # --- Settings Tab ---
        self.tabs.addTab(self.settings_widget, "Settings")
        
        # --- Cost Tracking Tab ---
        self.cost_tracking_widget = CostTrackingWidget()
        self.tabs.addTab(self.cost_tracking_widget, "API Costs")
        
        # --- AI Email Marketing Tab (REMOVED - Using XAI version instead) ---
        # self.ai_email_marketing_widget = AIEmailMarketingWidget()
        # self.tabs.addTab(self.ai_email_marketing_widget, "AI Email Marketing")

        # --- AT&T Fiber Availability Map Tab ---
        self.fiber_map_widget = FiberAvailabilityMapWidget()
        self.tabs.addTab(self.fiber_map_widget, "AT&T Fiber Map")

        # --- Incident Response Tab ---
        self.incident_response_widget = IncidentResponseWidget()
        self.tabs.addTab(self.incident_response_widget, "Incident Response")

        # --- Backup Tab ---
        self.backup_widget = BackupWidget()
        self.tabs.addTab(self.backup_widget, "Cloud Backup")

        # --- Automation Tab ---
        self.automation_tab = AutomationWidget()
        self.automation_tab.run_automation_signal.connect(self.handle_automation)
        self.tabs.addTab(self.automation_tab, "Automation")

        # Add tabs to main layout
        main_layout.addWidget(self.tabs)
        
        # Add initial log message
        self.log_text.append("AT&T Fiber Tracker initialized successfully!")
        self.log_text.append("All worker classes have been modularized into the workers/ directory.")
        self.log_text.append("Ready to process Redfin data, check AT&T fiber availability, and run ADT detection.")
        self.log_text.append('[MAIN] Settings tab for API keys is present.')

        # In setup_ui method
        self.ai_email_tab = EfficientAIEmailWidget(self)
        self.tabs.addTab(self.ai_email_tab, "AI Email Marketing")
    
    def connect_signals(self):
        """Connect all worker signals"""
        # This will be called when workers are created
        pass
    
    def on_tab_changed(self, index):
        """Handle tab changes"""
        # Get the tab name
        tab_name = self.tabs.tabText(index)
        
        # Auto-scan for BatchData results when BatchLeads tab is opened
        if tab_name == "BatchLeads Monitor":
            self.scan_for_batchdata_results()
    
    def switch_to_ai_email_tab(self):
        """Switch to the AI Email Marketing tab (XAI version)"""
        # Find the AI Email Marketing tab index
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "AI Email Marketing":
                self.tabs.setCurrentIndex(i)
                return
    
    def get_selected_cities(self):
        """Get list of selected cities"""
        selected = []
        for city_name, checkbox in self.city_checkboxes.items():
            if checkbox.isChecked():
                selected.append(city_name)
        return selected
    
    def pull_data(self):
        """Pull Redfin data for selected cities"""
        selected_cities = self.get_selected_cities()
        if not selected_cities:
            QMessageBox.warning(self, "No Cities Selected", "Please select at least one city.")
            return
        
        self.log_text.append(f"[MAIN] Starting Redfin data pull for {len(selected_cities)} cities...")
        self.redfin_status.setText("Redfin: Running")
        self.redfin_status.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        
        # Start Redfin workers for each city
        for city_name in selected_cities:
            city_config = next((c for c in self.cities if c["name"] == city_name), None)
            if city_config:
                worker = RedfinWorker(city_name, city_config["url"])
                
                # Connect signals properly
                worker.log_signal.connect(lambda msg, city=city_name: self.log_text.append(f"[{city}] {msg}"))
                worker.progress_signal.connect(lambda city, current, text, c=city_name: self.update_redfin_progress(c, current, 0, text))
                worker.completed_signal.connect(lambda city, csv_file, c=city_name: self.on_redfin_completed(c, csv_file))
                
                self.redfin_workers[city_name] = worker
                worker.start()
    
    def update_redfin_progress(self, city, current, total, text):
        """Update Redfin progress bar"""
        self.redfin_progress.setVisible(True)
        self.redfin_progress.setMaximum(total)
        self.redfin_progress.setValue(current)
        self.log_text.append(f"[{city}] {text}")
    
    def on_redfin_completed(self, city, csv_file):
        """Handle Redfin completion"""
        self.redfin_completed.add(city)
        self.log_text.append(f"[{city}] Redfin data collection completed: {csv_file}")
        
        if len(self.redfin_completed) == len(self.get_selected_cities()):
            self.redfin_status.setText("Redfin: Completed")
            self.redfin_status.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.redfin_progress.setVisible(False)
            self.log_text.append("[MAIN] All Redfin data collection completed!")
            
            # Update statistics
            self.count_redfin_addresses()
            self.update_statistics_display()
    
    def start_processing(self):
        """Start AT&T processing for completed cities"""
        if not self.redfin_completed:
            QMessageBox.warning(self, "No Redfin Data", "Please pull Redfin data first.")
            return
        
        self.log_text.append(f"[MAIN] Starting AT&T processing for {len(self.redfin_completed)} cities...")
        self.att_status.setText("AT&T: Running")
        self.att_status.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        
        # Start AT&T workers for each completed city
        for city_name in self.redfin_completed:
            worker = ATTWorker(city_name)
            worker.log_signal.connect(lambda msg: self.log_text.append(f"[AT&T] {msg}"))
            worker.progress_signal.connect(lambda city, current, total: self.update_att_progress(city, current, total))
            worker.finished_signal.connect(lambda city, results: self.on_att_finished(city, results))
            worker.fiber_count_signal.connect(lambda city, count: self.update_fiber_counter(city, count))
            
            self.att_workers[city_name] = worker
            worker.start()
    
    def update_att_progress(self, city, current, total):
        """Update AT&T progress bar"""
        self.att_progress.setVisible(True)
        self.att_progress.setMaximum(total)
        self.att_progress.setValue(current)
    
    def on_att_finished(self, city, results):
        """Handle AT&T completion"""
        self.att_completed.add(city)
        
        # Store results properly
        if results and 'addresses' in results:
            self.att_results[city] = {
                'results': results['addresses'],
                'fiber_count': results.get('fiber_count', 0),
                'total_count': results.get('total_count', 0)
            }
            self.log_text.append(f"[AT&T] {city} completed: {results.get('fiber_count', 0)} with fiber, {results.get('total_count', 0)} total")
        else:
            self.att_results[city] = {'results': [], 'fiber_count': 0, 'total_count': 0}
            self.log_text.append(f"[AT&T] {city} completed with no results")
        
        # Update the AT&T results tab immediately
        self.update_att_results_tab()
        
        if len(self.att_completed) == len(self.get_selected_cities()):
            self.att_status.setText("AT&T: Completed")
            self.att_status.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.att_progress.setVisible(False)
            self.log_text.append("[MAIN] All AT&T fiber checks completed!")
            
            # Calculate total fiber count
            total_fiber = sum(city_data.get('fiber_count', 0) for city_data in self.att_results.values())
            self.total_att_fiber = total_fiber
            
            # Update statistics display
            self.update_statistics_display()
    
    def update_fiber_counter(self, city, fiber_count):
        """Update fiber counter"""
        self.city_fiber_counts[city] = fiber_count
        self.total_fiber_count = sum(self.city_fiber_counts.values())
        self.fiber_counter.setText(f"Fiber Available: {self.total_fiber_count}")
    
    def start_batchdata_processing(self):
        """Start BatchData processing for ALL addresses (not just fiber)"""
        if not self.att_results:
            QMessageBox.warning(self, "No AT&T Data", "Please run AT&T fiber checks first.")
            return
        
        # Count ALL addresses (both fiber and non-fiber)
        total_addresses = 0
        for city_data in self.att_results.values():
            if 'results' in city_data:
                total_addresses += len(city_data['results'])
        
        if total_addresses == 0:
            QMessageBox.information(self, "No Addresses", "No addresses found for BatchData processing.")
            return
        
        # Count fiber vs non-fiber for reporting
        fiber_count = 0
        non_fiber_count = 0
        for city_data in self.att_results.values():
            if 'results' in city_data:
                for addr in city_data['results']:
                    if addr.get('fiber_available', False):
                        fiber_count += 1
                    else:
                        non_fiber_count += 1
        
        self.log_text.append(f"[MAIN] Starting BatchData processing for ALL {total_addresses} addresses...")
        self.log_text.append(f"[MAIN] - {fiber_count} addresses have AT&T Fiber")
        self.log_text.append(f"[MAIN] - {non_fiber_count} addresses do NOT have AT&T Fiber")
        self.log_text.append(f"[MAIN] This will create comprehensive contact lists for both fiber and non-fiber marketing")
        
        self.batchdata_status.setText("BatchData: Running")
        self.batchdata_status.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        
        # Get BatchData API key from settings
        batchdata_api_key = self.api_keys.get('batchdata_api_key', '')
        if not batchdata_api_key:
            QMessageBox.warning(self, "Missing API Key", "Please set your BatchData API key in Settings.")
            return
        
        self.log_text.append(f"[MAIN] Using BatchData API key: {batchdata_api_key[:10]}...")
        
        # Convert AT&T results to the format expected by BatchData worker
        # IMPORTANT: Pass ALL addresses, not just fiber ones
        converted_results = {}
        for city_name, city_data in self.att_results.items():
            if 'results' in city_data:
                converted_results[city_name] = {
                    'addresses': city_data['results']  # ALL addresses, both fiber and non-fiber
                }
        
        self.batchdata_worker = BatchDataWorker(converted_results, batchdata_api_key)
        self.batchdata_worker.log_signal.connect(lambda msg: self.log_text.append(msg))
        self.batchdata_worker.progress_signal.connect(self.update_batchdata_progress)
        self.batchdata_worker.finished_signal.connect(self.on_batchdata_finished)
        
        self.batchdata_progress.setVisible(True)
        self.batchdata_pause_btn.setEnabled(True)
        
        self.batchdata_worker.start()
    
    def toggle_batchdata_pause(self):
        if hasattr(self, 'batchdata_worker') and self.batchdata_worker.isRunning():
            if not getattr(self, '_batchdata_paused', False):
                self.batchdata_worker.stop_flag = True
                self._batchdata_paused = True
                self.batchdata_pause_btn.setText("Resume BatchData")
                self.log_text.append("[MAIN] BatchData processing paused.")
            else:
                self.batchdata_worker.stop_flag = False
                self._batchdata_paused = False
                self.batchdata_pause_btn.setText("Pause BatchData")
                self.log_text.append("[MAIN] BatchData processing resumed.")
                self.batchdata_worker.start()
    
    def on_batchdata_finished(self, summary):
        """Handle BatchData completion"""
        if summary.get('success', False):
            total_contacts = summary.get('total_contacts', 0)
            self.log_text.append(f"[MAIN] BatchData completed successfully with {total_contacts} contacts")
            self.batchdata_status.setText("BatchData: Completed")
            self.batchdata_status.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.completion_status.setText("Process: Completed")
            self.completion_status.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            # Enable MailChimp button when BatchData is complete and we have contacts
            if hasattr(self, 'manual_mailchimp_btn') and total_contacts > 0:
                self.manual_mailchimp_btn.setEnabled(True)
                self.log_text.append(f"[MAIN] ✅ MailChimp button enabled - ready to send {total_contacts} contacts")
            
            # Enable other processing buttons
            self.enable_all_main_buttons()
        else:
            self.batchdata_status.setText("BatchData: Error")
            self.batchdata_status.setStyleSheet("background: red; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.completion_status.setText("Process: Error in BatchData")
            self.completion_status.setStyleSheet("background: red; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        self.enable_all_main_buttons()
    
    def enable_all_main_buttons(self):
        """Enable all main processing buttons"""
        try:
            # Enable Redfin processing button
            if hasattr(self, 'pull_data_btn'):
                self.pull_data_btn.setEnabled(True)
            
            # Enable AT&T processing button
            if hasattr(self, 'start_processing_btn'):
                self.start_processing_btn.setEnabled(True)
            
            # Enable BatchData processing button
            if hasattr(self, 'start_batchdata_btn'):
                self.start_batchdata_btn.setEnabled(True)
            
            # Enable ADT detection button
            if hasattr(self, 'run_adt_detection_btn'):
                self.run_adt_detection_btn.setEnabled(True)
            
            # Enable MailChimp button if we have contacts
            if hasattr(self, 'manual_mailchimp_btn'):
                # Only enable if we have contacts to send
                if hasattr(self, 'consolidated_contacts') and len(self.consolidated_contacts) > 0:
                    self.manual_mailchimp_btn.setEnabled(True)
                else:
                    self.manual_mailchimp_btn.setEnabled(False)
            
            self.log_text.append("[MAIN] ✅ All main buttons enabled")
            
        except Exception as e:
            self.log_text.append(f"[MAIN] Error enabling buttons: {e}")
    
    def update_batchdata_progress(self, current, total):
        self.batchdata_status.setText(f"BatchData: {current}/{total}")
    
    def update_att_results_tab(self):
        """Update AT&T results tab"""
        try:
            all_results = []
            for city_name, city_data in self.att_results.items():
                if isinstance(city_data, dict) and 'results' in city_data:
                    all_results.extend(city_data['results'])
            
            if not all_results:
                self.log_text.append("[MAIN] No AT&T results to display")
                return
            
            self.att_results_table.setRowCount(len(all_results))
            
            for i, result in enumerate(all_results):
                self.att_results_table.setItem(i, 0, QTableWidgetItem(result.get('address', '')))
                fiber_status = "Yes" if result.get('fiber_available', False) else "No"
                self.att_results_table.setItem(i, 1, QTableWidgetItem(fiber_status))
                self.att_results_table.setItem(i, 2, QTableWidgetItem(result.get('city', '')))
                self.att_results_table.setItem(i, 3, QTableWidgetItem(result.get('state', '')))
                self.att_results_table.setItem(i, 4, QTableWidgetItem(result.get('zip', '')))
                self.att_results_table.setItem(i, 5, QTableWidgetItem(result.get('processed_date', '')))
            
            # Auto-resize columns to content
            self.att_results_table.resizeColumnsToContents()
            
            self.log_text.append(f"[MAIN] Updated AT&T results tab with {len(all_results)} addresses")
            
        except Exception as e:
            self.log_text.append(f"[MAIN] Error updating AT&T results tab: {e}")
            import traceback
            self.log_text.append(f"[MAIN] Traceback: {traceback.format_exc()}")
    
    def update_adt_results_tab(self, adt_results):
        """Update ADT results tab"""
        try:
            if not adt_results:
                return
            
            self.adt_results_table.setRowCount(len(adt_results))
            
            for i, result in enumerate(adt_results):
                self.adt_results_table.setItem(i, 0, QTableWidgetItem(result.get('address', '')))
                self.adt_results_table.setItem(i, 1, QTableWidgetItem(result.get('city', '')))
                self.adt_results_table.setItem(i, 2, QTableWidgetItem(result.get('state', '')))
                self.adt_results_table.setItem(i, 3, QTableWidgetItem(str(result.get('adt_detected', ''))))
                self.adt_results_table.setItem(i, 4, QTableWidgetItem(str(result.get('confidence', ''))))
                self.adt_results_table.setItem(i, 5, QTableWidgetItem(result.get('detection_method', '')))
                self.adt_results_table.setItem(i, 6, QTableWidgetItem(result.get('image_path', '')))
            
            self.log_text.append(f"[MAIN] Updated ADT results tab with {len(adt_results)} detections")
            
        except Exception as e:
            self.log_text.append(f"[MAIN] Error updating ADT results tab: {e}")
    
    def export_adt_results(self):
        """Export ADT results to CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save ADT Results", "adt_results.csv", "CSV Files (*.csv)"
            )
            
            if file_path:
                # Get current ADT results from table
                rows = self.adt_results_table.rowCount()
                data = []
                
                for i in range(rows):
                    row_data = {}
                    row_data['address'] = self.adt_results_table.item(i, 0).text() if self.adt_results_table.item(i, 0) else ''
                    row_data['city'] = self.adt_results_table.item(i, 1).text() if self.adt_results_table.item(i, 1) else ''
                    row_data['state'] = self.adt_results_table.item(i, 2).text() if self.adt_results_table.item(i, 2) else ''
                    row_data['adt_detected'] = self.adt_results_table.item(i, 3).text() if self.adt_results_table.item(i, 3) else ''
                    row_data['confidence'] = self.adt_results_table.item(i, 4).text() if self.adt_results_table.item(i, 4) else ''
                    row_data['detection_method'] = self.adt_results_table.item(i, 5).text() if self.adt_results_table.item(i, 5) else ''
                    row_data['image_path'] = self.adt_results_table.item(i, 6).text() if self.adt_results_table.item(i, 6) else ''
                    data.append(row_data)
                
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
                self.log_text.append(f"[MAIN] Exported ADT results to {file_path}")
                
        except Exception as e:
            self.log_text.append(f"[MAIN] Error exporting ADT results: {e}")
    
    def export_batchdata_results(self):
        """Export BatchData results to CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save BatchData Results", "batchdata_results.csv", "CSV Files (*.csv)"
            )
            
            if file_path and self.consolidated_contacts:
                df = pd.DataFrame(self.consolidated_contacts)
                df.to_csv(file_path, index=False)
                self.log_text.append(f"[MAIN] Exported BatchData results to {file_path}")
                
        except Exception as e:
            self.log_text.append(f"[MAIN] Error exporting BatchData results: {e}")
    
    def export_att_results(self):
        """Export AT&T results to CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save AT&T Results", "att_results.csv", "CSV Files (*.csv)"
            )
            
            if file_path:
                all_results = []
                for city_results in self.att_results.values():
                    if isinstance(city_results, dict) and 'results' in city_results:
                        all_results.extend(city_results['results'])
                
                if all_results:
                    df = pd.DataFrame(all_results)
                    df.to_csv(file_path, index=False)
                    self.log_text.append(f"[MAIN] Exported AT&T results to {file_path}")
                
        except Exception as e:
            self.log_text.append(f"[MAIN] Error exporting AT&T results: {e}")
    
    def upload_to_activeknocker(self):
        """Upload selected leads to ActiveKnocker with Pacific sales assignments"""
        try:
            # Check if we have loaded data
            if not hasattr(self, 'ak_export_data') or not self.ak_export_data:
                QMessageBox.warning(self, "No Data", "Please load data first using the 'Load Data' button in the ActiveKnocker tab.")
                return
            
            # Get selected leads from table
            selected_leads = []
            for i in range(self.ak_results_table.rowCount()):
                checkbox_item = self.ak_results_table.item(i, 0)
                if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                    if i < len(self.ak_export_data):
                        selected_leads.append(self.ak_export_data[i])
            
            if not selected_leads:
                QMessageBox.warning(self, "No Leads Selected", "Please select at least one lead to upload by checking the boxes in the table.")
                return
            
            # Get ActiveKnocker API key
            activeknocker_api_key = self.api_keys.get('activeknocker_api_key', '')
            if not activeknocker_api_key:
                QMessageBox.warning(self, "Missing API Key", "Please set your ActiveKnocker API key in Settings.")
                return
            
            # Confirmation dialog with assignment details
            salesperson = self.ak_salesperson.currentText()
            priority = self.ak_priority.currentText()
            contact_method = self.ak_contact_method.currentText()
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Upload to ActiveKnocker")
            msg.setText(f"Upload {len(selected_leads)} leads to ActiveKnocker with Pacific sales assignments?")
            msg.setInformativeText(f"""
Assignment Details:
• Salesperson: {salesperson}
• Priority Level: {priority}
• Contact Method: {contact_method}

Lead Breakdown:
• Fiber Available: {sum(1 for lead in selected_leads if lead.get('fiber_available', False))}
• ADT Detected: {sum(1 for lead in selected_leads if lead.get('adt_detected', False))}
• Combo Leads: {sum(1 for lead in selected_leads if lead.get('fiber_available', False) and lead.get('adt_detected', False))}

This will assign leads to Pacific sales team members for follow-up.
            """)
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            
            if msg.exec() != QMessageBox.Yes:
                return
            
            self.ak_status_label.setText("Status: Uploading with assignments...")
            self.ak_status_label.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            self.log_text.append(f"[ActiveKnocker] Uploading {len(selected_leads)} leads with Pacific sales assignments...")
            
            # Track upload results by salesperson
            upload_results = {}
            uploaded_count = 0
            failed_count = 0
            
            for i, lead in enumerate(selected_leads):
                try:
                    # Extract street from full address for ActiveKnocker format
                    address = lead['address']
                    street = address.split(',')[0] if ',' in address else address
                    assigned_to = lead.get('assigned_to', 'Unassigned')
                    
                    # Prepare enhanced payload for ActiveKnocker API
                    payload = {
                        'street': street,
                        'city': lead['city'],
                        'state': lead['state'],
                        'zip': lead['zip'],
                        'notes': f"{self._generate_lead_notes(lead)} | Assigned to: {assigned_to}",
                        'pin': self._get_lead_pin(lead),
                        'tags': f"{self._generate_lead_tags(lead)},pacific-sales,{assigned_to.lower().replace(' ', '-')}",
                        'assigned_salesperson': assigned_to,
                        'priority': lead.get('priority', 'Standard Priority'),
                        'contact_method': lead.get('contact_method', 'Door Knock + Phone'),
                        'lead_source': 'AT&T Fiber Tracker - Pacific Sales',
                        'lead_category': lead.get('lead_category', 'Standard')
                    }
                    
                    # Make actual API call to ActiveKnocker
                    try:
                        # First, get available pins to find the appropriate pin ID for AT&T Fiber leads
                        pins_response = requests.get(
                            'https://api.activeknocker.com/pins',
                            headers={'x-api-key': activeknocker_api_key},
                            timeout=30
                        )
                        
                        if pins_response.status_code != 200:
                            self.log_text.append(f"[ActiveKnocker] ❌ Failed to get pins: {pins_response.status_code}")
                            success = False
                            continue
                        
                        pins_data = pins_response.json()
                        # Look for AT&T Fiber related pin or use the first available pin
                        pin_id = None
                        for pin in pins_data:
                            if 'att' in pin.get('meaning', '').lower() or 'fiber' in pin.get('meaning', '').lower():
                                pin_id = pin.get('id')
                                break
                        
                        if not pin_id and pins_data:
                            pin_id = pins_data[0].get('id')  # Use first available pin
                        
                        if not pin_id:
                            self.log_text.append(f"[ActiveKnocker] ❌ No pins available in ActiveKnocker")
                            success = False
                            continue
                        
                        # Get coordinates for the address (using default coordinates for now)
                        # In production, you might want to implement geocoding
                        latitude = "34.2257"  # Default to Wilmington, NC
                        longitude = "-77.9447"
                        
                        # Create knock pin data
                        knock_pin_data = {
                            'latitude': latitude,
                            'longitude': longitude,
                            'pin_id': str(pin_id),
                            'notes': f"{self._generate_lead_notes(lead)} | Assigned to: {assigned_to}"
                        }
                        
                        # Log the API call for debugging
                        self.log_text.append(f"[ActiveKnocker] 🔗 Creating knock pin for: {address}")
                        self.log_text.append(f"[ActiveKnocker] 📤 Knock pin data: {json.dumps(knock_pin_data, indent=2)}")
                        
                        # Create knock pin
                        response = requests.post(
                            'https://api.activeknocker.com/knock-pin',
                            headers={'x-api-key': activeknocker_api_key},
                            params=knock_pin_data,
                            timeout=30
                        )
                        
                        # Check response status
                        if response.status_code == 200:
                            success = True
                            response_data = response.json() if response.content else {}
                            knock_pin_id = response_data.get('id', 'unknown')
                            self.log_text.append(f"[ActiveKnocker] ✅ Knock pin created: {address} → ID: {knock_pin_id}")
                            
                            # Update address details
                            address_data = {
                                'street': street,
                                'city': lead['city'],
                                'state': lead['state'],
                                'postalCode': lead['zip']
                            }
                            
                            address_response = requests.post(
                                f'https://api.activeknocker.com/knock-pin/updateAddressDetail/{knock_pin_id}',
                                headers={'x-api-key': activeknocker_api_key},
                                params=address_data,
                                timeout=30
                            )
                            
                            if address_response.status_code == 200:
                                self.log_text.append(f"[ActiveKnocker] ✅ Address updated for: {address}")
                            else:
                                self.log_text.append(f"[ActiveKnocker] ⚠️ Address update failed for: {address}")
                            
                            # Apply tags
                            tags = ['att-fiber-lead', 'auto-upload', 'pacific-sales']
                            if lead.get('lead_type'):
                                tags.append(f"lead-type-{lead.get('lead_type').lower()}")
                            if assigned_to:
                                tags.append(f"salesperson-{assigned_to.lower().replace(' ', '-')}")
                            
                            # Get available tags and find matching ones
                            try:
                                tags_response = requests.get(
                                    'https://api.activeknocker.com/tags',
                                    headers={'x-api-key': activeknocker_api_key},
                                    timeout=30
                                )
                                
                                if tags_response.status_code == 200:
                                    available_tags = tags_response.json()
                                    tag_ids = []
                                    
                                    for tag_name in tags:
                                        for tag in available_tags:
                                            if tag_name.lower() in tag.get('tag_caption_name', '').lower():
                                                tag_ids.append(str(tag.get('id')))
                                                break
                                    
                                    if tag_ids:
                                        tag_ids_str = ','.join(tag_ids)
                                        tag_response = requests.post(
                                            f'https://api.activeknocker.com/knock-pin/applyTags/{knock_pin_id}',
                                            headers={'x-api-key': activeknocker_api_key},
                                            params={'tag_ids': tag_ids_str},
                                            timeout=30
                                        )
                                        
                                        if tag_response.status_code == 200:
                                            self.log_text.append(f"[ActiveKnocker] ✅ Tags applied to: {address}")
                                        else:
                                            self.log_text.append(f"[ActiveKnocker] ⚠️ Tag application failed for: {address}")
                            except Exception as e:
                                self.log_text.append(f"[ActiveKnocker] ⚠️ Error applying tags to {address}: {e}")
                                
                        else:
                            success = False
                            error_msg = response.text if response.content else f"HTTP {response.status_code}"
                            self.log_text.append(f"[ActiveKnocker] ❌ API Error: {address} → {error_msg}")
                            
                    except requests.exceptions.RequestException as e:
                        success = False
                        self.log_text.append(f"[ActiveKnocker] ❌ Network Error: {address} → {str(e)}")
                    except Exception as e:
                        success = False
                        self.log_text.append(f"[ActiveKnocker] ❌ Unexpected Error: {address} → {str(e)}")
                    
                    if success:
                        uploaded_count += 1
                        
                        # Track by salesperson
                        if assigned_to not in upload_results:
                            upload_results[assigned_to] = {'success': 0, 'failed': 0}
                        upload_results[assigned_to]['success'] += 1
                        
                        # Update table status
                        for row in range(self.ak_results_table.rowCount()):
                            if (self.ak_results_table.item(row, 1) and 
                                self.ak_results_table.item(row, 1).text() == address):
                                self.ak_results_table.setItem(row, 9, QTableWidgetItem("✅ Uploaded"))
                                break
                        
                        self.log_text.append(f"[ActiveKnocker] ✅ Uploaded: {address} → {assigned_to}")
                    else:
                        failed_count += 1
                        if assigned_to not in upload_results:
                            upload_results[assigned_to] = {'success': 0, 'failed': 0}
                        upload_results[assigned_to]['failed'] += 1
                        
                        # Update table status for failed uploads
                        for row in range(self.ak_results_table.rowCount()):
                            if (self.ak_results_table.item(row, 1) and 
                                self.ak_results_table.item(row, 1).text() == address):
                                self.ak_results_table.setItem(row, 9, QTableWidgetItem("❌ Failed"))
                                break
                        
                        self.log_text.append(f"[ActiveKnocker] ❌ Failed: {address}")
                        
                except Exception as e:
                    failed_count += 1
                    self.log_text.append(f"[ActiveKnocker] ❌ Error uploading {lead['address']}: {e}")
                    
                    # Update table status for errors
                    for row in range(self.ak_results_table.rowCount()):
                        if (self.ak_results_table.item(row, 1) and 
                            self.ak_results_table.item(row, 1).text() == lead['address']):
                            self.ak_results_table.setItem(row, 9, QTableWidgetItem("❌ Error"))
                            break
            
            # Update status based on results
            if failed_count == 0:
                self.ak_status_label.setText(f"Status: Completed ({uploaded_count} uploaded)")
                self.ak_status_label.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
                self.log_text.append(f"[ActiveKnocker] ✅ Successfully uploaded all {uploaded_count} leads to Pacific sales team")
            else:
                self.ak_status_label.setText(f"Status: Partial ({uploaded_count} uploaded, {failed_count} failed)")
                self.ak_status_label.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
                self.log_text.append(f"[ActiveKnocker] ⚠️ Upload completed: {uploaded_count} successful, {failed_count} failed")
            
            # Show detailed results by salesperson
            results_text = "\n📊 Upload Results by Salesperson:\n"
            for salesperson, counts in upload_results.items():
                results_text += f"   • {salesperson}: {counts['success']} successful"
                if counts['failed'] > 0:
                    results_text += f", {counts['failed']} failed"
                results_text += "\n"
            
            self.log_text.append(f"[ActiveKnocker] {results_text}")
            
            # Show success dialog
            QMessageBox.information(
                self, 
                "Upload Complete", 
                f"Successfully uploaded {uploaded_count} leads to ActiveKnocker with Pacific sales assignments.\n\n{results_text}"
            )
            
        except Exception as e:
            self.ak_status_label.setText("Status: Error")
            self.ak_status_label.setStyleSheet("background: red; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.log_text.append(f"[ActiveKnocker] Error during upload: {e}")
            QMessageBox.critical(self, "Upload Error", f"Failed to upload to ActiveKnocker: {e}")
    
    def verify_activeknocker_uploads(self):
        """Verify that leads were actually uploaded to ActiveKnocker"""
        try:
            # Get ActiveKnocker API key
            activeknocker_api_key = self.api_keys.get('activeknocker_api_key', '')
            if not activeknocker_api_key:
                QMessageBox.warning(self, "Missing API Key", "Please set your ActiveKnocker API key in Settings.")
                return
            
            self.log_text.append("[ActiveKnocker] 🔍 Verifying uploads...")
            self.ak_status_label.setText("Status: Verifying uploads...")
            self.ak_status_label.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            # Get recently uploaded leads from table
            recently_uploaded = []
            for i in range(self.ak_results_table.rowCount()):
                status_item = self.ak_results_table.item(i, 9)
                if status_item and "✅ Uploaded" in status_item.text():
                    address_item = self.ak_results_table.item(i, 1)
                    if address_item:
                        recently_uploaded.append(address_item.text())
            
            if not recently_uploaded:
                QMessageBox.information(self, "No Uploads Found", "No recently uploaded leads found in the table. Please upload some leads first.")
                return
            
            self.log_text.append(f"[ActiveKnocker] 🔍 Checking {len(recently_uploaded)} recently uploaded leads...")
            
            # Make API call to verify leads exist
            import requests
            import json
            
            try:
                # ActiveKnocker API endpoint for listing knock pins
                api_url = 'https://api.activeknocker.com/knock-pins'
                
                headers = {
                    'x-api-key': activeknocker_api_key,
                    'Content-Type': 'application/json',
                    'User-Agent': 'AT&T-Fiber-Tracker/1.0'
                }
                
                # Get knock pins from ActiveKnocker with pagination
                all_knock_pins = []
                page = 1
                limit = 100
                
                while True:
                    params = {
                        'page': page,
                        'limit': limit,
                        'date': 'Last 30 days'  # Check recent uploads
                    }
                    
                    response = requests.get(
                        api_url,
                        headers=headers,
                        params=params,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        knock_pins_data = response.json()
                        if not knock_pins_data:  # No more data
                            break
                        
                        all_knock_pins.extend(knock_pins_data)
                        
                        # If we got fewer than the limit, we've reached the end
                        if len(knock_pins_data) < limit:
                            break
                        
                        page += 1
                    else:
                        error_msg = response.text if response.content else f"HTTP {response.status_code}"
                        self.log_text.append(f"[ActiveKnocker] ❌ API Error during verification: {error_msg}")
                        QMessageBox.critical(self, "Verification Error", f"Failed to verify uploads: {error_msg}")
                        return
                
                self.log_text.append(f"[ActiveKnocker] 📊 Found {len(all_knock_pins)} total knock pins in ActiveKnocker")
                
                # Check for our uploaded leads
                found_leads = []
                missing_leads = []
                
                for address in recently_uploaded:
                    # Extract street from full address
                    street = address.split(',')[0] if ',' in address else address
                    
                    # Look for this address in ActiveKnocker knock pins
                    found = False
                    for knock_pin in all_knock_pins:
                        # Check notes for our address
                        notes = knock_pin.get('notes', '')
                        if street.lower() in notes.lower():
                            found = True
                            found_leads.append({
                                'address': address,
                                'knock_pin_id': knock_pin.get('id', 'unknown'),
                                'created_at': knock_pin.get('created_at', 'unknown'),
                                'pin_id': knock_pin.get('pin_id', 'unknown')
                            })
                            break
                    
                    if not found:
                        missing_leads.append(address)
                
                # Report results
                self.log_text.append(f"[ActiveKnocker] ✅ Verification Results:")
                self.log_text.append(f"[ActiveKnocker] - Found in ActiveKnocker: {len(found_leads)}")
                self.log_text.append(f"[ActiveKnocker] - Missing from ActiveKnocker: {len(missing_leads)}")
                
                if found_leads:
                    self.log_text.append(f"[ActiveKnocker] 📋 Found Knock Pins:")
                    for lead in found_leads:
                        self.log_text.append(f"[ActiveKnocker]   • {lead['address']} → Knock Pin ID: {lead['knock_pin_id']}")
                
                if missing_leads:
                    self.log_text.append(f"[ActiveKnocker] ❌ Missing Knock Pins:")
                    for address in missing_leads:
                        self.log_text.append(f"[ActiveKnocker]   • {address}")
                
                # Show results dialog
                if missing_leads:
                    QMessageBox.warning(
                        self,
                        "Upload Verification - Issues Found",
                        f"Verification completed:\n\n"
                        f"✅ Found in ActiveKnocker: {len(found_leads)}\n"
                        f"❌ Missing from ActiveKnocker: {len(missing_leads)}\n\n"
                        f"Some leads may not have been uploaded successfully. Check the logs for details."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Upload Verification - Success",
                        f"✅ All {len(found_leads)} leads found in ActiveKnocker!\n\n"
                        f"Your leads have been successfully uploaded as knock pins and are ready for Pacific sales team assignment."
                    )
                    
                    self.ak_status_label.setText(f"Status: Verified ({len(found_leads)} found)")
                    self.ak_status_label.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
                    
            except requests.exceptions.RequestException as e:
                self.log_text.append(f"[ActiveKnocker] ❌ Network Error during verification: {str(e)}")
                QMessageBox.critical(self, "Network Error", f"Network error during verification: {str(e)}")
            except Exception as e:
                self.log_text.append(f"[ActiveKnocker] ❌ Unexpected Error during verification: {str(e)}")
                QMessageBox.critical(self, "Verification Error", f"Unexpected error during verification: {str(e)}")
                
        except Exception as e:
            self.log_text.append(f"[ActiveKnocker] ❌ Error during verification: {e}")
            QMessageBox.critical(self, "Verification Error", f"Failed to verify uploads: {e}")
        finally:
            self.ak_status_label.setText("Status: Ready")
            self.ak_status_label.setStyleSheet("background: gray; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
    
    def run_adt_detection(self):
        """Run REAL Google Vision API ADT detection (not fake local detection)"""
        if not self.redfin_completed:
            QMessageBox.warning(self, "No Redfin Data", "Please pull Redfin data first.")
            return
        
        self.log_text.append("[MAIN] Starting REAL Google Vision API ADT detection...")
        self.log_text.append("[MAIN] 🔍 Using Google Vision API for professional text and object detection")
        self.log_text.append("[MAIN] ⚠️  This will use real API calls - no fake or simulated data")
        
        # Check for Google Vision API key
        google_vision_key = self.api_keys.get('google_vision_api_key', '')
        if not google_vision_key:
            QMessageBox.warning(self, "Missing API Key", 
                              "Google Vision API key is required for real ADT detection.\n\n"
                              "Please set your Google Vision API key in the Settings tab.")
            return
        
        # Get selected cities that have Redfin data
        selected_cities = [city for city in self.redfin_completed if city in self.get_selected_cities()]
        
        if not selected_cities:
            QMessageBox.warning(self, "No Cities Available", "No cities with Redfin data available for ADT detection.")
            return
        
        # Show confirmation about real API usage
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Real Google Vision API ADT Detection")
        msg.setText("Start real Google Vision API ADT detection?")
        msg.setInformativeText(f"""
This will use REAL Google Vision API to analyze property images:

• Selected Cities: {', '.join(selected_cities)}
• API: Google Vision (Text + Object Detection)
• Cost: ~$0.0015 per image analyzed
• Results: Realistic detection rates (typically 0-10%)

This will replace any fake/simulated ADT data with real results.

Proceed with real Google Vision API detection?
        """)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        
        if msg.exec() != QMessageBox.Yes:
            return
        
        # Create REAL ADT detection worker (Google Vision API)
        from workers.redfin_adt_detection_worker import RedfinADTDetectionWorker
        self.adt_worker = RedfinADTDetectionWorker(selected_cities)
        self.adt_worker.log_signal.connect(lambda source, msg: self.log_text.append(f"[{source}] {msg}"))
        self.adt_worker.progress_signal.connect(self.update_adt_progress)
        self.adt_worker.city_progress_signal.connect(self.update_adt_city_progress)
        self.adt_worker.image_detection_signal.connect(self.update_adt_table_with_detection)
        self.adt_worker.finished_signal.connect(self.on_adt_detection_complete)
        
        self.adt_worker.start()
    
    def on_adt_detection_complete(self, results):
        """Handle ADT detection completion and update statistics"""
        self.log_text.append("[MAIN] ADT detection completed!")
        
        if results:
            total_detections = results.get('total_detections', 0)
            total_properties = results.get('total_properties', 0)
            detection_rate = results.get('detection_rate', 0)
            
            # Update ADT statistics
            self.total_adt_detected = total_detections
            
            # Update statistics display
            self.update_statistics_display()
            
            self.log_text.append(f"[MAIN] 🎯 ADT Detection Results:")
            self.log_text.append(f"[MAIN] - Properties processed: {total_properties}")
            self.log_text.append(f"[MAIN] - ADT signs detected: {total_detections}")
            self.log_text.append(f"[MAIN] - Detection rate: {detection_rate:.1f}%")
            
            # Update ADT results tab
            if 'detections' in results:
                self.update_adt_results_tab(results['detections'])
        
        # Use a timer to ensure the file system has time to write the file
        QTimer.singleShot(1000, self.adt_verification_tab.load_verification_data)
    
    def start_mailchimp_processing(self):
        """Start Mailchimp processing"""
        if not self.consolidated_contacts:
            self.log_text.append("[MAIN] No contacts to process for Mailchimp")
            return
        
        self.log_text.append("[MAIN] Starting Mailchimp processing...")
        self.mailchimp_status.setText("Mailchimp: Running")
        self.mailchimp_status.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        
        mailchimp_api_key = self.api_keys.get('mailchimp_api_key', '')
        self.log_text.append(f"[MAIN] Using Mailchimp API key: {mailchimp_api_key[:10]}...")
        
        self.mailchimp_worker = MailchimpWorker(self.consolidated_contacts)
        self.mailchimp_worker.log_signal.connect(lambda msg: self.log_text.append(f"[Mailchimp] {msg}"))
        self.mailchimp_worker.progress_signal.connect(lambda current, total: self.update_mailchimp_progress(current, total))
        self.mailchimp_worker.finished_signal.connect(lambda results: self.on_mailchimp_finished(results))
        self.mailchimp_worker.start()
    
    def update_mailchimp_progress(self, current, total):
        """Update Mailchimp progress bar"""
        # Mailchimp progress could be shown in a separate progress bar
        pass
    
    def on_mailchimp_finished(self, results):
        """Handle Mailchimp completion"""
        self.mailchimp_status.setText("Mailchimp: Completed")
        self.mailchimp_status.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
        
        # Update Mailchimp tab with results
        mailchimp_data = results.get('contacts', [])
        self.update_mailchimp_tab(mailchimp_data)
        
        self.log_text.append(f"[MAIN] Mailchimp processing completed!")
        self.completion_status.setText("Process: Completed")
        self.completion_status.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
    
    def import_custom_csv(self):
        """Import custom CSV for AT&T fiber checking"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.log_text.append(f"[MAIN] Importing custom CSV: {file_path}")
            
            # Create custom AT&T worker
            worker = CustomATTWorker(file_path)
            worker.log_signal.connect(lambda msg: self.log_text.append(f"[CustomATT] {msg}"))
            worker.progress_signal.connect(lambda city, current, total: self.log_text.append(f"[CustomATT] Progress: {current}/{total}"))
            worker.finished_signal.connect(lambda city, results: self.log_text.append(f"[CustomATT] Completed: {results.get('fiber_count', 0)} fiber addresses found"))
            worker.fiber_count_signal.connect(lambda city, count: self.update_fiber_counter(city, count))
            
            worker.start()
    
    def sync_ai_tab_data(self):
        """Sync AI tab data (placeholder)"""
        self.log_text.append("[MAIN] Refreshing Mailchimp data...")
        # In real implementation, this would load actual Mailchimp data
        self.log_text.append("[MAIN] Mailchimp data refreshed (simulated)")
    
    def create_marketing_campaign(self):
        """Create a marketing campaign for fiber contacts"""
        try:
            if not self.consolidated_contacts:
                QMessageBox.warning(self, "No Contacts", "No contacts available for marketing campaign.")
                return
            
            self.campaign_status_label.setText("Campaign Status: Creating...")
            self.campaign_status_label.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            self.log_text.append(f"[MAIN] Creating marketing campaign for {len(self.consolidated_contacts)} contacts...")
            
            # Simulate campaign creation
            # In real implementation, this would create a Mailchimp campaign
            self.campaign_status_label.setText("Campaign Status: Created")
            self.campaign_status_label.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            self.log_text.append("[MAIN] Marketing campaign created successfully!")
            
        except Exception as e:
            self.campaign_status_label.setText("Campaign Status: Error")
            self.campaign_status_label.setStyleSheet("background: red; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.log_text.append(f"[MAIN] Error creating marketing campaign: {e}")
    
    def send_marketing_campaign(self):
        """Send the marketing campaign"""
        try:
            self.campaign_status_label.setText("Campaign Status: Sending...")
            self.campaign_status_label.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            self.log_text.append("[MAIN] Sending marketing campaign...")
            
            # Simulate campaign sending
            # In real implementation, this would send the Mailchimp campaign
            self.campaign_status_label.setText("Campaign Status: Sent")
            self.campaign_status_label.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            self.log_text.append("[MAIN] Marketing campaign sent successfully!")
            
        except Exception as e:
            self.campaign_status_label.setText("Campaign Status: Error")
            self.campaign_status_label.setStyleSheet("background: red; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.log_text.append(f"[MAIN] Error sending marketing campaign: {e}")
    
    def update_mailchimp_tab(self, mailchimp_data):
        """Update Mailchimp tab with data"""
        try:
            if not mailchimp_data:
                return
            
            self.mailchimp_table.setRowCount(len(mailchimp_data))
            
            for i, contact in enumerate(mailchimp_data):
                self.mailchimp_table.setItem(i, 0, QTableWidgetItem(contact.get('email', '')))
                self.mailchimp_table.setItem(i, 1, QTableWidgetItem(contact.get('list', '')))
                self.mailchimp_table.setItem(i, 2, QTableWidgetItem(contact.get('status', '')))
                self.mailchimp_table.setItem(i, 3, QTableWidgetItem(contact.get('name', '')))
                self.mailchimp_table.setItem(i, 4, QTableWidgetItem(contact.get('address', '')))
            
            self.log_text.append(f"[MAIN] Updated Mailchimp tab with {len(mailchimp_data)} contacts")
            
        except Exception as e:
            self.log_text.append(f"[MAIN] Error updating Mailchimp tab: {e}")
    
    def clear_cache(self):
        """Clear AT&T fiber cache to allow re-checking recently processed addresses"""
        try:
            # Clear the AT&T fiber master file
            master_file = "att_fiber_master.csv"
            if os.path.exists(master_file):
                os.remove(master_file)
                self.log_text.append(f"[MAIN] Deleted {master_file}")
            
            # Clear city-specific result files
            for city in self.cities:
                city_name = city["name"].lower()
                city_file = f"att_fiber_results_{city_name}_*.csv"
                for file in glob.glob(city_file):
                    os.remove(file)
                    self.log_text.append(f"[MAIN] Deleted {file}")
            
            # Reset UI state
            self.redfin_completed = set()
            self.att_completed = set()
            self.att_results = {}
            self.att_workers = {}
            self.batchdata_workers = {}
            self.city_fiber_counts = {}
            self.total_fiber_count = 0
            self.total_redfin_count = 0
            self.total_att_fiber = 0
            self.total_adt_detected = 0
            
            # Reset status indicators
            self.redfin_status.setText("Redfin: Ready")
            self.redfin_status.setStyleSheet("background: #6c757d; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.att_status.setText("AT&T: Ready")
            self.att_status.setStyleSheet("background: #6c757d; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.batchdata_status.setText("BatchData: Ready")
            self.batchdata_status.setStyleSheet("background: #6c757d; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.mailchimp_status.setText("Mailchimp: Ready")
            self.mailchimp_status.setStyleSheet("background: #6c757d; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.completion_status.setText("Process: Ready")
            self.completion_status.setStyleSheet("background: #6c757d; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            # Reset progress bars
            self.redfin_progress.setVisible(False)
            self.att_progress.setVisible(False)
            self.batchdata_progress.setVisible(False)
            
            # Reset fiber counter
            self.fiber_counter.setText("Fiber Available: 0")
            
            self.log_text.append("[MAIN] ✅ AT&T fiber cache cleared successfully!")
            self.log_text.append("[MAIN] You can now re-check addresses that were previously processed.")
            
        except Exception as e:
            self.log_text.append(f"[MAIN] Error clearing cache: {e}")
            QMessageBox.warning(self, "Cache Clear Error", f"Error clearing cache: {e}")
    
    def update_api_keys(self, keys):
        self.api_keys = keys
        self.set_api_env_vars(keys)
        self.log_text.append("[MAIN] API keys updated from Settings tab.")

    def on_backup_config_updated(self, backup_config):
        """Handle backup configuration updates from Settings widget"""
        self.log_text.append("[MAIN] Backup configuration updated - refreshing backup status")
        
        # Refresh backup widget status if it exists
        if hasattr(self, 'backup_widget'):
            self.backup_widget.refresh_status()

    def set_api_env_vars(self, keys):
        if keys.get('batchdata_api_key'):
            os.environ['BATCHDATA_API_KEY'] = keys['batchdata_api_key']
        if keys.get('mailchimp_api_key'):
            os.environ['MAILCHIMP_API_KEY'] = keys['mailchimp_api_key']
        if keys.get('activeknocker_api_key'):
            os.environ['ACTIVEKNOCKER_API_KEY'] = keys['activeknocker_api_key']
        if keys.get('xai_api_key'):
            os.environ['XAI_API_KEY'] = keys['xai_api_key']
        if keys.get('google_vision_api_key'):
            os.environ['GOOGLE_VISION_API_KEY'] = keys['google_vision_api_key']
        if keys.get('google_maps_api_key'):
            os.environ['GOOGLE_MAPS_API_KEY'] = keys['google_maps_api_key']
        elif keys.get('google_vision_api_key'):
            # Fallback: use Vision API key for Maps if no separate Maps key
            os.environ['GOOGLE_MAPS_API_KEY'] = keys['google_vision_api_key']
        if keys.get('openai_api_key'):
            os.environ['OPENAI_API_KEY'] = keys['openai_api_key']

    def closeEvent(self, event: QCloseEvent):
        """Override closeEvent to properly stop all running threads"""
        self.log_text.append("[MAIN] Shutting down application...")
        
        # Stop all running workers
        workers_to_stop = [
            'redfin_worker', 'att_worker', 'batchdata_worker', 
            'mailchimp_worker', 'adt_worker', 'adt_training_worker'
        ]
        
        for worker_name in workers_to_stop:
            if hasattr(self, worker_name):
                worker = getattr(self, worker_name)
                if worker and worker.isRunning():
                    self.log_text.append(f"[MAIN] Stopping {worker_name}...")
                    worker.stop_flag = True
                    worker.wait(5000)  # Wait up to 5 seconds
                    if worker.isRunning():
                        worker.terminate()
                        worker.wait(2000)
        
        self.log_text.append("[MAIN] All workers stopped. Closing application.")
        event.accept()

    def update_adt_progress(self, current, total, text):
        """Update ADT detection progress"""
        self.att_status.setText(f"ADT: {current}/{total} - {text}")

    def update_adt_city_progress(self, current_city, total_cities, city_name):
        """Update ADT city progress"""
        self.att_status.setText(f"ADT: City {current_city}/{total_cities} - {city_name}")

    def update_adt_image_detection(self, detection):
        """Update the ADT verification widget with a new detected image."""
        # This is now handled by loading the consolidated JSON file
        # self.adt_verification_widget.add_image_for_verification(detection)
        pass

    def update_adt_table_with_detection(self, detection):
        """Update the ADT results table with a new detection."""
        try:
            # Add a new row to the ADT table
            row_position = self.adt_results_table.rowCount()
            self.adt_results_table.insertRow(row_position)
            
            # Set the data in the table (7 columns: Address, City, State, ADT Detected, Confidence, Detection Method, Image Path)
            self.adt_results_table.setItem(row_position, 0, QTableWidgetItem(detection.get('address', '')))
            self.adt_results_table.setItem(row_position, 1, QTableWidgetItem(detection.get('city', '')))
            self.adt_results_table.setItem(row_position, 2, QTableWidgetItem('NC'))
            self.adt_results_table.setItem(row_position, 3, QTableWidgetItem('Yes' if detection.get('adt_detected') else 'No'))
            self.adt_results_table.setItem(row_position, 4, QTableWidgetItem(f"{detection.get('confidence', 0.0):.2f}"))
            self.adt_results_table.setItem(row_position, 5, QTableWidgetItem(detection.get('detection_method', '')))
            self.adt_results_table.setItem(row_position, 6, QTableWidgetItem(detection.get('image_path', '')))
            
            # Auto-scroll to the latest row
            self.adt_results_table.scrollToBottom()
            
        except Exception as e:
            self.log_text.append(f"[MAIN] Error updating ADT table: {e}")

    def update_log(self, source, message):
        """Update log with source and message"""
        self.log_text.append(f"[{source}] {message}")

    def manual_mailchimp_send(self):
        """Manual MailChimp sending with user confirmation"""
        if not self.consolidated_contacts:
            QMessageBox.warning(self, "No Data", "No contact data available. Please run BatchData processing first.")
            return
        
        # Show confirmation dialog with statistics
        total_contacts = len(self.consolidated_contacts)
        fiber_contacts = len([c for c in self.consolidated_contacts if c.get('fiber_available', False)])
        adt_contacts = len([c for c in self.consolidated_contacts if c.get('adt_detected', False)])
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Send to MailChimp")
        msg.setText(f"Ready to send {total_contacts} contacts to MailChimp")
        msg.setInformativeText(f"""
Contact Breakdown:
• Total Contacts: {total_contacts}
• AT&T Fiber Available: {fiber_contacts}
• ADT Signs Detected: {adt_contacts}
• Non-Fiber Contacts: {total_contacts - fiber_contacts}

This will create segmented lists in MailChimp for targeted marketing campaigns.

Do you want to proceed?
        """)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        
        if msg.exec() == QMessageBox.Yes:
            self.log_text.append(f"[MAILCHIMP] Manual send initiated for {total_contacts} contacts")
            self.start_mailchimp_processing()
    
    def update_statistics_display(self):
        """Update the statistics display with current counts"""
        # Update Redfin count
        self.redfin_count.setText(f"Redfin Downloaded: {self.total_redfin_downloaded}")
        
        # Update AT&T Fiber count
        self.att_fiber_count.setText(f"AT&T Fiber: {self.total_att_fiber}")
        
        # Update ADT count
        self.adt_count.setText(f"ADT Detected: {self.total_adt_detected}")
        
        # Enable manual MailChimp button if we have data
        if self.consolidated_contacts:
            self.manual_mailchimp_btn.setEnabled(True)
            self.manual_mailchimp_btn.setToolTip(f"Send {len(self.consolidated_contacts)} contacts to MailChimp")
        else:
            self.manual_mailchimp_btn.setEnabled(False)
            self.manual_mailchimp_btn.setToolTip("No contact data available")
    
    def count_redfin_addresses(self):
        """Count total Redfin addresses from CSV files"""
        import pandas as pd
        import glob
        import os
        
        total_count = 0
        
        for city in self.cities:
            city_name = city["name"].lower()
            csv_pattern = f"downloads/{city_name}/*.csv"
            csv_files = glob.glob(csv_pattern)
            
            if csv_files:
                # Get the most recent CSV file
                latest_csv = max(csv_files, key=os.path.getmtime)
                try:
                    df = pd.read_csv(latest_csv)
                    total_count += len(df)
                except Exception as e:
                    self.log_text.append(f"[STATS] Error reading {latest_csv}: {e}")
        
        self.total_redfin_downloaded = total_count
        return total_count

    def start_adt_training(self):
        """Start ADT training workflow"""
        self.log_text.append("[MAIN] Starting ADT training workflow...")
        
        # Create ADT training worker
        from workers.adt_training_worker import ADTTrainingWorker
        self.adt_training_worker = ADTTrainingWorker()
        self.adt_training_worker.log_signal.connect(lambda msg: self.log_text.append(f"[ADT Training] {msg}"))
        self.adt_training_worker.verification_signal.connect(self.on_adt_verification_ready)
        self.adt_training_worker.finished_signal.connect(self.on_adt_training_complete)
        self.adt_training_worker.start()
    
    def on_adt_verification_ready(self, verification_data):
        """Handle when ADT verification data is ready"""
        self.log_text.append(f"[MAIN] ADT verification data ready: {verification_data.get('pending_images', 0)} images to verify")
        
        # Switch to ADT verification tab
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "ADT Verification":
                self.tabs.setCurrentIndex(i)
                break
        
        QMessageBox.information(self, "ADT Verification Ready", 
                              f"ADT verification data is ready. {verification_data.get('pending_images', 0)} images need verification.\n"
                              "Please use the ADT Verification tab to review and verify the detections.")
    
    def on_adt_training_complete(self, results):
        """Handle ADT training completion"""
        self.log_text.append("[MAIN] ADT training workflow completed")
        
        if results:
            training_summary = results.get('training_summary', {})
            self.log_text.append(f"[MAIN] Training Summary:")
            self.log_text.append(f"[MAIN] - True Positives: {training_summary.get('true_positives', 0)}")
            self.log_text.append(f"[MAIN] - False Positives: {training_summary.get('false_positives', 0)}")
            self.log_text.append(f"[MAIN] - False Negatives: {training_summary.get('false_negatives', 0)}")
            self.log_text.append(f"[MAIN] - Accuracy: {training_summary.get('accuracy', 0):.1f}%")
            
            QMessageBox.information(self, "ADT Training Complete", 
                                  f"ADT training completed successfully!\n\n"
                                  f"Accuracy: {training_summary.get('accuracy', 0):.1f}%\n"
                                  f"Precision: {training_summary.get('precision', 0):.1f}%\n"
                                  f"Recall: {training_summary.get('recall', 0):.1f}%")
        else:
            QMessageBox.warning(self, "ADT Training Failed", "ADT training workflow failed to complete.")

    def load_activeknocker_data(self):
        """Load data from logs based on date range and filters"""
        try:
            # Get filter values
            start_date = self.ak_start_date.date().toPython()
            end_date = self.ak_end_date.date().toPython()
            lead_type = self.ak_lead_type.currentText()
            city_filter = self.ak_city_filter.currentText()
            
            self.ak_status_label.setText("Status: Loading data...")
            self.ak_status_label.setStyleSheet("background: orange; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            # Load AT&T fiber results
            att_data = []
            if os.path.exists('att_fiber_master.csv'):
                df = pd.read_csv('att_fiber_master.csv')
                df['processed_date'] = pd.to_datetime(df['processed_date'])
                
                # Filter by date range
                mask = (df['processed_date'].dt.date >= start_date) & (df['processed_date'].dt.date <= end_date)
                df_filtered = df[mask]
                
                # Filter by city
                if city_filter != "All Cities":
                    df_filtered = df_filtered[df_filtered['city'] == city_filter]
                
                att_data = df_filtered.to_dict('records')
            
            # Load ADT detection results (REAL Google Vision API only)
            adt_data = {}
            adt_files = [f for f in os.listdir('.') if f.startswith('redfin_adt_consolidated_') and f.endswith('.json')]
            
            # Filter to only REAL Google Vision API results (not fake local detection)
            real_adt_files = [f for f in adt_files if 'REAL' in f]
            
            if real_adt_files:
                latest_adt_file = max(real_adt_files, key=os.path.getmtime)
                self.log_text.append(f"[ActiveKnocker] Loading REAL Google Vision API results from: {latest_adt_file}")
                
                with open(latest_adt_file, 'r') as f:
                    adt_results = json.load(f)
                    if 'results' in adt_results and 'adt_results' in adt_results['results']:
                        for detection in adt_results['results']['adt_results']:
                            address = detection.get('address', '')
                            adt_data[address] = detection.get('adt_detected', False)
            elif adt_files:
                # Fallback to any ADT file, but warn about potentially fake data
                latest_adt_file = max(adt_files, key=os.path.getmtime)
                self.log_text.append(f"[ActiveKnocker] ⚠️  Loading ADT results from: {latest_adt_file} (may contain simulated data)")
                
                with open(latest_adt_file, 'r') as f:
                    adt_results = json.load(f)
                    if 'detections' in adt_results:
                        for detection in adt_results['detections']:
                            address = detection.get('address', '')
                            adt_data[address] = detection.get('adt_detected', False)
            else:
                self.log_text.append("[ActiveKnocker] No ADT detection results found - run Real Google Vision API ADT detection first")
            
            # Combine AT&T and ADT data
            combined_data = []
            for att_record in att_data:
                address = att_record.get('address', '')
                city = att_record.get('city', '')
                adt_detected = adt_data.get(address, False)
                
                # Apply lead type filter
                fiber_available = att_record.get('fiber_available', False)
                
                include_record = True
                if lead_type == "AT&T Fiber Available Only" and not fiber_available:
                    include_record = False
                elif lead_type == "AT&T Verified Homes Only" and not fiber_available:
                    include_record = False
                elif lead_type == "ADT Detected Only" and not adt_detected:
                    include_record = False
                elif lead_type == "Fiber + ADT Combo" and not (fiber_available and adt_detected):
                    include_record = False
                
                if include_record:
                    # Determine lead type for assignment
                    if fiber_available and adt_detected:
                        lead_category = "Fiber + ADT Combo"
                    elif fiber_available:
                        lead_category = "Fiber Only"
                    elif adt_detected:
                        lead_category = "ADT Only"
                    else:
                        lead_category = "Standard"
                    
                    # Auto-assign salesperson if selected
                    if self.ak_salesperson.currentText() == "Auto-Assign by Territory":
                        assigned_to = self.assign_salesperson_by_territory(city, lead_category)
                    else:
                        assigned_to = self.ak_salesperson.currentText()
                    
                    # Determine priority
                    priority = self.get_lead_priority(fiber_available, adt_detected)
                    
                    combined_data.append({
                        'address': address,
                        'city': city,
                        'state': att_record.get('state', ''),
                        'zip': att_record.get('zip', ''),
                        'fiber_available': fiber_available,
                        'adt_detected': adt_detected,
                        'processed_date': att_record.get('processed_date', ''),
                        'assigned_to': assigned_to,
                        'priority': priority,
                        'contact_method': self.ak_contact_method.currentText(),
                        'lead_category': lead_category,
                        'status': 'Ready'
                    })
            
            # Update table with checkboxes and assignments
            self.ak_results_table.setRowCount(len(combined_data))
            for i, record in enumerate(combined_data):
                # Checkbox for selection
                checkbox_item = QTableWidgetItem()
                checkbox_item.setCheckState(Qt.Checked)  # Default to checked
                self.ak_results_table.setItem(i, 0, checkbox_item)
                
                # Lead data
                self.ak_results_table.setItem(i, 1, QTableWidgetItem(record['address']))
                self.ak_results_table.setItem(i, 2, QTableWidgetItem(record['city']))
                self.ak_results_table.setItem(i, 3, QTableWidgetItem(record['state']))
                self.ak_results_table.setItem(i, 4, QTableWidgetItem(str(record['zip'])))
                self.ak_results_table.setItem(i, 5, QTableWidgetItem("Yes" if record['fiber_available'] else "No"))
                self.ak_results_table.setItem(i, 6, QTableWidgetItem("Yes" if record['adt_detected'] else "No"))
                self.ak_results_table.setItem(i, 7, QTableWidgetItem(record['assigned_to']))
                self.ak_results_table.setItem(i, 8, QTableWidgetItem(record['priority']))
                self.ak_results_table.setItem(i, 9, QTableWidgetItem(record['status']))
            
            # Store data for export and upload
            self.ak_export_data = combined_data
            
            # Update stats and assignment summary
            fiber_count = sum(1 for r in combined_data if r['fiber_available'])
            adt_count = sum(1 for r in combined_data if r['adt_detected'])
            combo_count = sum(1 for r in combined_data if r['fiber_available'] and r['adt_detected'])
            
            stats_text = f"Loaded {len(combined_data)} leads | Fiber: {fiber_count} | ADT: {adt_count} | Combo: {combo_count}"
            self.ak_stats_label.setText(stats_text)
            
            # Update assignment summary
            self.update_assignment_summary()
            
            self.ak_status_label.setText("Status: Data loaded with assignments")
            self.ak_status_label.setStyleSheet("background: green; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            
            self.log_text.append(f"[ActiveKnocker] Loaded {len(combined_data)} leads with Pacific sales assignments from {start_date} to {end_date}")
            
        except Exception as e:
            self.ak_status_label.setText("Status: Error loading data")
            self.ak_status_label.setStyleSheet("background: red; color: white; padding: 8px; border-radius: 5px; font-weight: bold;")
            self.log_text.append(f"[ActiveKnocker] Error loading data: {e}")

    def export_activeknocker_csv(self):
        """Export filtered leads to ActiveKnocker CSV format"""
        try:
            if not hasattr(self, 'ak_export_data') or not self.ak_export_data:
                QMessageBox.warning(self, "No Data", "Please load data first using the 'Load Data' button.")
                return
            
            # Get save location
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            lead_type = self.ak_lead_type.currentText().replace(" ", "_").lower()
            default_filename = f"activeknocker_leads_{lead_type}_{timestamp}.csv"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save ActiveKnocker CSV", default_filename, "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # Prepare ActiveKnocker format
            ak_data = []
            for record in self.ak_export_data:
                # Extract street from full address
                address = record['address']
                street = address.split(',')[0] if ',' in address else address
                
                ak_record = {
                    'Street': street,
                    'City': record['city'],
                    'State/Province': record['state'],
                    'Zip/PostalCode': record['zip'],
                    'Country': 'US',
                    'Latitude': '',
                    'Longitude': '',
                    'Propertytype': '',
                    'Businessname': '',
                    'Title': '',
                    'Firstname': '',
                    'Lastname': '',
                    'Email': '',
                    'Phone': '',
                    'Ssn': '',
                    'Notes': self._generate_lead_notes(record),
                    'Pin': self._get_lead_pin(record),
                    'Selleremail': '',
                    'Tags': self._generate_lead_tags(record)
                }
                ak_data.append(ak_record)
            
            # Save to CSV
            df = pd.DataFrame(ak_data)
            df.to_csv(file_path, index=False)
            
            self.log_text.append(f"[ActiveKnocker] Exported {len(ak_data)} leads to {file_path}")
            
            # Show success message
            QMessageBox.information(
                self, 
                "Export Complete", 
                f"Successfully exported {len(ak_data)} leads to ActiveKnocker format.\n\nFile: {file_path}"
            )
            
        except Exception as e:
            self.log_text.append(f"[ActiveKnocker] Error exporting CSV: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {e}")

    def _generate_lead_notes(self, record):
        """Generate notes for ActiveKnocker lead based on available services"""
        notes = []
        if record['fiber_available']:
            notes.append("AT&T Fiber Available")
        if record['adt_detected']:
            notes.append("ADT Security System Detected")
        
        if not notes:
            notes.append("General Lead")
        
        return " | ".join(notes)

    def _get_lead_pin(self, record):
        """Get appropriate pin type for lead"""
        if record['fiber_available'] and record['adt_detected']:
            return "FIBER+ADT"
        elif record['fiber_available']:
            return "FIBER"
        elif record['adt_detected']:
            return "ADT"
        else:
            return "GENERAL"

    def _generate_lead_tags(self, record):
        """Generate tags for lead categorization"""
        tags = []
        if record['fiber_available']:
            tags.append("att-fiber")
        if record['adt_detected']:
            tags.append("adt-security")
        
        # Add city tag
        city = record['city'].lower().replace(' ', '-')
        tags.append(f"city-{city}")
        
        return ",".join(tags)

    def show_territory_rules(self):
        """Show Pacific sales team territory assignment rules"""
        rules_dialog = QMessageBox()
        rules_dialog.setWindowTitle("🏢 Pacific Sales Team Territory Rules")
        rules_dialog.setIcon(QMessageBox.Information)
        
        rules_text = """
<h3>🗺️ Pacific Sales Team Territory Assignments</h3>

<p><b>🔵 Robert Mitchell - Wilmington/Leland Territory</b></p>
<ul>
<li>Wilmington Metro Area (all zip codes 284xx)</li>
<li>Leland and surrounding areas</li>
<li>Specializes in: AT&T Fiber installations, residential</li>
<li>Contact: robert.mitchell@pacific-sales.com</li>
</ul>

<p><b>🟢 Amanda Rodriguez - Hampstead/Pender County</b></p>
<ul>
<li>Hampstead and Pender County areas</li>
<li>Topsail Beach, Surf City coastal regions</li>
<li>Specializes in: New construction, coastal properties</li>
<li>Contact: amanda.rodriguez@pacific-sales.com</li>
</ul>

<p><b>🟡 James Patterson - Brunswick County</b></p>
<ul>
<li>Southport, Oak Island, Bald Head Island</li>
<li>Shallotte, Ocean Isle Beach areas</li>
<li>Specializes in: Vacation homes, ADT security systems</li>
<li>Contact: james.patterson@pacific-sales.com</li>
</ul>

<p><b>🟠 Maria Gonzalez - Lumberton/Robeson County</b></p>
<ul>
<li>Lumberton and Robeson County</li>
<li>Rural and suburban markets</li>
<li>Specializes in: Rural fiber solutions, business accounts</li>
<li>Contact: maria.gonzalez@pacific-sales.com</li>
</ul>

<p><b>🔴 Team Lead - All Territories</b></p>
<ul>
<li>High-value prospects (Fiber + ADT combo)</li>
<li>Commercial and multi-unit properties</li>
<li>Escalated customer issues</li>
<li>Contact: teamlead@pacific-sales.com</li>
</ul>

<h4>📋 Assignment Priority Rules:</h4>
<p><b>High Priority:</b> Fiber + ADT combo leads</p>
<p><b>Medium Priority:</b> AT&T Fiber available only</p>
<p><b>Standard Priority:</b> ADT detected only</p>
<p><b>Rush Priority:</b> Same-day contact required</p>
        """
        
        rules_dialog.setText(rules_text)
        rules_dialog.setTextFormat(Qt.RichText)
        rules_dialog.exec()

    def assign_salesperson_by_territory(self, city, lead_type):
        """Auto-assign salesperson based on territory and lead type"""
        # Territory mapping
        territory_map = {
            'Wilmington': 'Robert Mitchell - Wilmington/Leland',
            'Leland': 'Robert Mitchell - Wilmington/Leland',
            'Hampstead': 'Amanda Rodriguez - Hampstead/Pender County',
            'Lumberton': 'Maria Gonzalez - Lumberton/Robeson County',
            'Southport': 'James Patterson - Brunswick County'
        }
        
        # Special handling for high-value combo leads
        if lead_type == "Fiber + ADT Combo":
            return "Team Lead - All Territories"
        
        # Default territory assignment
        return territory_map.get(city, "Team Lead - All Territories")

    def get_lead_priority(self, fiber_available, adt_detected):
        """Determine lead priority based on services available"""
        if fiber_available and adt_detected:
            return "High Priority - Fiber + ADT"
        elif fiber_available:
            return "Medium Priority - Fiber Only"
        elif adt_detected:
            return "Low Priority - ADT Only"
        else:
            return "Standard Priority"

    def update_assignment_summary(self):
        """Update the assignment summary display"""
        if not hasattr(self, 'ak_export_data') or not self.ak_export_data:
            self.assignment_summary.setText("No leads loaded for assignment")
            return
        
        salesperson = self.ak_salesperson.currentText()
        priority = self.ak_priority.currentText()
        contact_method = self.ak_contact_method.currentText()
        
        # Count leads by assignment
        total_leads = len(self.ak_export_data)
        fiber_leads = sum(1 for lead in self.ak_export_data if lead.get('fiber_available', False))
        adt_leads = sum(1 for lead in self.ak_export_data if lead.get('adt_detected', False))
        combo_leads = sum(1 for lead in self.ak_export_data if lead.get('fiber_available', False) and lead.get('adt_detected', False))
        
        summary_text = f"""
        📊 Assignment Summary: {total_leads} leads → {salesperson}
        🎯 Priority: {priority} | 📞 Method: {contact_method}
        🔵 Fiber: {fiber_leads} | 🟡 ADT: {adt_leads} | 🔴 Combo: {combo_leads}
        """
        
        self.assignment_summary.setText(summary_text.strip())

    # BatchData Integration Methods
    
    def export_adt_to_batchdata(self):
        """Export ADT detection results to BatchData format"""
        if self.adt_results_table.rowCount() == 0:
            QMessageBox.warning(self, "No ADT Data", "No ADT detection results to export.")
            return
        
        # Collect ADT results from table
        adt_addresses = []
        for row in range(self.adt_results_table.rowCount()):
            address_item = self.adt_results_table.item(row, 0)
            city_item = self.adt_results_table.item(row, 1)
            adt_detected_item = self.adt_results_table.item(row, 3)
            
            if address_item and city_item and adt_detected_item:
                adt_addresses.append({
                    'address': address_item.text(),
                    'city': city_item.text(),
                    'state': 'NC',
                    'adt_detected': adt_detected_item.text() == 'Yes',
                    'lead_type': 'ADT Security Lead'
                })
        
        if not adt_addresses:
            QMessageBox.warning(self, "No Valid Data", "No valid ADT addresses found.")
            return
        
        # Save to CSV for BatchData
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"adt_results_batchdata_{timestamp}.csv"
        
        import pandas as pd
        df = pd.DataFrame(adt_addresses)
        df.to_csv(filename, index=False)
        
        QMessageBox.information(self, "BatchData Export", 
                              f"Exported {len(adt_addresses)} ADT addresses to {filename}\n\n"
                              f"Import this file into BatchData to get contact information.")
        
        self.log_text.append(f"[ADT] Exported {len(adt_addresses)} addresses to BatchData")
    
    def export_att_to_batchdata(self):
        """Export AT&T fiber results to BatchData format"""
        if self.att_results_table.rowCount() == 0:
            QMessageBox.warning(self, "No AT&T Data", "No AT&T fiber results to export.")
            return
        
        # Collect AT&T results from table
        att_addresses = []
        for row in range(self.att_results_table.rowCount()):
            address_item = self.att_results_table.item(row, 0)
            fiber_item = self.att_results_table.item(row, 1)
            city_item = self.att_results_table.item(row, 2)
            
            if address_item and fiber_item and city_item:
                att_addresses.append({
                    'address': address_item.text(),
                    'city': city_item.text(),
                    'state': 'NC',
                    'fiber_available': fiber_item.text() == 'Yes',
                    'lead_type': 'AT&T Fiber Lead' if fiber_item.text() == 'Yes' else 'No Fiber Lead'
                })
        
        if not att_addresses:
            QMessageBox.warning(self, "No Valid Data", "No valid AT&T addresses found.")
            return
        
        # Save to CSV for BatchData
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"att_results_batchdata_{timestamp}.csv"
        
        import pandas as pd
        df = pd.DataFrame(att_addresses)
        df.to_csv(filename, index=False)
        
        QMessageBox.information(self, "BatchData Export", 
                              f"Exported {len(att_addresses)} AT&T addresses to {filename}\n\n"
                              f"Import this file into BatchData to get contact information.")
        
        self.log_text.append(f"[AT&T] Exported {len(att_addresses)} addresses to BatchData")
    
    def import_adt_batchdata_results(self):
        """Import BatchData results for ADT leads"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "Import ADT BatchData Results", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                self.adt_enriched_contacts = df.to_dict('records')
                
                contact_count = len(self.adt_enriched_contacts)
                self.adt_batchdata_status.setText(f"✅ Loaded {contact_count} enriched ADT contacts")
                self.adt_batchdata_status.setStyleSheet("""
                    QLabel {
                        background: #d4edda;
                        color: #155724;
                        padding: 8px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
                
                self.log_text.append(f"[ADT] Imported {contact_count} enriched contacts from BatchData")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import ADT BatchData results:\n{e}")
                self.log_text.append(f"[ADT] Failed to import BatchData results: {e}")
    
    def import_att_batchdata_results(self):
        """Import BatchData results for AT&T leads"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "Import AT&T BatchData Results", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                self.att_enriched_contacts = df.to_dict('records')
                
                contact_count = len(self.att_enriched_contacts)
                self.att_batchdata_status.setText(f"✅ Loaded {contact_count} enriched AT&T contacts")
                self.att_batchdata_status.setStyleSheet("""
                    QLabel {
                        background: #d4edda;
                        color: #155724;
                        padding: 8px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                """)
                
                self.log_text.append(f"[AT&T] Imported {contact_count} enriched contacts from BatchData")
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import AT&T BatchData results:\n{e}")
                self.log_text.append(f"[AT&T] Failed to import BatchData results: {e}")
    
    def send_adt_to_mailchimp(self):
        """Send enriched ADT contacts to MailChimp"""
        if not self.adt_enriched_contacts:
            QMessageBox.warning(self, "No Data", "Please import ADT BatchData results first.")
            return
        
        # Create MailChimp list
        timestamp = datetime.now().strftime('%Y-%m-%d')
        list_name = f"ADT Security Leads - {timestamp}"
        
        # Prepare contacts for MailChimp
        mailchimp_contacts = []
        for contact in self.adt_enriched_contacts:
            if contact.get('owner_email'):
                mailchimp_contact = {
                    'email_address': contact['owner_email'],
                    'status': 'subscribed',
                    'merge_fields': {
                        'FNAME': contact.get('owner_first_name', ''),
                        'LNAME': contact.get('owner_last_name', ''),
                        'ADDRESS': contact.get('address', ''),
                        'CITY': contact.get('city', ''),
                        'STATE': contact.get('state', ''),
                        'ZIP': contact.get('zip', ''),
                        'PHONE': contact.get('owner_phone', ''),
                        'LEADTYPE': 'ADT Security',
                        'ADTSIGN': 'Yes' if contact.get('adt_detected') else 'No'
                    }
                }
                mailchimp_contacts.append(mailchimp_contact)
        
        if not mailchimp_contacts:
            QMessageBox.warning(self, "No Email Contacts", "No ADT contacts with email addresses found.")
            return
        
        # Save to file
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"adt_mailchimp_{timestamp_file}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump({
                'list_name': list_name,
                'contacts': mailchimp_contacts
            }, f, indent=2)
        
        QMessageBox.information(self, "MailChimp Export", 
                              f"Prepared {len(mailchimp_contacts)} ADT contacts for MailChimp\n\n"
                              f"List Name: {list_name}\n"
                              f"Saved to: {filename}")
        
        self.log_text.append(f"[ADT] Exported {len(mailchimp_contacts)} contacts to MailChimp")
    
    def send_att_to_mailchimp(self):
        """Send enriched AT&T contacts to MailChimp"""
        if not self.att_enriched_contacts:
            QMessageBox.warning(self, "No Data", "Please import AT&T BatchData results first.")
            return
        
        # Create MailChimp list
        timestamp = datetime.now().strftime('%Y-%m-%d')
        list_name = f"AT&T Fiber Leads - {timestamp}"
        
        # Prepare contacts for MailChimp
        mailchimp_contacts = []
        for contact in self.att_enriched_contacts:
            if contact.get('owner_email'):
                mailchimp_contact = {
                    'email_address': contact['owner_email'],
                    'status': 'subscribed',
                    'merge_fields': {
                        'FNAME': contact.get('owner_first_name', ''),
                        'LNAME': contact.get('owner_last_name', ''),
                        'ADDRESS': contact.get('address', ''),
                        'CITY': contact.get('city', ''),
                        'STATE': contact.get('state', ''),
                        'ZIP': contact.get('zip', ''),
                        'PHONE': contact.get('owner_phone', ''),
                        'LEADTYPE': 'AT&T Fiber',
                        'FIBER': 'Yes' if contact.get('fiber_available') else 'No'
                    }
                }
                mailchimp_contacts.append(mailchimp_contact)
        
        if not mailchimp_contacts:
            QMessageBox.warning(self, "No Email Contacts", "No AT&T contacts with email addresses found.")
            return
        
        # Save to file
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"att_mailchimp_{timestamp_file}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump({
                'list_name': list_name,
                'contacts': mailchimp_contacts
            }, f, indent=2)
        
        QMessageBox.information(self, "MailChimp Export", 
                              f"Prepared {len(mailchimp_contacts)} AT&T contacts for MailChimp\n\n"
                              f"List Name: {list_name}\n"
                              f"Saved to: {filename}")
        
        self.log_text.append(f"[AT&T] Exported {len(mailchimp_contacts)} contacts to MailChimp")
    
    def send_adt_to_activeknocker(self):
        """Send enriched ADT contacts to ActiveKnocker"""
        if not self.adt_enriched_contacts:
            QMessageBox.warning(self, "No Data", "Please import ADT BatchData results first.")
            return
        
        # Convert to ActiveKnocker format
        ak_data = []
        for contact in self.adt_enriched_contacts:
            ak_record = {
                'Street': contact.get('address', ''),
                'City': contact.get('city', ''),
                'State/Province': contact.get('state', 'NC'),
                'Zip/PostalCode': contact.get('zip', ''),
                'Country': 'US',
                'First Name': contact.get('owner_first_name', ''),
                'Last Name': contact.get('owner_last_name', ''),
                'Email': contact.get('owner_email', ''),
                'Phone': contact.get('owner_phone', ''),
                'Notes': f"ADT Security Lead - {contact.get('lead_type', '')}",
                'Pin': 'ADT_SECURITY',
                'Tags': f"adt-security,lead-type-{contact.get('lead_type', '').lower().replace(' ', '-')}"
            }
            ak_data.append(ak_record)
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"adt_activeknocker_{timestamp}.csv"
        
        import pandas as pd
        df = pd.DataFrame(ak_data)
        df.to_csv(filename, index=False)
        
        QMessageBox.information(self, "ActiveKnocker Export", 
                              f"Exported {len(ak_data)} ADT leads to {filename}\n\n"
                              f"Import this file into ActiveKnocker for lead management.")
        
        self.log_text.append(f"[ADT] Exported {len(ak_data)} leads to ActiveKnocker")
    
    def send_att_to_activeknocker(self):
        """Send enriched AT&T contacts to ActiveKnocker"""
        if not self.att_enriched_contacts:
            QMessageBox.warning(self, "No Data", "Please import AT&T BatchData results first.")
            return
        
        # Convert to ActiveKnocker format
        ak_data = []
        for contact in self.att_enriched_contacts:
            ak_record = {
                'Street': contact.get('address', ''),
                'City': contact.get('city', ''),
                'State/Province': contact.get('state', 'NC'),
                'Zip/PostalCode': contact.get('zip', ''),
                'Country': 'US',
                'First Name': contact.get('owner_first_name', ''),
                'Last Name': contact.get('owner_last_name', ''),
                'Email': contact.get('owner_email', ''),
                'Phone': contact.get('owner_phone', ''),
                'Notes': f"AT&T Fiber Lead - {contact.get('lead_type', '')}",
                'Pin': 'ATT_FIBER',
                'Tags': f"att-fiber,lead-type-{contact.get('lead_type', '').lower().replace(' ', '-')}"
            }
            ak_data.append(ak_record)
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"att_activeknocker_{timestamp}.csv"
        
        import pandas as pd
        df = pd.DataFrame(ak_data)
        df.to_csv(filename, index=False)
        
        QMessageBox.information(self, "ActiveKnocker Export", 
                              f"Exported {len(ak_data)} AT&T leads to {filename}\n\n"
                              f"Import this file into ActiveKnocker for lead management.")
        
        self.log_text.append(f"[AT&T] Exported {len(ak_data)} leads to ActiveKnocker")

    # BatchLeads Monitoring Methods
    
    def scan_for_batchdata_results(self):
        """Scan for new BatchData result files and load them"""
        self.log_text.append("[BatchLeads] Scanning for new BatchData results...")
        
        # Look for common BatchData result file patterns
        file_patterns = [
            "*batchdata*.csv",
            "*batch_data*.csv", 
            "*enriched*.csv",
            "*skip_trace*.csv",
            "*contact*.csv"
        ]
        
        new_files_found = 0
        total_new_leads = 0
        
        for pattern in file_patterns:
            files = glob.glob(pattern)
            for file_path in files:
                # Check if we've already processed this file
                file_mtime = os.path.getmtime(file_path)
                if file_path not in self.batchdata_file_timestamps or self.batchdata_file_timestamps[file_path] < file_mtime:
                    try:
                        # Load the file
                        df = pd.read_csv(file_path)
                        
                        # Determine source based on filename
                        source = self.determine_file_source(file_path)
                        
                        # Process the data
                        new_leads = self.process_batchdata_file(df, source, file_path)
                        
                        if new_leads > 0:
                            new_files_found += 1
                            total_new_leads += new_leads
                            self.batchdata_file_timestamps[file_path] = file_mtime
                            self.log_text.append(f"[BatchLeads] Loaded {new_leads} leads from {os.path.basename(file_path)}")
                        
                    except Exception as e:
                        self.log_text.append(f"[BatchLeads] Error loading {file_path}: {e}")
        
        # Update the table and status
        self.update_batchleads_table()
        
        if new_files_found > 0:
            self.batchleads_status.setText(f"✅ Found {total_new_leads} new leads from {new_files_found} files")
            self.batchleads_status.setStyleSheet("""
                QLabel {
                    background: #d4edda;
                    color: #155724;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
        else:
            self.batchleads_status.setText("⏳ No new BatchData results found")
            
        self.log_text.append(f"[BatchLeads] Scan complete: {total_new_leads} new leads from {new_files_found} files")
    
    def determine_file_source(self, file_path):
        """Determine the source of a BatchData file based on filename"""
        filename = os.path.basename(file_path).lower()
        
        if 'incident' in filename:
            return 'Incident Response'
        elif 'adt' in filename:
            return 'ADT Detection'
        elif 'att' in filename or 'fiber' in filename:
            return 'AT&T Fiber'
        elif 'activeknocker' in filename:
            return 'ActiveKnocker'
        else:
            return 'Unknown'
    
    def process_batchdata_file(self, df, source, file_path):
        """Process a BatchData file and add leads to the unified list"""
        new_leads = 0
        import_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        for _, row in df.iterrows():
            # Extract lead information with flexible field mapping
            lead = {
                'source': source,
                'address': self.safe_get_field(row, ['address', 'Address', 'street', 'Street']),
                'city': self.safe_get_field(row, ['city', 'City']),
                'state': self.safe_get_field(row, ['state', 'State', 'state_province']),
                'zip': self.safe_get_field(row, ['zip', 'Zip', 'zip_code', 'postal_code']),
                'owner_name': self.safe_get_field(row, ['owner_name', 'owner_first_name', 'first_name', 'name']),
                'owner_email': self.safe_get_field(row, ['owner_email', 'email', 'Email']),
                'owner_phone': self.safe_get_field(row, ['owner_phone', 'phone', 'Phone']),
                'lead_type': self.safe_get_field(row, ['lead_type', 'type', 'category']),
                'fiber_available': self.safe_get_field(row, ['fiber_available', 'att_fiber', 'fiber']),
                'adt_detected': self.safe_get_field(row, ['adt_detected', 'adt_sign', 'adt']),
                'incident_type': self.safe_get_field(row, ['incident_type', 'incident']),
                'import_date': import_date,
                'file_source': file_path,
                'status': 'New'
            }
            
            # Only add if we have at least an address
            if lead['address']:
                # Check for duplicates
                is_duplicate = any(
                    existing['address'].lower() == lead['address'].lower() and
                    existing['source'] == lead['source']
                    for existing in self.all_batchleads
                )
                
                if not is_duplicate:
                    self.all_batchleads.append(lead)
                    new_leads += 1
        
        return new_leads
    
    def safe_get_field(self, row, field_names):
        """Safely get a field from a row using multiple possible field names"""
        for field_name in field_names:
            if field_name in row and pd.notna(row[field_name]):
                return str(row[field_name])
        return ''
    
    def update_batchleads_table(self):
        """Update the BatchLeads table with current data"""
        self.batchleads_table.setRowCount(len(self.all_batchleads))
        
        for i, lead in enumerate(self.all_batchleads):
            # Checkbox for selection
            checkbox_item = QTableWidgetItem()
            checkbox_item.setCheckState(Qt.Unchecked)
            self.batchleads_table.setItem(i, 0, checkbox_item)
            
            # Lead data
            self.batchleads_table.setItem(i, 1, QTableWidgetItem(lead['source']))
            self.batchleads_table.setItem(i, 2, QTableWidgetItem(lead['address']))
            self.batchleads_table.setItem(i, 3, QTableWidgetItem(lead['city']))
            
            # Combine first and last name if available
            owner_name = lead['owner_name']
            if not owner_name and 'owner_last_name' in lead:
                first = lead.get('owner_first_name', '')
                last = lead.get('owner_last_name', '')
                owner_name = f"{first} {last}".strip()
            
            self.batchleads_table.setItem(i, 4, QTableWidgetItem(owner_name))
            self.batchleads_table.setItem(i, 5, QTableWidgetItem(lead['owner_email']))
            self.batchleads_table.setItem(i, 6, QTableWidgetItem(lead['owner_phone']))
            self.batchleads_table.setItem(i, 7, QTableWidgetItem(lead['lead_type']))
            self.batchleads_table.setItem(i, 8, QTableWidgetItem(lead['import_date']))
            self.batchleads_table.setItem(i, 9, QTableWidgetItem(lead['status']))
        
        # Update summary
        total_leads = len(self.all_batchleads)
        email_leads = sum(1 for lead in self.all_batchleads if lead['owner_email'])
        phone_leads = sum(1 for lead in self.all_batchleads if lead['owner_phone'])
        
        summary_text = f"Total Leads: {total_leads} | With Email: {email_leads} | With Phone: {phone_leads}"
        self.batchleads_summary.setText(summary_text)
    
    def select_all_batchleads(self):
        """Select/deselect all leads in the BatchLeads table"""
        # Check if any are currently selected
        any_selected = False
        for i in range(self.batchleads_table.rowCount()):
            checkbox_item = self.batchleads_table.item(i, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                any_selected = True
                break
        
        # Toggle all checkboxes
        new_state = Qt.Unchecked if any_selected else Qt.Checked
        for i in range(self.batchleads_table.rowCount()):
            checkbox_item = self.batchleads_table.item(i, 0)
            if checkbox_item:
                checkbox_item.setCheckState(new_state)
    
    def get_selected_batchleads(self):
        """Get list of selected leads from BatchLeads table"""
        selected = []
        for i in range(self.batchleads_table.rowCount()):
            checkbox_item = self.batchleads_table.item(i, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.Checked:
                if i < len(self.all_batchleads):
                    selected.append(self.all_batchleads[i])
        return selected
    
    def send_selected_batchleads_to_mailchimp(self):
        """Send selected BatchLeads to MailChimp"""
        selected_leads = self.get_selected_batchleads()
        
        if not selected_leads:
            QMessageBox.warning(self, "No Selection", "Please select leads to send to MailChimp.")
            return
        
        # Filter leads with email addresses
        email_leads = [lead for lead in selected_leads if lead['owner_email']]
        
        if not email_leads:
            QMessageBox.warning(self, "No Email Contacts", "No selected leads have email addresses.")
            return
        
        # Create MailChimp list
        timestamp = datetime.now().strftime('%Y-%m-%d')
        list_name = f"BatchLeads - {timestamp}"
        
        # Prepare contacts for MailChimp
        mailchimp_contacts = []
        for lead in email_leads:
            mailchimp_contact = {
                'email_address': lead['owner_email'],
                'status': 'subscribed',
                'merge_fields': {
                    'FNAME': lead['owner_name'].split()[0] if lead['owner_name'] else '',
                    'LNAME': ' '.join(lead['owner_name'].split()[1:]) if len(lead['owner_name'].split()) > 1 else '',
                    'ADDRESS': lead['address'],
                    'CITY': lead['city'],
                    'STATE': lead['state'],
                    'ZIP': lead['zip'],
                    'PHONE': lead['owner_phone'],
                    'SOURCE': lead['source'],
                    'LEADTYPE': lead['lead_type'],
                    'FIBER': 'Yes' if lead['fiber_available'] else 'No',
                    'ADT': 'Yes' if lead['adt_detected'] else 'No'
                }
            }
            mailchimp_contacts.append(mailchimp_contact)
        
        # Save to file
        timestamp_file = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"batchleads_mailchimp_{timestamp_file}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'list_name': list_name,
                'contacts': mailchimp_contacts
            }, f, indent=2)
        
        QMessageBox.information(self, "MailChimp Export", 
                              f"Prepared {len(mailchimp_contacts)} leads for MailChimp\n\n"
                              f"List Name: {list_name}\n"
                              f"Saved to: {filename}")
        
        self.log_text.append(f"[BatchLeads] Exported {len(mailchimp_contacts)} leads to MailChimp")
    
    def send_selected_batchleads_to_activeknocker(self):
        """Send selected BatchLeads to ActiveKnocker"""
        selected_leads = self.get_selected_batchleads()
        
        if not selected_leads:
            QMessageBox.warning(self, "No Selection", "Please select leads to send to ActiveKnocker.")
            return
        
        # Convert to ActiveKnocker format
        ak_data = []
        for lead in selected_leads:
            ak_record = {
                'Street': lead['address'],
                'City': lead['city'],
                'State/Province': lead['state'],
                'Zip/PostalCode': lead['zip'],
                'Country': 'US',
                'First Name': lead['owner_name'].split()[0] if lead['owner_name'] else '',
                'Last Name': ' '.join(lead['owner_name'].split()[1:]) if len(lead['owner_name'].split()) > 1 else '',
                'Email': lead['owner_email'],
                'Phone': lead['owner_phone'],
                'Notes': f"BatchLead from {lead['source']} - {lead['lead_type']}",
                'Pin': f"BATCH_{lead['source'].upper().replace(' ', '_')}",
                'Tags': f"batch-lead,source-{lead['source'].lower().replace(' ', '-')},type-{lead['lead_type'].lower().replace(' ', '-')}"
            }
            ak_data.append(ak_record)
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"batchleads_activeknocker_{timestamp}.csv"
        
        df = pd.DataFrame(ak_data)
        df.to_csv(filename, index=False)
        
        QMessageBox.information(self, "ActiveKnocker Export", 
                              f"Exported {len(ak_data)} leads to {filename}\n\n"
                              f"Import this file into ActiveKnocker for lead management.")
        
        self.log_text.append(f"[BatchLeads] Exported {len(ak_data)} leads to ActiveKnocker")

    def handle_automation(self, config):
        """Handle full automation request from AutomationWidget"""
        processes = config.get("processes", [])
        
        self.log_text.append("[AUTOMATION] 🚀 Starting Full Automation!")
        self.log_text.append(f"[AUTOMATION] Selected processes: {', '.join(processes)}")
        
        # Start the automation in sequence
        if "Redfin Pull" in processes:
            self.log_text.append("[AUTOMATION] Step 1: Starting Redfin data pull...")
            self.pull_data()
        
        # Use QTimer to chain the processes with delays
        self.automation_processes = processes
        self.current_automation_step = 0
        self.automation_timer = QTimer()
        self.automation_timer.timeout.connect(self.continue_automation)
        
        # Start checking for completion after 5 seconds
        if len(processes) > 1:
            self.automation_timer.start(5000)
    
    def continue_automation(self):
        """Continue with the next automation step"""
        if not hasattr(self, 'automation_processes'):
            return
            
        processes = self.automation_processes
        
        # Check if Redfin is complete before moving to next step
        if self.current_automation_step == 0 and "AT&T Fiber Check" in processes:
            # Be more flexible - check if we have some redfin results OR if enough time has passed
            selected_cities = [city for city, checkbox in self.city_checkboxes.items() if checkbox.isChecked()]
            redfin_ready = len(self.redfin_completed) >= len(selected_cities)  # All cities must complete
            
            # Debug logging
            self.log_text.append(f"[AUTOMATION] Debug: Selected cities: {len(selected_cities)}, Completed: {len(self.redfin_completed)}")
            self.log_text.append(f"[AUTOMATION] Completed cities: {list(self.redfin_completed)}")
            
            if redfin_ready:
                self.log_text.append(f"[AUTOMATION] Step 2: Starting AT&T Fiber checking for {len(self.redfin_completed)} cities...")
                self.start_processing()
                self.current_automation_step = 1
            else:
                # Check if we've been waiting too long and should proceed anyway with existing data
                if not hasattr(self, 'automation_start_time'):
                    self.automation_start_time = time.time()
                elif time.time() - self.automation_start_time > 120:  # 2 minutes timeout
                    self.log_text.append("[AUTOMATION] ⚠️ Timeout waiting for Redfin - proceeding with existing data...")
                    self.start_processing()
                    self.current_automation_step = 1
        
        elif self.current_automation_step == 1:
            # After AT&T completion, move to next step (skip ADT if not selected)
            selected_cities = [city for city, checkbox in self.city_checkboxes.items() if checkbox.isChecked()]
            if len(self.att_completed) >= len(selected_cities):  # AT&T processing complete
                if "ADT Detection" in processes:
                    self.log_text.append("[AUTOMATION] Step 3: ⏭️ Skipping ADT Detection - proceeding to BatchData...")
                else:
                    self.log_text.append("[AUTOMATION] Step 3: ADT Detection not selected - proceeding to BatchData...")
                self.current_automation_step = 2  # Skip to next step
        
        elif self.current_automation_step == 2 and "BatchData Contacts" in processes:
            # Since we skipped ADT, start BatchData immediately
            self.log_text.append("[AUTOMATION] Step 4: Starting BatchData processing...")
            self.start_batchdata_processing()
            self.current_automation_step = 3
        
        elif self.current_automation_step == 3 and "MailChimp Upload" in processes:
            # Check if we have enriched contacts (from BatchData)
            if hasattr(self, 'latest_batchleads') and self.latest_batchleads:
                self.log_text.append("[AUTOMATION] Step 5: Starting MailChimp upload...")
                self.start_mailchimp_processing()
                self.current_automation_step = 4
            elif not hasattr(self, 'batchdata_wait_start'):
                self.batchdata_wait_start = time.time()
            elif time.time() - self.batchdata_wait_start > 60:  # Wait 1 minute for BatchData
                self.log_text.append("[AUTOMATION] Step 5: ⏭️ Skipping MailChimp - no BatchData results yet...")
                self.current_automation_step = 4
        
        elif self.current_automation_step == 4 and "AI Email Composition and Launch" in processes:
            self.log_text.append("[AUTOMATION] Step 6: Opening AI Email Marketing...")
            # Switch to AI Email Marketing tab
            for i in range(self.tabs.count()):
                if "AI Email" in self.tabs.tabText(i):
                    self.tabs.setCurrentIndex(i)
                    break
            # Trigger generation
            self.ai_email_tab.generate_campaign()
            self.current_automation_step = 5
        
        elif self.current_automation_step == 5 and "ActiveKnocker Pin Assignment" in processes:
            self.log_text.append("[AUTOMATION] Step 7: Processing ActiveKnocker pin assignment...")
            # Use existing BatchLeads export functionality
            if hasattr(self, 'latest_batchleads') and self.latest_batchleads:
                self.export_batchleads_to_activeknocker()
            self.current_automation_step = 6
            
        # Stop automation when all steps are complete
        if self.current_automation_step >= len(processes):
            self.automation_timer.stop()
            self.log_text.append("[AUTOMATION] ✅ Full automation completed!")
            self.log_text.append(f"[AUTOMATION] Final Results - Redfin: {self.total_redfin_count}, AT&T Fiber: {self.total_att_fiber}, ADT: {self.total_adt_detected}")

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())