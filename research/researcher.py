import os
from google import genai

CHANNEL_NAME = "Shadow Archive"


def research_topic(topic):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY bulunamadı.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are the research engine for a YouTube channel called "{CHANNEL_NAME}".

Research the following mystery topic:

{topic}

Create a structured research report for a future YouTube video.

Requirements:
- Focus on factual information.
- Separate confirmed facts from theories.
- Do not invent people, dates, places or events.
- Find the most interesting details.
- Identify the strongest opening hook.
- Suggest 5 possible video titles.
- Suggest 3 thumbnail concepts.
- Suggest possible Shorts angles.
- The final video should be suitable for a 15+ minute documentary-style narration.
- The writing must feel natural and human, not robotic.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text


def main():
    topic = input("Araştırılacak konu: ")

    print("\nShadow Archive araştırması başlıyor...\n")

    report = research_topic(topic)

    print(report)


if __name__ == "__main__":
    main()
