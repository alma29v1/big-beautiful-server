# ☁️ Google Cloud Backup Setup Guide

## Overview

The AT&T Fiber Tracker includes automatic backup functionality that securely stores your core program files to Google Cloud Storage. This ensures your program configuration and customizations are safely backed up to the cloud.

## What Gets Backed Up

### ✅ **Core Program Files (Included)**
- **Main application files**: `main_window.py`, `run_main_gui.py`, etc.
- **GUI components**: All files in `gui/` directory
- **Services**: All files in `services/` directory  
- **Workers**: All files in `workers/` directory
- **Configuration**: Settings and config files
- **Documentation**: README files and docs
- **Requirements**: `requirements.txt` and project files

### ❌ **Excluded Files (Not Backed Up)**
- **Data files**: CSV exports, JSON results, logs
- **Cache files**: Temporary files, Python cache
- **Large datasets**: ADT training images, downloaded data
- **Personal data**: Contact information, BatchData results
- **System files**: Git history, IDE settings

## Setup Instructions

### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**: https://console.cloud.google.com
2. **Create a new project** or select existing one
3. **Enable Cloud Storage API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Cloud Storage API"
   - Click "Enable"

### Step 2: Create Storage Bucket

1. **Go to Cloud Storage**: https://console.cloud.google.com/storage
2. **Create bucket**:
   - Click "Create bucket"
   - Choose unique bucket name (e.g., `your-company-att-tracker-backup`)
   - Select region close to you
   - Choose "Standard" storage class
   - Enable "Uniform" access control
   - Click "Create"

### Step 3: Create Service Account

1. **Go to IAM & Admin** > **Service Accounts**
2. **Create service account**:
   - Name: `att-tracker-backup`
   - Description: `Service account for AT&T Tracker backups`
   - Click "Create and Continue"
3. **Grant permissions**:
   - Role: `Storage Object Admin`
   - Click "Continue" > "Done"

### Step 4: Generate Credentials

1. **Click on your service account**
2. **Go to "Keys" tab**
3. **Add Key** > **Create new key**
4. **Choose JSON format**
5. **Download the JSON file** to your computer
6. **Store securely** (e.g., in `config/` directory)

### Step 5: Configure in Application

1. **Open AT&T Fiber Tracker**
2. **Go to "Cloud Backup" tab**
3. **Configure settings**:
   - **Credentials File**: Browse to your downloaded JSON file
   - **Storage Bucket**: Enter your bucket name
   - **Retention Period**: How long to keep old backups (default: 30 days)
4. **Test connection** to verify setup
5. **Save settings**

### Step 6: Enable Automatic Backups

1. **Check "Enable automatic backups"**
2. **Choose frequency**:
   - **Hourly**: For active development
   - **Daily**: Recommended for regular use
   - **Weekly**: For stable installations
3. **Save settings**

## Security Considerations

### 🔒 **Best Practices**

- **Secure credentials**: Store JSON file in secure location
- **Limit permissions**: Service account only has Storage Object Admin
- **Private bucket**: Bucket is not publicly accessible
- **Encrypted storage**: Google Cloud encrypts data at rest
- **Access logging**: Monitor bucket access in Cloud Console

### 🛡️ **Data Privacy**

- **No personal data**: Contact information is not backed up
- **No sensitive data**: BatchData results are excluded
- **Code only**: Only program files and configuration
- **Retention policy**: Old backups are automatically deleted

## Usage

### Manual Backup

1. **Go to "Cloud Backup" tab**
2. **Click "Backup Now"**
3. **Monitor progress** in the log
4. **Verify completion** message

### Automatic Backups

- **Runs in background** based on schedule
- **No user intervention** required
- **Logs all activity** for monitoring
- **Handles failures** gracefully

### Restore Process

1. **Download backup** from Google Cloud Console
2. **Extract ZIP file** to desired location
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Configure API keys** in Settings tab
5. **Run application**: `python run_main_gui.py`

## Monitoring

### Backup Status

- **Last backup time** shown in status area
- **Backup size** displayed after completion
- **Success/failure** notifications
- **Detailed logs** in backup tab

### Google Cloud Console

1. **Go to Cloud Storage** in console
2. **Open your bucket**
3. **View backup files** organized by date
4. **Monitor storage usage** and costs
5. **Check access logs** for security

## Troubleshooting

### Common Issues

#### "Credentials file not found"
- **Solution**: Verify file path is correct
- **Check**: File exists and is readable

#### "Bucket not found"
- **Solution**: Verify bucket name is correct
- **Check**: Bucket exists in your project

#### "Permission denied"
- **Solution**: Verify service account has Storage Object Admin role
- **Check**: Service account is enabled

#### "Connection failed"
- **Solution**: Check internet connection
- **Verify**: Google Cloud APIs are enabled

### Getting Help

1. **Check logs** in backup tab for detailed errors
2. **Test connection** to isolate issues
3. **Verify configuration** step by step
4. **Check Google Cloud Console** for bucket and permissions

## Cost Estimation

### Storage Costs (US regions)

- **Standard Storage**: $0.020 per GB/month
- **Typical backup size**: 5-10 MB
- **Monthly cost**: Less than $0.01 for daily backups
- **Annual cost**: Less than $0.12

### Operation Costs

- **Upload operations**: $0.005 per 1,000 operations
- **Download operations**: $0.004 per 10,000 operations
- **Daily backup cost**: Less than $0.01 per month

### Total Estimated Cost

- **Less than $1 per year** for typical usage
- **Extremely cost-effective** for data protection
- **Free tier** may cover small usage

## Advanced Configuration

### Custom Retention

Edit `config/backup_config.json`:
```json
{
  "retention_days": 90,
  "schedule": {
    "enabled": true,
    "frequency": "daily"
  }
}
```

### Multiple Backup Destinations

Create multiple configurations for different buckets:
- **Production backups**: Daily to primary bucket
- **Development backups**: Weekly to secondary bucket
- **Archive backups**: Monthly to long-term storage

---

*This backup system ensures your AT&T Fiber Tracker program is safely backed up to Google Cloud while maintaining security and privacy of your data.* 