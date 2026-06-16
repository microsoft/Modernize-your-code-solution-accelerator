from pathlib import Path
import subprocess


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    cmd = ["python", "-m", "pip", "--version"]
    return subprocess.call(cmd, cwd=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
