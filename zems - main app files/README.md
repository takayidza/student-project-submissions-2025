# Zimbabwe EMS - Your Emergency Health Companion

**Zimbabwe EMS** is a feature-rich mobile application crafted with Flutter, tailored to provide reliable emergency healthcare support specifically for Zimbabweans. Designed with accessibility and real-world challenges in mind, the app combines AI-driven medical support, emergency geolocation, blood pressure tracking, and NFC health sharing to serve as a personal health companion—online or offline.

---

## 🚑 Key Features

### 🧠 **AI Medical Assistant**

Ask medical questions and receive fast, context-aware responses from a built-in AI chatbot trained on trusted medical knowledge. The chatbot is optimized to work offline where possible, with fallback to cloud-based models like Gemini or OpenAI when internet access is available.

### 📍 **Real-Time Hospital Locator**

Quickly locate nearby hospitals or clinics with integrated geolocation support. The app utilizes Google Maps APIs to help users find the fastest route during emergencies, even in areas without formal addresses.

### ❤️ **Blood Pressure Tracker**

Log and monitor your blood pressure readings in a simple, WHO-compliant format. The app offers suggestions based on your measurements and allows users to track their vitals over time—helping detect early signs of hypertension or cardiovascular issues.

### ☎️ **Emergency Contacts Dashboard**

Save, categorize, and favorite important emergency numbers (ambulance, police, fire, etc.). With one-tap dialing, users can quickly reach help without fumbling through their phone during a crisis.

### 📶 **Offline-First Design**

Built with Zimbabwe’s infrastructure in mind, the app stores key data offline using the Hive database. Emergency contact features, BP logging, and chatbot responses are accessible without internet. Cloud sync with Firebase is used for backup and multi-device access.

### 🔐 **Secure Medical Records & NFC Sharing**

Users can store essential medical history, allergies, or conditions within the app and share via NFC—ideal in situations where a user is unconscious or unable to communicate.

### 🎨 **User-Friendly Interface**

Inspired by Material 3principles, the design is clean, modern, and intuitive for all age groups. Guest login is available for quick access without registration.

---

## 🔧 Technical Stack

* **Framework:** Flutter
* **Database:** Hive (local), Firebase (cloud)
* **State Management:** BLoC/Cubit
* **AI Integration:** Gemini Pro (Google AI Studio), LangChain fallback
* **Maps & Location:** Google Maps API, Geolocator
* **NFC:** nfc\_manager
* **UI/UX:** ScreenUtil, Gap, Flutter SVG, Material 3

---

## 📲 Getting Started

### Prerequisites

* Flutter SDK installed
* Firebase project setup (optional for remote sync)

### Installation Steps

```bash
git clone https://github.com/tateray/zimbabwe-ems.git
cd zimbabwe-ems
flutter pub get
flutter run
```

### Firebase Setup (Optional but Recommended)

1. Create a Firebase project
2. Add Android/iOS app
3. Download `google-services.json` (Android) or `GoogleService-Info.plist` (iOS)
4. Place files in respective directories
5. Initialize Firebase in `main.dart`

---

## 🤝 Why Zimbabwe EMS?

Unlike generic medical apps or basic phone features, Zimbabwe EMS is tailored to local needs:

* Works in **low-connectivity environments**
* Includes **Zimbabwe-specific emergency numbers**
* Provides **offline access to critical features**
* **Respects user privacy** and works without login if needed
* **Supports the local healthcare ecosystem**

Whether it’s for managing a chronic condition like hypertension, helping loved ones during a crisis, or getting trusted medical advice without internet, Zimbabwe EMS is your always-ready digital health ally.

---

## 👩🏾‍⚕️ Built For Zimbabwe, With Zimbabwe In Mind 🇿🇼

This project is open to local customization and community development. Contributions are welcome from health workers, developers, and civil society partners.

---

## 📬 Support

For technical support, partnership inquiries, or to contribute:
**Email:** h210065z@hit.ac.zw
