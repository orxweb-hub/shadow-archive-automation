import os
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
import re

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


# ==========================================
# GEMINI MODELS
# ==========================================

PRIMARY_GEMINI_MODEL = (
    "gemini-3.6-flash"
)

FALLBACK_GEMINI_MODEL = (
    "gemini-3.5-flash-lite"
)

MAX_GEMINI_RETRIES = 5

RETRY_DELAYS = [
    30,
    60,
    120,
    180,
    300
]


# ==========================================
# PEXELS FALLBACK QUERIES
# ==========================================

GENERIC_PEXELS_QUERIES = [
    "cinematic documentary",
    "cinematic nature",
    "dramatic landscape",
    "ocean waves",
    "storm ocean",
    "dark clouds",
    "night ocean",
    "coastline",
    "mysterious landscape",
    "documentary b roll"
]


def create_safe_filename(text):

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


# ==========================================
# GEMINI ERROR DETECTION
# ==========================================

def is_quota_error(error):

    error_text = str(error).lower()

    return (
        "429" in error_text
        or
        "resource_exhausted" in error_text
        or
        "quota" in error_text
        or
        "rate limit" in error_text
    )


def is_temporary_error(error):

    error_text = str(error).lower()

    return (
        "500" in error_text
        or
        "503" in error_text
        or
        "unavailable" in error_text
        or
        "internal" in error_text
        or
        "high demand" in error_text
    )


# ==========================================
# GEMINI SCENE GENERATION
# ==========================================

def generate_scenes_with_model(
    client,
    prompt,
    model
):

    for attempt in range(
        1,
        MAX_GEMINI_RETRIES + 1
    ):

        try:

            print()
            print(
                "Gemini Visual Research"
            )

            print(
                f"Model: {model}"
            )

            print(
                f"Deneme: "
                f"{attempt}/{MAX_GEMINI_RETRIES}"
            )

            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            text = (
                response.text.strip()
                if response.text
                else ""
            )

            if not text:

                raise RuntimeError(
                    "Gemini boş cevap döndürdü."
                )

            # Markdown JSON bloklarını temizle
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

            print()
            print(
                "Gemini Visual Research başarılı."
            )

            print(
                f"Model: {model}"
            )

            print(
                f"Sahne sayısı: {len(scenes)}"
            )

            return scenes

        except Exception as error:

            print()
            print(
                "Gemini hatası:"
            )

            print(error)

            # Kota hatasında bu modeli bırak.
            # create_scenes() fallback modele geçecek.
            if is_quota_error(error):

                print()
                print(
                    f"⚠️ {model} "
                    "kota/rate limit hatası."
                )

                raise

            # Geçici Google API hataları
            if is_temporary_error(error):

                if attempt == MAX_GEMINI_RETRIES:

                    raise RuntimeError(
                        f"{model} geçici hatalar "
                        "nedeniyle başarısız oldu."
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

                continue

            # Diğer hatalarda tekrar dene
            if attempt == MAX_GEMINI_RETRIES:

                raise RuntimeError(
                    f"{model} Visual Research "
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

    raise RuntimeError(
        f"{model} sahne üretimini tamamlayamadı."
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
- keep search queries short and concrete
- prefer 2-5 English keywords per search query

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

    # ==========================================
    # 1. GEMINI 3.6
    # ==========================================

    try:

        print()
        print(
            "=========================================="
        )

        print(
            "1. GEMINI MODELİ"
        )

        print(
            PRIMARY_GEMINI_MODEL
        )

        print(
            "=========================================="
        )

        return generate_scenes_with_model(
            client,
            prompt,
            PRIMARY_GEMINI_MODEL
        )

    except Exception as primary_error:

        if not is_quota_error(
            primary_error
        ):

            raise

        # ======================================
        # 2. GEMINI 3.5 FALLBACK
        # ======================================

        print()
        print(
            "=========================================="
        )

        print(
            "⚠️ 3.6 FLASH KOTASI DOLU"
        )

        print(
            "🔄 OTOMATİK FALLBACK"
        )

        print(
            f"{PRIMARY_GEMINI_MODEL}"
            " → "
            f"{FALLBACK_GEMINI_MODEL}"
        )

        print(
            "=========================================="
        )

        try:

            return generate_scenes_with_model(
                client,
                prompt,
                FALLBACK_GEMINI_MODEL
            )

        except Exception as fallback_error:

            if is_quota_error(
                fallback_error
            ):

                raise RuntimeError(
                    "Hem Gemini 3.6 Flash hem de "
                    "Gemini 3.5 Flash Lite kota/"
                    "rate limit nedeniyle "
                    "kullanılamıyor."
                ) from fallback_error

            raise


# ==========================================
# PEXELS SEARCH
# ==========================================

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
            "Authorization": api_key,
            "User-Agent": "ShadowArchive/1.0"
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
            and
            height >= 720
        ):

            valid_files.append(
                file
            )

    # 720p+ yoksa mevcut herhangi bir
    # kullanılabilir dosyayı kabul et.
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

    if not data:

        raise RuntimeError(
            "Pexels video dosyası boş."
        )

    output.write_bytes(
        data
    )

    if not output.exists():

        raise RuntimeError(
            f"Video indirilemedi: {output}"
        )

    if output.stat().st_size < 10000:

        raise RuntimeError(
            f"İndirilen video dosyası geçersiz: "
            f"{output}"
        )


# ==========================================
# PEXELS FALLBACK SEARCH
# ==========================================

def build_fallback_queries(
    original_query,
    scene
):

    queries = []

    if original_query:

        queries.append(
            original_query.strip()
        )

        # Çok uzun sorguları sadeleştir.
        words = original_query.split()

        if len(words) > 3:

            queries.append(
                " ".join(words[:3])
            )

    visual_description = (
        scene.get(
            "visual_description",
            ""
        )
        .strip()
    )

    if visual_description:

        words = re.findall(
            r"[A-Za-z]+",
            visual_description
        )

        if words:

            queries.append(
                " ".join(words[:4])
            )

    queries.extend(
        GENERIC_PEXELS_QUERIES
    )

    # Aynı sorguları kaldır.
    unique_queries = []

    seen = set()

    for query in queries:

        clean_query = (
            query
            .strip()
            .lower()
        )

        if not clean_query:

            continue

        if clean_query in seen:

            continue

        seen.add(
            clean_query
        )

        unique_queries.append(
            query.strip()
        )

    return unique_queries


def find_pexels_video(
    scene,
    api_key
):

    original_query = scene.get(
        "search_query",
        ""
    ).strip()

    queries = build_fallback_queries(
        original_query,
        scene
    )

    for attempt, query in enumerate(
        queries,
        start=1
    ):

        print(
            f"   Pexels arama "
            f"{attempt}/{len(queries)}: "
            f"{query}"
        )

        try:

            result = search_pexels(
                query,
                api_key
            )

            videos = result.get(
                "videos",
                []
            )

            if not videos:

                print(
                    "   → Sonuç yok."
                )

                continue

            for video in videos:

                selected = select_video(
                    video
                )

                if selected:

                    print(
                        "   → Video bulundu."
                    )

                    return (
                        selected,
                        query
                    )

            print(
                "   → Uygun çözünürlükte "
                "video yok."
            )

        except Exception as error:

            print(
                f"   → Pexels hatası: {error}"
            )

    return (
        None,
        None
    )


# ==========================================
# MAIN
# ==========================================

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

    print()

    topic = load_current_topic()

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

    # ==========================================
    # ESKİ KLİPLERİ TEMİZLE
    # ==========================================

    old_clips = list(
        CLIPS_DIR.glob("*.mp4")
    )

    if old_clips:

        print()
        print(
            f"{len(old_clips)} eski klip temizleniyor..."
        )

    for old_file in old_clips:

        old_file.unlink()

    downloaded_scenes = []

    # ==========================================
    # PEXELS VIDEO RESEARCH
    # ==========================================

    print()
    print(
        "=========================================="
    )

    print(
        "PEXELS VIDEO ARAŞTIRMASI"
    )

    print(
        "=========================================="
    )

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
            f"[{index}/{len(scenes)}]"
        )

        print(
            f"İlk sorgu: {query}"
        )

        try:

            selected, used_query = (
                find_pexels_video(
                    scene,
                    pexels_key
                )
            )

            if not selected:

                print(
                    "❌ Bu sahne için video bulunamadı."
                )

                continue

            output = (
                CLIPS_DIR /
                f"scene_{index:03d}.mp4"
            )

            print(
                f"Video indiriliyor:"
            )

            print(output)

            download_video(
                selected,
                output
            )

            downloaded_scenes.append({

                "scene_number": index,

                "search_query":
                    used_query,

                "original_search_query":
                    query,

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

            print(
                "✅ Klip başarıyla kaydedildi."
            )

        except Exception as error:

            print(
                f"❌ Video alınamadı: {error}"
            )

    # ==========================================
    # SAVE SCENES
    # ==========================================

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

    # ==========================================
    # FINAL VALIDATION
    # ==========================================

    actual_clips = sorted(
        CLIPS_DIR.glob("*.mp4")
    )

    print()
    print(
        "=========================================="
    )

    print(
        "PEXELS SONUÇ"
    )

    print(
        "=========================================="
    )

    print(
        f"Toplam Gemini sahnesi: "
        f"{len(scenes)}"
    )

    print(
        f"Başarılı Pexels klibi: "
        f"{len(actual_clips)}"
    )

    print(
        f"Başarısız/atlanmış sahne: "
        f"{len(scenes) - len(actual_clips)}"
    )

    # Hiç klip yoksa Cinematic Editor'e
    # boş klasör gönderme.
    if len(actual_clips) == 0:

        raise RuntimeError(
            "PEXELS'TEN HİÇ VİDEO KLİBİ ALINAMADI. "
            "Tüm alternatif aramalar başarısız oldu."
        )

    # En az birkaç gerçek klip olması daha sağlıklı.
    if len(actual_clips) < 3:

        print()
        print(
            "⚠️ UYARI:"
        )

        print(
            "Yalnızca "
            f"{len(actual_clips)} "
            "klip bulundu."
        )

        print(
            "Cinematic Video Editor "
            "bu klipleri tekrar kullanabilir."
        )

    print()
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
        f"{len(actual_clips)}"
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
