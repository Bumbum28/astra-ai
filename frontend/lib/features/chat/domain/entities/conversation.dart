class Conversation {
  const Conversation({
    required this.id,
    required this.provider,
    required this.model,
    required this.createdAt,
    required this.updatedAt,
    this.title,
    this.systemPrompt,
    this.lastMessageAt,
  });

  factory Conversation.fromJson(Map<String, Object?> json) {
    return Conversation(
      id: json['id']! as String,
      title: json['title'] as String?,
      provider: (json['provider'] as String?) ?? 'ollama',
      model: (json['model'] as String?) ?? 'roleplay-engine',
      systemPrompt: json['system_prompt'] as String?,
      lastMessageAt: _date(json['last_message_at']),
      createdAt: DateTime.parse(json['created_at']! as String),
      updatedAt: DateTime.parse(json['updated_at']! as String),
    );
  }

  final String id;
  final String? title;
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
