# backend/app/models.py
from . import db
import datetime
import pytz

harare = pytz.timezone("Africa/Harare")

def get_harare_time():
    return datetime.datetime.now(harare)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=False)

    faces = db.relationship("FaceImages", backref="user", lazy="dynamic")
    unknown_faces = db.relationship("UnknownFaces", backref="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        return {"id": self.id, "username": self.username, "phone": self.phone}


class FaceImages(db.Model):
    __tablename__ = "face_images"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    image_path = db.Column(db.String(255))

    def __repr__(self):
        return f"<Face image for user {self.user_id}>"
    
class UnknownFaces(db.Model):
    __tablename__ = "unknown_faces"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    image_path = db.Column(db.String(255))
    age = db.Column(db.Integer)
    race = db.Column(db.String(255))
    gender = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=get_harare_time)
