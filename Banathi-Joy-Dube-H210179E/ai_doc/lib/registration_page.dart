import 'package:ai_doc/login_page.dart';
import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class RegistrationPage extends StatefulWidget {
  @override
  _RegistrationPageState createState() => _RegistrationPageState();
}

class _RegistrationPageState extends State<RegistrationPage> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController =
      TextEditingController();
  final SupabaseClient _supabaseClient = Supabase.instance.client;

  @override
  void initState() {
    super.initState();
    // Supabase.initialize(
    //   url: 'https://your-supabase-url.supabase.co',
    //   anonKey: 'your-anon-key',
    // );
  }

  Future<void> _register() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    try {
      final response = await _supabaseClient.auth.signInWithPassword(
        email: email,
        password: 'dummy', // or actual password if available
      );
      print('User exists (login successful): ${response.user}');
    } catch (e) {
      if (e is AuthException) {
        if (e.message.contains('Invalid login credentials')) {
          print('User likely exists, but password is wrong.');
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('This email is already registered. Please log in.'),
            ),
          );
        } else if (e.message.contains('User not found')) {
          print('User does NOT exist.');
        } else {
          print('Other auth error: ${e.message}');
        }
      }
      return;
    }

    try {
      final response = await _supabaseClient.auth.signUp(
        email: email,
        password: password,
      );

      print('Registration response.....: $response');
      print('Session: ${response.session}');
      print('User: ${response.user}');

      if (response.user != null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Registration successful! Please check your email to confirm.',
            ),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Registration completed, but no user object returned.',
            ),
          ),
        );
      }
    } on AuthException catch (e) {
      final errorMsg = e.message.toLowerCase();
      print('Error details: $e');
      // Log the error for debugging
      print('Supabase AuthException: ${e.message}');

      if (errorMsg.contains('already registered') ||
          errorMsg.contains('user already exists') ||
          errorMsg.contains('email already registered') ||
          errorMsg.contains('duplicate') ||
          errorMsg.contains('unique constraint')) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('This email is already registered. Please log in.'),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Registration error: ${e.message}')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Unexpected error: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset(
                '/logo.jpeg',
                height: 40,
                width: 40,
                fit: BoxFit.cover,
              ),
            ),
            const SizedBox(width: 15),
            const Text(
              'AI Doctor',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                fontFamily: 'Roboto',
                letterSpacing: 1.2,
                color: Color.fromARGB(255, 246, 246, 247),
              ),
            ),
          ],
        ),
        centerTitle: false,
        backgroundColor: Color.fromARGB(255, 53, 10, 123),
        elevation: 2,
        iconTheme: IconThemeData(color: Colors.white),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const Text(
              'Welcome to AI Doctor!',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Color.fromARGB(255, 53, 10, 123),
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Please create a new account to get started.',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _emailController,
              decoration: InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _passwordController,
              decoration: InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            const SizedBox(height: 20),
            TextField(
              controller: _confirmPasswordController,
              decoration: InputDecoration(
                labelText: 'Confirm Password',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                if (_passwordController.text !=
                    _confirmPasswordController.text) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Passwords do not match!')),
                  );
                  return;
                }
                _register();
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Color.fromARGB(255, 53, 10, 123),
                padding: const EdgeInsets.symmetric(
                  horizontal: 50,
                  vertical: 15,
                ),
                textStyle: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white, // Ensures text is white
                ),
              ),
              child: const Text(
                'Register',
                style: TextStyle(color: Colors.white), // Ensures text is white
              ),
            ),

            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('Already have an account? '),
                GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => LoginPage()),
                    );
                  },
                  child: const Text(
                    'Log in',
                    style: TextStyle(
                      color: Color.fromARGB(255, 53, 10, 123),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
