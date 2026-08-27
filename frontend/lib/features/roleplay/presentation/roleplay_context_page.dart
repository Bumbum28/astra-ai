import 'package:astra_ai/features/roleplay/application/roleplay_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class RoleplayContextPage extends ConsumerWidget {
  const RoleplayContextPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(roleplayControllerProvider);
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Character & Memory'),
          bottom: const TabBar(
            tabs: <Widget>[
              Tab(text: 'Nhân vật'),
              Tab(text: 'Persona'),
              Tab(text: 'Memory'),
            ],
          ),
        ),
        body: state.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, stackTrace) => Center(
            child: FilledButton(
              onPressed: () => ref.invalidate(roleplayControllerProvider),
              child: const Text('Tải lại'),
            ),
          ),
          data: (data) => TabBarView(
            children: <Widget>[
              _SimpleList(
                items: data.characters
                    .map(
                      (item) =>
                          (item.name, item.tagline ?? item.personality ?? ''),
                    )
                    .toList(),
                emptyText: 'Chưa có nhân vật.',
                actionLabel: 'Thêm nhân vật',
                onAdd: () => _showTextDialog(
                  context,
                  title: 'Nhân vật mới',
                  hint: 'Tên nhân vật',
                  onSubmit: (value) => ref
                      .read(roleplayControllerProvider.notifier)
                      .addCharacter(name: value),
                ),
              ),
              _SimpleList(
                items: data.personas
                    .map((item) => (item.name, item.description ?? ''))
                    .toList(),
                emptyText: 'Chưa có persona.',
                actionLabel: 'Thêm persona',
                onAdd: () => _showTextDialog(
                  context,
                  title: 'Persona mới',
                  hint: 'Tên persona',
                  onSubmit: (value) => ref
                      .read(roleplayControllerProvider.notifier)
                      .addPersona(name: value),
                ),
              ),
              _SimpleList(
                items: data.memories
                    .map(
                      (item) => (
                        item.content,
                        '${item.kind} · ${(item.importance * 100).round()}%',
                      ),
                    )
                    .toList(),
                emptyText: 'Chưa có long-term memory.',
                actionLabel: 'Thêm memory',
                onAdd: () => _showTextDialog(
                  context,
                  title: 'Memory mới',
                  hint: 'Điều Astra cần ghi nhớ',
                  onSubmit: (value) => ref
                      .read(roleplayControllerProvider.notifier)
                      .addMemory(value),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showTextDialog(
    BuildContext context, {
    required String title,
    required String hint,
    required Future<void> Function(String value) onSubmit,
  }) async {
    final controller = TextEditingController();
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(hintText: hint),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: const Text('Lưu'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (value != null && value.isNotEmpty) {
      await onSubmit(value);
    }
  }
}

class _SimpleList extends StatelessWidget {
  const _SimpleList({
    required this.items,
    required this.emptyText,
    required this.actionLabel,
    required this.onAdd,
  });

  final List<(String, String)> items;
  final String emptyText;
  final String actionLabel;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        Padding(
          padding: const EdgeInsets.all(16),
          child: Align(
            alignment: Alignment.centerRight,
            child: FilledButton.icon(
              onPressed: onAdd,
              icon: const Icon(Icons.add),
              label: Text(actionLabel),
            ),
          ),
        ),
        Expanded(
          child: items.isEmpty
              ? Center(child: Text(emptyText))
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final item = items[index];
                    return Card(
                      child: ListTile(
                        leading: const Icon(Icons.auto_awesome),
                        title: Text(item.$1),
                        subtitle: item.$2.isEmpty ? null : Text(item.$2),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
}
