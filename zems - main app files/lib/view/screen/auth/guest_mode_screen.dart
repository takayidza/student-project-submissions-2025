import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';
import '../../../utils/constant/color.dart';
import '../../../utils/constant/image.dart';
import '../../../utils/constant/routes.dart';
import '../../../utils/helper/extention.dart';
import '../../widget/custom_button.dart';
import 'package:flutter_svg/flutter_svg.dart';

class GuestModeScreen extends StatelessWidget {
  const GuestModeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: 24.w),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Gap(40.h),
              // Logo and Title
              Center(
                child: Column(
                  children: [
                    SvgPicture.asset(
                      ImageManager.splashLogo,
                      width: 120.w,
                      height: 120.w,
                    ),
                    Gap(16.h),
                    Text(
                      "Zimbabwe Emergency\nMedical Services",
                      textAlign: TextAlign.center,
                      style: context.textTheme.bodyLarge?.copyWith(
                        fontSize: 24.spMin,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Gap(8.h),
                    Text(
                      "Help is just a tap away",
                      style: context.textTheme.bodySmall?.copyWith(
                        color: ColorManager.grey,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              Gap(40.h),
              
              // Guest Mode Features
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "Available Features",
                        style: context.textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Gap(16.h),
                      _buildFeatureCard(
                        context,
                        "Emergency SOS",
                        "Quick access to emergency services and contacts",
                        ImageManager.ambulanceIcon,
                        () => Navigator.pushNamed(context, RouteManager.emergencySOS),
                      ),
                      Gap(12.h),
                      _buildFeatureCard(
                        context,
                        "Hospital Finder",
                        "Locate nearby medical facilities",
                        ImageManager.mapIcon,
                        () => Navigator.pushNamed(context, RouteManager.hospitalFinder),
                      ),
                      Gap(12.h),
                      _buildFeatureCard(
                        context,
                        "Chatbot and First Aid Guide",
                        "Stay informed on any medical queries",
                        ImageManager.trueIcon,
                        () => Navigator.pushNamed(context, RouteManager.firstAidGuide),
                      ),
                    ],
                  ),
                ),
              ),
              
              // Action Buttons
              Gap(24.h),
              CustomButton(
                title: "Continue as Guest",
                onPressed: () => Navigator.pushReplacementNamed(context, RouteManager.nav),
              ),
              Gap(12.h),
              CustomButton(
                title: "Login",
                backgroundColor: ColorManager.green,
                onPressed: () => Navigator.pushReplacementNamed(context, RouteManager.login),
              ),
              Gap(24.h),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureCard(
    BuildContext context,
    String title,
    String description,
    String iconPath,
    VoidCallback onTap,
  ) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: EdgeInsets.all(16.w),
        decoration: BoxDecoration(
          color: ColorManager.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: ColorManager.green.withOpacity(0.2),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: ColorManager.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: EdgeInsets.all(12.w),
              decoration: BoxDecoration(
                color: ColorManager.green.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: SvgPicture.asset(
                iconPath,
                width: 24.w,
                height: 24.w,
                color: ColorManager.green,
              ),
            ),
            Gap(16.w),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: context.textTheme.bodyMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  Gap(4.h),
                  Text(
                    description,
                    style: context.textTheme.bodySmall?.copyWith(
                      color: ColorManager.grey,
                    ),
                  ),
                ],
              ),
            ),
            
          ],
        ),
      ),
    );
  }
}