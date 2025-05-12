# backend/app/tasks.py
from app import celery
from .models import User, UnknownFaces, db
from deepface import DeepFace
import math
import tensorflow as tf


@celery.task(name="tasks.add", bind=True)
def add_unknown_face(self, image_path, user_id):
    user = User.query.get(user_id)
    if not user:
        print("User not found")
        return

    try:
        face_metrics = DeepFace.analyze(
            img_path=image_path,
            actions=["age", "gender", "race"],
            enforce_detection=False,
        )
        print(face_metrics)
        unknown_face = UnknownFaces(
            user_id=user_id,
            image_path=image_path,
            age=math.floor(face_metrics[0]["age"]),
            race=face_metrics[0]["dominant_race"],
            gender=face_metrics[0]["dominant_gender"],
        )
        db.session.add(unknown_face)
        db.session.commit()
        print("Face added to database")
        return
    except Exception as e:
        print(f"Error adding face: {e}")
        return
    
