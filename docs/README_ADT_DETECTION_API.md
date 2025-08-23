# ADT Detection API Setup Guide

This guide explains how to set up and use the ADT Detection API for detecting ADT security signs in property images.

## Overview

The ADT Detection system supports two modes:
1. **External API Mode**: Uses a third-party API service for detection (more accurate)
2. **Local Computer Vision Mode**: Uses OpenCV and template matching (fallback option)

## Configuration

### 1. API Key Setup

Add your ADT detection API key to the configuration:

#### Option A: Environment Variable
```bash
export ADT_DETECTION_API_KEY='your_api_key_here'
```

#### Option B: .env File
Create a `.env` file in the project root:
```
ADT_DETECTION_API_KEY=your_api_key_here
```

#### Option C: Direct Configuration
Edit `scripts/config.py` and replace the empty string:
```python
ADT_DETECTION_API_KEY = "your_actual_api_key_here"
```

### 2. API Endpoint Configuration

Update the API endpoint in `att_fiber_tracker/services/adt_detection_service.py`:

```python
# Replace with your actual API endpoint
api_url = "https://your-adt-detection-api.com/v1/detect"
```

## Usage

### Basic Usage

```python
from att_fiber_tracker.services.adt_detection_service import ADTDetectionService

# Initialize service
adt_service = ADTDetectionService()

# Detect ADT signs in a single image
result = adt_service.detect_adt_signs("path/to/image.jpg", prefer_api=True)

if result.get('success', False):
    if result.get('detected', False):
        print(f"✅ ADT sign detected! Confidence: {result.get('confidence', 0):.2f}")
    else:
        print(f"❌ No ADT sign detected. Confidence: {result.get('confidence', 0):.2f}")
else:
    print(f"Error: {result.get('error', 'Unknown error')}")
```

### Batch Detection

```python
# Detect ADT signs in multiple images
image_paths = ["image1.jpg", "image2.jpg", "image3.jpg"]
results = adt_service.batch_detect(image_paths, prefer_api=True)

for result in results:
    image_name = os.path.basename(result['image_path'])
    if result.get('detected', False):
        print(f"{image_name}: ✅ ADT detected")
    else:
        print(f"{image_name}: ❌ No ADT detected")
```

### Using the Worker

```python
from workers.adt_detection_worker import ADTDetectionWorker

# Create worker with API preference
worker = ADTDetectionWorker("path/to/image/directory", prefer_api=True)

# Connect signals
worker.progress_signal.connect(update_progress)
worker.log_signal.connect(update_log)
worker.finished_signal.connect(on_finished)

# Start detection
worker.start()
```

## API Response Format

The service expects the external API to return responses in this format:

```json
{
    "detections": [
        {
            "bbox": [x, y, width, height],
            "confidence": 0.95,
            "label": "adt_sign"
        }
    ],
    "confidence": 0.95,
    "success": true
}
```

## Local Detection Features

When API is not available, the system falls back to local computer vision:

### Detection Methods

1. **Template Matching**: Matches against ADT sign templates
2. **Color-based Detection**: Looks for blue rectangles (common in ADT signs)
3. **Text Detection**: Identifies potential text regions

### Confidence Scoring

- Template matching: 40% weight
- Color detection: 30% weight  
- Text detection: 30% weight

## Testing

Run the test script to verify your setup:

```bash
cd scripts
python test_adt_detection.py
```

This will:
- Check if API key is configured
- Test both API and local detection
- Run batch detection on sample images
- Provide setup instructions

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure environment variable is set correctly
   - Check that `.env` file is in the right location
   - Verify the key is not empty

2. **API Request Fails**
   - Check API endpoint URL
   - Verify API key is valid
   - Check network connectivity
   - Review API service documentation

3. **Local Detection Issues**
   - Ensure OpenCV is installed: `pip install opencv-python`
   - Check image file formats (supports jpg, jpeg, png, bmp)
   - Verify image files are not corrupted

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- **API Mode**: Faster and more accurate, but requires internet connection
- **Local Mode**: Works offline, but may be less accurate
- **Batch Processing**: Use for large numbers of images
- **Rate Limiting**: Respect API rate limits if applicable

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure configuration management
- Rotate API keys regularly
- Monitor API usage for unexpected activity 