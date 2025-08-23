import os
import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, 
                             QTimeEdit, QComboBox, QLabel, QMessageBox, QGroupBox, QCheckBox,
                             QSpinBox, QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDateEdit, QDialog, QFormLayout)
from PySide6.QtCore import QTime, Signal, QTimer
from datetime import datetime
from workers.incident_automation_worker import IncidentAutomationWorker

class AutomationWidget(QWidget):
    run_automation_signal = Signal(dict)  # config
    handle_new_campaigns = Signal(list)  # incident campaigns

    PROCESSES = [
        "Redfin Pull",
        "AT&T Fiber Check", 
        "BatchData Contacts",
        "ADT Detection",
        "MailChimp Upload",
        "ActiveKnocker Pin Assignment",  # New process for Mark Walters
        "AI Email Composition and Launch",
        "Incident Monitoring"  # New process
    ]

    def __init__(self):
        print('Creating AutomationWidget at:', datetime.now())
        super().__init__()
        self.incident_worker = None
        self.pending_incident_campaigns = []
        
        # Setup timer for periodic incident monitoring BEFORE UI setup
        self.incident_timer = QTimer()
        self.incident_timer.timeout.connect(self.run_incident_monitoring)
        
        # Setup timer for weekly automation schedule checking
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.check_weekly_schedule)
        self.schedule_timer.start(60000)  # Check every minute
        
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tabbed interface
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Regular automation tab
        automation_tab = QWidget()
        self.setup_automation_tab(automation_tab)
        self.tab_widget.addTab(automation_tab, "📅 Scheduled Automation")
        
        # Incident monitoring tab
        incident_tab = QWidget()
        self.setup_incident_tab(incident_tab)
        self.tab_widget.addTab(incident_tab, "🚨 Incident Monitoring")

    def setup_automation_tab(self, tab):
        """Setup the regular automation controls"""
        layout = QVBoxLayout(tab)

        # Available processes
        avail_group = QHBoxLayout()
        avail_group.addWidget(QLabel("Available Processes:"))
        self.process_combo = QComboBox()
        self.process_combo.addItems(self.PROCESSES)
        avail_group.addWidget(self.process_combo)
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_process)
        avail_group.addWidget(add_btn)
        layout.addLayout(avail_group)

        # Selected processes list
        self.process_list = QListWidget()
        layout.addWidget(self.process_list)

        # Reorder buttons
        reorder_layout = QHBoxLayout()
        up_btn = QPushButton("Up")
        up_btn.clicked.connect(self.move_up)
        reorder_layout.addWidget(up_btn)
        down_btn = QPushButton("Down")
        down_btn.clicked.connect(self.move_down)
        reorder_layout.addWidget(down_btn)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self.remove_process)
        reorder_layout.addWidget(remove_btn)
        layout.addLayout(reorder_layout)

        # Schedule time
        schedule_layout = QHBoxLayout()
        schedule_layout.addWidget(QLabel("Schedule Time:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime.currentTime())
        schedule_layout.addWidget(self.time_edit)
        layout.addLayout(schedule_layout)

        # Weekly schedule
        weekly_layout = QVBoxLayout()
        weekly_label = QLabel("📅 Weekly Schedule:")
        weekly_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        weekly_layout.addWidget(weekly_label)
        
        # Day selection checkboxes
        days_layout = QHBoxLayout()
        self.weekly_enabled = QCheckBox("Enable Weekly Schedule")
        self.weekly_enabled.setChecked(True)
        weekly_layout.addWidget(self.weekly_enabled)
        
        # Days checkboxes
        self.monday_enabled = QCheckBox("Monday")
        self.monday_enabled.setChecked(True)
        self.wednesday_enabled = QCheckBox("Wednesday") 
        self.wednesday_enabled.setChecked(True)
        self.friday_enabled = QCheckBox("Friday")
        self.friday_enabled.setChecked(True)
        
        # Other days (disabled by default per your request)
        self.tuesday_enabled = QCheckBox("Tuesday")
        self.thursday_enabled = QCheckBox("Thursday")
        self.saturday_enabled = QCheckBox("Saturday")
        self.sunday_enabled = QCheckBox("Sunday")
        
        days_layout.addWidget(self.monday_enabled)
        days_layout.addWidget(self.tuesday_enabled)
        days_layout.addWidget(self.wednesday_enabled)
        days_layout.addWidget(self.thursday_enabled)
        days_layout.addWidget(self.friday_enabled)
        days_layout.addWidget(self.saturday_enabled)
        days_layout.addWidget(self.sunday_enabled)
        
        weekly_layout.addLayout(days_layout)
        layout.addLayout(weekly_layout)



        # Save and Run buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Config")
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        
        run_btn = QPushButton("Run Full Automation")
        run_btn.clicked.connect(self.run_now)
        btn_layout.addWidget(run_btn)
        
        layout.addLayout(btn_layout)

    def setup_incident_tab(self, tab):
        """Setup the incident monitoring controls"""
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("🚨 Automated Incident Response Email System")
        header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                padding: 10px;
                background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)
        
        # Configuration section
        config_group = QGroupBox("⚙️ Monitoring Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Enable/disable incident monitoring
        self.incident_enabled = QCheckBox("Enable Automated Incident Monitoring")
        self.incident_enabled.setChecked(False)
        self.incident_enabled.toggled.connect(self.toggle_incident_monitoring)
        config_layout.addWidget(self.incident_enabled)
        
        # Radius setting
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("Contact Radius:"))
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(25, 200)
        self.radius_spin.setValue(50)
        self.radius_spin.setSuffix(" yards")
        radius_layout.addWidget(self.radius_spin)
        radius_layout.addStretch()
        config_layout.addLayout(radius_layout)
        
        # Check interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Check Interval:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 24)
        self.interval_spin.setValue(6)
        self.interval_spin.setSuffix(" hours")
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        config_layout.addLayout(interval_layout)
        
        # Target cities
        cities_layout = QVBoxLayout()
        cities_layout.addWidget(QLabel("Target Cities:"))
        self.cities_text = QTextEdit()
        self.cities_text.setMaximumHeight(80)
        self.cities_text.setPlainText("Wilmington, NC\nLeland, NC\nHampstead, NC\nLumberton, NC\nSouthport, NC\nJacksonville, NC\nFayetteville, NC")
        cities_layout.addWidget(self.cities_text)
        config_layout.addLayout(cities_layout)
        
        layout.addWidget(config_group)
        
        # Status section
        status_group = QGroupBox("📊 Monitoring Status")
        status_layout = QVBoxLayout(status_group)
        
        self.incident_status = QLabel("🔴 Incident monitoring is disabled")
        status_layout.addWidget(self.incident_status)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        self.start_monitoring_btn = QPushButton("🚨 Start Monitoring")
        self.start_monitoring_btn.clicked.connect(self.start_incident_monitoring)
        self.start_monitoring_btn.setEnabled(False)
        controls_layout.addWidget(self.start_monitoring_btn)
        
        self.stop_monitoring_btn = QPushButton("⏹️ Stop Monitoring")
        self.stop_monitoring_btn.clicked.connect(self.stop_incident_monitoring)
        self.stop_monitoring_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_monitoring_btn)
        
        self.check_now_btn = QPushButton("🔍 Check Now")
        self.check_now_btn.clicked.connect(self.check_incidents_now)
        controls_layout.addWidget(self.check_now_btn)
        
        status_layout.addLayout(controls_layout)
        layout.addWidget(status_group)
        
        # Pending campaigns section
        campaigns_group = QGroupBox("📧 Pending Email Campaigns (Awaiting Approval)")
        campaigns_layout = QVBoxLayout(campaigns_group)
        
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(6)
        self.campaigns_table.setHorizontalHeaderLabels([
            "Incident Type", "Location", "Contacts", "Created", "Priority", "Actions"
        ])
        self.campaigns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        campaigns_layout.addWidget(self.campaigns_table)
        
        layout.addWidget(campaigns_group)

    def add_process(self):
        process = self.process_combo.currentText()
        if process not in [self.process_list.item(i).text() for i in range(self.process_list.count())]:
            self.process_list.addItem(process)

    def move_up(self):
        current_row = self.process_list.currentRow()
        if current_row > 0:
            item = self.process_list.takeItem(current_row)
            self.process_list.insertItem(current_row - 1, item)
            self.process_list.setCurrentRow(current_row - 1)

    def move_down(self):
        current_row = self.process_list.currentRow()
        if current_row < self.process_list.count() - 1:
            item = self.process_list.takeItem(current_row)
            self.process_list.insertItem(current_row + 1, item)
            self.process_list.setCurrentRow(current_row + 1)

    def remove_process(self):
        current_row = self.process_list.currentRow()
        if current_row >= 0:
            self.process_list.takeItem(current_row)

    def toggle_incident_monitoring(self, enabled):
        """Enable/disable incident monitoring controls"""
        # Safety check for initialization order
        if not hasattr(self, 'incident_timer'):
            return
            
        self.start_monitoring_btn.setEnabled(enabled and not self.incident_timer.isActive())
        self.stop_monitoring_btn.setEnabled(enabled and self.incident_timer.isActive())
        
        if enabled:
            self.incident_status.setText("🟡 Incident monitoring enabled but not running")
        else:
            self.incident_status.setText("🔴 Incident monitoring is disabled")
            if self.incident_timer.isActive():
                self.stop_incident_monitoring()

    def start_incident_monitoring(self):
        """Start automated incident monitoring"""
        if not self.incident_enabled.isChecked():
            return
        
        interval_hours = self.interval_spin.value()
        interval_ms = interval_hours * 60 * 60 * 1000  # Convert to milliseconds
        
        self.incident_timer.start(interval_ms)
        self.incident_status.setText(f"🟢 Incident monitoring active (checking every {interval_hours} hours)")
        
        self.start_monitoring_btn.setEnabled(False)
        self.stop_monitoring_btn.setEnabled(True)
        
        # Run initial check
        self.check_incidents_now()

    def stop_incident_monitoring(self):
        """Stop automated incident monitoring"""
        self.incident_timer.stop()
        
        if self.incident_worker and self.incident_worker.isRunning():
            self.incident_worker.stop()
            self.incident_worker.wait()
        
        self.incident_status.setText("🟡 Incident monitoring enabled but not running")
        self.start_monitoring_btn.setEnabled(True)
        self.stop_monitoring_btn.setEnabled(False)

    def check_incidents_now(self):
        """Manually trigger incident check"""
        if self.incident_worker and self.incident_worker.isRunning():
            return  # Already running
        
        self.incident_status.setText("🔍 Checking for new incidents...")
        
        # Get configuration
        target_cities = [city.strip() for city in self.cities_text.toPlainText().split('\n') if city.strip()]
        radius = self.radius_spin.value()
        
        # Create and start worker
        self.incident_worker = IncidentAutomationWorker(target_cities, radius)
        self.incident_worker.log_signal.connect(self.update_incident_status)
        # Use QueuedConnection for thread safety with UI updates
        from PySide6.QtCore import Qt
        self.incident_worker.email_campaigns_signal.connect(self.handle_incident_campaigns, Qt.QueuedConnection)
        self.incident_worker.finished_signal.connect(self.on_incident_check_finished)
        
        self.incident_worker.start()

    def run_incident_monitoring(self):
        """Periodic incident monitoring triggered by timer"""
        self.check_incidents_now()

    def update_incident_status(self, message):
        """Update incident monitoring status"""
        self.incident_status.setText(message)

    def handle_incident_campaigns(self, campaigns):
        """Handle new email campaigns generated from incidents"""
        for campaign in campaigns:
            self.pending_incident_campaigns.append(campaign)
        
        self.update_campaigns_table()
        
        # Emit campaigns to AI email widget for approval
        self.handle_new_campaigns.emit(campaigns)
        
        if campaigns:
            QMessageBox.information(self, "New Incident Campaigns", 
                                  f"Generated {len(campaigns)} new email campaigns from recent incidents.\n"
                                  f"These campaigns have been sent to the AI Email Marketing tab for approval.\n"
                                  f"Please review and approve them in the Campaign Review section.")

    def on_incident_check_finished(self, result):
        """Handle completed incident check"""
        if result['success']:
            incidents = result.get('incidents', 0)
            campaigns = result.get('campaigns', 0)
            
            if self.incident_timer.isActive():
                next_check = self.interval_spin.value()
                self.incident_status.setText(f"🟢 Monitoring active - Found {incidents} incidents, generated {campaigns} campaigns (next check in {next_check}h)")
            else:
                self.incident_status.setText(f"✅ Check complete - Found {incidents} incidents, generated {campaigns} campaigns")
        else:
            error = result.get('error', 'Unknown error')
            self.incident_status.setText(f"❌ Error checking incidents: {error}")

    def update_campaigns_table(self):
        """Update the pending campaigns table"""
        self.campaigns_table.setRowCount(len(self.pending_incident_campaigns))
        
        for row, campaign in enumerate(self.pending_incident_campaigns):
            # Incident type
            self.campaigns_table.setItem(row, 0, QTableWidgetItem(campaign['incident_details']['type'].title()))
            
            # Location
            self.campaigns_table.setItem(row, 1, QTableWidgetItem(campaign['incident_details']['address']))
            
            # Contacts
            self.campaigns_table.setItem(row, 2, QTableWidgetItem(str(campaign['target_contacts'])))
            
            # Created
            created_time = datetime.fromisoformat(campaign['created_at']).strftime('%m/%d %H:%M')
            self.campaigns_table.setItem(row, 3, QTableWidgetItem(created_time))
            
            # Priority
            self.campaigns_table.setItem(row, 4, QTableWidgetItem(campaign['priority']))
            
            # Actions
            action_text = f"{campaign['status']} - {campaign['campaign_type']}"
            self.campaigns_table.setItem(row, 5, QTableWidgetItem(action_text))

    def save_config(self):
        config = {
            "processes": [self.process_list.item(i).text() for i in range(self.process_list.count())],
            "schedule_time": self.time_edit.time().toString("HH:mm"),
            "weekly_schedule": {
                "enabled": self.weekly_enabled.isChecked(),
                "monday": self.monday_enabled.isChecked(),
                "tuesday": self.tuesday_enabled.isChecked(),
                "wednesday": self.wednesday_enabled.isChecked(),
                "thursday": self.thursday_enabled.isChecked(),
                "friday": self.friday_enabled.isChecked(),
                "saturday": self.saturday_enabled.isChecked(),
                "sunday": self.sunday_enabled.isChecked()
            },
            "incident_monitoring": {
                "enabled": self.incident_enabled.isChecked(),
                "radius_yards": self.radius_spin.value(),
                "check_interval_hours": self.interval_spin.value(),
                "target_cities": [city.strip() for city in self.cities_text.toPlainText().split('\n') if city.strip()]
            }
        }
        
        os.makedirs("config", exist_ok=True)
        with open("config/automation_config.json", "w") as f:
            json.dump(config, f, indent=2)
        QMessageBox.information(self, "Saved", "Automation config saved!")

    def load_config(self):
        if os.path.exists("config/automation_config.json"):
            try:
                with open("config/automation_config.json", "r") as f:
                    config = json.load(f)
                    
                    # Load regular automation config
                    for process in config.get("processes", []):
                        self.process_list.addItem(process)
                    time_str = config.get("schedule_time", "00:00")
                    self.time_edit.setTime(QTime.fromString(time_str, "HH:mm"))
                    
                    # Load weekly schedule config
                    weekly_config = config.get("weekly_schedule", {})
                    self.weekly_enabled.setChecked(weekly_config.get("enabled", True))
                    self.monday_enabled.setChecked(weekly_config.get("monday", True))
                    self.tuesday_enabled.setChecked(weekly_config.get("tuesday", False))
                    self.wednesday_enabled.setChecked(weekly_config.get("wednesday", True))
                    self.thursday_enabled.setChecked(weekly_config.get("thursday", False))
                    self.friday_enabled.setChecked(weekly_config.get("friday", True))
                    self.saturday_enabled.setChecked(weekly_config.get("saturday", False))
                    self.sunday_enabled.setChecked(weekly_config.get("sunday", False))
                    
                    # Load incident monitoring config
                    incident_config = config.get("incident_monitoring", {})
                    self.incident_enabled.setChecked(incident_config.get("enabled", False))
                    self.radius_spin.setValue(incident_config.get("radius_yards", 50))
                    self.interval_spin.setValue(incident_config.get("check_interval_hours", 6))
                    
                    cities = incident_config.get("target_cities", [
                        "Wilmington, NC", "Leland, NC", "Hampstead, NC", 
                        "Lumberton, NC", "Southport, NC", "Jacksonville, NC", "Fayetteville, NC"
                    ])
                    self.cities_text.setPlainText('\n'.join(cities))
                    
            except Exception as e:
                print(f"Error loading config: {e}")
        


    def run_now(self):
        config = {
            "processes": [self.process_list.item(i).text() for i in range(self.process_list.count())],
            "immediate": True
        }
        self.run_automation_signal.emit(config) 

    def check_weekly_schedule(self):
        """Check if automation should run based on weekly schedule"""
        try:
            if not hasattr(self, 'weekly_enabled') or not self.weekly_enabled.isChecked():
                return
                
            from datetime import datetime
            now = datetime.now()
            current_day = now.weekday()  # 0=Monday, 1=Tuesday, etc.
            current_time = now.time()
            scheduled_time = self.time_edit.time().toPython()
            
            # Check if it's the right day
            day_enabled = False
            if current_day == 0:  # Monday
                day_enabled = self.monday_enabled.isChecked()
            elif current_day == 1:  # Tuesday
                day_enabled = self.tuesday_enabled.isChecked()
            elif current_day == 2:  # Wednesday
                day_enabled = self.wednesday_enabled.isChecked()
            elif current_day == 3:  # Thursday
                day_enabled = self.thursday_enabled.isChecked()
            elif current_day == 4:  # Friday
                day_enabled = self.friday_enabled.isChecked()
            elif current_day == 5:  # Saturday
                day_enabled = self.saturday_enabled.isChecked()
            elif current_day == 6:  # Sunday
                day_enabled = self.sunday_enabled.isChecked()
            
            if not day_enabled:
                return
                
            # Check if it's the right time (within 1 minute of scheduled time)
            time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                           (scheduled_time.hour * 60 + scheduled_time.minute))
            
            if time_diff <= 1:  # Within 1 minute of scheduled time
                # Check if we haven't already run today
                last_run_file = 'last_automation_run.txt'
                today_str = now.strftime('%Y-%m-%d')
                
                should_run = True
                if os.path.exists(last_run_file):
                    try:
                        with open(last_run_file, 'r') as f:
                            last_run_date = f.read().strip()
                        if last_run_date == today_str:
                            should_run = False
                    except:
                        pass
                
                if should_run:
                    # Record that we're running today
                    with open(last_run_file, 'w') as f:
                        f.write(today_str)
                    
                    # Run automation
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    print(f"🕐 Scheduled automation triggered for {day_names[current_day]} at {scheduled_time}")
                    self.run_now()
                    
        except Exception as e:
            print(f"Error in weekly schedule check: {e}")



 