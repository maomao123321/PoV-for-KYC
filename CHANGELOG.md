# Changelog

## [0.2.0] - 2026-01-03

### 🎉 Major Improvements

#### 1. Fixed Structured Output Parsing
- **Changed from strict `json_schema` to `json_object` mode** for better reliability
- Added robust JSON parsing with fallback logic (strips code fences, extracts braces)
- Increased `max_tokens` to 2000 to prevent truncation
- Added detailed debug logging for troubleshooting

#### 2. Complete MRZ Cross-Validation
- **Implemented full MRZ line parsing** for passports
- Cross-checks document number, birth date, expiry date between MRZ and visual zone
- Flags mismatches in issues and reduces logic score appropriately
- Penalty: 0.3 points for MRZ inconsistencies

#### 3. Improved Exception Handling
- **No more raw exceptions** - all failures now return structured `PipelineResult`
- Status codes: `SUCCESS`, `MANUAL_REVIEW`, `RETRY_UPLOAD`, `SYSTEM_ERROR`
- Each status includes actionable `issues` array with clear error messages
- Graceful degradation when API fails

#### 4. PII Redaction Implementation
- **`ImageProcessor.redact_image()` now blacks out bbox regions**
- Changed from blur to solid black rectangles for audit compliance
- Accepts absolute pixel coordinates from evidence bboxes
- Returns redacted JPEG bytes for safe storage

#### 5. Batch Processing Mode
- **New `--batch` CLI flag** for directory-level processing
- Generates `summary.json` with success/failure statistics
- Individual JSON output per image
- Parallel-ready architecture (currently sequential for safety)

#### 6. Removed PDF Support
- **Eliminated `pdf2image` dependency** for simpler deployment
- Removed PDF conversion logic from `main.py`
- Updated documentation to reflect image-only support
- Reduces Docker image size and removes poppler requirement

#### 7. Example Scripts
- **Added `scripts/batch_process.sh`** with auto-activation and env loading
- Color-coded console output
- Summary statistics display
- Executable permissions set

### 🔧 Code Quality Improvements

- **Cleaner architecture**: Removed unused Tuple import, consolidated error handling
- **Better type hints**: Changed `Tuple[bytes, str]` to `tuple[bytes, str]`
- **Simplified `load_image_bytes()`**: No PDF branches, cleaner MIME detection
- **Consistent naming**: `run_single_file` instead of `run_pipeline_file`
- **No linter errors**: Passed all checks

### 📚 Documentation

- **Completely rewritten README.md** with:
  - Architecture diagram
  - Status threshold explanations
  - Design decision rationales (JSON mode, base64, MRZ logic)
  - Troubleshooting guide
  - Privacy & compliance section
- **Added scripts/README.md** for batch processing usage
- **Updated .gitignore** to exclude outputs/ (PII safety)

### ⚙️ Configuration

- **Updated `pyproject.toml`**: Removed pdf2image dependency
- **No more multi-entry points**: Single clean CLI via `src.cli:cli`
- **Simplified constants**: All thresholds/models in main.py top-level constants

### 🐛 Bug Fixes

- Fixed parsing failures by removing overly strict schema enforcement
- Fixed fallback model triggering (both primary and fallback now use same 32B model to avoid 404)
- Fixed exception propagation - all errors now return structured results

---

## [0.1.0] - Initial Release

- Basic pipeline with Qwen2.5-VL extraction
- Quality checks (Laplacian blur detection)
- pHash deduplication
- Simple validation logic
- Single file processing

