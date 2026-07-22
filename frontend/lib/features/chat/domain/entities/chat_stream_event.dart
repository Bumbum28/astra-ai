import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_message.dart';

sealed class ChatStreamEvent {
  const ChatStreamEvent();
}

class ChatStreamStartedEvent extends ChatStreamEvent {
  const ChatStreamStartedEvent({
    required this.userMessage,
    required this.assistantMessage,
    required this.reused,
  });

  final ChatMessage userMessage;
  final ChatMessage assistantMessage;
  final bool reused;
}

class ChatStreamDeltaEvent extends ChatStreamEvent {
  const ChatStreamDeltaEvent({required this.messageId, required this.delta});

  final String messageId;
  final String delta;
}

class ChatStreamCompletedEvent extends ChatStreamEvent {
  const ChatStreamCompletedEvent(this.message);

  final ChatMessage message;
}

class ChatStreamFailedEvent extends ChatStreamEvent {
  const ChatStreamFailedEvent({required this.messageId, required this.error});

  final String messageId;
  final AppException error;
}
