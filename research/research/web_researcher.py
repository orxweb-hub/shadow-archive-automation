import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from html import unescape
import re

TOPIC_FILE = Path("research/current_topic.json")
REPORT_DIR = Path("research/reports")


def clean_text(text):
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_current_topic():
    if not TOPIC_FILE.exists():
        raise FileNotFoundError(
            f"Güncel konu dosyası bulunamadı: {TOPIC_FILE}"
        )

    data = json.loads(
        TOPIC_FILE.read_text(encoding="utf-8")
    )

    topic = data.get("topic")

    if not topic:
        raise RuntimeError(
            "current_topic.json içinde topic bulunamadı."
        )

    return data


def create_rss_url(topic):
    return (
        "https://news.google.com/rss/search?"
        + urllib.parse.urlencode({
            "q": topic,
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en"
        })
    )


def fetch_rss(url):
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:
            data = response.read()

        root = ET.fromstring(data)
        articles = []

        for item in root.findall(".//item"):
            title = clean_text(
                item.findtext("title", "")
            )

            link = item.findtext(
                "link",
                ""
            ).strip()

            description = clean_text(
                item.findtext("description", "")
            )

            pub_date = clean_text(
                item.findtext("pubDate", "")
            )

            if title:
                articles.append({
                    "title": title,
                    "url": link,
                    "description": description,
                    "published": pub_date
                })

        return articles

    except Exception as error:
        print(
            f"RSS kaynağı okunamadı: {url}"
        )
        print(error)
        return []


def collect_sources(topic):
    rss_url = create_rss_url(topic)

    print("Araştırma konusu:")
    print(topic)
    print()

    print("Kaynak okunuyor:")
    print(rss_url)

    articles = fetch_rss(rss_url)

    unique = {}

    for article in articles:
        title = article.get(
            "title",
            ""
        ).strip().lower()

        if title and title not in unique:
            unique[title] = article

    return list(unique.values())[:20]


def build_report(topic_data, sources):
    topic = topic_data.get(
        "topic",
        ""
    )

    category = topic_data.get(
        "category",
        ""
    )

    summary = topic_data.get(
        "summary",
        ""
    )

    research_points = topic_data.get(
        "research_points",
        []
    )

    title = topic_data.get(
        "title",
        ""
    )

    important_details = []
    source_list = []

    for source in sources:
        title_text = source.get(
            "title",
            ""
        )

        description = source.get(
            "description",
            ""
        )

        url = source.get(
            "url",
            ""
        )

        published = source.get(
            "published",
            ""
        )

        if title_text:
            important_details.append({
                "title": title_text,
                "description": description,
                "published": published
            })

        if url:
            source_list.append({
                "title": title_text,
                "url": url
            })

    return {
        "topic": topic,
        "category": category,
        "suggested_title": title,
        "topic_summary": summary,
        "research_points": research_points,

        "summary": (
            "Bu rapor, günlük konu için "
            "Google News RSS üzerinden "
            "toplanan kaynakları içerir. "
            "RSS sonuçları ham araştırma "
            "verisi olarak değerlendirilmelidir."
        ),

        "timeline": [],
        "people": [],
        "locations": [],
        "confirmed_facts": [],
        "disputed_claims": [],
        "unverified_claims": [],
        "possible_explanations": [],

        "important_details": important_details,
        "sources": source_list
    }


def create_filename(topic):
    filename = topic.lower()

    filename = re.sub(
        r"[^a-z0-9]+",
        "_",
        filename
    )

    filename = filename.strip("_")

    if not filename:
        filename = "daily_topic"

    return (
        filename[:80]
        + "_web_research.json"
    )


def save_report(topic, report):
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = create_filename(topic)
    report_file = REPORT_DIR / filename

    report_file.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return report_file


def main():
    print(
        "SHADOW ARCHIVE — FREE WEB RESEARCH"
    )

    print("=" * 60)

    print(
        "Gemini kullanılmadan "
        "güncel konu araştırılıyor..."
    )

    print()

    topic_data = load_current_topic()
    topic = topic_data["topic"]

    print("CURRENT TOPIC:")
    print(topic)
    print()

    sources = collect_sources(topic)

    print()

    print(
        f"Toplanan kaynak sayısı: {len(sources)}"
    )

    print()

    report = build_report(
        topic_data,
        sources
    )

    report_file = save_report(
        topic,
        report
    )

    print(
        "WEB RESEARCH TAMAMLANDI"
    )

    print(
        f"Rapor: {report_file}"
    )

    print(
        f"Kaynak sayısı: {len(sources)}"
    )


if __name__ == "__main__":
    main()
