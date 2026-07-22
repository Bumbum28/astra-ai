enum ChatMessageRole { system, user, assistant, tool }

enum ChatMessageStatus { pending, streaming, completed, failed }

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.conversationId,
    required this.role,
    required this.content,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.parentMessageId,
    this.clientMessageId,
  });

  factory ChatMessage.fromJson(Map<String, Object?> json) {
    return ChatMessage(
      id: json['id']! as String,
      conversationId: json['conversation_id']! as String,
      parentMessageId: json['parent_message_id'] as String?,
      clientMessageId: json['client_message_id'] as String?,
      role: ChatMessageRole.values.byName(json['role']! as String),
      content: (json['content'] as String?) ?? '',
      status: ChatMessageStatus.values.byName(json['status']! as String),
      createdAt: DateTime.parse(json['created_at']! as String),
      updatedAt: DateTime.parse(json['updated_at']! as String),
    );
  }

  final String id;
  final String conversationId;
  final String? parentMessageId;
  final String? clientMessageId;
  final ChatMessageRole role;
  final String content;
  final ChatMessageStatus status;
  final DateTime createdAt;
  final DateTime updatedAt;

  bool get isUser => role == ChatMessageRole.user;
  bool get isAssistant => role == ChatMessageRole.assistant;

  ChatMessage copyWith({
    String? content,
    ChatMessageStatus? status,
    DateTime? updatedAt,
  }) {
    return ChatMessage(
      id: id,
      conversationId: conversationId,
      parentMessageId: parentMessageId,
      clientMessageId: clientMessageId,
      role: role,
      content: content ?? this.content,
      status: status ?? this.status,
      createdAt: createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }
}
