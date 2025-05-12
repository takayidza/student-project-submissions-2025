abstract class RouteManager {
  RouteManager._();
  // Core Routes
  static const initialRoute = "/";
  static const login = "/login";
  static const guestMode = "/guest-mode";
  static const home = "/home";
  static const nav = "/nav";
  
  // Authentication Routes
  static const email = "/email";
  static const password = "/password";
  static const information = "/information";
  static const register = "/register";
  
  // Emergency Features
  static const emergencyContacts = "/emergency-contacts";
  static const addEditContact = "/add-edit-contact";
  static const emergencySOS = "/emergency-sos";
  static const bloodPressure = "/blood-pressure";
  static const medicalHistory = "/medical-history";
  static const medicationReminders = "/medication-reminders";
  static const firstAidGuide = "/first-aid-guide";
  static const hospitalFinder = "/hospital-finder";
  static const medicalID = "/medical-id";
  static const symptomChecker = "/symptom-checker";
  
  // Other Functions
  static const otherFunctions = "/other-functions";
  static const chat = "/chat";
  static const maps = "/maps";
  static const personalHealth = "/personal-health";
  
  // Account Management
  static const editProfile = "/edit-profile";
  static const oldPassword = "/old-password";
  static const newPassword = "/new-password";
  static const aboutUs = "/about-us";
  static const reAuthScreen = "/re-auth-screen";
  static const deleteAccount = "/delete-account";
}
