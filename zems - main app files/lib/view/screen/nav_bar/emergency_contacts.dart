import 'package:zems/utils/constant/color.dart';
import 'package:zems/utils/helper/extention.dart';
import 'package:flutter/material.dart';

class EmergencyContactsScreen extends StatelessWidget {
  const EmergencyContactsScreen({super.key});

  final List<Map<String, String>> emergencyNumbers = const [
    {'category': 'Ambulance', 'number': '112'},
    {'category': 'Police', 'number': '995'},
    {'category': 'Fire Brigade', 'number': '993'},
    {'category': 'City Medical Services', 'number': '0800 3222'},
    {'category': 'Red Cross Emergency', 'number': '0242 708835'},
    {'category': 'Traffic Accidents', 'number': '977'},
    {'category': 'Zim Ambulance Harare', 'number': '0772 123 456'},
    {'category': 'Private Emergency Response', 'number': '0783 555 101'},
    {'category': 'Child Helpline', 'number': '116'},
    {'category': 'Poison Control', 'number': '0800 9111'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Emergency Numbers'),
        centerTitle: true,
        backgroundColor: ColorManager.green,
      ),
      backgroundColor: context.theme.scaffoldBackgroundColor,
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: emergencyNumbers.length,
        itemBuilder: (context, index) {
          final contact = emergencyNumbers[index];
          return Card(
            elevation: 3,
            margin: const EdgeInsets.symmetric(vertical: 8),
            child: ListTile(
              leading: const Icon(Icons.local_phone, color: ColorManager.green),
              title: Text(contact['category'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text(contact['number'] ?? ''),
              trailing: IconButton(
                icon: const Icon(Icons.call, color: Colors.teal),
                onPressed: () {
                  // Logic to dial the number (optional)
                },
              ),
            ),
          );
        },
      ),
    );
  }
}
