import os
import json
from pathlib import Path

from google import genai
from google.genai import types

REPORT_DIR = Path("research/reports")

TOPIC = """
The Ghost Ship That Kept Its Secrets:
What Happened to the MV Joyita?
"""


def research_with_web(topic):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the web research engine for the documentary YouTube channel
"Shadow Archive".

Research this real historical mystery:

{topic}

Use Google Search to find reliable web sources.

PRIORITY:
1. Official government records
2. National libraries and archives
3. Primary documents
4. Academic sources
5. Reputable journalism
6. Established historical references

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
  "sources": [
    {{
      "title": "",
      "url": "",
      "why_relevant": ""
    }}
  ]
}}

RULES:
- Search the web before answering.
- Never invent facts.
- Never treat rumors as confirmed facts.
- Separate confirmed facts, disputed claims and unverified claims.
- Prefer primary and official sources.
- Include source URLs whenever available.
- If reliable sources disagree, explain the disagreement.
- Do not write a documentary script.
- This is a research report only.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(
                google_search=types.GoogleSearch()
            )]
        )
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)


def main():
    report = research_with_web(TOPIC)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = REPORT_DIR / "mv_joyita_web_research.json"

    output_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("SHADOW ARCHIVE — WEB RESEARCH")
    print("=" * 50)
    print(f"Rapor kaydedildi: {output_file}")
    print()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
