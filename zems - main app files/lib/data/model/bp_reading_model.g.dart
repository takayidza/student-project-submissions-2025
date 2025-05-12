// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'bp_reading_model.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class BPReadingModelAdapter extends TypeAdapter<BPReadingModel> {
  @override
  final int typeId = 1;

  @override
  BPReadingModel read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return BPReadingModel(
      systolic: fields[0] as int,
      diastolic: fields[1] as int,
      pulse: fields[2] as int,
      dateTime: fields[3] as DateTime,
      description: fields[4] as String,
      details: fields[5] as String,
    );
  }

  @override
  void write(BinaryWriter writer, BPReadingModel obj) {
    writer
      ..writeByte(6)
      ..writeByte(0)
      ..write(obj.systolic)
      ..writeByte(1)
      ..write(obj.diastolic)
      ..writeByte(2)
      ..write(obj.pulse)
      ..writeByte(3)
      ..write(obj.dateTime)
      ..writeByte(4)
      ..write(obj.description)
      ..writeByte(5)
      ..write(obj.details);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is BPReadingModelAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
