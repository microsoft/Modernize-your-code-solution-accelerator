from pathlib import Path


def main() -> int:
    data_root = Path(__file__).resolve().parents[3] / "data"
    print(f"Data root available at: {data_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
