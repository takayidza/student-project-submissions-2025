import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:uuid/uuid.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../data/model/emergency_contact_model.dart';
import 'dart:convert';

// Events
abstract class EmergencyContactsEvent extends Equatable {
  const EmergencyContactsEvent();

  @override
  List<Object?> get props => [];
}

class LoadEmergencyContacts extends EmergencyContactsEvent {}

class AddEmergencyContact extends EmergencyContactsEvent {
  final String name;
  final String relationship;
  final String phoneNumber;
  final int priority;
  final String? medicalNotes;
  final String category;

  const AddEmergencyContact({
    required this.name,
    required this.relationship,
    required this.phoneNumber,
    required this.priority,
    this.medicalNotes,
    required this.category,
  });

  @override
  List<Object?> get props => [name, relationship, phoneNumber, priority, medicalNotes, category];
}

class UpdateEmergencyContact extends EmergencyContactsEvent {
  final EmergencyContact contact;

  const UpdateEmergencyContact(this.contact);

  @override
  List<Object?> get props => [contact];
}

class DeleteEmergencyContact extends EmergencyContactsEvent {
  final String id;

  const DeleteEmergencyContact(this.id);

  @override
  List<Object?> get props => [id];
}

// States
abstract class EmergencyContactsState extends Equatable {
  const EmergencyContactsState();

  @override
  List<Object?> get props => [];
}

class EmergencyContactsInitial extends EmergencyContactsState {}

class EmergencyContactsLoading extends EmergencyContactsState {}

class EmergencyContactsLoaded extends EmergencyContactsState {
  final List<EmergencyContact> contacts;

  const EmergencyContactsLoaded(this.contacts);

  @override
  List<Object?> get props => [contacts];
}

class EmergencyContactsError extends EmergencyContactsState {
  final String message;

  const EmergencyContactsError(this.message);

  @override
  List<Object?> get props => [message];
}

// Cubit
class EmergencyContactsCubit extends Cubit<EmergencyContactsState> {
  final SharedPreferences _prefs;
  static const String _contactsKey = 'emergency_contacts';

  EmergencyContactsCubit(this._prefs) : super(EmergencyContactsInitial());

  Future<void> loadContacts() async {
    emit(EmergencyContactsLoading());
    try {
      final contactsJson = _prefs.getStringList(_contactsKey) ?? [];
      final contacts = contactsJson
          .map((json) => EmergencyContact.fromJson(jsonDecode(json)))
          .toList();
      emit(EmergencyContactsLoaded(contacts));
    } catch (e) {
      emit(EmergencyContactsError('Failed to load contacts: $e'));
    }
  }

  Future<void> addContact(AddEmergencyContact event) async {
    try {
      final currentState = state;
      if (currentState is EmergencyContactsLoaded) {
        final newContact = EmergencyContact(
          id: const Uuid().v4(),
          name: event.name,
          relationship: event.relationship,
          phoneNumber: event.phoneNumber,
          priority: event.priority,
          medicalNotes: event.medicalNotes,
          category: event.category,
        );

        final updatedContacts = [...currentState.contacts, newContact];
        await _saveContacts(updatedContacts);
        emit(EmergencyContactsLoaded(updatedContacts));
      }
    } catch (e) {
      emit(EmergencyContactsError('Failed to add contact: $e'));
    }
  }

  Future<void> updateContact(UpdateEmergencyContact event) async {
    try {
      final currentState = state;
      if (currentState is EmergencyContactsLoaded) {
        final updatedContacts = currentState.contacts.map((contact) {
          return contact.id == event.contact.id ? event.contact : contact;
        }).toList();

        await _saveContacts(updatedContacts);
        emit(EmergencyContactsLoaded(updatedContacts));
      }
    } catch (e) {
      emit(EmergencyContactsError('Failed to update contact: $e'));
    }
  }

  Future<void> deleteContact(DeleteEmergencyContact event) async {
    try {
      final currentState = state;
      if (currentState is EmergencyContactsLoaded) {
        final updatedContacts = currentState.contacts
            .where((contact) => contact.id != event.id)
            .toList();

        await _saveContacts(updatedContacts);
        emit(EmergencyContactsLoaded(updatedContacts));
      }
    } catch (e) {
      emit(EmergencyContactsError('Failed to delete contact: $e'));
    }
  }

  Future<void> _saveContacts(List<EmergencyContact> contacts) async {
    final contactsJson = contacts
        .map((contact) => jsonEncode(contact.toJson()))
        .toList();
    await _prefs.setStringList(_contactsKey, contactsJson);
  }
} 