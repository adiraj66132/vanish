"""Write PyInstaller's Windows VERSIONINFO resource from app_config.__version__."""

from pathlib import Path
import sys

# Running this script as `packaging/write_version.py` puts packaging/ (not the
# project root) on sys.path, so make the root importable explicitly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_config import __version__


def main() -> None:
    numbers = [int(part) for part in __version__.split(".")]
    numbers += [0] * (4 - len(numbers))
    version = ",".join(str(number) for number in numbers)
    text = (
        "VSVersionInfo(\n"
        f"  ffi=FixedFileInfo(filevers=({version}), prodvers=({version}),\n"
        "  mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),\n"
        "  kids=[StringFileInfo([StringTable('040904E4', [\n"
        "    StringStruct('CompanyName', 'Vanish Lab'),\n"
        "    StringStruct('FileDescription', 'VanishCam'),\n"
        f"    StringStruct('FileVersion', '{__version__}.0'),\n"
        "    StringStruct('ProductName', 'VanishCam'),\n"
        f"    StringStruct('ProductVersion', '{__version__}.0')\n"
        "  ])]), VarFileInfo([VarStruct('Translation', [1033, 1252])])]\n"
        ")\n"
    )
    path = ROOT / "build" / "version_info.txt"
    path.parent.mkdir(exist_ok=True)
    path.write_text(text, encoding="utf-8")
    version_iss = ROOT / "installer" / "version.iss"
    version_iss.parent.mkdir(exist_ok=True)
    version_iss.write_text(
        f'#define AppVersion "{__version__}"\n', encoding="utf-8"
    )


if __name__ == "__main__":
    main()
