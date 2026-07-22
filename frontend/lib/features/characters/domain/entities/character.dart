class CharacterProfile {
  const CharacterProfile({
    required this.id,
    required this.currentVersion,
    required this.name,
    required this.createdAt,
    required this.updatedAt,
    this.summary,
    this.personality,
    this.speakingStyle,
    this.scenario,
    this.greeting,
    this.systemInstructions,
    this.avatarUrl,
    this.provider,
    this.model,
    this.temperature,
    this.maxTokens,
  });

  factory CharacterProfile.fromJson(Map<String, Object?> json) {
    return CharacterProfile(
      id: json['id']! as String,
      currentVersion: json['current_version']! as int,
      name: json['name']! as String,
      summary: json['summary'] as String?,
      personality: json['personality'] as String?,
      speakingStyle: json['speaking_style'] as String?,
      scenario: json['scenario'] as String?,
      greeting: json['greeting'] as String?,
      systemInstructions: json['system_instructions'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      provider: json['provider'] as String?,
      model: json['model'] as String?,
      temperature: (json['temperature'] as num?)?.toDouble(),
      maxTokens: json['max_tokens'] as int?,
      createdAt: DateTime.parse(json['created_at']! as String),
      updatedAt: DateTime.parse(json['updated_at']! as String),
    );
  }

  final String id;
  final int currentVersion;
  final String name;
  final String? summary;
  final String? personality;
  final String? speakingStyle;
  final String? scenario;
  final String? greeting;
  final String? systemInstructions;
  final String? avatarUrl;
  final String? provider;
  final String? model;
  final double? temperature;
  final int? maxTokens;
  final DateTime createdAt;
  final DateTime updatedAt;
}
