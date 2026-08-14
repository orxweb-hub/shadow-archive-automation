import os
import json
from pathlib import Path
from google import genai

REPORT_DIR = Path("research/reports")

TOPIC = """
The Ghost Ship That Kept Its Secrets:
What Happened to the MV Joyita?
"""


def research_topic(topic):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the factual research engine for the YouTube documentary
channel "Shadow Archive".

Research this topic:

{topic}

Create a detailed factual research report.

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
  "source_types_to_check": []
}}

Rules:
- Never invent facts.
- Separate confirmed facts from disputed claims.
- Never present rumors as facts.
- If something is uncertain, put it under unverified_claims.
- Prefer official records, reputable journalism, academic sources,
  archives, books and primary documents.
- This report will later be used to create an original documentary.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)


def main():
    report = research_topic(TOPIC)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_file = REPORT_DIR / "mv_joyita.json"

    report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("SHADOW ARCHIVE — RESEARCH REPORT")
    print("=" * 45)
    print(f"Rapor kaydedildi: {report_file}")
    print()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
