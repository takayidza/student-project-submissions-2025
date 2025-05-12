from flask import Blueprint, request, jsonify, send_from_directory
from app.models import db, User, UnknownFaces
from bcrypt import hashpw, gensalt, checkpw
import base64
import os

users_blueprint = Blueprint("users", __name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(app_dir) 


@users_blueprint.route("/", methods=["GET"])
def get_users():
    users = User.query.all()
    users = [
        {"id": user.id, "username": user.username, "phone": user.phone}
        for user in users
    ]
    return jsonify({"users": users, "count": len(users)})


@users_blueprint.route("/", methods=["POST"])
def create_user():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get("username")
    password = data.get("password")
    phone = data.get("phone")

    if not username or not password or not phone:
        return jsonify({"error": "Missing required fields"}), 400

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    hashed_password = hashpw(password.encode("utf-8"), gensalt())

    new_user = User(username=username, password=hashed_password, phone=phone)
    try:
        db.session.add(new_user)
        db.session.commit()
        user_id = new_user.id
        print(f"Username: {username}, Password: {password}")
        return (
            jsonify({"message": f"User {username} created!", "user_id": user_id}),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@users_blueprint.route("/activate", methods=["POST"])
def activate_user():
    user_id = request.args.get("user_id")
    user_id = base64.b64decode(user_id).decode("utf-8")
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found", "success": False}), 404

    user.is_active = True
    db.session.commit()
    return jsonify({"message": "User activated", "success": True}), 200


@users_blueprint.route("/login", methods=["POST"])
def login():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing required fields"}), 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not checkpw(password.encode("utf-8"), user.password):
        return jsonify({"error": "Invalid password"}), 401

    return (
        jsonify(
            {"message": "Login successful", "id": user.id, "username": user.username}
        ),
        200,
    )


@users_blueprint.route("/me", methods=["GET"])
def get_user():
    user_id = request.headers.get("Authorization", "").replace("Bearer ", "")
    print(f"user id: {user_id}")
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200


@users_blueprint.route("/unknown_faces/<int:id>", methods=["GET"])
def get_unknown_faces(id):
    user_id = id
    if not user_id:
        return jsonify({"error": "No user_id provided"}), 400
    
    try:
        # Assuming you have a timestamp column like 'created_at'
        results = UnknownFaces.query.filter_by(user_id=user_id).order_by(UnknownFaces.created_at.desc()).all()
        formatted_results = []
        
        for result in results:
            filename = os.path.basename(result.image_path)
            relative_path = f"users/verified_faces/{filename}"
            
            formatted_results.append({
                "id": result.id,
                "image_path": relative_path,
                "age": result.age,
                "race": result.race,
                "gender": result.gender,
                "created_at": result.created_at
            })
        
        print(formatted_results)
        return jsonify({"results": formatted_results, "count": len(formatted_results)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@users_blueprint.route('/verified_faces/<path:filename>', methods=['GET'])
def serve_verified_faces(filename):
    verified_faces_dir = os.path.join(parent_dir, 'verified_faces')
    return send_from_directory(verified_faces_dir, filename)
