import json
from pathlib import Path

QUEUE_FILE = Path("research/topic_queue.json")


def save_topics(topics):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "topics": topics
    }

    QUEUE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def load_topics():
    if not QUEUE_FILE.exists():
        return []

    data = json.loads(
        QUEUE_FILE.read_text(encoding="utf-8")
    )

    return data.get("topics", [])


def add_topic(topic):
    topics = load_topics()
    topics.append(topic)
    save_topics(topics)


if __name__ == "__main__":
    print("Shadow Archive topic queue hazır.")
