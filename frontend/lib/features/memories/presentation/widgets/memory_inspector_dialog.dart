import 'dart:async';

import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/features/memories/data/memory_providers.dart';
import 'package:astra_ai/features/memories/domain/memory.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MemoryInspectorDialog extends ConsumerStatefulWidget {
  const MemoryInspectorDialog({required this.conversationId, super.key});

  final String conversationId;

  @override
  ConsumerState<MemoryInspectorDialog> createState() =>
      _MemoryInspectorDialogState();
}

class _MemoryInspectorDialogState extends ConsumerState<MemoryInspectorDialog> {
  ConversationMemorySnapshot? _snapshot;
  Object? _error;
  bool _loading = true;
  bool _refreshing = false;

  @override
  void initState() {
    super.initState();
    unawaited(_load());
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref
          .read(memoryRemoteDataSourceProvider)
          .getSnapshot(widget.conversationId);
      if (mounted) {
        setState(() => _snapshot = result);
      }
    } catch (error) {
      if (mounted) {
        setState(() => _error = error);
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _refresh() async {
    setState(() => _refreshing = true);
    try {
      final queued = await ref
          .read(memoryRemoteDataSourceProvider)
          .refresh(widget.conversationId);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            queued
                ? 'Đã xếp hàng cập nhật bộ nhớ.'
                : 'Chưa có đủ tin nhắn để tạo bộ nhớ.',
          ),
        ),
      );
      await _load();
    } finally {
      if (mounted) {
        setState(() => _refreshing = false);
      }
    }
  }

  Future<void> _archive(MemoryItem memory) async {
    await ref.read(memoryRemoteDataSourceProvider).archive(memory.id);
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Row(
        children: <Widget>[
          Icon(Icons.psychology_alt_outlined),
          SizedBox(width: 8),
          Text('Bộ nhớ hội thoại'),
        ],
      ),
      content: SizedBox(width: 680, height: 560, child: _buildContent(context)),
      actions: <Widget>[
        TextButton.icon(
          onPressed: _refreshing ? null : _refresh,
          icon: _refreshing
              ? const SizedBox.square(
                  dimension: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.auto_awesome),
          label: const Text('Cập nhật bộ nhớ'),
        ),
        FilledButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Đóng'),
        ),
      ],
    );
  }

  Widget _buildContent(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      final message = _error is AppException
          ? (_error! as AppException).message
          : 'Không thể tải bộ nhớ.';
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Text(message),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: () async => _load(),
              child: const Text('Thử lại'),
            ),
          ],
        ),
      );
    }
    final snapshot = _snapshot!;
    return ListView(
      children: <Widget>[
        if (snapshot.pendingTasks > 0)
          MaterialBanner(
            content: Text(
              '${snapshot.pendingTasks} tác vụ bộ nhớ đang được xử lý.',
            ),
            actions: <Widget>[
              TextButton(
                onPressed: () async => _load(),
                child: const Text('Làm mới'),
              ),
            ],
          ),
        Text('Tóm tắt', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        SelectableText(
          snapshot.summary?.content ??
              'Chưa có tóm tắt. Bộ nhớ tự động chạy sau một số lượt chat.',
        ),
        const Divider(height: 32),
        Text(
          'Ký ức dài hạn (${snapshot.memories.length})',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        if (snapshot.memories.isEmpty)
          const Text('Chưa có ký ức dài hạn cho hội thoại này.'),
        for (final memory in snapshot.memories)
          Card(
            child: ListTile(
              title: Text(memory.content),
              subtitle: Text(
                '${memory.scope} · ${memory.kind} · '
                'độ tin cậy ${(memory.confidence * 100).round()}%',
              ),
              trailing: IconButton(
                tooltip: 'Quên ký ức này',
                onPressed: () async => _archive(memory),
                icon: const Icon(Icons.delete_outline),
              ),
            ),
          ),
      ],
    );
  }
}
