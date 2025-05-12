import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class AppointmentPage extends StatefulWidget {
  @override
  _AppointmentPageState createState() => _AppointmentPageState();
}

class _AppointmentPageState extends State<AppointmentPage> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _reasonController = TextEditingController();
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;
  final SupabaseClient _supabaseClient = Supabase.instance.client;
  bool _isLoading = false;
  List<Map<String, dynamic>> _appointmentsList = [];
  bool _isFetchingAppointments = false;

  @override
  void initState() {
    super.initState();
    _fetchAppointments();
  }

  Future<void> _fetchAppointments() async {
    setState(() {
      _isFetchingAppointments = true;
    });

    try {
      final userId = _supabaseClient.auth.currentUser?.id;
      if (userId == null) {
        _appointmentsList = [];
        return;
      }

      final response = await _supabaseClient
          .from('appointments')
          .select()
          .eq('user_id', userId)
          .order('appointment_date', ascending: false)
          .order('appointment_time', ascending: false);

      if (response is List) {
        _appointmentsList = List<Map<String, dynamic>>.from(response);
      } else {
        print(
          'Unexpected response type from Supabase: ${response.runtimeType}',
        );
        _appointmentsList = [];
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Could not load appointments: Unexpected data format',
            ),
          ),
        );
      }
    } catch (e) {
      print('Error fetching appointments: $e');
      _appointmentsList = [];
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Could not load appointments: ${e is PostgrestException ? e.message : e.toString()}',
          ),
        ),
      );
    } finally {
      setState(() {
        _isFetchingAppointments = false;
      });
    }
  }

  Future<void> _pickDate(BuildContext context) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate ?? DateTime.now(),
      firstDate: DateTime.now(),
      lastDate: DateTime(2101),
    );
    if (picked != null && picked != _selectedDate) {
      setState(() {
        _selectedDate = picked;
      });
    }
  }

  Future<void> _pickTime(BuildContext context) async {
    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: _selectedTime ?? TimeOfDay.now(),
    );
    if (picked != null && picked != _selectedTime) {
      setState(() {
        _selectedTime = picked;
      });
    }
  }

  Future<void> _submitAppointment() async {
    if (_formKey.currentState!.validate()) {
      if (_selectedDate == null || _selectedTime == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Please select a date and time.')),
        );
        return;
      }

      setState(() {
        _isLoading = true;
      });

      try {
        final userId = _supabaseClient.auth.currentUser?.id;
        if (userId == null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('User not authenticated. Please log in again.'),
            ),
          );
          setState(() {
            _isLoading = false;
          });
          return;
        }

        final reason = _reasonController.text;
        final appointmentDate =
            '${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}';
        final appointmentTime =
            '${_selectedTime!.hour.toString().padLeft(2, '0')}:${_selectedTime!.minute.toString().padLeft(2, '0')}:00';

        await _supabaseClient.from('appointments').insert({
          'user_id': userId,
          'reason': reason,
          'appointment_date': appointmentDate,
          'appointment_time': appointmentTime,
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Appointment request submitted successfully!'),
          ),
        );
        _reasonController.clear();
        setState(() {
          _selectedDate = null;
          _selectedTime = null;
        });
        _fetchAppointments();
      } catch (e) {
        print('Error submitting appointment: $e');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              'Failed to submit appointment: ${e is PostgrestException ? e.message : e.toString()}',
            ),
          ),
        );
      } finally {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Request an Appointment'),
        titleTextStyle: TextStyle(color: Colors.white),
        backgroundColor: Color.fromARGB(255, 53, 10, 123),
        elevation: 2,
        iconTheme: IconThemeData(color: Colors.white),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: ListView(
            children: <Widget>[
              Text(
                'Book Your Slot',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Color.fromARGB(255, 53, 10, 123),
                ),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 20),
              TextFormField(
                controller: _reasonController,
                decoration: InputDecoration(
                  labelText: 'Reason for Appointment',
                  hintText:
                      'e.g., General check-up, follow-up, specific symptom',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.notes),
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter the reason for your appointment.';
                  }
                  return null;
                },
                maxLines: 3,
              ),
              SizedBox(height: 20),
              Row(
                children: <Widget>[
                  Expanded(
                    child: Text(
                      _selectedDate == null
                          ? 'No date chosen'
                          : 'Date: ${_selectedDate!.year}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}',
                      style:
                          _selectedDate == null
                              ? null
                              : TextStyle(
                                color: Colors.red,
                                fontWeight: FontWeight.bold,
                              ),
                    ),
                  ),
                  TextButton.icon(
                    icon: Icon(Icons.calendar_today),
                    label: Text('Select Date'),
                    onPressed: () => _pickDate(context),
                    style: TextButton.styleFrom(
                      foregroundColor: Color.fromARGB(255, 53, 10, 123),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 10),
              Row(
                children: <Widget>[
                  Expanded(
                    child: Text(
                      _selectedTime == null
                          ? 'No time chosen'
                          : 'Time: ${_selectedTime!.format(context)}',
                      style:
                          _selectedTime == null
                              ? null
                              : TextStyle(
                                color: Colors.red,
                                fontWeight: FontWeight.bold,
                              ),
                    ),
                  ),
                  TextButton.icon(
                    icon: Icon(Icons.access_time),
                    label: Text('Select Time'),
                    onPressed: () => _pickTime(context),
                    style: TextButton.styleFrom(
                      foregroundColor: Color.fromARGB(255, 53, 10, 123),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 30),
              ElevatedButton(
                onPressed: _isLoading ? null : _submitAppointment,
                child:
                    _isLoading
                        ? SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2.0,
                          ),
                        )
                        : Text(
                          'Submit Request',
                          style: TextStyle(color: Colors.white),
                        ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Color.fromARGB(255, 53, 10, 123),
                  padding: EdgeInsets.symmetric(horizontal: 50, vertical: 15),
                  textStyle: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              SizedBox(height: 30),
              Divider(),
              SizedBox(height: 10),
              Text(
                'Your Appointments',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: Color.fromARGB(255, 53, 10, 123),
                ),
                textAlign: TextAlign.center,
              ),
              SizedBox(height: 10),
              _buildAppointmentsList(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAppointmentsList() {
    if (_isFetchingAppointments) {
      return Center(child: CircularProgressIndicator());
    }
    if (_appointmentsList.isEmpty) {
      return Center(child: Text('No appointments found.'));
    }
    return ListView.builder(
      shrinkWrap: true,
      physics: NeverScrollableScrollPhysics(),
      itemCount: _appointmentsList.length,
      itemBuilder: (context, index) {
        final appointment = _appointmentsList[index];
        final appointmentDate =
            appointment['appointment_date'] as String? ?? 'N/A';
        final appointmentTime =
            appointment['appointment_time'] as String? ?? 'N/A';
        final reason = appointment['reason'] as String? ?? 'No reason provided';
        final status = appointment['status'] as String? ?? 'Unknown';

        String formattedTime = appointmentTime;
        if (appointmentTime.contains(':')) {
          final parts = appointmentTime.split(':');
          if (parts.length >= 2) {
            formattedTime = '${parts[0]}:${parts[1]}';
          }
        }

        return Card(
          margin: EdgeInsets.symmetric(vertical: 8.0, horizontal: 4.0),
          elevation: 2.0,
          child: ListTile(
            title: Text(reason, style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(
              'Date: $appointmentDate\nTime: $formattedTime\nStatus: ${status.capitalize()}',
            ),
            isThreeLine: true,
            leading: Icon(
              status == 'confirmed'
                  ? Icons.check_circle
                  : status == 'pending'
                  ? Icons.hourglass_empty
                  : status == 'cancelled'
                  ? Icons.cancel
                  : status == 'completed'
                  ? Icons.event_available
                  : Icons.info_outline,
              color:
                  status == 'confirmed'
                      ? Colors.green
                      : status == 'pending'
                      ? Colors.orange
                      : status == 'cancelled'
                      ? Colors.red
                      : status == 'completed'
                      ? Colors.blue
                      : Colors.grey,
            ),
          ),
        );
      },
    );
  }
}

extension StringExtension on String {
  String capitalize() {
    if (this.isEmpty) {
      return "";
    }
    return "${this[0].toUpperCase()}${this.substring(1).toLowerCase()}";
  }
}
