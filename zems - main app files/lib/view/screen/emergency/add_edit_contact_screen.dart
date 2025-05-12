import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';
import '../../../utils/constant/color.dart';
import '../../../utils/helper/extention.dart';
import '../../../data/model/emergency_contact_model.dart';
import '../../../logic/emergency_contacts/emergency_contacts_cubit.dart';
import '../../widget/custom_button.dart';
import '../../widget/custom_scrollable_appbar.dart';
import '../../widget/custom_text_field.dart';

class AddEditContactScreen extends StatefulWidget {
  final EmergencyContact? contact;

  const AddEditContactScreen({super.key, this.contact});

  @override
  State<AddEditContactScreen> createState() => _AddEditContactScreenState();
}

class _AddEditContactScreenState extends State<AddEditContactScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  late TextEditingController _relationshipController;
  late TextEditingController _phoneController;
  late TextEditingController _medicalNotesController;
  String _selectedCategory = 'Family';
  int _selectedPriority = 1;

  final List<String> _categories = [
    'Family',
    'Medical',
    'Police',
    'Fire',
    'Ambulance',
    'Other'
  ];

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.contact?.name);
    _relationshipController = TextEditingController(text: widget.contact?.relationship);
    _phoneController = TextEditingController(text: widget.contact?.phoneNumber);
    _medicalNotesController = TextEditingController(text: widget.contact?.medicalNotes);
    if (widget.contact != null) {
      _selectedCategory = widget.contact!.category;
      _selectedPriority = widget.contact!.priority;
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _relationshipController.dispose();
    _phoneController.dispose();
    _medicalNotesController.dispose();
    super.dispose();
  }

  void _saveContact() {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();

      if (widget.contact == null) {
        // Add new contact
        context.read<EmergencyContactsCubit>().addContact(
          AddEmergencyContact(
            name: _nameController.text,
            relationship: _relationshipController.text,
            phoneNumber: _phoneController.text,
            priority: _selectedPriority,
            medicalNotes: _medicalNotesController.text,
            category: _selectedCategory,
          ),
        );
      } else {
        // Update existing contact
        context.read<EmergencyContactsCubit>().updateContact(
          UpdateEmergencyContact(
            widget.contact!.copyWith(
              name: _nameController.text,
              relationship: _relationshipController.text,
              phoneNumber: _phoneController.text,
              priority: _selectedPriority,
              medicalNotes: _medicalNotesController.text,
              category: _selectedCategory,
            ),
          ),
        );
      }

      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          CustomTitleBackButton(
            title: widget.contact == null ? "Add Contact" : "Edit Contact",
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.all(16.w),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CustomTextFormField(
                      controller: _nameController,
                      title: "Name",
                      hintText: "Enter contact name",
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter a name';
                        }
                        return null;
                      },
                    ),
                    Gap(16.h),
                    CustomTextFormField(
                      controller: _relationshipController,
                      title: "Relationship",
                      hintText: "Enter relationship",
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter a relationship';
                        }
                        return null;
                      },
                    ),
                    Gap(16.h),
                    CustomTextFormField(
                      controller: _phoneController,
                      title: "Phone Number",
                      hintText: "Enter phone number",
                      keyboardType: TextInputType.phone,
                      validator: (value) {
                        if (value == null || value.isEmpty) {
                          return 'Please enter a phone number';
                        }
                        return null;
                      },
                    ),
                    Gap(16.h),
                    Text(
                      "Category",
                      style: context.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Gap(8.h),
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 12.w),
                      decoration: BoxDecoration(
                        border: Border.all(color: ColorManager.grey),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          value: _selectedCategory,
                          isExpanded: true,
                          items: _categories.map((String category) {
                            return DropdownMenuItem<String>(
                              value: category,
                              child: Text(category),
                            );
                          }).toList(),
                          onChanged: (String? newValue) {
                            if (newValue != null) {
                              setState(() {
                                _selectedCategory = newValue;
                              });
                            }
                          },
                        ),
                      ),
                    ),
                    Gap(16.h),
                    Text(
                      "Priority Level",
                      style: context.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Gap(8.h),
                    Row(
                      children: List.generate(3, (index) {
                        final priority = index + 1;
                        return Expanded(
                          child: GestureDetector(
                            onTap: () {
                              setState(() {
                                _selectedPriority = priority;
                              });
                            },
                            child: Container(
                              margin: EdgeInsets.symmetric(horizontal: 4.w),
                              padding: EdgeInsets.symmetric(vertical: 8.h),
                              decoration: BoxDecoration(
                                color: _selectedPriority == priority
                                    ? ColorManager.green
                                    : ColorManager.grey.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(
                                  color: _selectedPriority == priority
                                      ? ColorManager.green
                                      : ColorManager.grey,
                                ),
                              ),
                              child: Center(
                                child: Text(
                                  "Level $priority",
                                  style: context.textTheme.bodySmall?.copyWith(
                                    color: _selectedPriority == priority
                                        ? ColorManager.white
                                        : ColorManager.grey,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        );
                      }),
                    ),
                    Gap(16.h),
                    CustomTextFormField(
                      controller: _medicalNotesController,
                      title: "Medical Notes (Optional)",
                      hintText: "Enter any relevant medical information",
                    ),
                    Gap(32.h),
                    CustomButton(
                      title: widget.contact == null ? "Add Contact" : "Save Changes",
                      onPressed: _saveContact,
                    ),
                    Gap(16.h),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
} 