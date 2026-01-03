# Fireworks AI KYC PoV System

Identity verification pipeline for FSI (Financial Services Industry) leveraging Fireworks AI's `qwen2p5-vl-32b-instruct` vision model.

## Features

- **Multi-format ingestion**: JPG, JPEG, PNG, GIF, BMP, TIFF, WebP
- **Intelligent extraction**: Structured JSON output for passport and driver's license fields
- **Three-layer validation**:
  1. **Technical**: Blur detection, pHash deduplication
  2. **Business logic**: Date consistency, regex patterns, MRZ cross-validation
  3. **AI confidence**: Model-reported probability scores
- **Unified Confidence Score (UCS)**: Weighted composite of AI probability (40%), image quality (20%), and logic checks (40%)
- **Privacy-first**: Zero Data Retention (ZDR), in-memory processing, optional PII redaction
- **Batch processing**: Directory-level automation with summary reports

---

## Architecture

```
Image Input → Preprocessing (quality/dedup/resize) → VLM Extraction (Fireworks) →
Validation (logic/MRZ/regex) → Status Routing (SUCCESS/MANUAL_REVIEW/RETRY_UPLOAD) →
Optional Output (JSON + redacted image)
```

**Status Thresholds:**
- `SUCCESS`: UCS ≥ 0.9
- `MANUAL_REVIEW`: 0.7 ≤ UCS < 0.9
- `RETRY_UPLOAD`: UCS < 0.7 or technical rejection (blur, duplicate)
- `SYSTEM_ERROR`: API/parsing failures

---

## Setup

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Navigate to project directory
cd path/to/POV_Lei

# Create virtual environment with uv
uv venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows (Command Prompt):
.venv\Scripts\activate.bat

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -e .
```

### Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env and set your Fireworks API key
# FIREWORKS_API_KEY=fw_YOUR_KEY_HERE
```

---

## Quick Start

### Web Interface (Recommended)

Launch the Streamlit UI for interactive document verification:

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501` and:
1. Upload a passport or driver's license image
2. View real-time extraction results
3. See confidence scores and validation issues
4. Download results as JSON

---

### Command Line

#### Single Image

```bash
# Zero Data Retention (results to console only, no files saved)
kyc-pov --image data/uploads/passport-1.jpeg

# With output storage
kyc-pov --image data/uploads/License-3.jpeg --output outputs/License-3.json

# Custom absolute paths (replace with your actual path)
# macOS/Linux:   ~/Documents/my-license.png
# Windows:       C:\Users\YourName\Documents\my-license.png
kyc-pov --image /path/to/your/document.jpg --output /path/to/output.json
```

#### Batch Processing

```bash
# Process directory (saves to outputs/ by default)
kyc-pov --batch data/uploads

# Custom directory (replace with your actual path)
kyc-pov --batch /path/to/your/documents --output /path/to/results

# Using bash script (macOS/Linux, or Git Bash on Windows)
./scripts/batch_process.sh data/uploads outputs
```

If you see `"status": "SUCCESS"` or `"MANUAL_REVIEW"` (not `SYSTEM_ERROR`), the fix worked!

---

## Output Format

```json
{
  "status": "SUCCESS",
  "score": 0.98,
  "logic_score": 1.0,
  "phash": "bfbe4018602d1de7",
  "issues": [],
  "flagged_fields": [],
  "payload": {
    "document_type": "drivers_license",
    "ai_confidence": 0.95,
    "missing_fields": [],
    "drivers_license": {
      "full_name": "John Doe",
      "birth_date": "1990-05-15",
      "document_number": "D1234567",
      "issue_date": "2020-01-01",
      "expiry_date": "2025-01-01",
      "evidence": {
        "full_name": {"snippet": "John Doe", "bbox": [100, 200, 300, 250]}
      }
    }
  }
}
```

---

## Known Limitations

**Fireworks API constraints**:
   - Base64 total: <10MB
   - Max images per request: 30
   - Supported formats: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`

---

## Privacy & Compliance

- **Zero Data Retention**: Images processed in-memory only; no disk persistence by default.
- **PII Redaction**: Use `ImageProcessor.redact_image(image_bytes, bboxes)` to black out sensitive regions based on evidence bboxes.
- **Audit Trail**: Enable structured logging or save sanitized results to `--output`.

---

## Troubleshooting

### Parsing Failures
If you see `Failed to parse structured output`:
1. Check that `FIREWORKS_API_KEY` is valid
2. Increase `max_tokens` in `src/extractor.py` if JSON is truncated
3. Review raw model output in debug logs (`logging.basicConfig(level=logging.DEBUG)`)

### Blur Detection False Positives
Adjust `QUALITY_THRESHOLD` in `src/main.py` (default: 80.0). Lower for more lenient checks.

### Batch Script Permission Denied
```bash
chmod +x scripts/batch_process.sh
```

---

## Development

```bash
# Run linter
ruff check src/

# Format code
ruff format src/

# Type check
mypy src/
```