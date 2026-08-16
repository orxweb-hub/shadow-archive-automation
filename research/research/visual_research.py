import os
import json
import urllib.parse
import urllib.request
from pathlib import Path

from google import genai


SCRIPT_FILE = Path("research/scripts/mv_joyita_script.txt")
OUTPUT_DIR = Path("research/video")
CLIPS_DIR = OUTPUT_DIR / "clips"
SCENE_FILE = OUTPUT_DIR / "scenes.json"

PEXELS_API_URL = "https://api.pexels.com/videos/search"


def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    return genai.Client(api_key=api_key)


def create_scenes(client, script):

    prompt = f"""
You are a professional documentary visual director.

Channel:
Shadow Archive

Documentary topic:
MV Joyita

Below is the narration:

{script}

Break this narration into approximately 25–35 visual scenes.

For every scene return:

{{
  "scene": 1,
  "description": "",
  "search_queries": ["", "", ""],
  "mood": "",
  "duration_hint": 0
}}

Rules:

- Search queries must be suitable for stock video searches.
- Use concrete visual subjects.
- Prefer locations, oceans, ships, maps, weather, documents,
  historical atmosphere and investigative visuals.
- Do not search for abstract concepts.
- Do not invent historical footage.
- Do not claim a stock clip is actual MV Joyita footage.
- If real historical footage is unavailable, use atmospheric
  B-roll that visually represents the narration.
- Search queries should be in English because stock libraries
  generally have better English results.
- Keep queries short.
- Avoid repeating the same query excessively.
- Duration hints should generally be between 10 and 45 seconds.

Return ONLY valid JSON.

Example:

[
  {{
    "scene": 1,
    "description": "A cargo ship travelling across a dark ocean",
    "search_queries": [
      "cargo ship ocean",
      "ship at sea",
      "dark ocean waves"
    ],
    "mood": "mysterious",
    "duration_hint": 20
  }}
]
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return json.loads(text)


def search_pexels(query):

    api_key = os.environ.get("PEXELS_API_KEY")

    if not api_key:
        raise RuntimeError("PEXELS_API_KEY bulunamadı.")

    params = urllib.parse.urlencode({
        "query": query,
        "per_page": 5,
        "orientation": "landscape"
    })

    url = f"{PEXELS_API_URL}?{params}"

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": api_key,
            "User-Agent": "ShadowArchive/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    return data.get("videos", [])


def select_video(videos):

    if not videos:
        return None

    # Tercih edilen kalite:
    # yatay video + HD/Full HD
    candidates = []

    for video in videos:

        width = video.get("width", 0)
        height = video.get("height", 0)

        if width >= 1280 and height >= 720:
            candidates.append(video)

    if candidates:
        return candidates[0]

    return videos[0]


def download_video(video, output_file):

    video_files = video.get("video_files", [])

    if not video_files:
        return False

    suitable = []

    for file in video_files:

        width = file.get("width", 0)
        height = file.get("height", 0)

        if width >= 1280 and height >= 720:
            suitable.append(file)

    if not suitable:
        suitable = video_files

    selected = suitable[0]

    video_url = selected.get("link")

    if not video_url:
        return False

    request = urllib.request.Request(
        video_url,
        headers={
            "User-Agent": "ShadowArchive/1.0"
        }
    )

    with urllib.request.urlopen(request, timeout=60) as response:

        with open(output_file, "wb") as file:

            while True:

                chunk = response.read(1024 * 1024)

                if not chunk:
                    break

                file.write(chunk)

    return True


def main():

    print("SHADOW ARCHIVE — VISUAL RESEARCH")
    print("=" * 60)

    if not SCRIPT_FILE.exists():
        raise FileNotFoundError(
            f"Senaryo bulunamadı: {SCRIPT_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    CLIPS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    script = SCRIPT_FILE.read_text(
        encoding="utf-8"
    )

    client = get_gemini_client()

    print("Sahneler oluşturuluyor...")

    scenes = create_scenes(
        client,
        script
    )

    print(f"Oluşturulan sahne sayısı: {len(scenes)}")

    SCENE_FILE.write_text(
        json.dumps(
            scenes,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("Pexels görüntüleri aranıyor...")

    results = []

    for index, scene in enumerate(scenes, start=1):

        queries = scene.get(
            "search_queries",
            []
        )

        video = None
        used_query = None

        for query in queries:

            print(
                f"[{index}/{len(scenes)}] "
                f"Aranıyor: {query}"
            )

            videos = search_pexels(query)

            video = select_video(videos)

            if video:
                used_query = query
                break

        if not video:

            print("  Görüntü bulunamadı.")
            continue

        filename = (
            CLIPS_DIR /
            f"scene_{index:03d}.mp4"
        )

        print(
            f"  İndiriliyor: {filename.name}"
        )

        success = download_video(
            video,
            filename
        )

        if success:

            results.append({
                "scene": index,
                "query": used_query,
                "file": str(filename),
                "pexels_id": video.get("id"),
                "duration_hint": scene.get(
                    "duration_hint",
                    20
                )
            })

    result_file = OUTPUT_DIR / "visual_assets.json"

    result_file.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 60)
    print("GÖRÜNTÜ TOPLAMA TAMAMLANDI")
    print("=" * 60)
    print(f"Sahneler: {SCENE_FILE}")
    print(f"Görüntüler: {CLIPS_DIR}")
    print(f"Sonuç: {result_file}")
    print(f"Toplam indirilen klip: {len(results)}")


if __name__ == "__main__":
    main()
