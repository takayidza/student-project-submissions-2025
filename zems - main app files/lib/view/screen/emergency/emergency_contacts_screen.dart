import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../utils/constant/color.dart';
import '../../../utils/constant/image.dart';
import '../../../utils/helper/extention.dart';
import '../../../utils/helper/scaffold_snakbar.dart';
import '../../../data/model/emergency_contact_model.dart';
import '../../../logic/emergency_contacts/emergency_contacts_cubit.dart';
import '../../widget/custom_button.dart';
import '../../widget/custom_scrollable_appbar.dart';
import 'add_edit_contact_screen.dart';

class EmergencyContactsScreen extends StatefulWidget {
  const EmergencyContactsScreen({super.key});

  @override
  State<EmergencyContactsScreen> createState() => _EmergencyContactsScreenState();
}

class _EmergencyContactsScreenState extends State<EmergencyContactsScreen> {
  @override
  void initState() {
    super.initState();
    context.read<EmergencyContactsCubit>().loadContacts();
  }

  Future<void> _makePhoneCall(String phoneNumber) async {
    final Uri launchUri = Uri(
      scheme: 'tel',
      path: phoneNumber,
    );
    try {
      if (await canLaunchUrl(launchUri)) {
        await launchUrl(launchUri);
      } else {
        customSnackBar(context, 'Could not launch phone call');
      }
    } catch (e) {
      customSnackBar(context, 'Error making phone call: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          const CustomTitleBackButton(
            title: "Emergency Contacts",
          ),
          Expanded(
            child: BlocBuilder<EmergencyContactsCubit, EmergencyContactsState>(
              builder: (context, state) {
                if (state is EmergencyContactsLoading) {
                  return const Center(child: CircularProgressIndicator());
                }

                if (state is EmergencyContactsError) {
                  return Center(
                    child: Text(
                      state.message,
                      style: context.textTheme.bodyMedium?.copyWith(
                        color: ColorManager.error,
                      ),
                    ),
                  );
                }

                if (state is EmergencyContactsLoaded) {
                  if (state.contacts.isEmpty) {
                    return _buildEmptyState();
                  }

                  return _buildContactsList(state.contacts);
                }

                return const SizedBox();
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => const AddEditContactScreen(),
            ),
          );
        },
        backgroundColor: ColorManager.green,
        child: const Icon(Icons.add, color: ColorManager.white),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SvgPicture.asset(
            ImageManager.userIcon,
            width: 100.w,
            height: 100.w,
            color: ColorManager.grey,
          ),
          Gap(16.h),
          Text(
            "No Emergency Contacts",
            style: context.textTheme.bodyLarge?.copyWith(
              color: ColorManager.grey,
            ),
          ),
          Gap(8.h),
          Text(
            "Add your emergency contacts to get started",
            style: context.textTheme.bodySmall?.copyWith(
              color: ColorManager.grey,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildContactsList(List<EmergencyContact> contacts) {
    // Group contacts by category
    final Map<String, List<EmergencyContact>> groupedContacts = {};
    for (var contact in contacts) {
      if (!groupedContacts.containsKey(contact.category)) {
        groupedContacts[contact.category] = [];
      }
      groupedContacts[contact.category]!.add(contact);
    }

    return ListView.builder(
      padding: EdgeInsets.all(16.w),
      itemCount: groupedContacts.length,
      itemBuilder: (context, index) {
        final category = groupedContacts.keys.elementAt(index);
        final categoryContacts = groupedContacts[category]!;
        
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              category,
              style: context.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
                color: ColorManager.green,
              ),
            ),
            Gap(8.h),
            ...categoryContacts.map((contact) => _buildContactCard(contact)),
            Gap(16.h),
          ],
        );
      },
    );
  }

  Widget _buildContactCard(EmergencyContact contact) {
    return Card(
      margin: EdgeInsets.only(bottom: 8.h),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        contact.name,
                        style: context.textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Gap(4.h),
                      Text(
                        contact.relationship,
                        style: context.textTheme.bodySmall?.copyWith(
                          color: ColorManager.grey,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => _makePhoneCall(contact.phoneNumber),
                  icon: const Icon(
                    Icons.phone,
                    color: ColorManager.green,
                  ),
                ),
                IconButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => AddEditContactScreen(
                          contact: contact,
                        ),
                      ),
                    );
                  },
                  icon: const Icon(
                    Icons.edit,
                    color: ColorManager.grey,
                  ),
                ),
              ],
            ),
            if (contact.medicalNotes != null) ...[
              Gap(8.h),
              Text(
                "Medical Notes:",
                style: context.textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              Gap(4.h),
              Text(
                contact.medicalNotes!,
                style: context.textTheme.bodySmall,
              ),
            ],
          ],
        ),
      ),
    );
  }
} 