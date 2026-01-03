from __future__ import annotations

import argparse
import asyncio

from .main import main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fireworks KYC PoV pipeline runner.")
    parser.add_argument(
        "--image",
        help="Path to single image file (JPG/PNG/etc.).",
    )
    parser.add_argument(
        "--batch",
        help="Path to directory for batch processing all images.",
    )
    parser.add_argument(
        "--mime",
        help="Optional MIME type override (e.g., image/jpeg). Otherwise inferred by file extension.",
    )
    parser.add_argument(
        "--output",
        help="Output path: single JSON file (--image) or directory (--batch). Defaults to 'outputs/' for batch.",
    )
    return parser


def cli() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(
        main(
            image_path=args.image,
            batch_dir=args.batch,
            mime=args.mime,
            output_path=args.output,
        )
    )

