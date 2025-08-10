from classroom_auth import get_classroom_service

def create_google_course(course_name, section=None, room=None, ownerId=None):
    service = get_classroom_service()

    course = {
        "name": course_name,
        "section": section,
        "room": room
    }

    if ownerId:
        course["ownerId"] = ownerId  # ✅ Required when using a service account

    created = service.courses().create(body=course).execute()

    # Join code often isn't available immediately—fetch full object
    full = service.courses().get(id=created["id"]).execute()
    joinCode = full.get("enrollmentCode", "")

    return {
        "courseId": created["id"],
        "joinCode": joinCode,
        "name": created["name"]
    }

