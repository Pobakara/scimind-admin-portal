import json
from app import app, db, Class

# Load old JSON data
with open("data/classes.json") as f:
    classes = json.load(f)

with app.app_context():
    for code, data in classes.items():
        # Create a Class object, using .get() for missing fields
        c = Class(
            code=code,
            class_name=data.get("class_name"),
            subject=data.get("subject"),
            year_level=data.get("year_level"),
            batch=data.get("batch"),
            sub_batch=data.get("sub_batch"),  # new field, may be None
            class_type=data.get("class_type"),  # new field, may be None
            description=data.get("description"),
            playlist_id=data.get("playlist_id"),
            courseId=data.get("courseId"),
            joinCode=data.get("joinCode"),
            classroom_name=data.get("classroom_name"),
            classroom_section=data.get("classroom_section"),
            class_teacher=data.get("class_teacher"),  # new field, may be None
            class_day=data.get("class_day"),          # new field, may be None
            class_time=data.get("class_time"),        # new field, may be None
            class_location=data.get("class_location") # new field, may be None
            # Add other new fields as needed
        )
        db.session.add(c)
    db.session.commit()
    print("Migration complete!")