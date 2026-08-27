import 'package:astra_ai/app/router/route_paths.dart';
import 'package:astra_ai/features/chat/application/conversation_list_controller.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';
import 'package:astra_ai/features/roleplay/application/roleplay_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class ConversationListPanel extends ConsumerWidget {
  const ConversationListPanel({
    required this.selectedConversationId,
    this.showHeader = true,
    super.key,
  });

  final String? selectedConversationId;
  final bool showHeader;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final conversations = ref.watch(conversationListControllerProvider);
    return Column(
      children: <Widget>[
        if (showHeader)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 18, 12, 10),
            child: Row(
              children: <Widget>[
                Expanded(
                  child: Text(
                    'Trò chuyện',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                IconButton(
                  tooltip: 'Làm mới',
                  onPressed: () => ref
                      .read(conversationListControllerProvider.notifier)
                      .refreshList(),
                  icon: const Icon(Icons.refresh),
                ),
              ],
            ),
          ),
        Padding(
          padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
          child: FilledButton.icon(
            onPressed: () => _createConversation(context, ref),
            icon: const Icon(Icons.add_comment_outlined),
            label: const Text('Cuộc trò chuyện mới'),
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: conversations.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, stackTrace) => _ConversationError(
              onRetry: () => ref
                  .read(conversationListControllerProvider.notifier)
                  .refreshList(),
            ),
            data: (state) {
              if (state.items.isEmpty) {
                return const _EmptyConversations();
              }
              return ListView.builder(
                padding: const EdgeInsets.symmetric(vertical: 8),
                itemCount:
                    state.items.length + (state.nextCursor != null ? 1 : 0),
                itemBuilder: (context, index) {
                  if (index == state.items.length) {
                    return Padding(
                      padding: const EdgeInsets.all(12),
                      child: OutlinedButton(
                        onPressed: state.isLoadingMore
                            ? null
                            : () => ref
                                  .read(
                                    conversationListControllerProvider.notifier,
                                  )
                                  .loadMore(),
                        child: state.isLoadingMore
                            ? const SizedBox.square(
                                dimension: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Text('Tải thêm'),
                      ),
                    );
                  }
                  final conversation = state.items[index];
                  return _ConversationTile(
                    conversation: conversation,
                    selected: conversation.id == selectedConversationId,
                    onTap: () => context.go(RoutePaths.chat(conversation.id)),
                    onArchive: () => _archive(context, ref, conversation),
                  );
                },
              );
            },
          ),
        ),
      ],
    );
  }

  Future<void> _createConversation(BuildContext context, WidgetRef ref) async {
    final roleplay = ref.read(roleplayControllerProvider).asData?.value;
    String? selectedCharacterId;
    String? selectedPersonaId;
    if (roleplay != null) {
      for (final persona in roleplay.personas) {
        if (persona.isDefault) {
          selectedPersonaId = persona.id;
          break;
        }
      }
    }
    if (roleplay != null &&
        (roleplay.characters.isNotEmpty || roleplay.personas.isNotEmpty)) {
      final selection = await showDialog<(String?, String?)>(
        context: context,
        builder: (context) => StatefulBuilder(
          builder: (context, setState) => AlertDialog(
            title: const Text('Ngữ cảnh cuộc trò chuyện'),
            content: SizedBox(
              width: 420,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  DropdownButtonFormField<String?>(
                    initialValue: selectedCharacterId,
                    decoration: const InputDecoration(labelText: 'Nhân vật'),
                    items: <DropdownMenuItem<String?>>[
                      const DropdownMenuItem<String?>(
                        value: null,
                        child: Text('Không chọn nhân vật'),
                      ),
                      ...roleplay.characters.map(
                        (item) => DropdownMenuItem<String?>(
                          value: item.id,
                          child: Text(item.name),
                        ),
                      ),
                    ],
                    onChanged: (value) =>
                        setState(() => selectedCharacterId = value),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String?>(
                    initialValue: selectedPersonaId,
                    decoration: const InputDecoration(labelText: 'Persona'),
                    items: <DropdownMenuItem<String?>>[
                      const DropdownMenuItem<String?>(
                        value: null,
                        child: Text('Không chọn persona'),
                      ),
                      ...roleplay.personas.map(
                        (item) => DropdownMenuItem<String?>(
                          value: item.id,
                          child: Text(item.name),
                        ),
                      ),
                    ],
                    onChanged: (value) =>
                        setState(() => selectedPersonaId = value),
                  ),
                ],
              ),
            ),
            actions: <Widget>[
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Hủy'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, (
                  selectedCharacterId,
                  selectedPersonaId,
                )),
                child: const Text('Tạo'),
              ),
            ],
          ),
        ),
      );
      if (selection == null) {
        return;
      }
      selectedCharacterId = selection.$1;
      selectedPersonaId = selection.$2;
    }
    final conversation = await ref
        .read(conversationListControllerProvider.notifier)
        .createConversation(
          characterId: selectedCharacterId,
          personaId: selectedPersonaId,
        );
    if (context.mounted) {
      context.go(RoutePaths.chat(conversation.id));
    }
  }

  Future<void> _archive(
    BuildContext context,
    WidgetRef ref,
    Conversation conversation,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Lưu trữ cuộc trò chuyện?'),
        content: Text(
          '“${conversation.displayTitle}” sẽ biến mất khỏi danh sách.',
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Lưu trữ'),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      return;
    }
    await ref
        .read(conversationListControllerProvider.notifier)
        .archiveConversation(conversation.id);
    if (context.mounted && conversation.id == selectedConversationId) {
      context.go(RoutePaths.chats);
    }
  }
}

class _ConversationTile extends StatelessWidget {
  const _ConversationTile({
    required this.conversation,
    required this.selected,
    required this.onTap,
    required this.onArchive,
  });

  final Conversation conversation;
  final bool selected;
  final VoidCallback onTap;
  final VoidCallback onArchive;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: Material(
        color: selected ? colorScheme.secondaryContainer : Colors.transparent,
        borderRadius: BorderRadius.circular(14),
        child: ListTile(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          onTap: onTap,
          leading: const Icon(Icons.chat_bubble_outline),
          title: Text(
            conversation.displayTitle,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          subtitle: Text(
            '${conversation.provider} · ${conversation.model}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          trailing: PopupMenuButton<String>(
            tooltip: 'Tùy chọn',
            onSelected: (value) {
              if (value == 'archive') {
                onArchive();
              }
            },
            itemBuilder: (context) => const <PopupMenuEntry<String>>[
              PopupMenuItem<String>(
                value: 'archive',
                child: ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.archive_outlined),
                  title: Text('Lưu trữ'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyConversations extends StatelessWidget {
  const _EmptyConversations();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Text(
          'Chưa có cuộc trò chuyện.\nHãy tạo một cuộc trò chuyện mới.',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

class _ConversationError extends StatelessWidget {
  const _ConversationError({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const Icon(Icons.cloud_off_outlined, size: 42),
            const SizedBox(height: 12),
            const Text('Không tải được danh sách trò chuyện.'),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: onRetry, child: const Text('Thử lại')),
          ],
        ),
      ),
    );
  }
}
