import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:gap/gap.dart';
import '../../../utils/constant/color.dart';
import '../../../utils/helper/extention.dart';
import '../../../utils/constant/image.dart';
import '../../../utils/constant/routes.dart';
import 'widgets/bp_testing_section.dart';
import 'widgets/health_education_section.dart';

class PersonalHealthScreen extends StatefulWidget {
  const PersonalHealthScreen({Key? key}) : super(key: key);

  @override
  State<PersonalHealthScreen> createState() => _PersonalHealthScreenState();
}

class _PersonalHealthScreenState extends State<PersonalHealthScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Personal Health"),
        bottom: TabBar(
          controller: _tabController,
          labelColor: ColorManager.green,
          unselectedLabelColor: ColorManager.grey,
          indicatorColor: ColorManager.green,
          tabs: const [
            Tab(text: "BP Testing"),
            Tab(text: "Health Guide"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          BPTestingSection(),
          HealthEducationSection(),
        ],
      ),
    );
  }
} 