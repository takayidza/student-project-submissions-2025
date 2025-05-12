import 'package:hive/hive.dart';
part 'bp_reading_model.g.dart';

@HiveType(typeId: 1)
class BPReadingModel {
  @HiveField(0)
  final int systolic;
  @HiveField(1)
  final int diastolic;
  @HiveField(2)
  final int pulse;
  @HiveField(3)
  final DateTime dateTime;
  @HiveField(4)
  final String description;
  @HiveField(5)
  final String details;

  BPReadingModel({
    required this.systolic,
    required this.diastolic,
    required this.pulse,
    required this.dateTime,
    this.description = '',
    this.details = '',
  });
} 