import 'dart:async';
import 'dart:developer';
import 'package:bloc/bloc.dart';
import 'package:flutter/material.dart';
import 'package:hive/hive.dart';
import 'package:intl/intl.dart';
import 'package:path_provider/path_provider.dart';

import '../../data/model/chat_message_model.dart';
import '../../data/service/api/google_generative_ai.dart';
part 'chat_state.dart';

class ChatCubit extends Cubit<ChatState> {
  Box<ChatMessageModel>? _messagesBox;
  static const String _boxName = 'chat_history';

  ChatCubit() : super(ChatInitial());

  Future<void> openMessagesBox() async {
    try {
      _messagesBox = await Hive.openBox<ChatMessageModel>(_boxName);
      log('Messages box opened successfully');
    } on HiveError catch (err) {
      log('Error opening messages box: ${err.message}');
    }
  }

  Future<void> initHive() async {
    try {
      final appDocumentDir = await getApplicationDocumentsDirectory();
      Hive.init(appDocumentDir.path);
      await openMessagesBox();
      startListeningToMessages();
      log('Hive initialized successfully');
    } on HiveError catch (err) {
      log('Error initializing Hive: ${err.message}');
    }
  }

  void startListeningToMessages() {
    try {
      List<ChatMessageModel> messages =
          _messagesBox?.values.toList().reversed.toList() ?? [];
      log('Initial messages loaded: ${messages.length}');
      emit(ChatReceiveSuccess(response: messages));
      _messagesBox?.watch().listen((event) {
        List<ChatMessageModel> updatedMessages =
            _messagesBox?.values.toList().reversed.toList() ?? [];
        log('Messages updated: ${updatedMessages.length}');
        emit(ChatReceiveSuccess(response: updatedMessages));
      });
    } on HiveError catch (err) {
      log('Error listening to messages: ${err.message}');
    }
  }

  Future<void> sendMessage({required String message}) async {
    if (message.trim().isEmpty) return;
    
    emit(ChatSenderLoading());
    try {
      log('Sending user message: $message');
      final chatMessageModel = ChatMessageModel(
        isUser: true,
        message: message.trim(),
        timeTamp: dateTimeFormatter(),
      );
      await _messagesBox?.add(chatMessageModel);
      emit(ChatSendSuccess());
      await Future.delayed(const Duration(milliseconds: 350));

      emit(ChatReceiverLoading());
      log('Requesting AI response...');
      final response = await GenerativeAiWebService.postData(text: message);
      if (response == null) {
        log('No response received from AI');
        emit(ChatFailure(message: 'Failed to get response from AI'));
        return;
      }
      log('AI response received: $response');
      
      await _messagesBox?.add(ChatMessageModel(
        isUser: false,
        message: response,
        timeTamp: dateTimeFormatter(),
      ));
      emit(ChatSendSuccess());
    } on HiveError catch (err) {
      log('Error in sendMessage: ${err.message}');
      emit(ChatFailure(message: err.message.toString()));
    } catch (e) {
      log('Unexpected error in sendMessage: $e');
      emit(ChatFailure(message: e.toString()));
    }
  }

  Future<void> deleteAllMessages() async {
    emit(ChatDeletingLoading());
    try {
      await _messagesBox?.clear();
      log('All messages deleted successfully');
      emit(ChatDeleteSuccess());
    } on HiveError catch (err) {
      log('Error deleting messages: ${err.message}');
      emit(ChatDeleteFailure(message: "Failed to delete chat history: $err"));
    }
  }

  String dateTimeFormatter() {
    DateTime now = DateTime.now();
    DateFormat formatter = DateFormat('yyyy-MM-dd hh:mm a');
    String formattedDate = formatter.format(now);
    return formattedDate;
  }
}
