import os
import json
from pathlib import Path
from google import genai

CHANNEL_NAME = "Shadow Archive"
QUEUE_FILE = Path("research/topic_queue.json")


def find_topics(count=10):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the topic discovery engine for the YouTube channel "{CHANNEL_NAME}".

Generate {count} ORIGINAL mystery documentary topics.

Focus on:
- unexplained mysteries
- unsolved cases
- strange historical events
- mysterious places
- unexplained discoveries
- forgotten stories

For every topic provide:
- title_idea
- subject
- why_viewers_would_click
- long_video_potential
- shorts_potential
- research_difficulty

Rules:
- Never invent real events.
- Do not present rumors as facts.
- Prefer topics that can support a 15+ minute documentary.
- Prefer strong curiosity and storytelling potential.
- Avoid generic or repetitive ideas.

Return ONLY valid JSON.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    text = response.text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)


def save_topics(topics):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    QUEUE_FILE.write_text(
        json.dumps(
            {"topics": topics},
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def main():
    topics = find_topics(10)
    save_topics(topics)

    print("\nSHADOW ARCHIVE — TOPIC QUEUE")
    print("=" * 45)

    for number, topic in enumerate(topics, start=1):
        print(f"{number}. {topic['title_idea']}")
        print(f"   Uzun video: {topic['long_video_potential']}/10")
        print(f"   Shorts: {topic['shorts_potential']}/10")
        print()


if __name__ == "__main__":
    main()
