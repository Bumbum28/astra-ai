class PersonaProfile {
  const PersonaProfile({
    required this.id,
    required this.currentVersion,
    required this.name,
    required this.createdAt,
    required this.updatedAt,
    this.description,
    this.pronouns,
    this.background,
    this.traits,
    this.writingStyle,
  });

  factory PersonaProfile.fromJson(Map<String, Object?> json) {
    return PersonaProfile(
      id: json['id']! as String,
      currentVersion: json['current_version']! as int,
      name: json['name']! as String,
      description: json['description'] as String?,
      pronouns: json['pronouns'] as String?,
      background: json['background'] as String?,
      traits: json['traits'] as String?,
      writingStyle: json['writing_style'] as String?,
      createdAt: DateTime.parse(json['created_at']! as String),
      updatedAt: DateTime.parse(json['updated_at']! as String),
    );
  }

  final String id;
  final int currentVersion;
  final String name;
  final String? description;
  final String? pronouns;
  final String? background;
  final String? traits;
  final String? writingStyle;
  final DateTime createdAt;
  final DateTime updatedAt;
}
