import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
celery = Celery(__name__)

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
    app.config["broker_url"] = os.getenv('broker_url')
    app.config["result_backend"] = os.getenv('result_backend')
    
    
    # Application configurations
    app.config['MAX_FACES_PER_USER'] = int(os.getenv('MAX_FACES_PER_USER'))
    app.config['FACE_MATCH_THRESHOLD'] = float(os.getenv('FACE_MATCH_THRESHOLD'))
    app.config['FACE_MODEL_NAME'] = os.getenv('FACE_MODEL_NAME')
    app.config['FACE_DETECTOR_BACKEND'] = os.getenv('FACE_DETECTOR_BACKEND')
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    celery.conf.update(app.config)
    celery.autodiscover_tasks(['app.tasks'])
    class FlaskTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            with app.app_context():
                super().on_failure(exc, task_id, args, kwargs, einfo)

    celery.Task = FlaskTask
    
    # Register blueprints
    from .blueprints import register_blueprints
    register_blueprints(app)
    
    return app