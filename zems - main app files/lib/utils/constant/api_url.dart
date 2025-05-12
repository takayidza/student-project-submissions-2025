import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'dart:developer';

abstract class ApiUrlManager {
  ApiUrlManager._();
  
  
  static String get googleMapApiKey => dotenv.env['mapApiKey'] ?? '';
  static String get placeSuggetion => dotenv.env['placeSuggetionBaseUrl'] ?? '';
  static String get placeLocation => dotenv.env['placeLocationBaseUrl'] ?? '';
  static String get directions => dotenv.env['placedirectionsBaseUrl'] ?? '';
  static String get nearestHospital => dotenv.env['nearestHospitalBaseUrl'] ?? '';
  
  static String get generativeModelApiKey {
    final key = dotenv.env['generativeModelApiKey'];
    if (key == null || key.isEmpty) {
      log('Error: Gemini API key is missing or empty in .env file');
    }
    return key ?? '';
  }
  
  static String get generativeModelVersion {
    final version = dotenv.env['generativeModelVersion'];
    if (version == null || version.isEmpty) {
      log('Error: Gemini model version is missing or empty in .env file');
      return 'gemini-pro'; // Default to gemini-pro if not specified
    }
    return version;
  }
}
