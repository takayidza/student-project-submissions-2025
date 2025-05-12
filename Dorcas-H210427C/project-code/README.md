# Face Recognition Security System

A comprehensive face recognition security system with user authentication, security logging, and real-time monitoring.

## Features

- 👤 **Face Recognition Authentication**: Secure login using facial biometrics
- 📊 **Security Dashboard**: Monitor security events and face detections
- 🔔 **Unauthorized Access Alerts**: Email notifications for unauthorized access attempts
- 📱 **Responsive UI**: Works on desktop and mobile devices
- 📈 **Analytics**: Track security metrics and visualize data
- 🔒 **Multi-factor Authentication**: Username/password + face verification

## Project Structure

```
├── frontend/              # SvelteKit frontend application
│   ├── src/               # Source code
│   │   ├── lib/           # Reusable components and utilities
│   │   ├── routes/        # Application routes and pages
│   │   └── app.html       # HTML template
│   ├── static/            # Static assets
│   └── tailwind.config.js # Tailwind CSS configuration
│
└── backend/               # Flask backend application
    ├── app/               # Application code
    │   ├── blueprints/    # API routes
    │   ├── models.py      # Database models
    │   └── tasks.py       # Background tasks (Celery)
    ├── chroma_db/         # Vector database for face embeddings
    └── wsgi.py            # WSGI entry point
```

## Prerequisites

- Python 3.9+ for backend
- Bun 1.0+ for frontend
- RabbitMQ for Celery message broker
- Camera for face recognition

## Installation

### Backend Setup

1. Clone the repository
   ```bash
   git clone https://github.com/chinakwetudee/submissions-H210427C-DORCAS.git
   cd submissions-H210427C-DORCAS
   ```

2. Create and activate a virtual environment (optional but recommended)
   ```bash
   cd backend
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. Install backend dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Install and start RabbitMQ (if not already running)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install rabbitmq-server
   sudo systemctl start rabbitmq-server
   
   # macOS (with Homebrew)
   brew install rabbitmq
   brew services start rabbitmq
   
   # Windows
   # Download and install from https://www.rabbitmq.com/download.html
   ```

5. Configure environment variables
   ```bash
   cp backend/.env.example backend/.env
   # Edit .env file with your configuration
   ```

6. Initialize the database
   ```bash
   cd backend
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

### Frontend Setup

1. Navigate to the frontend directory
   ```bash
   cd frontend
   ```

2. Install dependencies using Bun
   ```bash
   bun install
   ```

3. Configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env file with your API URL
   ```

## Running the Application

### Start the Backend

1. Ensure RabbitMQ is running
   ```bash
   # Check RabbitMQ status
   sudo systemctl status rabbitmq-server  # Linux
   brew services info rabbitmq  # macOS
   ```

2. Run the Flask application
   ```bash
   cd backend
   python wsgi.py
   ```

3. In a separate terminal, start the Celery worker
   ```bash
   cd backend
   celery -A app.celery_worker.celery worker --loglevel=info --pool=solo
   ```

### Start the Frontend

```bash
cd frontend
bun run dev
```

The application will be available at http://localhost:5173

## Deployment

### Backend Deployment

The backend can be deployed using Gunicorn and Nginx:

```bash
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:5001 wsgi:app
```

For production, ensure RabbitMQ is properly configured with security settings and is accessible to your application server.

### Frontend Deployment

Build the frontend for production:

```bash
cd frontend
bun run build
```

Deploy the static files from the `build` directory to your web server.

## Environment Variables

### Backend (.env)

```
SQLALCHEMY_DATABASE_URI=sqlite:///app.db
SQLALCHEMY_TRACK_MODIFICATIONS=False
broker_url=pyamqp://guest@localhost//
result_backend=rpc://

MAX_FACES_PER_USER=3
FACE_MATCH_THRESHOLD=0.15
FACE_MODEL_NAME=Facenet
FACE_DETECTOR_BACKEND=ssd

SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password
SENDER_EMAIL=alerts@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
BASE_URL=http://localhost:5001
```

Notice that `broker_url=pyamqp://guest@localhost//` is configured to use RabbitMQ as the message broker for Celery.

### Frontend (.env)

```
VITE_PUBLIC_API_URL=http://localhost:5001
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
