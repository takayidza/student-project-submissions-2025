import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class PrescriptionPage extends StatelessWidget {
  const PrescriptionPage({super.key});

  Future<List<Map<String, dynamic>>> fetchPrescriptions() async {
    try {
      final user = Supabase.instance.client.auth.currentUser;
      if (user == null) {
        throw Exception('No user is logged in.');
      }

      final data = await Supabase.instance.client
          .from('prescription')
          .select()
          .eq('email', user.email)
          .withConverter<List<Map<String, dynamic>>>(
            (data) => List<Map<String, dynamic>>.from(data as List),
          );

      return data;
    } on PostgrestException catch (error) {
      throw Exception('Failed to fetch prescriptions: ${error.message}');
    } catch (e) {
      throw Exception('Unexpected error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Prescriptions')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: fetchPrescriptions(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text('No prescriptions found.'));
          }

          final prescriptions = snapshot.data!;

          return SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: const [
                DataColumn(label: Text('ID')),
                DataColumn(label: Text('Disease')),
                DataColumn(label: Text('Medication')),
                DataColumn(label: Text('Dosage')),
                DataColumn(label: Text('Frequency')),
                DataColumn(label: Text('Duration')),
                DataColumn(label: Text('Date')),
                DataColumn(label: Text('Doctor')),
              ],
              rows:
                  prescriptions.map((prescription) {
                    return DataRow(
                      cells: [
                        DataCell(Text(prescription['id'].toString())),
                        DataCell(Text(prescription['disease'] ?? '')),
                        DataCell(Text(prescription['medication'] ?? '')),
                        DataCell(Text(prescription['dosage'] ?? '')),
                        DataCell(Text(prescription['frequency'] ?? '')),
                        DataCell(Text(prescription['duration'] ?? '')),
                        DataCell(Text(prescription['created_at'] ?? '')),
                        DataCell(Text(prescription['doctor_fullname'] ?? '')),
                      ],
                    );
                  }).toList(),
            ),
          );
        },
      ),
    );
  }
}
