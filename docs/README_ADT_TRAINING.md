# ADT Training System & BatchData API Integration

## Overview

This update adds two major features to the AT&T Fiber Tracker:

1. **Real BatchData API Integration** - Replaces fake email generation with real API calls
2. **ADT Detection Training System** - Allows verification of ADT detections and collects training data

## 🚀 New Features

### 1. Real BatchData API Integration

**Problem Solved:** The system was generating fake emails (`owner1@example.com`, etc.) which caused Mailchimp to reject all contacts.

**Solution:** 
- Updated `BatchDataWorker` to use the real BatchData API
- Added proper error handling and logging
- Configurable API key via environment variable

**How to Use:**
1. Set your BatchData API key:
   ```bash
   export BATCHDATA_API_KEY="your_real_api_key_here"
   ```
2. Run the system normally - it will now use real owner data

### 2. ADT Detection Training System

**Problem Solved:** No way to verify ADT detection accuracy or improve the model over time.

**Solution:**
- **ADT Training Worker** - Processes detection results and prepares verification data
- **ADT Verification Widget** - GUI for reviewing images and verifying detections
- **Training Data Collection** - Categorizes results into true/false positives/negatives
- **Model Improvement Reports** - Provides recommendations for improving accuracy

## 📋 Workflow

### Step 1: Run ADT Detection
1. Pull Redfin data for your cities
2. Click "Run ADT Detection" button
3. System downloads property images and analyzes them for ADT signs
4. Results are saved to CSV files

### Step 2: Start ADT Training
1. Click "Start ADT Training" button
2. System loads ADT detection results
3. Prepares images for verification
4. Automatically switches to "ADT Verification" tab

### Step 3: Verify Detections
1. In the ADT Verification tab, click "Load Verification Data"
2. Review each image and verify if ADT is actually present
3. Use buttons:
   - ✅ **ADT Present** - AI correctly detected ADT
   - ❌ **No ADT** - AI incorrectly detected ADT
   - ❓ **Unsure** - Cannot determine
4. Add optional notes for each verification
5. System auto-advances to next image

### Step 4: Export Training Data
1. After verifying all images, click "Export Training Data"
2. Choose location to save training data JSON file
3. Use this data to improve the ADT detection model

## 🏗️ System Architecture

### New Files Created:
- `workers/adt_training_worker.py` - Handles training workflow
- `gui/adt_verification_widget.py` - GUI for image verification
- `test_adt_training.py` - Test script for new features

### Updated Files:
- `workers/batchdata_worker.py` - Added real API integration
- `main_window.py` - Added ADT training tab and functionality

### Directory Structure:
```
adt_training_data/
├── pending/           # Images waiting for verification
├── true_positives/    # Correctly detected ADT signs
├── false_positives/   # Incorrectly detected ADT signs  
├── false_negatives/   # Missed ADT signs
└── verification_data_*.json  # Verification records
```

## 🔧 Configuration

### Environment Variables:
```bash
# Required for real BatchData API
export BATCHDATA_API_KEY="your_batchdata_api_key"

# Optional: Override default API endpoint
export BATCHDATA_API_URL="https://api.batchdata.com/v1"
```

### API Key Setup:
1. Sign up for BatchData API access
2. Get your API key from their dashboard
3. Set the environment variable before running the application

## 📊 Training Metrics

The system calculates and reports:
- **Accuracy** - Overall correct predictions
- **Precision** - Correct positive predictions / Total positive predictions
- **Recall** - Correct positive predictions / Total actual positives
- **True Positives** - Correctly detected ADT signs
- **False Positives** - Incorrectly detected ADT signs
- **False Negatives** - Missed ADT signs

## 🧪 Testing

Run the test script to verify everything works:
```bash
python test_adt_training.py
```

This will test:
- BatchData API integration
- ADT training system
- GUI components

## 🚨 Troubleshooting

### BatchData API Issues:
- **401 Unauthorized**: Check your API key
- **429 Too Many Requests**: Reduce batch size or add delays
- **500 Server Error**: Contact BatchData support

### ADT Training Issues:
- **No images found**: Run ADT detection first
- **GUI not loading**: Check PySide6 installation
- **Verification data missing**: Check file permissions

### Common Solutions:
1. **Mailchimp still rejecting emails**: Verify BatchData API key is set correctly
2. **No ADT verification tab**: Check that all imports are working
3. **Images not displaying**: Verify image paths and file permissions

## 📈 Model Improvement

After collecting training data:
1. Analyze false positives/negatives for patterns
2. Adjust confidence thresholds
3. Add new ADT sign templates
4. Retrain the detection model
5. Test with new verification data

## 🔄 Future Enhancements

Planned improvements:
- **Automated model retraining** based on verification data
- **Confidence calibration** using training results
- **Advanced image preprocessing** for better detection
- **Integration with external ADT databases**
- **Real-time verification feedback** during detection

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run the test script to identify problems
3. Review the logs for error messages
4. Contact support with specific error details

---

**Note:** This system requires a valid BatchData API key for real owner data. Without it, the system will fall back to demo mode with limited functionality. 