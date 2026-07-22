class Conversation {
  const Conversation({
    required this.id,
    required this.provider,
    required this.model,
    required this.createdAt,
    required this.updatedAt,
    this.title,
    this.characterId,
    this.characterVersionId,
    this.personaId,
    this.personaVersionId,
    this.systemPrompt,
    this.lastMessageAt,
  });

  factory Conversation.fromJson(Map<String, Object?> json) {
    return Conversation(
      id: json['id']! as String,
      title: json['title'] as String?,
      characterId: json['character_id'] as String?,
      characterVersionId: json['character_version_id'] as String?,
      personaId: json['persona_id'] as String?,
      personaVersionId: json['persona_version_id'] as String?,
      provider: (json['provider'] as String?) ?? 'openai',
      model: (json['model'] as String?) ?? 'gpt-5.6-terra',
      systemPrompt: json['system_prompt'] as String?,
      lastMessageAt: _date(json['last_message_at']),
      createdAt: DateTime.parse(json['created_at']! as String),
      updatedAt: DateTime.parse(json['updated_at']! as String),
    );
  }

  final String id;
  final String? title;
  final String? characterId;
  final String? characterVersionId;
  final String? personaId;
  final String? personaVersionId;
  final String provider;
  final String model;
  final String? systemPrompt;
  final DateTime? lastMessageAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  String get displayTitle =>
      title?.trim().isNotEmpty == true ? title!.trim() : 'Cuộc trò chuyện mới';

  Conversation copyWith({String? title, DateTime? lastMessageAt}) {
    return Conversation(
      id: id,
      title: title ?? this.title,
      characterId: characterId,
      characterVersionId: characterVersionId,
      personaId: personaId,
      personaVersionId: personaVersionId,
      provider: provider,
      model: model,
      systemPrompt: systemPrompt,
      lastMessageAt: lastMessageAt ?? this.lastMessageAt,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }

  static DateTime? _date(Object? value) {
    return value is String ? DateTime.tryParse(value) : null;
  }
}
