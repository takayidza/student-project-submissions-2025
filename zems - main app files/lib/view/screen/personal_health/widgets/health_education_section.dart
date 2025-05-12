import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';
import '../../../../utils/constant/color.dart';
import '../../../../utils/helper/extention.dart';

class HealthEducationSection extends StatelessWidget {
  const HealthEducationSection({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(16.w),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(context),
          Gap(24.h),
          _buildHowToCheckBP(context),
          Gap(24.h),
          _buildHealthyRanges(context),
          Gap(24.h),
          _buildLifestyleTips(context),
          Gap(24.h),
          _buildLocalFoodOptions(context),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
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
            "Blood Pressure Guide",
            style: context.textTheme.titleLarge?.copyWith(
              color: ColorManager.green,
              fontWeight: FontWeight.bold,
            ),
          ),
          Gap(8.h),
          Text(
            "Learn about blood pressure, how to measure it, and ways to maintain healthy levels.",
            style: context.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }

  Widget _buildHowToCheckBP(BuildContext context) {
    return _buildSection(
      context,
      title: "How to Check Blood Pressure",
      content: [
        "1. Sit in a quiet place for 5 minutes before measuring",
        "2. Rest your arm on a flat surface at heart level",
        "3. Place the cuff on your bare upper arm",
        "4. Keep your feet flat on the floor",
        "5. Don't talk during the measurement",
        "6. Take multiple readings for accuracy",
      ],
      icon: Icons.health_and_safety,
    );
  }

  Widget _buildHealthyRanges(BuildContext context) {
    return _buildSection(
      context,
      title: "Healthy Blood Pressure Ranges",
      content: [
        "Normal: Less than 120/80 mmHg",
        "Elevated: 120-129/<80 mmHg",
        "Stage 1 Hypertension: 130-139/80-89 mmHg",
        "Stage 2 Hypertension: 140+/90+ mmHg",
        "Hypertensive Crisis: Higher than 180/120 mmHg",
      ],
      icon: Icons.show_chart,
    );
  }

  Widget _buildLifestyleTips(BuildContext context) {
    return _buildSection(
      context,
      title: "Lifestyle Tips",
      content: [
        "• Exercise regularly (30 minutes daily)",
        "• Maintain a healthy weight",
        "• Reduce salt intake",
        "• Limit alcohol consumption",
        "• Quit smoking",
        "• Manage stress through meditation or yoga",
        "• Get adequate sleep (7-8 hours)",
      ],
      icon: Icons.favorite,
    );
  }

  Widget _buildLocalFoodOptions(BuildContext context) {
    return _buildSection(
      context,
      title: "Local Food Options for Blood Pressure",
      content: [
        "Foods to Include:",
        "• Fresh vegetables (especially leafy greens)",
        "• Fruits (bananas, oranges, berries)",
        "• Whole grains (brown rice, whole wheat)",
        "• Lean proteins (fish, chicken)",
        "• Low-fat dairy products",
        "• Nuts and seeds",
        "• Herbs and spices instead of salt",
        "",
        "Foods to Limit:",
        "• Processed foods",
        "• Canned soups and vegetables",
        "• Deli meats",
        "• Fast food",
        "• Salty snacks",
        "• Pickled foods",
      ],
      icon: Icons.restaurant,
    );
  }

  Widget _buildSection(
    BuildContext context, {
    required String title,
    required List<String> content,
    required IconData icon,
  }) {
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
          Row(
            children: [
              Icon(icon, color: ColorManager.green),
              Gap(8.w),
              Text(
                title,
                style: context.textTheme.titleMedium?.copyWith(
                  color: ColorManager.green,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          Gap(16.h),
          ...content.map((item) => Padding(
                padding: EdgeInsets.only(bottom: 8.h),
                child: Text(
                  item,
                  style: context.textTheme.bodyMedium,
                ),
              )),
        ],
      ),
    );
  }
} 