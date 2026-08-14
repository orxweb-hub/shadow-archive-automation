from datetime import datetime


CHANNEL_NAME = "Shadow Archive"


def create_research_request(topic):
    return {
        "channel": CHANNEL_NAME,
        "topic": topic,
        "created_at": datetime.utcnow().isoformat(),
        "requirements": {
            "original": True,
            "fact_checked": True,
            "story_driven": True,
            "long_video": True,
            "shorts_possible": True,
        },
    }


def main():
    topic = input("Araştırılacak konu: ")

    request = create_research_request(topic)

    print("\nSHADOW ARCHIVE RESEARCH")
    print("-----------------------")
    print(f"Kanal: {request['channel']}")
    print(f"Konu: {request['topic']}")
    print("Özgün içerik: EVET")
    print("Kaynak kontrolü: EVET")
    print("Uzun video: EVET")
    print("Shorts üretilebilir: EVET")


if __name__ == "__main__":
    main()
