from app import create_app, celery
from dotenv import load_dotenv

load_dotenv()

app = create_app()
app.app_context().push()

if __name__ == '__main__':
    celery.start()