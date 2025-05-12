import 'package:zems/utils/constant/image.dart';
import 'package:zems/utils/constant/routes.dart';
import 'package:zems/utils/helper/extention.dart';
import 'package:zems/utils/helper/scaffold_snakbar.dart';
import 'package:zems/logic/auth/log_out/log_out_cubit.dart';
import 'package:zems/view/widget/loading_indicator.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_svg/flutter_svg.dart';
import '../../utils/constant/color.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  void _initializeApp() {
    Future.delayed(
      const Duration(milliseconds: 1500),
      () {
        // Direct to guest mode screen by default
        Navigator.pushReplacementNamed(context, RouteManager.guestMode);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: context.theme.scaffoldBackgroundColor,
      body: Center(
        child: Stack(
          alignment: Alignment.center,
          children: [
            Image.asset(
              ImageManager.splashLogo,
              width: context.width / 3,
              height: context.width / 3,
            ),
            const BuidSplashLoadingIndicator(),
          ],
        ),
      ),
    );
  }
}
