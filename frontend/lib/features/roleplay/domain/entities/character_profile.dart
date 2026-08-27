class CharacterProfile {
  const CharacterProfile({
    required this.id,
    required this.name,
    this.tagline,
    this.description,
    this.personality,
  });

  factory CharacterProfile.fromJson(Map<String, Object?> json) {
    return CharacterProfile(
      id: json['id']! as String,
      name: json['name']! as String,
      tagline: json['tagline'] as String?,
      description: json['description'] as String?,
      personality: json['personality'] as String?,
    );
  }

  final String id;
  final String name;
  final String? tagline;
  final String? description;
  final String? personality;
}
