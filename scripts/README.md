# Scripts

## batch_process.sh

Automates batch processing of all images in a directory.

### Usage

```bash
# Default: processes data/uploads → outputs/
./scripts/batch_process.sh

# Custom paths
./scripts/batch_process.sh /path/to/images /path/to/outputs
```

### Requirements

- Virtual environment activated with dependencies installed
- `FIREWORKS_API_KEY` set (via .env or environment variable)

### Output

- Individual JSON files for each image
- `summary.json` with batch statistics (success/failure counts)

