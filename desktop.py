"""Desktop entry point used by packaged builds (Qt shell, no console)."""

from app_config import setup_logging

setup_logging()

if __name__ == "__main__":
    import sys

    if "--self-test" in sys.argv[1:]:
        from vanish_cam import main
    else:
        from desktop_ui import run_desktop as main
    raise SystemExit(main())
