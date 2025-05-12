from flask import Blueprint, request, jsonify, send_from_directory
from app.models import db, FaceImages, User  # type: ignore
import os
from PIL import Image
import numpy as np
import cv2
import uuid
import time
import base64
from pathlib import Path
import binascii
from deepface import DeepFace
import tempfile
import os
from joblib import Parallel, delayed


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Adjust to project root
SAVE_DIR = BASE_DIR / "detected_faces"

if not SAVE_DIR.exists():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def generate_filename():
    return f"{uuid.uuid4()}_{int(time.time())}.jpg"


def detect_faces(img):
    open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    height, width = open_cv_image.shape[:2]

    try:
        # Detect faces and extract them using DeepFace
        faces = DeepFace.extract_faces(img_path=open_cv_image, enforce_detection=False)

        if not faces:
            return []

        face_paths = []
        for i, face in enumerate(faces):
            # Check if 'facial_area' exists
            if "facial_area" not in face:
                print(f"Face object missing 'facial_area' key: {face}")
                continue

            # Extract bounding box coordinates from 'facial_area'
            facial_area = face["facial_area"]
            x, y, w, h = (
                facial_area["x"],
                facial_area["y"],
                facial_area["w"],
                facial_area["h"],
            )

            # Expand the bounding box slightly for better cropping
            expand_ratio = 0.3
            new_x1 = max(0, int(x - w * expand_ratio))
            new_y1 = max(0, int(y - h * expand_ratio))
            new_x2 = min(width, int(x + w * (1 + expand_ratio)))
            new_y2 = min(height, int(y + h * (1 + expand_ratio)))

            # Crop the face
            cropped_face = open_cv_image[new_y1:new_y2, new_x1:new_x2]

            # Generate a filename and save the cropped face
            face_filename = generate_filename()
            face_path = os.path.join(SAVE_DIR, face_filename)
            cv2.imwrite(face_path, cropped_face)

            # Append the file name to the results
            face_paths.append(face_filename)

        return face_paths

    except Exception as e:
        print(f"Error in detecting faces: {e}")
        return []


faces_blueprint = Blueprint("faces", __name__)


@faces_blueprint.route("/", methods=["GET"])
def get_faces():
    return jsonify({"message": "List of faces"})


# Process frame (detect faces)
@faces_blueprint.route("/process_frame/<string:user_id>", methods=["POST"])
def process_frame(user_id):
    try:
        if "image" not in request.files:
            return jsonify({"success": False, "message": "No image provided"}), 400

        if not user_id:
            return jsonify({"success": False, "message": "No user_id provided"}), 400

        user_id = base64.b64decode(user_id).decode("utf-8")

        file = request.files["image"]
        img = Image.open(file.stream)

        face_filenames = detect_faces(img)

        if not face_filenames:
            return jsonify({"success": False, "message": "No faces detected"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # Return detected faces but do not save them yet
        return jsonify({"success": True, "faces": face_filenames}), 201

    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)}), 500


# Save face to database
@faces_blueprint.route("/save_face", methods=["POST"])
def save_face():
    try:
        filename = request.args.get("filename")
        user_id = request.args.get("user_id")
        user_id = base64.b64decode(user_id).decode("utf-8")

        if not filename or not user_id:
            return jsonify({"success": False, "message": "Invalid parameters"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # Check if the user has reached the maximum number of faces
        current_face_count = FaceImages.query.filter_by(user_id=user_id).count()
        if current_face_count >= 3:
            return (
                jsonify({"success": False, "message": f"Maximum of 3 faces allowed"}),
                400,
            )

        # Save the face into the database
        new_face_image = FaceImages(user_id=user_id, image_path=filename)
        db.session.add(new_face_image)
        db.session.commit()
        return jsonify({"success": True, "message": "Face saved to database"}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# Delete face
@faces_blueprint.route("/delete_face", methods=["DELETE"])  # Add OPTIONS
def delete_face():

    if request.method == "OPTIONS":
        return jsonify({"success": True}), 200

    filename = request.args.get("filename", None)
    user_id = request.args.get("user_id", None)

    if not user_id:
        return jsonify({"success": False, "message": "No user_id provided"}), 400

    if not filename:
        return jsonify({"success": False, "message": "No filename provided"}), 400

    try:
        # Decode user_id (same as other routes)
        user_id = base64.b64decode(user_id).decode("utf-8")
        user_id = int(user_id)
    except (binascii.Error, ValueError) as e:
        return jsonify({"success": False, "message": "Invalid user ID"}), 400

    # Define the full path to the file in the 'detected_faces' folder
    file_path = os.path.join(SAVE_DIR, filename)

    # Check if the file exists in the directory
    file_deleted = False
    if os.path.exists(file_path):
        os.remove(file_path)  # Delete the file from the filesystem
        file_deleted = True
        print(f"File {filename} deleted from the filesystem.")

    # If the file was found in the database, delete it from the database
    deleted_image = FaceImages.query.filter_by(
        user_id=user_id, image_path=filename
    ).first()
    if deleted_image:
        db.session.delete(deleted_image)  # Delete the record from the database
        db.session.commit()
        print(f"File {filename} deleted from the database.")

    # Log status of deletion
    print(f"File deleted: {file_deleted}, Image deleted from DB: {bool(deleted_image)}")

    # If either the file or the database entry is deleted, respond accordingly
    if file_deleted or deleted_image:
        return (
            jsonify(
                {
                    "success": True,
                    "message": "File deleted successfully",
                    "filename": filename,
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "File not found in both the filesystem and database",
                }
            ),
            404,
        )


# Serve saved face images
@faces_blueprint.route("/detected_faces/<path:filename>")
def serve_detected_face(filename):
    try:
        return send_from_directory(SAVE_DIR, filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


# Get saved faces
@faces_blueprint.route("/get_saved_images", methods=["GET"])
def get_saved_images():
    user_id = request.args.get("user_id")  # Get user_id from query params
    if not user_id:
        return jsonify({"success": False, "message": "No user_id provided"}), 400

    try:
        # Decode user_id (same as other routes)
        user_id = base64.b64decode(user_id).decode("utf-8")
        user_id = int(user_id)
    except (binascii.Error, ValueError) as e:
        return jsonify({"success": False, "message": "Invalid user ID"}), 400

    # Get faces from database (not directory)
    faces = FaceImages.query.filter_by(user_id=user_id).all()
    files = [face.image_path for face in faces]

    return jsonify({"success": True, "images": files}), 200


@faces_blueprint.route("/verify", methods=["POST"])
def verify():
    print("\n=== New Verification Request ===")
    print(f"Received headers: {dict(request.headers)}")
    print(f"Received args: {dict(request.args)}")

    user = request.args.get("user_id")
    print(f"Raw user param: {user}")

    try:
        user_id = base64.b64decode(user).decode("utf-8")
        print(f"Decoded user_id: {user_id}")
    except Exception as e:
        print(f"Decoding error: {str(e)}")
        return jsonify({"error": "Unauthorized"}), 401

    if not user:
        print("Unauthorized: No user_id provided")
        return jsonify({"error": "Unauthorized"}), 401

    # File handling
    if "image" not in request.files:
        print("No image in request.files")
        return jsonify({"error": "No image provided"}), 400

    uploaded_file = request.files["image"]
    print(
        f"Received file: {uploaded_file.filename} ({uploaded_file.content_length} bytes)"
    )

    if uploaded_file.filename == "":
        print("Empty filename received")
        return jsonify({"error": "Empty file"}), 400

    # Database query
    stored_faces = FaceImages.query.filter_by(user_id=user_id).all()
    print(f"Found {len(stored_faces)} reference faces for user {user_id}")

    if not stored_faces:
        print("No stored faces found")
        return jsonify({"error": "No reference faces found"}), 404

    # Temporary file handling
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            uploaded_file.save(temp_file)
            temp_path = temp_file.name
            print(f"Saved temporary file to: {temp_path}")

        image_paths = [f"./detected_faces/{face.image_path}" for face in stored_faces]
        print(f"Comparing against {len(image_paths)} reference images")

        # Parallel processing
        results = Parallel(n_jobs=-1, prefer="processes")(
            delayed(process_face)(temp_path, ref_path) for ref_path in image_paths
        )
        print(f"Processing completed with {len(results)} results")

        valid_results = [r for r in results if r is not None]
        print(f"Valid results: {len(valid_results)}")

        matches = sum(1 for r in valid_results if r[0])
        total = len(valid_results)
        distances = [r[1] for r in valid_results if r[0]]

        avg_confidence = sum(distances) / len(distances) if distances else 0
        print(f"Matches: {matches}/{total}, Avg Confidence: {avg_confidence:.2f}")

        # Verification logic
        min_matches = 2
        min_confidence = 0.5
        is_verified = (
            matches >= min_matches
            and avg_confidence >= min_confidence
            and total >= min_matches
        )

        print(f"Verification result: {'SUCCESS' if is_verified else 'FAILURE'}")

        return jsonify(
            {
                "success": is_verified,  # Changed from "verified" to match frontend
                "matches": matches,
                "total": total,
                "confidence": avg_confidence,
                "message": "Face verified successfully",
            }
        ), (200 if is_verified else 401)

    finally:
        if os.path.exists(temp_path):
            print(f"Cleaning up temporary file: {temp_path}")
            os.remove(temp_path)


def process_face(temp_path, ref_path):
    try:
        print(f"\nComparing {temp_path} with {ref_path}")
        result = DeepFace.verify(
            img1_path=temp_path,
            img2_path=ref_path,
            model_name="Facenet512",
            detector_backend="retinaface",
            distance_metric="cosine",
            enforce_detection=True,
            align=True,
        )
        print(
            f"Comparison result: {result['verified']} (Distance: {result['distance']:.2f})"
        )
        return (result["verified"], result["distance"])
    except Exception as e:
        print(f"Error processing {ref_path}: {str(e)}")
        return None
