"""
Google Cloud Backup Service with Version Control
Automatically backs up core program files to Google Cloud Storage with version management
"""

import os
import json
import zipfile
import tempfile
import hashlib
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import fnmatch

from google.cloud import storage
from google.oauth2 import service_account

class GoogleCloudBackupService:
    """Service for backing up core program files to Google Cloud Storage with versioning"""
    
    def __init__(self, config=None):
        from PySide6.QtCore import QThread, Signal
        super().__init__()
        self.config = config or {}
        self.stop_flag = False
        self.version_info = self.get_version_info()
        
        # Core program files to backup (relative to project root)
        self.core_files_patterns = [
            # Main application files
            "main_window.py",
            "run_main_gui.py",
            "run_app.py",
            
            # GUI components
            "gui/*.py",
            
            # Services
            "services/*.py",
            
            # Workers
            "workers/*.py",
            
            # Utilities
            "utils/*.py",
            
            # Logic
            "logic/*.py",
            
            # Configuration files
            "config/*.json",
            "requirements.txt",
            "README.md",
            
            # Documentation
            "docs/*.md",
            
            # Scripts (core ones only)
            "scripts/config.py",
            "scripts/version.py",
            
            # AT&T Fiber Tracker module
            "att_fiber_tracker/*.py",
            "att_fiber_tracker/**/*.py",
            
            # Project configuration
            "*.toml",
            "*.cfg",
            "*.ini"
        ]
        
        # Files and patterns to exclude
        self.exclude_patterns = [
            # Temporary and cache files
            "*.pyc",
            "__pycache__",
            "*.pyo",
            "*.pyd",
            ".DS_Store",
            "Thumbs.db",
            
            # Log files
            "*.log",
            "logs/*",
            
            # Data files
            "*.csv",
            "*.json",
            "redfin_*",
            "mailchimp_results_*",
            "batchdata_*",
            "adt_detection_*",
            "incident_response_*",
            
            # Backup files
            "*.backup",
            "*.bak",
            "backups/*",
            
            # IDE and editor files
            ".vscode/*",
            ".idea/*",
            "*.swp",
            "*.swo",
            "*~",
            
            # System files
            ".git/*",
            ".gitignore",
            
            # Chrome profiles and downloads
            "chrome_profiles/*",
            "chrome-profile-*",
            "downloads/*",
            
            # Test and debug files
            "test_*",
            "debug_*",
            "*_test.py",
            
            # Large data directories
            "adt_detections/*",
            "adt_test_images/*",
            "adt_training_data/*",
            "data/*",
            "contacts/*",
            
            # Sample and temporary files
            "sample_*",
            "temp_*",
            "tmp_*"
        ]
    
    def get_version_info(self) -> Dict[str, Any]:
        """Get version information for the backup"""
        version_info = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',  # Default version
            'git_hash': None,
            'git_branch': None,
            'content_hash': None,
            'backup_type': 'manual'
        }
        
        try:
            # Try to get version from scripts/version.py
            if os.path.exists('scripts/version.py'):
                with open('scripts/version.py', 'r') as f:
                    content = f.read()
                    if '__version__' in content:
                        # Extract version string
                        for line in content.split('\n'):
                            if '__version__' in line and '=' in line:
                                version_info['version'] = line.split('=')[1].strip().strip('"\'')
                                break
        except Exception:
            pass
        
        try:
            # Try to get git information
            git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], 
                                             stderr=subprocess.DEVNULL).decode().strip()
            version_info['git_hash'] = git_hash[:8]  # Short hash
            
            git_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                               stderr=subprocess.DEVNULL).decode().strip()
            version_info['git_branch'] = git_branch
        except Exception:
            pass
        
        return version_info
    
    def calculate_content_hash(self, files_to_backup: List[str]) -> str:
        """Calculate a hash of the content to detect changes"""
        hasher = hashlib.sha256()
        
        # Sort files for consistent hashing
        sorted_files = sorted(files_to_backup)
        
        for file_path in sorted_files:
            try:
                with open(file_path, 'rb') as f:
                    hasher.update(f.read())
            except Exception:
                continue
        
        return hasher.hexdigest()[:12]  # Short hash
    
    def generate_backup_filename(self, content_hash: str) -> str:
        """Generate a versioned backup filename"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version = self.version_info['version']
        
        # Create version code
        version_parts = []
        version_parts.append(f"v{version}")
        
        if self.version_info['git_hash']:
            version_parts.append(f"git-{self.version_info['git_hash']}")
        
        if self.version_info['git_branch'] and self.version_info['git_branch'] != 'main':
            version_parts.append(f"branch-{self.version_info['git_branch']}")
        
        version_parts.append(f"hash-{content_hash}")
        
        version_code = "_".join(version_parts)
        
        return f"att_fiber_tracker_backup_{timestamp}_{version_code}.zip"
    
    def run(self):
        """Run the backup process"""
        try:
            self.log_signal.emit("🔄 Starting Google Cloud backup with versioning...")
            
            # Validate configuration
            if not self.validate_config():
                return
            
            # Create backup archive
            backup_file = self.create_backup_archive()
            if not backup_file:
                return
            
            # Upload to Google Cloud
            upload_result = self.upload_to_google_cloud(backup_file)
            
            # Cleanup temporary file
            if os.path.exists(backup_file):
                os.remove(backup_file)
            
            # Send results
            self.finished_signal.emit(upload_result)
            
        except Exception as e:
            self.error_signal.emit(f"Backup failed: {str(e)}")
            self.log_signal.emit(f"❌ Backup error: {e}")
    
    def validate_config(self):
        """Validate Google Cloud configuration"""
        required_keys = ['bucket_name', 'credentials_path']
        
        for key in required_keys:
            if key not in self.config:
                self.error_signal.emit(f"Missing configuration: {key}")
                return False
        
        # Check if credentials file exists
        if not os.path.exists(self.config['credentials_path']):
            self.error_signal.emit(f"Credentials file not found: {self.config['credentials_path']}")
            return False
        
        return True
    
    def should_include_file(self, file_path: str) -> bool:
        """Check if a file should be included in the backup"""
        # Convert to relative path for pattern matching
        rel_path = os.path.relpath(file_path)
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return False
            
            # Check directory patterns
            if '/' in pattern and pattern.endswith('/*'):
                dir_pattern = pattern[:-2]
                if rel_path.startswith(dir_pattern + '/') or rel_path == dir_pattern:
                    return False
        
        # Check include patterns
        for pattern in self.core_files_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            
            # Handle directory patterns
            if pattern.endswith('/*.py'):
                dir_pattern = pattern[:-5]
                if rel_path.startswith(dir_pattern + '/') and rel_path.endswith('.py'):
                    return True
            elif pattern.endswith('/**/*.py'):
                dir_pattern = pattern[:-8]
                if rel_path.startswith(dir_pattern + '/') and rel_path.endswith('.py'):
                    return True
        
        return False
    
    def get_files_to_backup(self) -> List[str]:
        """Get list of files to backup"""
        files_to_backup = []
        project_root = os.getcwd()
        
        self.log_signal.emit("📋 Scanning for core program files...")
        
        for root, dirs, files in os.walk(project_root):
            # Skip certain directories entirely
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in [
                '__pycache__', '.git', '.vscode', '.idea', 'logs', 'backups', 
                'chrome_profiles', 'chrome-profile-*', 'downloads', 'adt_detections',
                'adt_test_images', 'adt_training_data', 'data', 'contacts'
            ])]
            
            for file in files:
                file_path = os.path.join(root, file)
                if self.should_include_file(file_path):
                    files_to_backup.append(file_path)
        
        self.log_signal.emit(f"📁 Found {len(files_to_backup)} core files to backup")
        return files_to_backup
    
    def create_backup_archive(self) -> str:
        """Create a ZIP archive of core program files with version metadata"""
        try:
            files_to_backup = self.get_files_to_backup()
            
            if not files_to_backup:
                self.error_signal.emit("No files found to backup")
                return None
            
            # Calculate content hash
            content_hash = self.calculate_content_hash(files_to_backup)
            self.version_info['content_hash'] = content_hash
            
            # Generate versioned filename
            backup_filename = self.generate_backup_filename(content_hash)
            backup_path = os.path.join(tempfile.gettempdir(), backup_filename)
            
            self.log_signal.emit(f"📦 Creating versioned backup: {backup_filename}")
            self.log_signal.emit(f"🏷️  Version: {self.version_info['version']}")
            if self.version_info['git_hash']:
                self.log_signal.emit(f"🔗 Git: {self.version_info['git_hash']} ({self.version_info['git_branch']})")
            self.log_signal.emit(f"🔢 Content Hash: {content_hash}")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                total_files = len(files_to_backup)
                
                # Add version metadata file
                version_json = json.dumps(self.version_info, indent=2)
                zipf.writestr('backup_metadata.json', version_json)
                
                for i, file_path in enumerate(files_to_backup):
                    if self.stop_flag:
                        break
                    
                    try:
                        # Get relative path for archive
                        arcname = os.path.relpath(file_path)
                        zipf.write(file_path, arcname)
                        
                        # Update progress
                        self.progress_signal.emit(i + 1, total_files, f"Adding {os.path.basename(file_path)}")
                        
                    except Exception as e:
                        self.log_signal.emit(f"⚠️  Skipped {file_path}: {e}")
            
            # Get file size
            file_size = os.path.getsize(backup_path)
            file_size_mb = file_size / (1024 * 1024)
            
            self.log_signal.emit(f"✅ Versioned backup created: {file_size_mb:.1f} MB")
            return backup_path
            
        except Exception as e:
            self.error_signal.emit(f"Failed to create backup archive: {e}")
            return None
    
    def upload_to_google_cloud(self, backup_file: str) -> Dict[str, Any]:
        """Upload backup file to Google Cloud Storage with versioning"""
        try:
            self.log_signal.emit("☁️  Connecting to Google Cloud Storage...")
            
            # Initialize Google Cloud Storage client
            credentials = service_account.Credentials.from_service_account_file(
                self.config['credentials_path']
            )
            client = storage.Client(credentials=credentials)
            bucket = client.bucket(self.config['bucket_name'])
            
            # Create blob name with version organization
            date_path = datetime.now().strftime('%Y/%m/%d')
            blob_name = f"att_fiber_tracker_backups/{date_path}/{os.path.basename(backup_file)}"
            
            blob = bucket.blob(blob_name)
            
            # Upload with progress tracking
            file_size = os.path.getsize(backup_file)
            self.log_signal.emit(f"⬆️  Uploading to gs://{self.config['bucket_name']}/{blob_name}")
            
            with open(backup_file, 'rb') as f:
                blob.upload_from_file(f)
            
            # Verify upload
            if blob.exists():
                self.log_signal.emit("✅ Versioned backup uploaded successfully!")
                
                # Clean up old backups with smart retention
                self.smart_cleanup_backups(bucket)
                
                return {
                    'success': True,
                    'bucket': self.config['bucket_name'],
                    'blob_name': blob_name,
                    'file_size': file_size,
                    'upload_time': datetime.now().isoformat(),
                    'version_info': self.version_info,
                    'public_url': f"gs://{self.config['bucket_name']}/{blob_name}"
                }
            else:
                raise Exception("Upload verification failed")
                
        except Exception as e:
            self.error_signal.emit(f"Google Cloud upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def smart_cleanup_backups(self, bucket):
        """Smart cleanup that retains multiple recent backups and important versions"""
        try:
            # Get retention settings
            retention_days = self.config.get('retention_days', 30)
            keep_recent_count = self.config.get('keep_recent_backups', 5)   # Keep 5 most recent
            keep_daily_count = self.config.get('keep_daily_backups', 7)     # Keep 7 daily backups
            
            self.log_signal.emit(f"🧹 Smart cleanup: keeping {keep_recent_count} recent, {keep_daily_count} daily, {retention_days} days total")
            
            # Get all backups
            blobs = list(bucket.list_blobs(prefix='att_fiber_tracker_backups/'))
            
            if not blobs:
                return
            
            # Sort by creation time (newest first)
            blobs.sort(key=lambda b: b.time_created, reverse=True)
            
            # Categorize backups
            to_keep = set()
            to_delete = []
            
            # 1. Keep most recent backups (regardless of age)
            for i, blob in enumerate(blobs[:keep_recent_count]):
                to_keep.add(blob.name)
                if i == 0:
                    self.log_signal.emit(f"📌 Keeping most recent: {blob.name}")
            
            # 2. Keep one backup per day for the last N days
            daily_backups = {}
            for blob in blobs:
                date_key = blob.time_created.strftime('%Y-%m-%d')
                if date_key not in daily_backups:
                    daily_backups[date_key] = blob
            
            # Keep the most recent daily backups
            daily_keys = sorted(daily_backups.keys(), reverse=True)[:keep_daily_count]
            for date_key in daily_keys:
                blob = daily_backups[date_key]
                to_keep.add(blob.name)
            
            # 3. Apply retention period
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Determine what to delete
            deleted_count = 0
            for blob in blobs:
                if (blob.name not in to_keep and 
                    blob.time_created.replace(tzinfo=None) < cutoff_date):
                    to_delete.append(blob)
            
            # Delete old backups
            for blob in to_delete:
                try:
                    blob.delete()
                    deleted_count += 1
                except Exception as e:
                    self.log_signal.emit(f"⚠️  Failed to delete {blob.name}: {e}")
            
            if deleted_count > 0:
                self.log_signal.emit(f"🗑️  Deleted {deleted_count} old backup(s)")
            
            # Log retention summary
            remaining_count = len(blobs) - deleted_count
            self.log_signal.emit(f"📊 Retention summary: {remaining_count} backups kept, {deleted_count} deleted")
                
        except Exception as e:
            self.log_signal.emit(f"⚠️  Cleanup warning: {e}")
    
    def stop(self):
        """Stop the backup process"""
        self.stop_flag = True


class BackupScheduler:
    """Scheduler for automatic backups"""
    
    def __init__(self, schedule_config=None):
        from PySide6.QtCore import QThread, Signal
        super().__init__()
        self.schedule_config = schedule_config or {}
        self.stop_flag = False
    
    def run(self):
        """Run the backup scheduler"""
        import time
        
        while not self.stop_flag:
            if self.should_run_backup():
                self.log_signal.emit("⏰ Scheduled backup triggered")
                self.backup_triggered.emit()
                
                # Update last backup time
                self.update_last_backup_time()
            
            # Check every hour
            time.sleep(3600)
    
    def should_run_backup(self) -> bool:
        """Check if backup should run based on schedule"""
        if not self.schedule_config.get('enabled', False):
            return False
        
        frequency = self.schedule_config.get('frequency', 'daily')
        last_backup_file = 'last_backup_time.txt'
        
        # Get last backup time
        last_backup = None
        if os.path.exists(last_backup_file):
            try:
                with open(last_backup_file, 'r') as f:
                    last_backup = datetime.fromisoformat(f.read().strip())
            except:
                pass
        
        now = datetime.now()
        
        if frequency == 'daily':
            if last_backup is None or (now - last_backup).days >= 1:
                return True
        elif frequency == 'weekly':
            if last_backup is None or (now - last_backup).days >= 7:
                return True
        elif frequency == 'hourly':
            if last_backup is None or (now - last_backup).seconds >= 3600:
                return True
        
        return False
    
    def update_last_backup_time(self):
        """Update the last backup timestamp"""
        with open('last_backup_time.txt', 'w') as f:
            f.write(datetime.now().isoformat())
    
    def stop(self):
        """Stop the scheduler"""
        self.stop_flag = True 