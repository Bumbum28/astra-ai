import 'package:astra_ai/app/router/route_paths.dart';
import 'package:astra_ai/features/characters/application/roleplay_catalog_controller.dart';
import 'package:astra_ai/features/characters/domain/entities/character.dart';
import 'package:astra_ai/features/characters/domain/entities/persona.dart';
import 'package:astra_ai/features/chat/application/conversation_list_controller.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';
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
    final catalog = await ref.read(roleplayCatalogControllerProvider.future);
    if (!context.mounted) {
      return;
    }
    final selection = await showDialog<_ConversationProfileSelection>(
      context: context,
      builder: (context) => _NewConversationDialog(
        characters: catalog.characters,
        personas: catalog.personas,
      ),
    );
    if (selection == null) {
      return;
    }
    final conversation = await ref
        .read(conversationListControllerProvider.notifier)
        .createConversation(
          characterId: selection.characterId,
          personaId: selection.personaId,
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

class _ConversationProfileSelection {
  const _ConversationProfileSelection({this.characterId, this.personaId});

  final String? characterId;
  final String? personaId;
}

class _NewConversationDialog extends StatefulWidget {
  const _NewConversationDialog({
    required this.characters,
    required this.personas,
  });

  final List<CharacterProfile> characters;
  final List<PersonaProfile> personas;

  @override
  State<_NewConversationDialog> createState() => _NewConversationDialogState();
}

class _NewConversationDialogState extends State<_NewConversationDialog> {
  String _characterId = '';
  String _personaId = '';

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Cuộc trò chuyện mới'),
      content: SizedBox(
        width: 480,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            DropdownButtonFormField<String>(
              initialValue: _characterId,
              decoration: const InputDecoration(
                labelText: 'Nhân vật',
                helperText: 'Profile của AI trong cuộc trò chuyện.',
              ),
              items: <DropdownMenuItem<String>>[
                const DropdownMenuItem<String>(
                  value: '',
                  child: Text('Không chọn nhân vật'),
                ),
                ...widget.characters.map(
                  (item) => DropdownMenuItem<String>(
                    value: item.id,
                    child: Text(item.name),
                  ),
                ),
              ],
              onChanged: (value) => setState(() => _characterId = value ?? ''),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: _personaId,
              decoration: const InputDecoration(
                labelText: 'Persona của bạn',
                helperText: 'Danh tính mà nhân vật sẽ dùng để hiểu người dùng.',
              ),
              items: <DropdownMenuItem<String>>[
                const DropdownMenuItem<String>(
                  value: '',
                  child: Text('Không chọn persona'),
                ),
                ...widget.personas.map(
                  (item) => DropdownMenuItem<String>(
                    value: item.id,
                    child: Text(item.name),
                  ),
                ),
              ],
              onChanged: (value) => setState(() => _personaId = value ?? ''),
            ),
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Hủy'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(
            _ConversationProfileSelection(
              characterId: _characterId.isEmpty ? null : _characterId,
              personaId: _personaId.isEmpty ? null : _personaId,
            ),
          ),
          child: const Text('Tạo'),
        ),
      ],
    );
  }
}
