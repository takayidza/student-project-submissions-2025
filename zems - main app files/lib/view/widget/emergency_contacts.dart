import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';
import '../../utils/constant/color.dart';
import '../../utils/helper/extention.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class EmergencyContacts extends StatefulWidget {
  const EmergencyContacts({super.key});

  @override
  State<EmergencyContacts> createState() => _EmergencyContactsState();
}

class _EmergencyContactsState extends State<EmergencyContacts> {
  final List<Map<String, String>> emergencyServices = [
    {
      'name': 'Zimbabwe Police',
      'number': '995',
      'icon': Icons.local_police.codePoint.toString()
    },
    {
      'name': 'Ambulance',
      'number': '994',
      'icon': Icons.emergency.codePoint.toString()
    },
    {
      'name': 'Fire Brigade',
      'number': '993',
      'icon': Icons.fire_truck.codePoint.toString()
    },
    {
      'name': 'National Emergency',
      'number': '999',
      'icon': Icons.emergency_share.codePoint.toString()
    },
  ];

  List<Map<String, String>> favoriteContacts = [];
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _numberController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadFavoriteContacts();
  }

  Future<void> _loadFavoriteContacts() async {
    final prefs = await SharedPreferences.getInstance();
    final contactsJson = prefs.getString('favoriteContacts');
    if (contactsJson != null) {
      setState(() {
        favoriteContacts = List<Map<String, String>>.from(
          json.decode(contactsJson).map((x) => Map<String, String>.from(x)),
        );
      });
    }
  }

  Future<void> _saveFavoriteContacts() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('favoriteContacts', json.encode(favoriteContacts));
  }

  void _addContact() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Add Emergency Contact',
            style: context.textTheme.titleMedium),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Name',
                border: OutlineInputBorder(),
              ),
            ),
            Gap(8.h),
            TextField(
              controller: _numberController,
              decoration: const InputDecoration(
                labelText: 'Phone Number',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.phone,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              if (_nameController.text.isNotEmpty &&
                  _numberController.text.isNotEmpty) {
                setState(() {
                  favoriteContacts.add({
                    'name': _nameController.text,
                    'number': _numberController.text,
                    'icon': Icons.person.codePoint.toString(),
                  });
                });
                _saveFavoriteContacts();
                _nameController.clear();
                _numberController.clear();
                Navigator.pop(context);
              }
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  void _removeContact(int index) {
    setState(() {
      favoriteContacts.removeAt(index);
    });
    _saveFavoriteContacts();
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: ColorManager.grey.withOpacity(0.3),
          width: 0.5,
        ),
      ),
      color: ColorManager.white.withOpacity(0.9),
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Emergency Contacts',
                  style: context.textTheme.titleLarge,
                ),
                IconButton(
                  icon: const Icon(Icons.add),
                  onPressed: _addContact,
                  color: ColorManager.green,
                ),
              ],
            ),
            Gap(16.h),
            Text(
              'Zimbabwe Emergency Services',
              style: context.textTheme.titleMedium,
            ),
            Gap(8.h),
            Wrap(
              spacing: 8.w,
              runSpacing: 8.h,
              children: emergencyServices.map((service) {
                return _buildContactCard(
                  name: service['name']!,
                  number: service['number']!,
                  iconData: IconData(
                    int.parse(service['icon']!),
                    fontFamily: 'MaterialIcons',
                  ),
                  isEmergencyService: true,
                );
              }).toList(),
            ),
            if (favoriteContacts.isNotEmpty) ...[
              Gap(16.h),
              Text(
                'Favorite Contacts',
                style: context.textTheme.titleMedium,
              ),
              Gap(8.h),
              Wrap(
                spacing: 8.w,
                runSpacing: 8.h,
                children: List.generate(
                  favoriteContacts.length,
                  (index) => _buildContactCard(
                    name: favoriteContacts[index]['name']!,
                    number: favoriteContacts[index]['number']!,
                    iconData: IconData(
                      int.parse(favoriteContacts[index]['icon']!),
                      fontFamily: 'MaterialIcons',
                    ),
                    onDelete: () => _removeContact(index),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildContactCard({
    required String name,
    required String number,
    required IconData iconData,
    bool isEmergencyService = false,
    VoidCallback? onDelete,
  }) {
    return Container(
      width: 150.w,
      padding: EdgeInsets.all(12.w),
      decoration: BoxDecoration(
        color: isEmergencyService
            ? ColorManager.green.withOpacity(0.1)
            : ColorManager.grey.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(iconData,
                  color: isEmergencyService
                      ? ColorManager.green
                      : ColorManager.grey),
              if (!isEmergencyService && onDelete != null)
                IconButton(
                  icon: const Icon(Icons.close, size: 16),
                  onPressed: onDelete,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                  color: ColorManager.grey,
                ),
            ],
          ),
          Gap(8.h),
          Text(
            name,
            style: context.textTheme.bodyMedium,
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          Gap(4.h),
          Text(
            number,
            style: context.textTheme.bodyLarge?.copyWith(
              color: ColorManager.green,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _numberController.dispose();
    super.dispose();
  }
}
