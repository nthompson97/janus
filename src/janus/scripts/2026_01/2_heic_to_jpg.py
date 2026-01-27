import logging
from PIL import Image
import pillow_heif
from pathlib import Path

SRC = Path("/data/Bimba")
DEST = Path("/data/filtered")


def heic_to_jpg(heic_fp: Path, jpg_fp: Path) -> None:
    if heic_fp.exists():
        logging.info(f"Filepath exists, continuing: {heic_fp}")

    else:
        image = Image(heic_fp)
        image.convert("RGB").save(jpg_fp, "JPEG", quality=100)

        logging.info(f"Created new file:             {jpg_fp}")


def main() -> None:
    pillow_heif.register_heif_opener()

    for filepath in SRC.glob("**/*.HEIC"):
        target_filepath = DEST / filepath.relative_to(SRC).with_suffix(".jpg")
        target_filepath.parent.mkdir(parent=True, exist_ok=True)
        print(filepath, target_filepath)


if __name__ == "__main__":
    main()
