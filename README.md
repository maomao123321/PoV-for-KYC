# Fireworks AI KYC PoV System

Production-grade identity verification pipeline for FSI (Financial Services Industry) leveraging Fireworks AI's `qwen2p5-vl-32b-instruct` vision model.

## Features

- **Multi-format ingestion**: JPG, PNG, GIF, BMP, TIFF, WebP
- **Intelligent extraction**: Structured JSON output for passport and driver's license fields
- **Three-layer validation**:
  1. **Technical**: Laplacian blur detection, pHash deduplication
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
# Clone/navigate to project
cd /Users/maomao/POV_Lei

# Create virtual environment
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

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

## Usage

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

**Features:**
- 🎨 Clean, ChatGPT-inspired interface
- 📊 Visual confidence metrics
- ⚠️ Inline issue detection
- 📥 One-click JSON export

---

### Command Line

#### Single Image

```bash
# Basic usage (auto-detects MIME from extension)
kyc-pov --image /path/to/passport.jpg

# With output file
kyc-pov --image /path/to/license.png --output results/license.json

# Override MIME type
kyc-pov --image /path/to/document --mime image/jpeg
```

#### Batch Processing

```bash
# Process entire directory
kyc-pov --batch data/uploads --output outputs

# Or use the provided script
./scripts/batch_process.sh data/uploads outputs
```

**Batch Output:**
- Individual JSON files: `outputs/filename.json`
- Summary report: `outputs/summary.json` (includes success/failure counts)

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

## Design Decisions

### Why JSON Object Mode (not strict schema)?
Fireworks' strict `json_schema` mode can be fragile with complex nested structures. We use `json_object` mode with schema in prompt for better reliability while maintaining structure through Pydantic validation.

### Why base64 encoding (not URLs)?
**Compliance**: KYC data must not be exposed via public URLs. Base64 keeps PII within the encrypted API request body, aligning with ZDR principles.

### Why remove PDF support?
Simplicity and dependency reduction. Most production KYC flows pre-convert documents to images. If needed, add `pdf2image` back and uncomment PDF logic in `main.py`.

### MRZ Cross-Validation
For passports with Machine Readable Zone (MRZ), we:
1. Parse MRZ line 2 to extract document number, birth date, expiry date
2. Cross-check against visual zone fields
3. Flag mismatches in `issues` and reduce logic score

---

## Known Limitations

1. **Fireworks API constraints**:
   - Base64 total: <10MB
   - Max images per request: 30
   - Supported formats: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp`

2. **No real-time liveness detection**: This PoV focuses on document OCR, not biometric matching.

3. **No external DB lookups**: Does not validate against government registries (out of scope for 24h delivery).

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

---

## License

MIT (or specify your license)

---

## Contact

For questions or production deployment inquiries, contact [your-email@example.com].
