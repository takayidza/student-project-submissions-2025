class EmergencyContact {
  final String id;
  final String name;
  final String relationship;
  final String phoneNumber;
  final int priority;
  final String? medicalNotes;
  final String category; // e.g., "Family", "Medical", "Police", "Fire", etc.

  EmergencyContact({
    required this.id,
    required this.name,
    required this.relationship,
    required this.phoneNumber,
    required this.priority,
    this.medicalNotes,
    required this.category,
  });

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'relationship': relationship,
      'phoneNumber': phoneNumber,
      'priority': priority,
      'medicalNotes': medicalNotes,
      'category': category,
    };
  }

  factory EmergencyContact.fromJson(Map<String, dynamic> json) {
    return EmergencyContact(
      id: json['id'] as String,
      name: json['name'] as String,
      relationship: json['relationship'] as String,
      phoneNumber: json['phoneNumber'] as String,
      priority: json['priority'] as int,
      medicalNotes: json['medicalNotes'] as String?,
      category: json['category'] as String,
    );
  }

  EmergencyContact copyWith({
    String? id,
    String? name,
    String? relationship,
    String? phoneNumber,
    int? priority,
    String? medicalNotes,
    String? category,
  }) {
    return EmergencyContact(
      id: id ?? this.id,
      name: name ?? this.name,
      relationship: relationship ?? this.relationship,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      priority: priority ?? this.priority,
      medicalNotes: medicalNotes ?? this.medicalNotes,
      category: category ?? this.category,
    );
  }
} 