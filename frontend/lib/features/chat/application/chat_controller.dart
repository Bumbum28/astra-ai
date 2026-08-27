import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/features/chat/application/conversation_list_controller.dart';
import 'package:astra_ai/features/chat/data/chat_providers.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_message.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_stream_event.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

class ChatState {
  const ChatState({
    required this.messages,
    this.nextCursor,
    this.isLoadingOlder = false,
    this.isSending = false,
    this.streamError,
  });

  final List<ChatMessage> messages;
  final String? nextCursor;
  final bool isLoadingOlder;
  final bool isSending;
  final AppException? streamError;

  ChatState copyWith({
    List<ChatMessage>? messages,
    String? nextCursor,
    bool clearNextCursor = false,
    bool? isLoadingOlder,
    bool? isSending,
    AppException? streamError,
    bool clearStreamError = false,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      nextCursor: clearNextCursor ? null : nextCursor ?? this.nextCursor,
      isLoadingOlder: isLoadingOlder ?? this.isLoadingOlder,
      isSending: isSending ?? this.isSending,
      streamError: clearStreamError ? null : streamError ?? this.streamError,
    );
  }
}

class ChatController extends AsyncNotifier<ChatState> {
  ChatController(this._conversationId);

  final String _conversationId;

  @override
  Future<ChatState> build() async {
    final page = await ref
        .watch(chatRepositoryProvider)
        .listMessages(_conversationId);
    return ChatState(messages: page.items, nextCursor: page.nextCursor);
  }

  Future<void> loadOlder() async {
    final current = state.asData?.value;
    if (current == null ||
        current.isLoadingOlder ||
        current.nextCursor == null) {
      return;
    }
    state = AsyncData(current.copyWith(isLoadingOlder: true));
    try {
      final page = await ref
          .read(chatRepositoryProvider)
          .listMessages(_conversationId, cursor: current.nextCursor);
      state = AsyncData(
        current.copyWith(
          messages: <ChatMessage>[...page.items, ...current.messages],
          nextCursor: page.nextCursor,
          clearNextCursor: page.nextCursor == null,
          isLoadingOlder: false,
        ),
      );
    } on Object catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
    }
  }

  Future<void> send(String content) async {
    await _sendInternal(content: content, clientMessageId: const Uuid().v4());
  }

  Future<void> retry(ChatMessage failedAssistant) async {
    final current = state.asData?.value;
    if (current == null || failedAssistant.parentMessageId == null) {
      return;
    }
    ChatMessage? userMessage;
    for (final message in current.messages) {
      if (message.id == failedAssistant.parentMessageId) {
        userMessage = message;
        break;
      }
    }
    if (userMessage?.clientMessageId == null) {
      return;
    }
    await _sendInternal(
      content: userMessage!.content,
      clientMessageId: userMessage.clientMessageId!,
    );
  }

  Future<void> _sendInternal({
    required String content,
    required String clientMessageId,
  }) async {
    final normalized = content.trim();
    final current = state.asData?.value;
    if (normalized.isEmpty || current == null || current.isSending) {
      return;
    }
    state = AsyncData(
      current.copyWith(isSending: true, clearStreamError: true),
    );
    try {
      var receivedTerminalEvent = false;
      await for (final event
          in ref
              .read(chatRepositoryProvider)
              .streamMessage(
                conversationId: _conversationId,
                content: normalized,
                clientMessageId: clientMessageId,
              )) {
        _applyEvent(event);
        receivedTerminalEvent =
            event is ChatStreamCompletedEvent || event is ChatStreamFailedEvent;
      }
      if (!receivedTerminalEvent) {
        throw const AppException(
          code: 'CHAT_STREAM_INCOMPLETE',
          message: 'Kết nối đã đóng trước khi phản hồi AI hoàn tất.',
        );
      }
      ref.invalidate(conversationListControllerProvider);
    } on AppException catch (error) {
      _recordStreamFailure(error);
    } on Object catch (error) {
      _recordStreamFailure(
        AppException(
          code: 'CHAT_STREAM_FAILED',
          message: 'Không thể hoàn tất phản hồi AI.',
          details: error.toString(),
        ),
      );
    } finally {
      final latest = state.asData?.value;
      if (latest != null) {
        state = AsyncData(latest.copyWith(isSending: false));
      }
    }
  }

  void _recordStreamFailure(AppException error) {
    final latest = state.asData?.value;
    if (latest == null) {
      return;
    }
    state = AsyncData(
      latest.copyWith(
        messages: latest.messages
            .map(
              (message) =>
                  message.isAssistant &&
                      message.status == ChatMessageStatus.streaming
                  ? message.copyWith(status: ChatMessageStatus.failed)
                  : message,
            )
            .toList(growable: false),
        streamError: error,
      ),
    );
  }

  void _applyEvent(ChatStreamEvent event) {
    final current = state.asData?.value;
    if (current == null) {
      return;
    }
    switch (event) {
      case ChatStreamStartedEvent():
        state = AsyncData(
          current.copyWith(
            messages: _upsertAll(current.messages, <ChatMessage>[
              event.userMessage,
              event.assistantMessage,
            ]),
          ),
        );
      case ChatStreamDeltaEvent():
        state = AsyncData(
          current.copyWith(
            messages: current.messages
                .map(
                  (message) => message.id == event.messageId
                      ? message.copyWith(
                          content: '${message.content}${event.delta}',
                          status: ChatMessageStatus.streaming,
                        )
                      : message,
                )
                .toList(growable: false),
          ),
        );
      case ChatStreamCompletedEvent():
        state = AsyncData(
          current.copyWith(
            messages: _upsertAll(current.messages, <ChatMessage>[
              event.message,
            ]),
          ),
        );
      case ChatStreamFailedEvent():
        state = AsyncData(
          current.copyWith(
            messages: current.messages
                .map(
                  (message) => message.id == event.messageId
                      ? message.copyWith(status: ChatMessageStatus.failed)
                      : message,
                )
                .toList(growable: false),
            streamError: event.error,
          ),
        );
    }
  }

  List<ChatMessage> _upsertAll(
    List<ChatMessage> current,
    List<ChatMessage> incoming,
  ) {
    final byId = <String, ChatMessage>{
      for (final item in current) item.id: item,
    };
    for (final item in incoming) {
      byId[item.id] = item;
    }
    final result = byId.values.toList()
      ..sort((left, right) {
        final timestampOrder = left.createdAt.compareTo(right.createdAt);
        if (timestampOrder != 0) {
          return timestampOrder;
        }
        if (right.parentMessageId == left.id) {
          return -1;
        }
        if (left.parentMessageId == right.id) {
          return 1;
        }
        return left.id.compareTo(right.id);
      });
    return result;
  }
}

final chatControllerProvider =
    AsyncNotifierProvider.family<ChatController, ChatState, String>(
      ChatController.new,
    );
