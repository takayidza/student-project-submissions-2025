import 'package:zems/utils/helper/extention.dart';
import 'package:zems/logic/validation/formvalidation_cubit.dart';
import 'package:zems/view/widget/button_loading_indicator.dart';
import 'package:zems/view/widget/custom_text_field.dart';
import 'package:zems/view/widget/my_stepper_form.dart';
import 'package:zems/view/widget/custom_scrollable_appbar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:gap/gap.dart';

import '../../../../utils/constant/color.dart';
import '../../../../utils/helper/custom_dialog.dart';
import '../../../../utils/helper/scaffold_snakbar.dart';
import '../../../../logic/account/account_cubit.dart';
import '../../../widget/custom_button.dart';

class NewPasswordScreen extends StatefulWidget {
  const NewPasswordScreen({super.key});

  @override
  State<NewPasswordScreen> createState() => _NewPasswordScreenState();
}

class _NewPasswordScreenState extends State<NewPasswordScreen> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  String? _password;
  String? _confirmPassword;
  bool _isLoading = false;
  @override
  Widget build(BuildContext context) {
    final password = context.bloc<AccountCubit>();
    final validator = context.bloc<ValidationCubit>();
    return BlocConsumer<AccountCubit, AccountState>(
      listener: (context, state) {
        if (state is AccountUpdatePasswordLoading) {
          _isLoading = true;
        }
        if (state is AccountUpdatePasswordSuccess) {
          _isLoading = false;
          customDialogWithAnimation(
            context,
            dismiss: false,
            screen: const ChangePasswordDialog(),
          );
        }
        if (state is AccountUpdatePasswordFailure) {
          _isLoading = false;
          customSnackBar(context, state.message, ColorManager.error, 4);
        }
      },
      builder: (context, state) {
        return Scaffold(
            body: SingleChildScrollView(
              child: Column(
                children: [
                  Gap(32.h),
                  const CustomTitleBackButton(
                    title: "Change Password",
                  ),
                  Gap(20.h),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 18),
                    child: Form(
                      key: _formKey,
                      child: Column(
                        children: [
                          const ReAuthanticateStepper(stepReachedNumber: 1),
                          CustomTextFormField(
                            keyboardType: TextInputType.visiblePassword,
                            isVisible: true,
                            title: "New Password",
                            hintText: "Enter Your New Password",
                            onSaved: (data) {
                              _password = data;
                            },
                            validator: validator.validatePassword,
                          ),
                          CustomTextFormField(
                            obscureText: true,
                            keyboardType: TextInputType.visiblePassword,
                            title: "Confirm New Password",
                            hintText: "Enter Your Confirm New Password",
                            onSaved: (data) {
                              _confirmPassword = data;
                            },
                            validator: validator.validateConfirmPassword,
                          ),
                          Gap(25.h),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            bottomNavigationBar: Padding(
              padding: EdgeInsets.only(
                  left: 18.w,
                  right: 18.w,
                  bottom: MediaQuery.viewInsetsOf(context).bottom + 25.h),
              child: CustomButton(
                isDisabled: _isLoading,
                widget: _isLoading ? const ButtonLoadingIndicator() : null,
                title: "Update",
                onPressed: () {
                  if (_formKey.currentState!.validate()) {
                    _formKey.currentState?.save();
                    password.updatePassword(_confirmPassword!);
                  }
                },
              ),
            ));
      },
    );
  }
}
