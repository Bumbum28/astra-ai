import 'dart:async';

import 'package:astra_ai/app/router/route_paths.dart';
import 'package:astra_ai/features/chat/application/chat_controller.dart';
import 'package:astra_ai/features/chat/application/conversation_list_controller.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_message.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';
import 'package:astra_ai/features/chat/presentation/widgets/chat_composer.dart';
import 'package:astra_ai/features/chat/presentation/widgets/conversation_list_panel.dart';
import 'package:astra_ai/features/chat/presentation/widgets/message_bubble.dart';
import 'package:astra_ai/features/memories/presentation/widgets/memory_inspector_dialog.dart';
import 'package:astra_ai/features/relationships/data/relationship_providers.dart';
import 'package:astra_ai/features/relationships/domain/entities/relationship.dart';
import 'package:astra_ai/features/relationships/presentation/widgets/relationship_editor_dialog.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class ChatPage extends StatelessWidget {
  const ChatPage({this.conversationId, super.key});

  final String? conversationId;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final desktop = constraints.maxWidth >= 900;
        if (desktop) {
          return Row(
            children: <Widget>[
              SizedBox(
                width: 330,
                child: ConversationListPanel(
                  selectedConversationId: conversationId,
                ),
              ),
              const VerticalDivider(width: 1),
              Expanded(
                child: conversationId == null
                    ? const _NoConversationSelected()
                    : ConversationView(conversationId: conversationId!),
              ),
            ],
          );
        }
        if (conversationId == null) {
          return const ConversationListPanel(selectedConversationId: null);
        }
        return ConversationView(
          conversationId: conversationId!,
          showBackButton: true,
        );
      },
    );
  }
}

class ConversationView extends ConsumerStatefulWidget {
  const ConversationView({
    required this.conversationId,
    this.showBackButton = false,
    super.key,
  });

  final String conversationId;
  final bool showBackButton;

  @override
  ConsumerState<ConversationView> createState() => _ConversationViewState();
}

class _ConversationViewState extends ConsumerState<ConversationView> {
  final _scrollController = ScrollController();

  String? _conversationTitle(List<Conversation> conversations) {
    for (final conversation in conversations) {
      if (conversation.id == widget.conversationId) {
        return conversation.displayTitle;
      }
    }
    return null;
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) {
        return;
      }
      unawaited(
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOut,
        ),
      );
    });
  }

  Future<void> _editRelationship(RelationshipProfile current) async {
    final data = await showDialog<Map<String, Object?>>(
      context: context,
      barrierDismissible: false,
      builder: (context) => RelationshipEditorDialog(current: current),
    );
    if (data == null) {
      return;
    }
    await ref
        .read(relationshipRepositoryProvider)
        .update(widget.conversationId, data);
    ref.invalidate(relationshipProvider(widget.conversationId));
  }

  @override
  Widget build(BuildContext context) {
    final provider = chatControllerProvider(widget.conversationId);
    final chatState = ref.watch(provider);
    final conversations = ref.watch(conversationListControllerProvider);
    final relationship = ref.watch(relationshipProvider(widget.conversationId));
    final title = _conversationTitle(
      conversations.value?.items ?? const <Conversation>[],
    );

    ref.listen(provider, (previous, next) {
      final previousCount = previous?.value?.messages.length ?? 0;
      final nextCount = next.value?.messages.length ?? 0;
      final wasSending = previous?.value?.isSending ?? false;
      final isSending = next.value?.isSending ?? false;
      if (nextCount > previousCount || isSending || wasSending != isSending) {
        _scrollToBottom();
      }
      if (wasSending && !isSending) {
        ref.invalidate(relationshipProvider(widget.conversationId));
      }
    });

    return Column(
      children: <Widget>[
        Material(
          color: Theme.of(context).colorScheme.surface,
          child: SafeArea(
            bottom: false,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Row(
                children: <Widget>[
                  if (widget.showBackButton)
                    IconButton(
                      tooltip: 'Danh sách trò chuyện',
                      onPressed: () => context.go(RoutePaths.chats),
                      icon: const Icon(Icons.arrow_back),
                    ),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          title ?? 'Cuộc trò chuyện',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        Text(
                          'Streaming qua Astra AI Platform',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ),
                  relationship.when(
                    loading: () => const SizedBox.square(
                      dimension: 28,
                      child: Padding(
                        padding: EdgeInsets.all(6),
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    ),
                    error: (error, stackTrace) => const SizedBox.shrink(),
                    data: (value) => value == null
                        ? const SizedBox.shrink()
                        : Padding(
                            padding: const EdgeInsets.only(right: 4),
                            child: ActionChip(
                              avatar: const Icon(Icons.favorite_outline, size: 18),
                              label: Text(
                                '${value.level.toUpperCase()} · ${value.affectionScore}',
                              ),
                              onPressed: () => _editRelationship(value),
                            ),
                          ),
                  ),
                  IconButton(
                    tooltip: 'Bộ nhớ hội thoại',
                    onPressed: () => showDialog<void>(
                      context: context,
                      builder: (context) => MemoryInspectorDialog(
                        conversationId: widget.conversationId,
                      ),
                    ),
                    icon: const Icon(Icons.psychology_alt_outlined),
                  ),
                  IconButton(
                    tooltip: 'Tải lại tin nhắn',
                    onPressed: () {
                      ref.invalidate(provider);
                      ref.invalidate(relationshipProvider(widget.conversationId));
                    },
                    icon: const Icon(Icons.refresh),
                  ),
                ],
              ),
            ),
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: chatState.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stackTrace) =>
                _ChatLoadError(onRetry: () => ref.invalidate(provider)),
            data: (state) => Column(
              children: <Widget>[
                if (state.streamError != null)
                  MaterialBanner(
                    content: Text(state.streamError!.message),
                    leading: const Icon(Icons.error_outline),
                    actions: <Widget>[
                      TextButton(
                        onPressed: () => ref.invalidate(provider),
                        child: const Text('Tải lại'),
                      ),
                    ],
                  ),
                Expanded(
                  child: state.messages.isEmpty
                      ? const _EmptyTimeline()
                      : ListView.builder(
                          controller: _scrollController,
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          itemCount:
                              state.messages.length +
                              (state.nextCursor != null ? 1 : 0),
                          itemBuilder: (context, index) {
                            if (state.nextCursor != null && index == 0) {
                              return Center(
                                child: TextButton.icon(
                                  onPressed: state.isLoadingOlder
                                      ? null
                                      : () => ref
                                            .read(provider.notifier)
                                            .loadOlder(),
                                  icon: state.isLoadingOlder
                                      ? const SizedBox.square(
                                          dimension: 16,
                                          child: CircularProgressIndicator(
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : const Icon(Icons.history),
                                  label: const Text('Tải tin nhắn cũ hơn'),
                                ),
                              );
                            }
                            final messageIndex = state.nextCursor != null
                                ? index - 1
                                : index;
                            final message = state.messages[messageIndex];
                            return MessageBubble(
                              key: ValueKey(message.id),
                              message: message,
                              onRetry:
                                  message.status == ChatMessageStatus.failed &&
                                      message.isAssistant
                                  ? () => ref
                                        .read(provider.notifier)
                                        .retry(message)
                                  : null,
                            );
                          },
                        ),
                ),
                Align(
                  alignment: Alignment.center,
                  child: ChatComposer(
                    isSending: state.isSending,
                    onSend: (content) =>
                        ref.read(provider.notifier).send(content),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _NoConversationSelected extends StatelessWidget {
  const _NoConversationSelected();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(Icons.forum_outlined, size: 64),
            SizedBox(height: 16),
            Text(
              'Chọn một cuộc trò chuyện hoặc tạo cuộc trò chuyện mới.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyTimeline extends StatelessWidget {
  const _EmptyTimeline();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(Icons.auto_awesome_outlined, size: 56),
            SizedBox(height: 16),
            Text(
              'Hãy gửi tin nhắn đầu tiên.\nAstra sẽ phản hồi theo thời gian thực.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatLoadError extends StatelessWidget {
  const _ChatLoadError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          const Icon(Icons.cloud_off_outlined, size: 48),
          const SizedBox(height: 12),
          const Text('Không tải được lịch sử trò chuyện.'),
          const SizedBox(height: 12),
          OutlinedButton(onPressed: onRetry, child: const Text('Thử lại')),
        ],
      ),
    );
  }
}
