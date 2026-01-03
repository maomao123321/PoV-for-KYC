# Streamlit Web Interface Guide

## Features

### 🎨 Clean Interface
- ChatGPT-inspired minimal design
- Centered layout with optimal reading width
- Smooth animations and transitions

### 📤 Easy Upload
- Drag & drop or click to browse
- Supports JPG, PNG, GIF, BMP
- Instant preview of uploaded document

### 📊 Visual Results
- Color-coded status badges:
  - 🟢 **SUCCESS**: High confidence, all checks passed
  - 🟡 **MANUAL_REVIEW**: Medium confidence, needs human review
  - 🔴 **RETRY_UPLOAD**: Low quality or failed validation
  - ⚫ **SYSTEM_ERROR**: API or processing failure

### 💯 Confidence Metrics
Three separate scores displayed:
- **AI Confidence**: Model's self-assessment
- **Logic Score**: Business rule validation
- **Overall (UCS)**: Weighted combination

### 🔍 Detailed Extraction
All document fields displayed in clean grid:
- Full Name
- Date of Birth (formatted nicely)
- Document Number
- Issue/Expiry Dates
- Nationality
- License Class (for driver's licenses)
- Address (for driver's licenses)

### ⚠️ Issue Tracking
Clear display of:
- Validation issues (date logic, format mismatches)
- Flagged fields (highlighted in results)
- Helpful suggestions for common problems

### 📥 Export
- Download results as JSON
- Filename includes perceptual hash for tracking
- Contains full payload for auditing

## Usage

### 1. Start the Server

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Launch Streamlit
streamlit run app.py
```

### 2. Access the Interface

Open your browser to: **http://localhost:8501**

### 3. Upload Document

Click "Browse files" or drag & drop:
- Passport (any country)
- Driver's License (US formats tested)

### 4. Review Results

Wait 2-5 seconds for processing, then:
- Check overall status badge
- Review confidence scores
- Verify extracted fields
- Note any issues/warnings

### 5. Export or Retry

- Click "Download Result" to save JSON
- Click "Process Another Document" to start over

## Advanced Features

### Show Raw JSON
Expand "Advanced Details" section and check "Show Raw JSON" to see:
- Full API response
- Evidence bounding boxes
- Missing fields list
- Perceptual hash

### Batch Processing
For multiple documents, use CLI instead:

```bash
kyc-pov --batch data/uploads --output outputs
```

## Troubleshooting

### Port Already in Use
```bash
streamlit run app.py --server.port 8502
```

### Slow Processing
- Check internet connection (API calls to Fireworks)
- Reduce image size before upload
- Verify API key is valid

### Image Rejected
If you see "Image Quality Issue":
- Ensure good lighting
- Avoid glare/reflections
- Keep document flat and fully visible
- Retake photo with better focus

## Configuration

### Custom Theme
Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor="#10a37f"  # Accent color
backgroundColor="#ffffff"  # Main background
secondaryBackgroundColor="#f7f7f8"  # Card backgrounds
textColor="#1a1a1a"  # Text color
```

### Server Settings
```toml
[server]
port = 8501
headless = true
maxUploadSize = 10  # MB
```

## Privacy & Security

- ✅ All processing in-memory (Zero Data Retention)
- ✅ Images not saved to disk
- ✅ API key loaded from `.env` (never exposed in UI)
- ✅ No external logging or analytics
- ✅ XSRF protection enabled

## Keyboard Shortcuts

- `Ctrl/Cmd + R`: Reload page
- `Ctrl/Cmd + K`: Clear cache and rerun

## Tips

1. **Best Image Quality**: High resolution, good lighting, no blur
2. **Supported Documents**: US/International passports, US driver's licenses
3. **Batch Mode**: Use CLI for processing 10+ documents
4. **Export Everything**: Download JSON for audit trail

---

For CLI usage, see main [README.md](../README.md)

