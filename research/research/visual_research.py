import os
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from google import genai


TOPIC_FILE = Path(
    "research/current_topic.json"
)

SCRIPT_DIR = Path(
    "research/scripts"
)

OUTPUT_DIR = Path(
    "research/video"
)

CLIPS_DIR = OUTPUT_DIR / "clips"

SCENE_FILE = OUTPUT_DIR / "scenes.json"

PEXELS_API_URL = (
    "https://api.pexels.com/videos/search"
)

GEMINI_MODEL = "gemini-3.6-flash"

MAX_GEMINI_RETRIES = 5

RETRY_DELAYS = [
    30,
    60,
    120,
    180,
    300
]


def create_safe_filename(text):

    import re

    filename = text.lower()

    filename = re.sub(
        r"[^a-z0-9]+",
        "_",
        filename
    )

    filename = filename.strip("_")

    if not filename:
        filename = "daily_topic"

    return filename[:80]


def load_current_topic():

    if not TOPIC_FILE.exists():

        raise FileNotFoundError(
            f"Güncel konu bulunamadı: {TOPIC_FILE}"
        )

    data = json.loads(
        TOPIC_FILE.read_text(
            encoding="utf-8"
        )
    )

    topic = data.get("topic")

    if not topic:

        raise RuntimeError(
            "current_topic.json içinde topic bulunamadı."
        )

    return topic


def find_script(topic):

    safe_name = create_safe_filename(
        topic
    )

    expected_file = (
        SCRIPT_DIR /
        f"{safe_name}_script.txt"
    )

    if expected_file.exists():

        return expected_file

    scripts = list(
        SCRIPT_DIR.glob(
            "*_script.txt"
        )
    )

    if not scripts:

        raise FileNotFoundError(
            "Hiçbir senaryo dosyası bulunamadı."
        )

    scripts.sort(
        key=lambda file: file.stat().st_mtime,
        reverse=True
    )

    return scripts[0]


def get_gemini_client():

    api_key = os.environ.get(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GEMINI_API_KEY bulunamadı."
        )

    return genai.Client(
        api_key=api_key
    )


def create_scenes(
    client,
    script
):

    prompt = f"""
You are a professional documentary visual researcher.

Analyze the following Turkish documentary script.

Create 25-35 visual scenes.

For each scene return:

- scene_number
- narration_summary
- visual_description
- search_query

IMPORTANT:

- search_query must be in English
- search_query must work well with the Pexels video API
- prefer cinematic landscape, ocean, ship, storm, night,
  archival atmosphere, abandoned places, maps, waves,
  clouds, coastline and documentary B-roll
- adapt the visuals to the actual story
- do NOT claim that stock footage is actual historical footage
- visuals are atmospheric B-roll only
- avoid copyrighted movie footage
- avoid logos and text-heavy footage
- avoid repeating the same visual idea unnecessarily

Return ONLY valid JSON.

JSON format:

[
  {{
    "scene_number": 1,
    "narration_summary": "...",
    "visual_description": "...",
    "search_query": "..."
  }}
]

DOCUMENTARY SCRIPT:

{script}
"""

    for attempt in range(
        1,
        MAX_GEMINI_RETRIES + 1
    ):

        try:

            print(
                "Gemini Visual Research "
                f"denemesi {attempt}/"
                f"{MAX_GEMINI_RETRIES}"
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            text = response.text.strip()

            if text.startswith("```"):

                text = text.replace(
                    "```json",
                    ""
                )

                text = text.replace(
                    "```",
                    ""
                )

                text = text.strip()

            scenes = json.loads(
                text
            )

            if not isinstance(
                scenes,
                list
            ):

                raise ValueError(
                    "Gemini geçerli bir "
                    "sahne listesi döndürmedi."
                )

            if len(scenes) < 10:

                raise ValueError(
                    "Gemini yeterli sayıda "
                    "sahne üretmedi."
                )

            print(
                "Gemini Visual Research başarılı."
            )

            return scenes

        except Exception as error:

            error_text = str(error)

            print()
            print(
                "Gemini hatası:"
            )
            print(error)

            if (
                "429" in error_text
                or "RESOURCE_EXHAUSTED"
                in error_text
                or "quota"
                in error_text.lower()
            ):

                raise RuntimeError(
                    "Gemini günlük ücretsiz "
                    "kotası doldu. Visual "
                    "Research durduruldu."
                ) from error

            if attempt == MAX_GEMINI_RETRIES:

                raise RuntimeError(
                    "Gemini Visual Research "
                    "5 denemede de başarısız oldu."
                ) from error

            delay = RETRY_DELAYS[
                attempt - 1
            ]

            print(
                f"{delay} saniye bekleniyor "
                "ve tekrar deneniyor..."
            )

            time.sleep(
                delay
            )


def search_pexels(
    query,
    api_key
):

    params = urllib.parse.urlencode({

        "query": query,

        "per_page": 5,

        "orientation": "landscape",

        "size": "large"

    })

    request = urllib.request.Request(

        f"{PEXELS_API_URL}?{params}",

        headers={
            "Authorization": api_key
        }

    )

    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        return json.loads(
            response.read().decode(
                "utf-8"
            )
        )


def select_video(video):

    files = video.get(
        "video_files",
        []
    )

    valid_files = []

    for file in files:

        width = file.get(
            "width"
        ) or 0

        height = file.get(
            "height"
        ) or 0

        link = file.get(
            "link"
        )

        if not link:
            continue

        if (
            width >= 1280
            and height >= 720
        ):

            valid_files.append(
                file
            )

    if not valid_files:

        for file in files:

            if file.get("link"):

                valid_files.append(
                    file
                )

    if not valid_files:

        return None

    valid_files.sort(

        key=lambda x:
        (
            x.get("width", 0)
            *
            x.get("height", 0)
        ),

        reverse=True

    )

    return valid_files[0]["link"]


def download_video(
    url,
    output
):

    request = urllib.request.Request(

        url,

        headers={
            "User-Agent": "Mozilla/5.0"
        }

    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:

        data = response.read()

    output.write_bytes(
        data
    )


def main():

    print(
        "=========================================="
    )

    print(
        "SHADOW ARCHIVE VISUAL RESEARCH"
    )

    print(
        "=========================================="
    )

    topic = load_current_topic()

    print()
    print(
        "GÜNCEL KONU:"
    )
    print(topic)

    print()

    script_file = find_script(
        topic
    )

    print(
        "SENARYO:"
    )
    print(script_file)

    print()

    pexels_key = os.environ.get(
        "PEXELS_API_KEY"
    )

    if not pexels_key:

        raise RuntimeError(
            "PEXELS_API_KEY bulunamadı."
        )

    script = script_file.read_text(
        encoding="utf-8"
    )

    if not script.strip():

        raise RuntimeError(
            "Senaryo dosyası boş."
        )

    client = get_gemini_client()

    print(
        "Gemini sahneleri oluşturuyor..."
    )

    scenes = create_scenes(
        client,
        script
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CLIPS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for old_file in CLIPS_DIR.glob(
        "*.mp4"
    ):

        old_file.unlink()

    downloaded_scenes = []

    for index, scene in enumerate(
        scenes,
        start=1
    ):

        query = scene.get(
            "search_query",
            "cinematic documentary"
        )

        print()

        print(
            f"[{index}/{len(scenes)}] "
            f"Pexels: {query}"
        )

        try:

            result = search_pexels(
                query,
                pexels_key
            )

            videos = result.get(
                "videos",
                []
            )

            if not videos:

                print(
                    "Video bulunamadı."
                )

                continue

            selected = None

            for video in videos:

                selected = select_video(
                    video
                )

                if selected:
                    break

            if not selected:

                print(
                    "Uygun video bulunamadı."
                )

                continue

            output = (
                CLIPS_DIR /
                f"scene_{index:03d}.mp4"
            )

            print(
                f"Video indiriliyor: "
                f"{output}"
            )

            download_video(
                selected,
                output
            )

            downloaded_scenes.append({

                "scene_number": index,

                "search_query": query,

                "file": str(output),

                "visual_description":
                    scene.get(
                        "visual_description",
                        ""
                    ),

                "narration_summary":
                    scene.get(
                        "narration_summary",
                        ""
                    )

            })

        except Exception as error:

            print(
                f"Video alınamadı: {error}"
            )

    SCENE_FILE.write_text(

        json.dumps(
            scenes,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"

    )

    visual_assets_file = (
        OUTPUT_DIR /
        "visual_assets.json"
    )

    visual_assets_file.write_text(

        json.dumps(
            downloaded_scenes,
            ensure_ascii=False,
            indent=2
        ),

        encoding="utf-8"

    )

    print()
    print(
        "=========================================="
    )

    print(
        "VISUAL RESEARCH TAMAMLANDI"
    )

    print(
        "=========================================="
    )

    print(
        f"Konu: {topic}"
    )

    print(
        f"Toplam sahne: {len(scenes)}"
    )

    print(
        f"İndirilen klip: "
        f"{len(downloaded_scenes)}"
    )

    print(
        f"Scenes: {SCENE_FILE}"
    )

    print(
        f"Visual assets: "
        f"{visual_assets_file}"
    )

    print(
        "=========================================="
    )


if __name__ == "__main__":
    main()
