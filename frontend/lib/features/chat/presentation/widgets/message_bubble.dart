import 'package:astra_ai/features/chat/domain/entities/chat_message.dart';
import 'package:flutter/material.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';

class MessageBubble extends StatelessWidget {
  const MessageBubble({required this.message, this.onRetry, super.key});

  final ChatMessage message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final isUser = message.isUser;
    final bubbleColor = isUser
        ? colorScheme.primaryContainer
        : colorScheme.surfaceContainerHighest;
    final foreground = isUser
        ? colorScheme.onPrimaryContainer
        : colorScheme.onSurface;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 760),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: bubbleColor,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  if (message.content.isEmpty &&
                      message.status == ChatMessageStatus.streaming)
                    const _TypingIndicator()
                  else
                    SelectionArea(
                      child: MarkdownBody(
                        data: message.content.isEmpty ? '…' : message.content,
                        selectable: false,
                        styleSheet:
                            MarkdownStyleSheet.fromTheme(
                              Theme.of(context),
                            ).copyWith(
                              p: Theme.of(context).textTheme.bodyLarge
                                  ?.copyWith(color: foreground, height: 1.45),
                              code: TextStyle(
                                color: foreground,
                                fontFamily: 'monospace',
                                backgroundColor: colorScheme.surface.withValues(
                                  alpha: 0.55,
                                ),
                              ),
                            ),
                      ),
                    ),
                  if (message.status ==
                      ChatMessageStatus.streaming) ...<Widget>[
                    const SizedBox(height: 8),
                    LinearProgressIndicator(
                      minHeight: 2,
                      color: colorScheme.primary,
                      backgroundColor: Colors.transparent,
                    ),
                  ],
                  if (message.status == ChatMessageStatus.failed) ...<Widget>[
                    const SizedBox(height: 8),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: <Widget>[
                        Icon(
                          Icons.error_outline,
                          size: 18,
                          color: colorScheme.error,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'Phản hồi bị gián đoạn',
                          style: TextStyle(color: colorScheme.error),
                        ),
                        if (onRetry != null) ...<Widget>[
                          const SizedBox(width: 8),
                          TextButton(
                            onPressed: onRetry,
                            child: const Text('Thử lại'),
                          ),
                        ],
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _TypingIndicator extends StatelessWidget {
  const _TypingIndicator();

  @override
  Widget build(BuildContext context) {
    return const Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        SizedBox.square(
          dimension: 16,
          child: CircularProgressIndicator(strokeWidth: 2),
        ),
        SizedBox(width: 10),
        Text('Astra đang trả lời…'),
      ],
    );
  }
}
