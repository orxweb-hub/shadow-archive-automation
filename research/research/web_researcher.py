import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from google import genai
import os


REPORT_DIR = Path("research/reports")

TOPIC = "MV Joyita disappearance 1955"


RSS_SOURCES = [
    "https://news.google.com/rss/search?q=MV+Joyita",
    "https://www.google.com/alerts/feeds/00000000000000000000",
]


def fetch_rss(url):
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read()

        root = ET.fromstring(data)

        articles = []

        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            description = item.findtext("description", "")

            if title:
                articles.append({
                    "title": title,
                    "url": link,
                    "description": description
                })

        return articles

    except Exception as e:
        print(f"RSS kaynağı okunamadı: {url}")
        print(e)
        return []


def collect_sources():
    all_articles = []

    for source in RSS_SOURCES:
        articles = fetch_rss(source)
        all_articles.extend(articles)

    # Aynı başlıkları temizle
    unique = {}
    for article in all_articles:
        unique[article["title"]] = article

    return list(unique.values())[:20]


def research_with_gemini(topic, sources):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    source_text = json.dumps(
        sources,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are the factual research engine for the YouTube documentary
channel "Shadow Archive".

Research topic:

{topic}

Below are web sources collected externally.

SOURCE MATERIAL:
{source_text}

Create a factual research report.

Return ONLY valid JSON:

{{
  "topic": "",
  "summary": "",
  "timeline": [],
  "people": [],
  "locations": [],
  "confirmed_facts": [],
  "disputed_claims": [],
  "unverified_claims": [],
  "possible_explanations": [],
  "important_details": [],
  "sources": []
}}

Rules:

- Use only information supported by the supplied sources.
- Never invent facts.
- Never present rumors as confirmed facts.
- Clearly separate confirmed facts from theories.
- If the sources are insufficient, say so.
- Keep source URLs.
- Do not write a documentary script.
- This is a research report only.
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


def main():
    print("SHADOW ARCHIVE — FREE WEB RESEARCH")
    print("=" * 50)

    print("Web kaynakları toplanıyor...")

    sources = collect_sources()

    print(f"Toplanan kaynak sayısı: {len(sources)}")

    if not sources:
        raise RuntimeError(
            "Hiç web kaynağı bulunamadı."
        )

    print("Gemini kaynakları analiz ediyor...")

    report = research_with_gemini(
        TOPIC,
        sources
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        REPORT_DIR /
        "mv_joyita_web_research.json"
    )

    output_file.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("ARAŞTIRMA TAMAMLANDI")
    print("=" * 50)
    print(f"Rapor: {output_file}")


if __name__ == "__main__":
    main()
