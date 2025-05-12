# backend/app/blueprints/faces.py
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from app.models import db, User
import chromadb
import os
from PIL import Image
import numpy as np
import cv2
import uuid
import time
import base64
from pathlib import Path
from deepface import DeepFace
import tempfile
from typing import List, Optional


chroma_client = chromadb.PersistentClient(path="./chroma_db")
face_collection = chroma_client.get_or_create_collection(
    name="face_embeddings", metadata={"hnsw:space": "cosine"}
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAVE_DIR = BASE_DIR / "detected_faces"
VERIFY_DIR = BASE_DIR / "verified_faces"

if not SAVE_DIR.exists():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    
if not VERIFY_DIR.exists():
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)


def generate_filename():
    return f"{uuid.uuid4()}_{int(time.time())}.jpg"

def get_face_embedding(image_path: str) -> Optional[List[float]]:
    try:
        img = cv2.imread(image_path)
        img = cv2.resize(img, (160, 160))
        embedding_obj = DeepFace.represent(
            img_path=img,
            model_name=current_app.config.get("FACE_MODEL_NAME"),
            detector_backend=current_app.config.get("FACE_DETECTOR_BACKEND"),
            enforce_detection=False,
            align=False,
            normalization="base",
            max_faces=1
        )
        
        embedding = embedding_obj[0]["embedding"]
        
        import numpy as np
        embedding_array = np.array(embedding)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            normalized_embedding = embedding_array / norm
            return normalized_embedding.tolist() 
        
        return embedding
    except Exception as e:
        print(f"Embedding extraction failed: {str(e)}")
        return None

def detect_faces(img, dir=SAVE_DIR):
    open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    height, width = open_cv_image.shape[:2]

    try:
        faces = DeepFace.extract_faces(img_path=open_cv_image, enforce_detection=False)
        face_paths = []

        for i, face in enumerate(faces):
            if "facial_area" not in face:
                continue

            facial_area = face["facial_area"]
            x, y, w, h = (
                facial_area["x"],
                facial_area["y"],
                facial_area["w"],
                facial_area["h"],
            )

            expand_ratio = 0.3
            new_x1 = max(0, int(x - w * expand_ratio))
            new_y1 = max(0, int(y - h * expand_ratio))
            new_x2 = min(width, int(x + w * (1 + expand_ratio)))
            new_y2 = min(height, int(y + h * (1 + expand_ratio)))

            cropped_face = open_cv_image[new_y1:new_y2, new_x1:new_x2]
            face_filename = generate_filename()
            face_path = os.path.join(dir, face_filename)
            cv2.imwrite(face_path, cropped_face)
            face_paths.append(face_filename)

        return face_paths

    except Exception as e:
        print(f"Error detecting faces: {e}")
        return []

faces_blueprint = Blueprint("faces", __name__)


@faces_blueprint.route("/", methods=["GET"])
def get_faces():
    return jsonify({"message": "List of faces"})


@faces_blueprint.route("/process_frame/<string:user_id>", methods=["POST"])
def process_frame(user_id):
    try:
        if "image" not in request.files:
            return jsonify({"success": False, "message": "No image provided"}), 400

        user_id = int(base64.b64decode(user_id).decode("utf-8"))
        file = request.files["image"]
        img = Image.open(file.stream)

        face_filenames = detect_faces(img)
        if not face_filenames:
            return jsonify({"success": False, "message": "No faces detected"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        return jsonify({"success": True, "faces": face_filenames}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@faces_blueprint.route("/save_face", methods=["POST"])
def save_face():
    try:
        start_time = time.time()
        filename = request.args.get("filename")
        user_id = request.args.get("user_id")
        user_id = int(base64.b64decode(user_id).decode("utf-8"))
        
        if not filename or not user_id:
            return jsonify({"success": False, "message": "Invalid parameters"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        results = face_collection.get(where={"user_id": user_id}, include=["metadatas"])
        existing_count = len(results["metadatas"])
        if existing_count >= current_app.config.get("MAX_FACES_PER_USER"):
            return (
                jsonify({"success": False, "message": "Maximum 3 faces allowed"}),
                400,
            )

        face_path = os.path.join(SAVE_DIR, filename)
        embedding = get_face_embedding(face_path)

        if not embedding:
            return jsonify({"success": False, "message": "Face embedding failed"}), 400

        face_collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            metadatas=[{"user_id": user_id, "filename": filename}],
            documents=[face_path],
        )
        end_time = time.time()

        duration = end_time - start_time
        print(f"Process duration: {duration} seconds")
        return jsonify({"success": True, "message": "Face saved"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@faces_blueprint.route("/delete_face", methods=["DELETE"])
def delete_face():
    filename = request.args.get("filename")
    user_id = request.args.get("user_id")

    try:
        user_id = int(base64.b64decode(user_id).decode("utf-8"))

        face_collection.delete(where={"user_id": user_id, "filename": filename})

        file_path = os.path.join(SAVE_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": True, "message": "Face deleted"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@faces_blueprint.route("/detected_faces/<path:filename>")
def serve_detected_face(filename):
    try:
        return send_from_directory(SAVE_DIR, filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


@faces_blueprint.route("/get_saved_images", methods=["GET"])
def get_saved_images():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "No user_id provided"}), 400

    try:
        user_id = int(base64.b64decode(user_id).decode("utf-8"))
        print(f"User ID: {user_id}")
        results = face_collection.get(where={"user_id": user_id}, include=["metadatas"])
        print(results)
        files = [meta["filename"] for meta in results["metadatas"]]
        return jsonify({"success": True, "images": files}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@faces_blueprint.route("/verify", methods=["POST"])
def verify():
    try:
        start_time = time.time()
        user = request.args.get("user_id")
        user_id = int(base64.b64decode(user).decode("utf-8"))
        attempts = request.form.get('attempts')
        is_blocked = request.form.get('blocked').lower()  == 'true'

        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 401

        uploaded_file = request.files["image"]
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            uploaded_file.save(temp_file)
            temp_path = temp_file.name
            
        try:
            faces = detect_faces(Image.open(temp_path), dir=VERIFY_DIR)
            face_path = os.path.join(VERIFY_DIR, faces[0])
            
            if is_blocked:
                from app.tasks import add_unknown_face
                task = add_unknown_face.delay(face_path, user_id)
                return jsonify({"error": "User is blocked"}), 401
            
            query_embedding = get_face_embedding(face_path)
            if not query_embedding:
                return jsonify({"error": "No face detected"}), 400

            results = face_collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                where={"user_id": user_id},
                include=["distances"],
            )

            distances = results["distances"][0]
            matches = [d for d in distances if d < current_app.config.get('FACE_MATCH_THRESHOLD')]
            avg_distance = sum(matches) / len(matches) if matches else 1.0
            is_verified = len(matches) >= 2 

            end_time = time.time()
            duration = end_time - start_time
            print(f"Verification duration: {duration} seconds")
            print(f"Distances: {distances}")

            return jsonify(
                {
                    "success": is_verified,
                    "matches": len(matches),
                    "total": len(distances),
                    "confidence": avg_distance,
                    "message": "Verified" if is_verified else "Verification failed",
                }
            ), (200 if is_verified else 401)

        finally:
            if not is_blocked:
                os.remove(face_path)
            os.remove(temp_path)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@faces_blueprint.route("/migrate_faces", methods=["POST"])
def migrate_faces():
    from app.models import FaceImages

    try:
        faces = FaceImages.query.all()
        migrated_count = 0

        for face in faces:
            face_path = os.path.join(SAVE_DIR, face.image_path)

            # Check if already migrated
            existing = face_collection.get(
                where={"filename": face.image_path}, include=["metadatas"]
            )
            if existing["ids"]:
                continue

            embedding = get_face_embedding(face_path)
            if embedding:
                face_collection.add(
                    ids=[str(uuid.uuid4())],
                    embeddings=[embedding],
                    metadatas=[{"user_id": face.user_id, "filename": face.image_path}],
                    documents=[face_path],
                )
                migrated_count += 1

        return (
            jsonify(
                {
                    "success": True,
                    "message": f"Migrated {migrated_count} faces",
                    "total": migrated_count,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@faces_blueprint.route("/add")
def run_task():
    from app.tasks import add
    task = add.delay(10, 20)
    return jsonify({"task_id": task.id}), 202
