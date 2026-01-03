# Quick Start Guide

## Installation

```bash
cd /Users/maomao/POV_Lei

# Activate virtual environment
source .venv/bin/activate

# Reinstall with latest changes
uv pip install -e .
```

## Launch Web Interface (Easiest)

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser:
1. Drag & drop a passport/license image
2. View real-time extraction
3. See confidence scores and issues
4. Download JSON result

---

## Test Single Image (CLI)

```bash
# Test with existing sample
kyc-pov --image data/uploads/License-3.jpeg --output outputs/test.json

# Check result
cat outputs/test.json | python -m json.tool
```

## Test Batch Processing

### Method 1: CLI
```bash
kyc-pov --batch data/uploads --output outputs
```

### Method 2: Script
```bash
./scripts/batch_process.sh data/uploads outputs
```

### View Summary
```bash
cat outputs/summary.json | python -m json.tool
```

Expected output structure:
```json
{
  "total": 5,
  "success": 3,
  "manual_review": 1,
  "retry": 1,
  "error": 0,
  "results": [...]
}
```

## Verify Parsing Fix

The previous `License-2.jpg` parsing failures should now succeed:

```bash
kyc-pov --image data/uploads/License-2.jpg --output outputs/license-2-test.json
echo "Exit code: $?"  # Should be 0
```

If you see `"status": "SUCCESS"` or `"MANUAL_REVIEW"` (not `SYSTEM_ERROR`), the fix worked!

## Test MRZ Validation (if you have passport samples)

```bash
# Process a passport image
kyc-pov --image data/uploads/passport-1.jpeg --output outputs/passport-test.json

# Check for MRZ cross-validation in issues
cat outputs/passport-test.json | grep -A5 "issues"
```

Expected: No "MRZ mismatch" errors if document is valid.

## Test Redaction (programmatic)

```python
from src.processor import ImageProcessor
from pathlib import Path

processor = ImageProcessor()
img_bytes = Path("data/uploads/License-1.png").read_bytes()

# Example bbox: [x1, y1, x2, y2] in pixels
redacted = processor.redact_image(img_bytes, [[100, 200, 300, 400]])

Path("outputs/redacted_sample.jpg").write_bytes(redacted)
print("Redacted image saved")
```

## Troubleshooting

### Still Getting Parse Errors?
1. Check debug logs:
   ```bash
   python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
   kyc-pov --image data/uploads/License-2.jpg 2>&1 | grep "Raw content"
   ```

2. Verify API key:
   ```bash
   grep FIREWORKS_API_KEY .env
   ```

3. Test with a known-good image (License-3.jpeg worked before)

### Batch Script Not Executable?
```bash
chmod +x scripts/batch_process.sh
```

### Import Errors?
Reinstall:
```bash
uv pip uninstall pov-kyc
uv pip install -e .
```

---

## Next Steps

1. **Production Deployment**: Add volume mounts, secrets management, rate limiting
2. **Monitoring**: Integrate with Datadog/Prometheus for UCS distribution tracking
3. **A/B Testing**: Compare UCS thresholds (0.9 vs 0.85) for optimal manual review rates
4. **Fine-tuning**: Collect edge cases and fine-tune Qwen2.5-VL on your specific document types

