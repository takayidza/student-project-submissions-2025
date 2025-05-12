import 'package:zems/utils/constant/image.dart';
import 'package:zems/utils/constant/routes.dart';
import 'package:zems/utils/helper/extention.dart';
import 'package:zems/view/widget/custom_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';
import '../../../utils/constant/color.dart';
import '../../../logic/chat/chat_cubit.dart';
import '../../widget/emergency_contacts.dart';
import 'package:intl/intl.dart';
import '../../../data/model/bp_reading_model.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:share_plus/share_plus.dart';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../data/model/medical_guides_data.dart';
import '../../../data/model/medical_guide_model.dart';
import '../../widget/bp_tester.dart';
import '../bp_tracker_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: context.theme.scaffoldBackgroundColor,
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
          child: Column(
            children: [
              Gap(32.h),
              _buildChatCard(context),
              Gap(24.h),
              _buildBPTrackerCard(context),
              Gap(32.h),
              _buildPanicButton(context),
              Gap(32.h),
              _buildMedicalAidGuides(context),
              Gap(32.h),
              const EmergencyContacts(),
              Gap(32.h),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChatCard(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: ColorManager.green.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Message the Chatbot ",
            style: context.textTheme.titleLarge?.copyWith(
              color: ColorManager.green,
              fontWeight: FontWeight.bold,
            ),
          ),
          Gap(8.h),
          Text(
            "Get information on all your medical enquiries  ",
            style: context.textTheme.bodyMedium,
          ),
          Gap(16.h),
          CustomButton(
            title: "Start Chat",
            onPressed: () {
              context.bloc<ChatCubit>().initHive();
              Navigator.pushNamed(context, RouteManager.chat);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildBPTrackerCard(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const BPTrackerScreen()),
      ),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: EdgeInsets.all(16.w),
        decoration: BoxDecoration(
          color: ColorManager.green.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Container(
              padding: EdgeInsets.all(12.w),
              decoration: BoxDecoration(
                color: ColorManager.green.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(Icons.monitor_heart, color: ColorManager.green, size: 32),
            ),
            Gap(16.w),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'B.P Tracker',
                    style: context.textTheme.titleMedium?.copyWith(
                      color: ColorManager.green,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Gap(4.h),
                  Text(
                    'Track, import, and export your blood pressure readings.',
                    style: context.textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            Icon(Icons.arrow_forward_ios, color: ColorManager.green, size: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildBPTester(BuildContext context) {
    return BPTesterWidget();
  }

  Widget _buildPanicButton(BuildContext context) {
    return PanicButtonCard();
  }

  Widget _buildMedicalAidGuides(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: ColorManager.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: ColorManager.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Medical Aid Guides",
            style: context.textTheme.titleLarge?.copyWith(
              color: ColorManager.green,
              fontWeight: FontWeight.bold,
            ),
          ),
          Gap(16.h),
          SizedBox(
            height: 140,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: medicalGuides.length,
              separatorBuilder: (context, index) => Gap(12.w),
              itemBuilder: (context, index) {
                final guide = medicalGuides[index];
                return GestureDetector(
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => MedicalGuideDetailPage(guide: guide),
                    ),
                  ),
                  child: Container(
                    width: 200,
                    padding: EdgeInsets.all(12.w),
                    decoration: BoxDecoration(
                      color: ColorManager.green.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          guide.title,
                          style: context.textTheme.titleSmall?.copyWith(
                            color: ColorManager.green,
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Gap(8.h),
                        Text(
                          guide.description,
                          style: context.textTheme.bodySmall,
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class BPTesterWidget extends StatefulWidget {
  @override
  State<BPTesterWidget> createState() => _BPTesterWidgetState();
}

class _BPTesterWidgetState extends State<BPTesterWidget> {
  final _formKey = GlobalKey<FormState>();
  int _systolic = 120;
  int _diastolic = 80;
  int _pulse = 80;
  DateTime _selectedDate = DateTime.now();
  String _description = '';
  String _details = '';
  bool _saving = false;

  late Box<BPReadingModel> _bpBox;

  @override
  void initState() {
    super.initState();
    _bpBox = Hive.box<BPReadingModel>('bp_readings');
  }

  Future<void> _pickDateTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
    );
    if (date == null) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_selectedDate),
    );
    if (time == null) return;
    setState(() {
      _selectedDate = DateTime(date.year, date.month, date.day, time.hour, time.minute);
    });
  }

  Future<void> _saveReading() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    _formKey.currentState!.save();
    final reading = BPReadingModel(
      systolic: _systolic,
      diastolic: _diastolic,
      pulse: _pulse,
      dateTime: _selectedDate,
      description: _description,
      details: _details,
    );
    await _bpBox.add(reading);
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('BP Reading saved!'), backgroundColor: ColorManager.green),
    );
  }

  Future<void> _exportCSV() async {
    final readings = _bpBox.values.toList();
    if (readings.isEmpty) return;
    final buffer = StringBuffer();
    buffer.writeln('Date,Time,Systolic,Diastolic,Pulse,Description,Details');
    for (final r in readings) {
      final date = DateFormat('yyyy-MM-dd').format(r.dateTime);
      final time = DateFormat('HH:mm').format(r.dateTime);
      buffer.writeln('"$date","$time",${r.systolic},${r.diastolic},${r.pulse},"${r.description}","${r.details}"');
    }
    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/bp_readings.csv');
    await file.writeAsString(buffer.toString());
    await Share.shareXFiles([XFile(file.path)], text: 'My BP Readings');
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: ColorManager.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: ColorManager.grey.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Blood Pressure', style: context.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
          Gap(8.h),
          Form(
            key: _formKey,
            child: Column(
              children: [
                TextFormField(
                  initialValue: _description,
                  decoration: InputDecoration(labelText: 'Add description'),
                  onSaved: (v) => _description = v ?? '',
                ),
                Gap(8.h),
                InkWell(
                  onTap: _pickDateTime,
                  child: InputDecorator(
                    decoration: InputDecoration(
                      labelText: 'Date & Time',
                      border: OutlineInputBorder(),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.calendar_today, size: 20),
                        Gap(8.w),
                        Text(DateFormat('dd.MM.yyyy HH:mm').format(_selectedDate)),
                      ],
                    ),
                  ),
                ),
                Gap(16.h),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _numberPicker('Systolic', 60, 250, _systolic, (v) => setState(() => _systolic = v)),
                    _numberPicker('Diastolic', 40, 150, _diastolic, (v) => setState(() => _diastolic = v)),
                    _numberPicker('Pulse', 30, 200, _pulse, (v) => setState(() => _pulse = v)),
                  ],
                ),
                Gap(16.h),
                TextFormField(
                  initialValue: _details,
                  decoration: InputDecoration(labelText: 'Add details (optional)'),
                  onSaved: (v) => _details = v ?? '',
                ),
                Gap(16.h),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _saving ? null : _saveReading,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: ColorManager.green,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        child: _saving ? CircularProgressIndicator(color: Colors.white) : Text('Save'),
                      ),
                    ),
                    Gap(12.w),
                    ElevatedButton.icon(
                      onPressed: _exportCSV,
                      icon: Icon(Icons.download),
                      label: Text('Export CSV'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: ColorManager.green.withOpacity(0.8),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Gap(24.h),
          Text('Previous Readings', style: context.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          Gap(8.h),
          ValueListenableBuilder(
            valueListenable: _bpBox.listenable(),
            builder: (context, Box<BPReadingModel> box, _) {
              final readings = box.values.toList().reversed.toList();
              if (readings.isEmpty) {
                return Text('No readings yet.', style: context.textTheme.bodyMedium);
              }
              return ListView.separated(
                shrinkWrap: true,
                physics: NeverScrollableScrollPhysics(),
                itemCount: readings.length,
                separatorBuilder: (context, i) => Gap(8.h),
                itemBuilder: (context, i) {
                  final r = readings[i];
                  return Container(
                    padding: EdgeInsets.all(12.w),
                    decoration: BoxDecoration(
                      color: ColorManager.green.withOpacity(0.06),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('${r.systolic}/${r.diastolic} mmHg', style: context.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                            Text('Pulse: ${r.pulse} BPM', style: context.textTheme.bodySmall),
                            Text(DateFormat('dd.MM.yyyy HH:mm').format(r.dateTime), style: context.textTheme.bodySmall),
                            if (r.description.isNotEmpty) Text(r.description, style: context.textTheme.bodySmall),
                          ],
                        ),
                        Icon(Icons.favorite, color: ColorManager.green),
                      ],
                    ),
                  );
                },
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _numberPicker(String label, int min, int max, int value, ValueChanged<int> onChanged) {
    return Column(
      children: [
        Text(label, style: TextStyle(fontWeight: FontWeight.bold)),
        SizedBox(
          height: 80,
          width: 60,
          child: ListWheelScrollView.useDelegate(
            itemExtent: 32,
            diameterRatio: 1.2,
            physics: FixedExtentScrollPhysics(),
            onSelectedItemChanged: (i) => onChanged(min + i),
            childDelegate: ListWheelChildBuilderDelegate(
              builder: (context, i) => Text('${min + i}', style: TextStyle(fontSize: 18)),
              childCount: max - min + 1,
            ),
            controller: FixedExtentScrollController(initialItem: value - min),
          ),
        ),
      ],
    );
  }
}

class PanicButtonCard extends StatefulWidget {
  @override
  State<PanicButtonCard> createState() => _PanicButtonCardState();
}

class _PanicButtonCardState extends State<PanicButtonCard> {
  String _defaultAction = 'call';
  String _phoneNumber = '';
  String _smsMessage = 'This is an emergency! Please help!';
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _defaultAction = prefs.getString('panic_action') ?? 'call';
      _phoneNumber = prefs.getString('panic_number') ?? '';
      _smsMessage = prefs.getString('panic_sms') ?? 'This is an emergency! Please help!';
      _loading = false;
    });
  }

  Future<void> _saveSettings() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('panic_action', _defaultAction);
    await prefs.setString('panic_number', _phoneNumber);
    await prefs.setString('panic_sms', _smsMessage);
    setState(() {});
  }

  void _showSettingsDialog() {
    String tempAction = _defaultAction;
    String tempNumber = _phoneNumber;
    String tempSms = _smsMessage;
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Panic Button Settings'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Expanded(child: Text('Default Action:')),
                  DropdownButton<String>(
                    value: tempAction,
                    items: [
                      DropdownMenuItem(value: 'call', child: Text('Call')),
                      DropdownMenuItem(value: 'sms', child: Text('SMS')),
                    ],
                    onChanged: (v) {
                      setState(() => tempAction = v ?? 'call');
                    },
                  ),
                ],
              ),
              TextField(
                decoration: InputDecoration(labelText: 'Phone Number'),
                keyboardType: TextInputType.phone,
                controller: TextEditingController(text: tempNumber),
                onChanged: (v) => tempNumber = v,
              ),
              TextField(
                decoration: InputDecoration(labelText: 'SMS Message'),
                controller: TextEditingController(text: tempSms),
                onChanged: (v) => tempSms = v,
                maxLines: 2,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _defaultAction = tempAction;
                _phoneNumber = tempNumber;
                _smsMessage = tempSms;
              });
              _saveSettings();
              Navigator.pop(context);
            },
            child: Text('Save'),
          ),
        ],
      ),
    );
  }

  Future<void> _triggerPanic() async {
    if (_phoneNumber.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please set a phone number in Panic Button settings.'), backgroundColor: Colors.red),
      );
      return;
    }
    if (_defaultAction == 'call') {
      final uri = Uri(scheme: 'tel', path: _phoneNumber);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not launch phone dialer.'), backgroundColor: Colors.red),
        );
      }
    } else {
      final uri = Uri(scheme: 'sms', path: _phoneNumber, queryParameters: {'body': _smsMessage});
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not launch SMS app.'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Emergency Panic Button', style: context.textTheme.titleLarge?.copyWith(color: Colors.red, fontWeight: FontWeight.bold)),
                Gap(8.h),
                Text('Press to immediately call or text emergency services.', style: context.textTheme.bodyMedium),
                Gap(12.h),
                ElevatedButton(
                  onPressed: _loading ? null : _triggerPanic,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    minimumSize: Size(double.infinity, 48),
                  ),
                  child: Text(_defaultAction == 'call' ? 'EMERGENCY CALL' : 'EMERGENCY SMS', style: TextStyle(color: Colors.white)),
                ),
              ],
            ),
          ),
          IconButton(
            icon: Icon(Icons.settings, color: Colors.red),
            onPressed: _showSettingsDialog,
            tooltip: 'Settings',
          ),
        ],
      ),
    );
  }
}

class MedicalGuideDetailPage extends StatelessWidget {
  final MedicalGuideModel guide;
  const MedicalGuideDetailPage({required this.guide});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(guide.title),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                guide.title,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 12),
              Text(
                guide.description,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              SizedBox(height: 24),
              Text(
                guide.expandedInfo,
                style: Theme.of(context).textTheme.bodyLarge,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
