from app import app, db, Video
import os
import json

VIDEOS_FILE = "data/videos.json"

def migrate_videos():
    if not os.path.exists(VIDEOS_FILE):
        print("No videos.json file found.")
        return

    with open(VIDEOS_FILE, "r") as f:
        videos = json.load(f)

    if isinstance(videos, dict):
        videos = list(videos.values())

    for v in videos:
        if Video.query.get(v["id"]):
            continue
        video = Video(
            id=v["id"],
            title=v.get("title"),
            date=v.get("date"),
            class_code=v.get("class_code"),
            youtube_id=v.get("youtube_id"),
            classroom_posted=v.get("classroom_posted", False)
        )
        db.session.add(video)

    db.session.commit()
    print("Migration complete! All videos imported.")

if __name__ == "__main__":
    with app.app_context():
        migrate_videos()