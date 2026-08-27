import 'package:astra_ai/features/knowledge/application/knowledge_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class KnowledgePage extends ConsumerStatefulWidget {
  const KnowledgePage({super.key});

  @override
  ConsumerState<KnowledgePage> createState() => _KnowledgePageState();
}

class _KnowledgePageState extends ConsumerState<KnowledgePage> {
  final _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(knowledgeControllerProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Knowledge / RAG')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addSource,
        icon: const Icon(Icons.note_add_outlined),
        label: const Text('Thêm nguồn'),
      ),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(
          child: FilledButton(
            onPressed: () => ref.invalidate(knowledgeControllerProvider),
            child: const Text('Tải lại'),
          ),
        ),
        data: (data) => ListView(
          padding: const EdgeInsets.all(20),
          children: <Widget>[
            Text(
              'Nguồn kiến thức',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 12),
            if (data.sources.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Text('Chưa có nguồn kiến thức.'),
                ),
              )
            else
              ...data.sources.map(
                (item) => Card(
                  child: ListTile(
                    leading: const Icon(Icons.library_books_outlined),
                    title: Text(item.name),
                    subtitle: Text(item.sourceType),
                  ),
                ),
              ),
            const SizedBox(height: 28),
            Text(
              'Thử retrieval',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 12),
            Row(
              children: <Widget>[
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: const InputDecoration(
                      labelText: 'Tìm trong knowledge base',
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                FilledButton(
                  onPressed: () => ref
                      .read(knowledgeControllerProvider.notifier)
                      .search(_searchController.text.trim()),
                  child: const Text('Tìm'),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...data.hits.map(
              (hit) => Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(hit.content),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _addSource() async {
    final name = TextEditingController();
    final content = TextEditingController();
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Nguồn kiến thức mới'),
        content: SizedBox(
          width: 560,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              TextField(
                controller: name,
                decoration: const InputDecoration(labelText: 'Tên nguồn'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: content,
                minLines: 6,
                maxLines: 12,
                decoration: const InputDecoration(labelText: 'Nội dung'),
              ),
            ],
          ),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Lưu'),
          ),
        ],
      ),
    );
    if (accepted == true &&
        name.text.trim().isNotEmpty &&
        content.text.trim().isNotEmpty) {
      await ref
          .read(knowledgeControllerProvider.notifier)
          .addSource(name: name.text.trim(), content: content.text.trim());
    }
    name.dispose();
    content.dispose();
  }
}
