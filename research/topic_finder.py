import os
import json
from google import genai

CHANNEL_NAME = "Shadow Archive"


def find_topics(count=10):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the topic discovery engine for the YouTube channel "{CHANNEL_NAME}".

The channel focuses on:
- unexplained mysteries
- unsolved cases
- strange historical events
- mysterious places
- unexplained discoveries
- forgotten stories

Generate {count} ORIGINAL video topic ideas.

For every topic provide:
1. title_idea
2. subject
3. why_viewers_would_click
4. long_video_potential
5. shorts_potential
6. research_difficulty

Important:
- Do not invent real events.
- Do not present rumors as facts.
- Avoid topics that are extremely overused unless there is a genuinely new angle.
- Prefer stories that can support a 15+ minute documentary-style video.
- Prefer topics with strong curiosity and storytelling potential.

Return ONLY valid JSON in this format:

[
  {{
    "title_idea": "...",
    "subject": "...",
    "why_viewers_would_click": "...",
    "long_video_potential": 1,
    "shorts_potential": 1,
    "research_difficulty": 1
  }}
]
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    text = response.text.strip()

    # Markdown kod bloğu gelirse temizle
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)


def main():
    topics = find_topics(10)

    print("\nSHADOW ARCHIVE — TOPIC DISCOVERY")
    print("=" * 45)

    for number, topic in enumerate(topics, start=1):
        print(f"\n{number}. {topic['title_idea']}")
        print(f"Konu: {topic['subject']}")
        print(f"İzleyici ilgisi: {topic['why_viewers_would_click']}")
        print(f"Uzun video: {topic['long_video_potential']}/10")
        print(f"Shorts: {topic['shorts_potential']}/10")
        print(f"Araştırma zorluğu: {topic['research_difficulty']}/10")


if __name__ == "__main__":
    main()
