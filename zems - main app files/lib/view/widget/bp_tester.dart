import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';
import 'package:intl/intl.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import 'package:share_plus/share_plus.dart';
import 'package:file_picker/file_picker.dart';
import '../../utils/constant/color.dart';
import '../../data/model/bp_reading_model.dart';

class BPTesterWidget extends StatefulWidget {
  const BPTesterWidget({Key? key}) : super(key: key);

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
  String _arm = '';
  String _position = '';
  String _condition = '';
  bool _saving = false;
  late Box<BPReadingModel> _bpBox;
  String _insight = '';

  @override
  void initState() {
    super.initState();
    _bpBox = Hive.box<BPReadingModel>('bp_readings');
    _updateInsight();
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

  String _bpLevel() {
    if (_systolic < 90 || _diastolic < 60) return 'Low';
    if (_systolic < 120 && _diastolic < 80) return 'Normal';
    if (_systolic < 130 && _diastolic < 80) return 'Elevated';
    if (_systolic < 140 || _diastolic < 90) return 'Stage 1 Hypertension';
    return 'Stage 2 Hypertension';
  }

  Color _bpLevelColor() {
    switch (_bpLevel()) {
      case 'Low':
        return Colors.blue;
      case 'Normal':
        return ColorManager.green;
      case 'Elevated':
        return Colors.orange;
      case 'Stage 1 Hypertension':
        return Colors.deepOrange;
      case 'Stage 2 Hypertension':
        return Colors.red;
      default:
        return ColorManager.green;
    }
  }

  IconData _bpLevelIcon() {
    switch (_bpLevel()) {
      case 'Low':
        return Icons.arrow_downward;
      case 'Normal':
        return Icons.check_circle;
      case 'Elevated':
        return Icons.warning_amber_rounded;
      case 'Stage 1 Hypertension':
      case 'Stage 2 Hypertension':
        return Icons.error;
      default:
        return Icons.check_circle;
    }
  }

  String _bpLevelDescription() {
    switch (_bpLevel()) {
      case 'Low':
        return 'SYS < 90 or DIA < 60';
      case 'Normal':
        return 'SYS < 120 and DIA < 80';
      case 'Elevated':
        return 'SYS 120 – 129 or DIA 80 – 89';
      case 'Stage 1 Hypertension':
        return 'SYS 130 – 139 or DIA 90 – 99';
      case 'Stage 2 Hypertension':
        return 'SYS ≥ 140 or DIA ≥ 100';
      default:
        return '';
    }
  }

  String _bpInsight() {
    switch (_bpLevel()) {
      case 'Low':
        return 'Your blood pressure is below normal. Consider consulting a healthcare provider if you experience symptoms.';
      case 'Normal':
        return 'Your blood pressure is within the normal range. Keep up the healthy lifestyle!';
      case 'Elevated':
        return 'Your blood pressure is slightly elevated. Consider lifestyle modifications like reducing salt intake and increasing physical activity.';
      case 'Stage 1 Hypertension':
        return 'You have Stage 1 hypertension. Consult with a healthcare provider about lifestyle changes and potential medication.';
      case 'Stage 2 Hypertension':
        return 'You have Stage 2 hypertension. Immediate medical attention is recommended.';
      default:
        return '';
    }
  }

  void _updateInsight() {
    setState(() {
      _insight = _bpInsight();
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
      details: '${_arm.isNotEmpty ? 'Arm: $_arm. ' : ''}${_position.isNotEmpty ? 'Position: $_position. ' : ''}${_condition.isNotEmpty ? 'Condition: $_condition.' : ''}',
    );
    await _bpBox.add(reading);
    setState(() => _saving = false);
    _updateInsight();
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

  Future<void> _importCSV() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['csv']);
    if (result != null && result.files.single.path != null) {
      final file = File(result.files.single.path!);
      final lines = await file.readAsLines();
      if (lines.length <= 1) return; // No data
      for (int i = 1; i < lines.length; i++) {
        final row = lines[i].split(',');
        if (row.length < 7) continue;
        try {
          final date = DateFormat('yyyy-MM-dd').parse(row[0].replaceAll('"', ''));
          final time = DateFormat('HH:mm').parse(row[1].replaceAll('"', ''));
          final dateTime = DateTime(date.year, date.month, date.day, time.hour, time.minute);
          final systolic = int.parse(row[2]);
          final diastolic = int.parse(row[3]);
          final pulse = int.parse(row[4]);
          final description = row[5].replaceAll('"', '');
          final details = row[6].replaceAll('"', '');
          await _bpBox.add(BPReadingModel(
            systolic: systolic,
            diastolic: diastolic,
            pulse: pulse,
            dateTime: dateTime,
            description: description,
            details: details,
          ));
        } catch (_) {}
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('CSV imported!'), backgroundColor: ColorManager.green),
      );
      _updateInsight();
    }
  }

  Widget _chip(String label, String value, void Function(String) onSelected) {
    return ChoiceChip(
      label: Text(label),
      selected: value.isNotEmpty,
      onSelected: (_) async {
        final result = await showDialog<String>(
          context: context,
          builder: (context) => AlertDialog(
            title: Text('Select $label'),
            content: TextField(
              autofocus: true,
              decoration: InputDecoration(hintText: 'Enter $label'),
              onSubmitted: (v) => Navigator.pop(context, v),
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context), child: Text('Cancel')),
            ],
          ),
        );
        if (result != null && result.isNotEmpty) onSelected(result);
      },
      selectedColor: ColorManager.green.withOpacity(0.2),
      backgroundColor: ColorManager.green.withOpacity(0.08),
      labelStyle: TextStyle(color: ColorManager.green),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Padding(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Blood Pressure', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                IconButton(
                  icon: Icon(Icons.watch),
                  tooltip: 'Pair Wearable Watch',
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Pairing feature coming soon!'), backgroundColor: ColorManager.green),
                    );
                  },
                ),
              ],
            ),
            Gap(8.h),
            Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextFormField(
                    initialValue: _description,
                    decoration: InputDecoration(labelText: 'Add description'),
                    onSaved: (v) => _description = v ?? '',
                  ),
                  Gap(16.h),
                  InkWell(
                    onTap: _pickDateTime,
                    child: InputDecorator(
                      decoration: InputDecoration(
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.calendar_today, size: 20, color: ColorManager.green),
                          Gap(8.w),
                          Text(DateFormat('dd.MM.yyyy HH:mm').format(_selectedDate), style: TextStyle(color: ColorManager.green)),
                        ],
                      ),
                    ),
                  ),
                  Gap(16.h),
                  Container(
                    padding: EdgeInsets.all(12.w),
                    decoration: BoxDecoration(
                      color: _bpLevelColor().withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(_bpLevelIcon(), color: _bpLevelColor()),
                        Gap(8.w),
                        Text(
                          _bpLevel(),
                          style: TextStyle(fontWeight: FontWeight.bold, color: _bpLevelColor()),
                        ),
                        Gap(8.w),
                        Expanded(
                          child: Text(
                            _bpLevelDescription(),
                            style: TextStyle(color: _bpLevelColor()),
                          ),
                        ),
                        Tooltip(
                          message: _insight,
                          child: Icon(Icons.info_outline, color: _bpLevelColor()),
                        ),
                      ],
                    ),
                  ),
                  Gap(8.h),
                  Text(
                    _insight,
                    style: TextStyle(color: _bpLevelColor(), fontWeight: FontWeight.w600),
                  ),
                  Gap(16.h),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _numberPicker('Systolic', 60, 250, _systolic, (v) => setState(() { _systolic = v; _updateInsight(); })),
                      _numberPicker('Diastolic', 40, 150, _diastolic, (v) => setState(() { _diastolic = v; _updateInsight(); })),
                      _numberPicker('Pulse', 30, 200, _pulse, (v) => setState(() { _pulse = v; })),
                    ],
                  ),
                  Gap(16.h),
                  Text('Add details', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  Gap(8.h),
                  Row(
                    children: [
                      _chip('Arm', _arm, (v) => setState(() => _arm = v)),
                      Gap(8.w),
                      _chip('Position', _position, (v) => setState(() => _position = v)),
                      Gap(8.w),
                      _chip('Conditions', _condition, (v) => setState(() => _condition = v)),
                    ],
                  ),
                  Gap(24.h),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _saving ? null : _saveReading,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: ColorManager.green,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                        minimumSize: Size(double.infinity, 48),
                      ),
                      child: _saving ? CircularProgressIndicator(color: Colors.white) : Text('Done'),
                    ),
                  ),
                  Gap(12.h),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _exportCSV,
                          icon: Icon(Icons.download, color: ColorManager.green),
                          label: Text('Export to CSV', style: TextStyle(color: ColorManager.green)),
                          style: OutlinedButton.styleFrom(
                            side: BorderSide(color: ColorManager.green),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                          ),
                        ),
                      ),
                      Gap(12.w),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _importCSV,
                          icon: Icon(Icons.upload, color: ColorManager.green),
                          label: Text('Import CSV', style: TextStyle(color: ColorManager.green)),
                          style: OutlinedButton.styleFrom(
                            side: BorderSide(color: ColorManager.green),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            Gap(24.h),
            Text('History', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            Gap(8.h),
            ValueListenableBuilder(
              valueListenable: _bpBox.listenable(),
              builder: (context, Box<BPReadingModel> box, _) {
                final readings = box.values.toList().reversed.toList();
                if (readings.isEmpty) {
                  return Text('No readings yet.', style: Theme.of(context).textTheme.bodyMedium);
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
                              Text('${r.systolic}/${r.diastolic} mmHg', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                              Text('Pulse: ${r.pulse} BPM', style: Theme.of(context).textTheme.bodySmall),
                              Text(DateFormat('dd.MM.yyyy HH:mm').format(r.dateTime), style: Theme.of(context).textTheme.bodySmall),
                              if (r.description.isNotEmpty) Text(r.description, style: Theme.of(context).textTheme.bodySmall),
                              if (r.details.isNotEmpty) Text(r.details, style: Theme.of(context).textTheme.bodySmall),
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