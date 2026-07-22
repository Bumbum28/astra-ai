import 'package:astra_ai/features/chat/domain/entities/chat_page_data.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_stream_event.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';

abstract interface class ChatRepository {
  Future<ConversationPageData> listConversations({String? cursor});

  Future<Conversation> createConversation({
    String? title,
    String? systemPrompt,
    String? characterId,
    String? personaId,
  });

  Future<void> archiveConversation(String conversationId);

  Future<MessagePageData> listMessages(String conversationId, {String? cursor});

  Stream<ChatStreamEvent> streamMessage({
    required String conversationId,
    required String content,
    required String clientMessageId,
  });
}
