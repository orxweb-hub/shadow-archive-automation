import os
import json
from google import genai

CHANNEL_NAME = "Shadow Archive"


def research_topic(topic):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the research engine for the YouTube documentary channel "{CHANNEL_NAME}".

Research this topic:

{topic}

Create a factual research report for a documentary.

Return ONLY valid JSON with this structure:

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
- Clearly separate confirmed facts from disputed or unverified claims.
- Do not present rumors as facts.
- Prefer official records, reputable journalism, academic sources,
  books, archives and primary documents.
- If a detail cannot be confidently established, put it in
  "unverified_claims".
- The report will later be used to write an original documentary script.
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
    topic = """
The Ghost Ship That Kept Its Secrets:
What Happened to the MV Joyita?
"""

    report = research_topic(topic)

    print("\nSHADOW ARCHIVE — SOURCE RESEARCH")
    print("=" * 45)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
