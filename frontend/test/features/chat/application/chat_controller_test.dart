import 'package:astra_ai/features/chat/application/chat_controller.dart';
import 'package:astra_ai/features/chat/data/chat_providers.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_message.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_page_data.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_stream_event.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';
import 'package:astra_ai/features/chat/domain/repositories/chat_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('applies streaming chunks to the assistant message', () async {
    final repository = _FakeChatRepository();
    final container = ProviderContainer(
      overrides: [chatRepositoryProvider.overrideWithValue(repository)],
    );
    addTearDown(container.dispose);
    final provider = chatControllerProvider('conversation-1');

    await container.read(provider.future);
    await container.read(provider.notifier).send('Xin chào');

    final state = container.read(provider).requireValue;
    expect(state.messages, hasLength(2));
    expect(state.messages.last.content, 'Chào bạn!');
    expect(state.messages.last.status, ChatMessageStatus.completed);
    expect(state.isSending, isFalse);
  });

  test(
    'marks a streaming assistant failed when the transport closes early',
    () async {
      final repository = _FakeChatRepository(completeStream: false);
      final container = ProviderContainer(
        overrides: [chatRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);
      final provider = chatControllerProvider('conversation-1');

      await container.read(provider.future);
      await container.read(provider.notifier).send('Xin chào');

      final state = container.read(provider).requireValue;
      expect(state.messages.last.status, ChatMessageStatus.failed);
      expect(state.streamError?.code, 'CHAT_STREAM_INCOMPLETE');
      expect(state.isSending, isFalse);
    },
  );
}

class _FakeChatRepository implements ChatRepository {
  _FakeChatRepository({this.completeStream = true});

  final bool completeStream;
  final now = DateTime.utc(2026, 7, 22);

  @override
  Future<ConversationPageData> listConversations({String? cursor}) async {
    return const ConversationPageData(items: <Conversation>[]);
  }

  @override
  Future<Conversation> createConversation({
    String? title,
    String? systemPrompt,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<void> archiveConversation(String conversationId) async {}

  @override
  Future<MessagePageData> listMessages(
    String conversationId, {
    String? cursor,
  }) async {
    return const MessagePageData(items: <ChatMessage>[]);
  }

  @override
  Stream<ChatStreamEvent> streamMessage({
    required String conversationId,
    required String content,
    required String clientMessageId,
  }) async* {
    final user = ChatMessage(
      id: 'user-1',
      conversationId: conversationId,
      clientMessageId: clientMessageId,
      role: ChatMessageRole.user,
      content: content,
      status: ChatMessageStatus.completed,
      createdAt: now,
      updatedAt: now,
    );
    final assistant = ChatMessage(
      id: 'assistant-1',
      conversationId: conversationId,
      parentMessageId: user.id,
      role: ChatMessageRole.assistant,
      content: '',
      status: ChatMessageStatus.streaming,
      createdAt: now.add(const Duration(milliseconds: 1)),
      updatedAt: now,
    );
    yield ChatStreamStartedEvent(
      userMessage: user,
      assistantMessage: assistant,
      reused: false,
    );
    yield const ChatStreamDeltaEvent(messageId: 'assistant-1', delta: 'Chào ');
    yield const ChatStreamDeltaEvent(messageId: 'assistant-1', delta: 'bạn!');
    if (!completeStream) {
      return;
    }
    yield ChatStreamCompletedEvent(
      assistant.copyWith(
        content: 'Chào bạn!',
        status: ChatMessageStatus.completed,
      ),
    );
  }
}
