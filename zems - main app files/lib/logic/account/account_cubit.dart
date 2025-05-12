import 'dart:developer';

import 'package:bloc/bloc.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:zems/cache/cache.dart';
import 'package:zems/data/model/user_data_model.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:meta/meta.dart';
part 'account_state.dart';

class AccountCubit extends Cubit<AccountState> {
  AccountCubit() : super(AccountInitial());
  final _firestore = FirebaseFirestore.instance;
  Future<void> getprofileData() async {
    emit(AccountLoading());
    try {
      UserDataModel? userDataModel;
      _firestore
          .collection('users')
          .doc(FirebaseAuth.instance.currentUser!.uid)
          .snapshots()
          .listen((event) {
        userDataModel = UserDataModel.fromJson(event.data()!);
        CacheData.setData(key: "name", value: userDataModel!.name);
        CacheData.setMapData(key: "userData", value: userDataModel!.toJson());
        emit(AccountSuccess(userDataModel: userDataModel!));
      });
    } on FirebaseException catch (err) {
      emit(AccountFailure(message: err.toString()));
    }
  }

  Future<void> logout() async {
    emit(AccountLogoutLoading());
    try {
      await Future.delayed(const Duration(seconds: 1));
      await CacheData.clearData(clearData: true);
      await FirebaseAuth.instance.signOut();
      emit(AccountLogoutSuccess(message: "Logout successfully"));
    } on FirebaseException catch (err) {
      emit(AccountFailure(message: err.toString()));
    }
  }

  Future<void> deleteAccount() async {
    emit(AccountDeleteLoading());
    try {
      await Future.delayed(const Duration(milliseconds: 500));
      await _deleteChatHistory();
      await _firestore
          .collection('users')
          .doc(FirebaseAuth.instance.currentUser!.uid)
          .update(
        {'isActive': false},
      );
      // await _deleteUserData();
      log("DELETED CHAT HISTORY");
      await FirebaseAuth.instance.currentUser?.delete();
      log("DELETED USER ACCOUNT");
      await CacheData.clearData(clearData: true);
      log("DELETED CACHE DATA");
      await FirebaseAuth.instance.signOut();
      log("LOGGED OUT");
      emit(AccountDeleteSuccess(message: "Account deleted successfully"));
      log("ACCOUNT DELETED SUCCESSFULLY");
    } on FirebaseException catch (err) {
      log("DELETE ACCOUNT ERROR: ${err.toString()}");
      emit(AccountDeleteFailure(message: err.message.toString()));
    }
  }

  //! DELETE USER DATA
  Future<void> _deleteUserData() async {
    emit(UserDataDeletingLoading());
    try {
      await _firestore
          .collection('users')
          .doc(FirebaseAuth.instance.currentUser?.uid)
          .get();
      log("DELETED USER DATA");
      await CacheData.clearData(clearData: true);
      log("DELETED CACHE DATA");
      emit(UserDataDeleteSuccess());
      log("ACCOUNT DELETED SUCCESSFULLY");
    } on FirebaseException catch (err) {
      log("${err.message} \n ${err.stackTrace} \n ${err.code.toString()} \n ${err.plugin}");
      emit(UserDataDeleteFailure(message: "Failed to delete user data"));
    }
  }

//! DELETE Chat History

  Future<void> _deleteChatHistory() async {
    CollectionReference messagesCollection = FirebaseFirestore.instance
        .collection('chat_history')
        .doc(FirebaseAuth.instance.currentUser?.uid)
        .collection('messages');
    emit(ChatDeletingLoading());
    try {
      final messagesQuerySnapshot = await messagesCollection.get();

      for (var doc in messagesQuerySnapshot.docs) {
        await messagesCollection.doc(doc.id).delete();
      }
      emit(ChatDeleteSuccess());
      log("CHAT HISTORY DELETED SUCCESSFULLY");
    } on FirebaseException catch (_) {
      emit(ChatDeleteFailure(message: "Failed to delete chat history"));
    }
  }

  //   Future<void> deleteAccount() async {
  //   emit(AccountDeleteLoading());
  //   try {
  //     final user = FirebaseAuth.instance.currentUser;
  //     if (user != null) {
  //       final uid = user.uid;
  //       final batch = FirebaseFirestore.instance.batch();
  //       batch.delete(
  //           FirebaseFirestore.instance.collection('chat_history').doc(uid));
  //       batch.delete(FirebaseFirestore.instance.collection('users').doc(uid));
  //       await batch
  //           .commit()
  //           .then((_) => log("DELETED CHAT HISTORY AND USER DATA"));

  //       await CacheData.clearData(clearData: true);
  //       log("DELETED CACHE DATA");

  //       await user.delete();
  //       log("DELETED USER ACCOUNT");

  //       await FirebaseAuth.instance.signOut();
  //       log("LOGGED OUT");

  //       emit(AccountDeleteSuccess(message: "Account deleted successfully"));
  //       log("ACCOUNT DELETED SUCCESSFULLY");
  //     }
  //   } catch (err) {
  //     emit(AccountFailure(message: err.toString()));
  //     log("ERROR: ${err.toString()}");
  //   }
  // }

  //? update user name

  Future<void> updateUserName({required String newName}) async {
    emit(ProfileUpdateLoading());
    try {
      await Future.delayed(const Duration(milliseconds: 400));
      await _firestore
          .collection('users')
          .doc(FirebaseAuth.instance.currentUser!.uid)
          .update({'name': newName})
          .whenComplete(() => emit(ProfileUpdateSuccess()))
          .timeout(const Duration(seconds: 5),
              onTimeout: () => emit(ProfileUpdateFailure(
                  message: "There was an error, please try again")));
    } on FirebaseException catch (err) {
      emit(ProfileUpdateFailure(message: err.toString()));
    }
  }

  Future<void> updateProfile({
    String? name,
    String? email,
    String? phoneNumber,
    String? dob,
    String? height,
    String? weight,
    String? chronicDiseases,
    String? familyHistoryOfChronicDiseases,
  }) async {
    emit(ProfileUpdateLoading());
    try {
      await Future.delayed(const Duration(milliseconds: 400));
      await _firestore
          .collection('users')
          .doc(FirebaseAuth.instance.currentUser!.uid)
          .update({
            'name': name,
            'email': email,
            'phoneNumber': phoneNumber,
            'dob': dob,
            'height': height,
            'weight': weight,
            'chronicDiseases': chronicDiseases,
            'familyHistoryOfChronicDiseases': familyHistoryOfChronicDiseases
          })
          .whenComplete(() => emit(ProfileUpdateSuccess()))
          .timeout(const Duration(seconds: 5),
              onTimeout: () => emit(ProfileUpdateFailure(
                  message: "There was an error, please try again")));
    } on FirebaseException catch (err) {
      emit(ProfileUpdateFailure(message: err.toString()));
    }
  }

  Future<void> reAuthenticateUser(String password) async {
    emit(AccountReAuthLoading());
    await Future.delayed(const Duration(milliseconds: 400));
    final FirebaseAuth auth = FirebaseAuth.instance;
    final User? user = auth.currentUser;

    if (user != null) {
      AuthCredential credential = EmailAuthProvider.credential(
          email: (user.email).toString(), password: password);
      try {
        await user.reauthenticateWithCredential(credential);
        emit(AccountReAuthSuccess());
        log('User re-authenticated successfully');
      } on FirebaseAuthException catch (err) {
        if (err.code == 'wrong-password' || err.code == 'invalid-credential') {
          emit(AccountReAuthFailure(message: 'Wrong password'));
        } else if (err.code == 'too-many-requests') {
          emit(AccountReAuthFailure(
              message: 'Too many requests, try again later'));
        } else {
          emit(AccountReAuthFailure(message: err.message.toString()));
        }
      }
    } else {
      log('No user found. Please sign in first.');
    }
  }

  Future<void> updatePassword(String newPassword) async {
    emit(AccountUpdatePasswordLoading());
    await Future.delayed(const Duration(milliseconds: 400));
    final FirebaseAuth auth = FirebaseAuth.instance;
    final User? user = auth.currentUser;

    if (user != null) {
      try {
        await user.updatePassword(newPassword).whenComplete(() {
          emit(AccountUpdatePasswordSuccess(
              message: 'Password updated successfully'));
          log('Password updated successfully');
        }).timeout(const Duration(seconds: 5),
            onTimeout: () => emit(AccountUpdatePasswordFailure(
                message: "There was an error, please try again")));
      } on FirebaseAuthException catch (err) {
        emit(AccountUpdatePasswordFailure(message: err.message.toString()));
        log('Password update failed: ${err.message}');
      }
    } else {
      log('No user found. Please sign in first.');
    }
  }

  Future<void> storeUserRating(int rating) async {
    emit(AccountRatingLoading());
    try {
      await Future.delayed(const Duration(milliseconds: 400));
      DocumentReference userDocRef = _firestore
          .collection('ratings')
          .doc(FirebaseAuth.instance.currentUser!.uid);
      await userDocRef.set({
        'rating': '$rating / 5',
      }, SetOptions(merge: true)).whenComplete(() async {
        emit(AccountRatingSuccess());
        await CacheData.setData(key: "rating", value: rating);
        log('User rating updated successfully.');
      }).timeout(const Duration(seconds: 5),
          onTimeout: () => emit(AccountRatingFailure(
              message: "There was an error, please try again")));
    } on FirebaseException catch (err) {
      emit(AccountRatingFailure(message: err.message.toString()));
      log('Error updating user rating: $err');
    }
  }

  Future<void> getUserRating() async {
    try {
      DocumentSnapshot<Map<String, dynamic>>? userDocRef = await _firestore
          .collection('ratings')
          .doc(FirebaseAuth.instance.currentUser!.uid)
          .get();

      if (userDocRef.data() != null && userDocRef.data()!['rating'] != null) {
        int? rating = int.tryParse(userDocRef.data()!['rating'][0]);
        if (rating != null) {
          await CacheData.setData(key: "rating", value: rating);
          emit(AccountRatingResult(rating: rating));
          log('User rating: $rating');
        }
      } else {
        log('User rating not found');
      }
    } on FirebaseException catch (err) {
      emit(AccountRatingFailure(message: err.toString()));
    }
  }

  // //? update email
  // Future<void> updateEmail({required String newEmail}) async {
  //   emit(ProfileUpdateLoading());
  //   try {
  //     await FirebaseService.updateEmailWithReauth(newEmail: newEmail, password: );

  //     await _firestore
  //         .collection('users')
  //         .doc(FirebaseAuth.instance.currentUser!.email)
  //         .update({'email': newEmail});

  //     emit(ProfileUpdateSuccess());
  //   } on Exception catch (err) {
  //     emit(ProfileUpdateFailure(message: err.toString()));
  //   }
  // }

  // //? update password
  // Future<void> updatePassword({required String newPassword}) async {
  //   emit(AccountLoading());
  //   try {
  //     await FirebaseAuth.instance.currentUser!.updatePassword(newPassword);
  //   } on Exception catch (err) {
  //     emit(AccountFailure(message: err.toString()));
  //   }
  // }

  // Future<void> loadPhoto() async {
  //   emit(AccountLoadingImage());
  //   try {
  //     String fileName = '${FirebaseAuth.instance.currentUser!.uid}.jpg';
  //     Reference storageRef = FirebaseStorage.instance.ref().child(fileName);

  //     final url = await storageRef.getDownloadURL();
  //     await CacheData.setData(key: "image", value: url);

  //     emit(AccountLoadedImage(urlImage: url));
  //   } catch (err) {
  //     emit(AccountLoadedFailure(message: err.toString()));
  //     log('Error occurred while loading the image: $err');
  //     log(err.toString());
  //   }
  // }

  // Future<void> uploadUserPhoto() async {
  //   emit(AccountUpdateImageLoading());
  //   try {
  //     final returnImage =
  //         await ImagePicker().pickImage(source: ImageSource.camera);
  //     if (returnImage != null) {
  //       String fileName = '${FirebaseAuth.instance.currentUser!.uid}.jpg';
  //       // String fileName =
  //       //     '${FirebaseAuth.instance.currentUser!.uid}_${DateTime.now().millisecondsSinceEpoch}.jpg';
  //       Reference storageRef = FirebaseStorage.instance.ref().child(fileName);
  //       storageRef.putFile(File(returnImage.path));
  //       await loadPhoto();
  //       emit(AccountUpdateImageSuccess());
  //     } else {
  //       log("Image picking cancelled by user.");
  //       emit(AccountUpdateImageFailure(
  //           message: 'Image picking cancelled by user.'));
  //     }
  //   } catch (err) {
  //     log(err.toString());
  //     emit(AccountUpdateImageFailure(message: err.toString()));
  //   }
  // }
}
