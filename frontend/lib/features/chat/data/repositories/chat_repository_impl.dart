import 'package:astra_ai/features/chat/data/datasources/chat_remote_data_source.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_page_data.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_stream_event.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';
import 'package:astra_ai/features/chat/domain/repositories/chat_repository.dart';

class ChatRepositoryImpl implements ChatRepository {
  const ChatRepositoryImpl(this._remoteDataSource);

  final ChatRemoteDataSource _remoteDataSource;

  @override
  Future<ConversationPageData> listConversations({String? cursor}) {
    return _remoteDataSource.listConversations(cursor: cursor);
  }

  @override
  Future<Conversation> createConversation({
    String? title,
    String? systemPrompt,
    String? characterId,
    String? personaId,
  }) {
    return _remoteDataSource.createConversation(
      title: title,
      systemPrompt: systemPrompt,
      characterId: characterId,
      personaId: personaId,
    );
  }

  @override
  Future<void> archiveConversation(String conversationId) {
    return _remoteDataSource.archiveConversation(conversationId);
  }

  @override
  Future<MessagePageData> listMessages(
    String conversationId, {
    String? cursor,
  }) {
    return _remoteDataSource.listMessages(conversationId, cursor: cursor);
  }

  @override
  Stream<ChatStreamEvent> streamMessage({
    required String conversationId,
    required String content,
    required String clientMessageId,
  }) {
    return _remoteDataSource.streamMessage(
      conversationId: conversationId,
      content: content,
      clientMessageId: clientMessageId,
    );
  }
}
