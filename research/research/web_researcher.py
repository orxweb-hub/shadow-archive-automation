import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from html import unescape
import re


REPORT_DIR = Path("research/reports")

TOPIC = "MV Joyita disappearance 1955"

RSS_SOURCES = [
    "https://news.google.com/rss/search?"
    + urllib.parse.urlencode({
        "q": TOPIC,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en"
    }),
]


def clean_text(text):
    if not text:
        return ""

    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


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
                item.findtext(
                    "description",
                    ""
                )
            )

            pub_date = clean_text(
                item.findtext(
                    "pubDate",
                    ""
                )
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


def collect_sources():

    all_articles = []

    for source in RSS_SOURCES:

        print(
            f"Kaynak okunuyor: {source}"
        )

        articles = fetch_rss(
            source
        )

        all_articles.extend(
            articles
        )

    unique = {}

    for article in all_articles:

        title = article.get(
            "title",
            ""
        ).strip().lower()

        if title and title not in unique:
            unique[title] = article

    return list(unique.values())[:20]


def build_report(topic, sources):

    confirmed_facts = []

    important_details = []

    source_list = []

    timeline = []

    for source in sources:

        title = source.get(
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

        if title:

            important_details.append(
                {
                    "title": title,
                    "description": description,
                    "published": published
                }
            )

        if url:

            source_list.append(
                {
                    "title": title,
                    "url": url
                }
            )

    report = {
        "topic": topic,

        "summary": (
            "Bu rapor, Google News RSS üzerinden "
            "toplanan kaynakların ham araştırma "
            "özetidir. Kaynaklarda bulunmayan "
            "bilgiler doğrulanmış gerçek olarak "
            "eklenmemiştir."
        ),

        "timeline": timeline,

        "people": [],

        "locations": [],

        "confirmed_facts": confirmed_facts,

        "disputed_claims": [],

        "unverified_claims": [],

        "possible_explanations": [],

        "important_details": important_details,

        "sources": source_list
    }

    return report


def main():

    print(
        "SHADOW ARCHIVE — FREE WEB RESEARCH"
    )

    print("=" * 50)

    print(
        "Gemini kullanılmadan web kaynakları "
        "toplanıyor..."
    )

    sources = collect_sources()

    print(
        f"Toplanan kaynak sayısı: {len(sources)}"
    )

    if not sources:

        raise RuntimeError(
            "Hiç web kaynağı bulunamadı."
        )

    report = build_report(
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
    print(
        "ARAŞTIRMA TAMAMLANDI"
    )

    print("=" * 50)

    print(
        f"Rapor: {output_file}"
    )

    print(
        "Gemini isteği: 0"
    )

    print("=" * 50)


if __name__ == "__main__":
    main()
