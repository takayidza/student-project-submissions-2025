from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_mail import Mail
from datetime import timedelta



app = Flask(__name__)
CORS(app, resources={
    r"/*": {  # Allow all routes
        "origins": [
            "http://localhost:81",
            "https://127.0.0.1:81",
            "http://localhost:8080",  # Add this line
            "http://127.0.0.1:8080"   # Add this line
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost:3306/incident_management'
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['SECRET_KEY'] = "123456"




db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch = True)
from server.api.v1.endpoints import *