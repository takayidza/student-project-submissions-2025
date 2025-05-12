import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'app.dart';
import 'data/model/chat_message_model.dart';
import 'data/model/bp_reading_model.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    // Load environment variables
    await dotenv.load(fileName: '.env').catchError((error) {
      print('Warning: Failed to load .env file: $error');
      // Continue anyway, as env variables might not be critical
    });

    // Initialize Hive
    await Hive.initFlutter();
    Hive.registerAdapter(ChatMessageModelAdapter());
    Hive.registerAdapter(BPReadingModelAdapter());
    
    // Open the chat history and bp_readings boxes
    await Hive.openBox<ChatMessageModel>('chat_history');
    await Hive.openBox<BPReadingModel>('bp_readings');

    // Launch the app
    runApp(const MyApp());
  } catch (e) {
    print('Error during app initialization: $e');
    // Fallback to minimal app if initialization fails
    runApp(MaterialApp(
      home: Scaffold(
        body: Center(
          child: Text('App initialization failed: $e'),
        ),
      ),
    ));
  }
}