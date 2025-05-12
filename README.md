# � Accident-Prone Area Detection System

A real-time, GPS-based accident-prone zone detection system using Machine Learning and voice alerts, designed to enhance road safety — especially in developing countries like Zimbabwe.

---

## � Overview

This system predicts whether a location is accident-prone based on GPS coordinates and traffic conditions using a trained Random Forest model. It provides **voice alerts** to drivers in real-time via a web interface, reducing the risk of accidents.

---

## � Features

- � Real-time accident zone prediction using GPS and speed
- � Machine Learning model (Random Forest Classifier)
- � Voice alert system for high-risk area warnings
- � HTML/CSS/JavaScript frontend
- � Python backend with Flask/FastAPI
- � Model trained on synthetic traffic and visibility data

---

## � Machine Learning Model

- **Model type:** Random Forest Classifier
- **Features:**
  - Speed
  - Time of Day
  - Vehicle Count
  - Visibility Score
- **Target Variable:** `accident_prone` (1 = Yes, 0 = No)
- **Training Data:** Synthetic dataset (~1000 records) generated using Python (NumPy, Pandas)
- **Saved model:** `accident_model.pkl` via joblib

---

## ⚙️ System Workflow

1. User accesses the frontend (HTML interface)
2. GPS location and speed are captured
3. Data is sent to the Python backend
4. Random Forest model makes prediction
5. If high-risk, a voice alert is triggered
6. Logs are stored for future improvements

---

## � Getting Started

### Prerequisites

- Python 3.8+
- Flask or FastAPI
- Pandas, NumPy, scikit-learn
- Joblib
- A browser (for frontend)

### Installation

```bash
git clone https://github.com/your-username/accident-prone-area-detector.git
cd accident-prone-area-detector
pip install -r requirements.txt







