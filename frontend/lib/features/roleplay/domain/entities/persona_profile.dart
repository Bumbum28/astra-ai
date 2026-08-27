class PersonaProfile {
  const PersonaProfile({
    required this.id,
    required this.name,
    required this.isDefault,
    this.description,
    this.instructions,
  });

  factory PersonaProfile.fromJson(Map<String, Object?> json) {
    return PersonaProfile(
      id: json['id']! as String,
      name: json['name']! as String,
      isDefault: json['is_default'] == true,
      description: json['description'] as String?,
      instructions: json['instructions'] as String?,
    );
  }

  final String id;
  final String name;
  final bool isDefault;
  final String? description;
  final String? instructions;
}
