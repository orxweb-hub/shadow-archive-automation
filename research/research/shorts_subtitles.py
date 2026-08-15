import json
from pathlib import Path

SELECTION_FILE = Path("research/video/shorts_selection.json")
OUTPUT_DIR = Path("research/video/subtitles")


def main():

    print("=" * 60)
    print("SHADOW ARCHIVE — ENGLISH SUBTITLES")
    print("=" * 60)

    if not SELECTION_FILE.exists():
        raise FileNotFoundError(
            "shorts_selection.json bulunamadı."
        )

    data = json.loads(
        SELECTION_FILE.read_text(
            encoding="utf-8"
        )
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for short in data["shorts"]:

        number = short["short"]

        # Shorts seçiminde İngilizce metin
        # daha sonra eklenecek.
        english = short.get(
            "english_script",
            ""
        ).strip()

        if not english:
            print(
                f"Short {number}: "
                "İngilizce metin henüz bulunmuyor."
            )

            continue

        output_file = (
            OUTPUT_DIR /
            f"short_{number}_english.txt"
        )

        output_file.write_text(
            english,
            encoding="utf-8"
        )

        print(
            f"Short {number} altyazısı hazır."
        )

    print()
    print("=" * 60)
    print("ENGLISH SUBTITLE FILES HAZIR")
    print("=" * 60)


if __name__ == "__main__":
    main()
