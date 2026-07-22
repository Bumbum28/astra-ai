import 'package:astra_ai/features/chat/domain/entities/chat_message.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';

class ConversationPageData {
  const ConversationPageData({required this.items, this.nextCursor});

  final List<Conversation> items;
  final String? nextCursor;
}

class MessagePageData {
  const MessagePageData({required this.items, this.nextCursor});

  final List<ChatMessage> items;
  final String? nextCursor;
}
