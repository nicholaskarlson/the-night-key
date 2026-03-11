from __future__ import annotations

import argparse
from pathlib import Path

from btg.gallery import build_gallery


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build deterministic story pack gallery.")
    p.add_argument(
        "--stories",
        default="stories",
        help="Stories source folder (default: stories/).",
    )
    p.add_argument(
        "--out",
        default="dist/packs",
        help="Output folder (default: dist/packs/).",
    )
    args = p.parse_args(argv)

    index_path = build_gallery(Path(args.stories), Path(args.out))
    print(f"Wrote: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
