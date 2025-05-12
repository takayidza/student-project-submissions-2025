import 'dart:developer';
import 'dart:math' as math;
import 'package:zems/utils/constant/api_url.dart';
import 'package:google_generative_ai/google_generative_ai.dart';

class GenerativeAiWebService {
  static final _model = GenerativeModel(
    model: ApiUrlManager.generativeModelVersion,
    apiKey: ApiUrlManager.generativeModelApiKey,
  );
  
  static Future<String?> postData({required String text}) async {
    try {
      // Enhanced API configuration logging
      log('API Configuration Details:');
      log('- Model Version: ${ApiUrlManager.generativeModelVersion}');
      log('- API Key Present: ${ApiUrlManager.generativeModelApiKey.isNotEmpty}');
      log('- API Key Length: ${ApiUrlManager.generativeModelApiKey.length}');
      if (ApiUrlManager.generativeModelApiKey.isNotEmpty) {
        log('- API Key First 4 chars: ${ApiUrlManager.generativeModelApiKey.substring(0, math.min(4, ApiUrlManager.generativeModelApiKey.length))}');
      }
      
      // Validate API key
      if (ApiUrlManager.generativeModelApiKey.isEmpty) {
        log('Error: API key is empty');
        return 'Error: API key is not configured. Please check your .env file.';
      }
      
      if (text.trim().isEmpty) {
        log('Error: Empty message text');
        return 'Error: Please enter a message.';
      }

      // Add medical context and restrictions
      final medicalContext = '''
You are a medical assistant for Zimbabwe Emergency Medical Services. 
You should ONLY respond to medical-related questions and emergencies.
If asked about non-medical topics, respond with: "I'm sorry, I can only assist with medical-related questions.."

For medical emergencies, always provide the nearest medical facility information:
Belvedere Medical Centre (BMC)
Location: -17.828483, 30.9387013
Phone: 08677186798

User question: $text
''';
      
      final content = [Content.text(medicalContext)];
      log('Sending request to Gemini API with medical context');
      
      try {
        final response = await _model.generateContent(content);
        if (response.text == null) {
          log('Error: Response text is null');
          return 'Error: No response received from the AI. Please try again.';
        }

        final cleanResponse = response.text!.trim();
        log('Successfully received response from Gemini API');
        return cleanResponse;
      } catch (apiError) {
        log('API Error:');
        log('- Error message: ${apiError.toString()}');
        log('- Error type: ${apiError.runtimeType}');
        return 'Error: Failed to get response from AI. Please check your internet connection and try again.';
      }
    } catch (err) {
      log('Error in postData:');
      log('- Error message: ${err.toString()}');
      log('- Error type: ${err.runtimeType}');
      if (err is FormatException) {
        log('- Format error details: ${err.message}');
      }
      return 'Error: An unexpected error occurred. Please try again later.';
    }
  }

  static Future<void> streamData({required String text}) async {
    try {
      if (ApiUrlManager.generativeModelApiKey.isEmpty) {
        log('Error: API key is empty for streaming');
        return;
      }
      
      final content = [Content.text(text)];
      final response = _model.generateContentStream(content);
      await for (final chunk in response) {
        log('Stream chunk received: ${chunk.text}');
      }
    } catch (err) {
      log('Error in streamData:');
      log('- Error message: ${err.toString()}');
      log('- Error type: ${err.runtimeType}');
    }
  }
}
