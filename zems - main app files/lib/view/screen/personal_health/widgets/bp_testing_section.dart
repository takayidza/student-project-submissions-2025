import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';
import '../../../../utils/constant/color.dart';
import '../../../../utils/helper/extention.dart';

class BPTestingSection extends StatefulWidget {
  const BPTestingSection({Key? key}) : super(key: key);

  @override
  State<BPTestingSection> createState() => _BPTestingSectionState();
}

class _BPTestingSectionState extends State<BPTestingSection> {
  int _systolicValue = 120;
  int _diastolicValue = 80;
  String _result = '';
  String _resultDescription = '';

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(16.w),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(),
          Gap(24.h),
          _buildBPInputs(),
          Gap(24.h),
          if (_result.isNotEmpty) _buildResult(),
          Gap(24.h),
          _buildSaveButton(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
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
            "Blood Pressure Testing",
            style: context.textTheme.titleLarge?.copyWith(
              color: ColorManager.green,
              fontWeight: FontWeight.bold,
            ),
          ),
          Gap(8.h),
          Text(
            "Enter your blood pressure readings to get an analysis based on WHO guidelines.",
            style: context.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }

  Widget _buildBPInputs() {
    return Row(
      children: [
        Expanded(
          child: _buildNumberPicker(
            title: "Systolic",
            value: _systolicValue,
            min: 60,
            max: 200,
            onChanged: (value) {
              setState(() {
                _systolicValue = value;
                _calculateResult();
              });
            },
          ),
        ),
        Gap(16.w),
        Expanded(
          child: _buildNumberPicker(
            title: "Diastolic",
            value: _diastolicValue,
            min: 40,
            max: 120,
            onChanged: (value) {
              setState(() {
                _diastolicValue = value;
                _calculateResult();
              });
            },
          ),
        ),
      ],
    );
  }

  Widget _buildNumberPicker({
    required String title,
    required int value,
    required int min,
    required int max,
    required ValueChanged<int> onChanged,
  }) {
    return Column(
      children: [
        Text(
          title,
          style: context.textTheme.titleMedium,
        ),
        Gap(8.h),
        Container(
          height: 150.h,
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
          child: ListWheelScrollView(
            itemExtent: 50.h,
            diameterRatio: 1.5,
            physics: const FixedExtentScrollPhysics(),
            children: List.generate(
              max - min + 1,
              (index) => Center(
                child: Text(
                  '${min + index}',
                  style: context.textTheme.titleLarge?.copyWith(
                    color: min + index == value ? ColorManager.green : ColorManager.grey,
                    fontWeight: min + index == value ? FontWeight.bold : FontWeight.normal,
                  ),
                ),
              ),
            ),
            onSelectedItemChanged: (index) => onChanged(min + index),
          ),
        ),
      ],
    );
  }

  Widget _buildResult() {
    return Container(
      padding: EdgeInsets.all(16.w),
      decoration: BoxDecoration(
        color: _getResultColor().withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            _result,
            style: context.textTheme.titleLarge?.copyWith(
              color: _getResultColor(),
              fontWeight: FontWeight.bold,
            ),
          ),
          Gap(8.h),
          Text(
            _resultDescription,
            style: context.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }

  Widget _buildSaveButton() {
    return ElevatedButton(
      onPressed: _saveBPReading,
      style: ElevatedButton.styleFrom(
        backgroundColor: ColorManager.green,
        minimumSize: Size(double.infinity, 50.h),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      child: Text(
        "Save Reading",
        style: context.textTheme.titleMedium?.copyWith(
          color: ColorManager.white,
        ),
      ),
    );
  }

  void _calculateResult() {
    if (_systolicValue < 90 || _diastolicValue < 60) {
      _result = "Low Blood Pressure";
      _resultDescription = "Your blood pressure is below normal. Consider consulting a healthcare provider if you experience symptoms like dizziness or fainting.";
    } else if (_systolicValue < 120 && _diastolicValue < 80) {
      _result = "Normal";
      _resultDescription = "Your blood pressure is within the normal range. Continue maintaining a healthy lifestyle.";
    } else if (_systolicValue < 130 && _diastolicValue < 80) {
      _result = "Elevated";
      _resultDescription = "Your blood pressure is slightly elevated. Consider lifestyle modifications like reducing salt intake and increasing physical activity.";
    } else if (_systolicValue < 140 || _diastolicValue < 90) {
      _result = "Stage 1 Hypertension";
      _resultDescription = "You have Stage 1 hypertension. Consult with a healthcare provider about lifestyle changes and potential medication.";
    } else {
      _result = "Stage 2 Hypertension";
      _resultDescription = "You have Stage 2 hypertension. Immediate medical attention is recommended.";
    }
  }

  Color _getResultColor() {
    switch (_result) {
      case "Low Blood Pressure":
        return Colors.blue;
      case "Normal":
        return Colors.green;
      case "Elevated":
        return Colors.orange;
      case "Stage 1 Hypertension":
        return Colors.deepOrange;
      case "Stage 2 Hypertension":
        return Colors.red;
      default:
        return ColorManager.green;
    }
  }

  void _saveBPReading() {
    // TODO: Implement saving BP reading to local storage or cloud
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("BP Reading saved: $_systolicValue/$_diastolicValue"),
        backgroundColor: ColorManager.green,
      ),
    );
  }
} 