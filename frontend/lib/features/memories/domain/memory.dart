class MemoryItem {
  const MemoryItem({
    required this.id,
    required this.scope,
    required this.kind,
    required this.status,
    required this.content,
    required this.importance,
    required this.confidence,
    required this.updatedAt,
  });

  factory MemoryItem.fromJson(Map<String, Object?> json) {
    return MemoryItem(
      id: json['id']! as String,
      scope: json['scope']! as String,
      kind: json['kind']! as String,
      status: json['status']! as String,
      content: json['content']! as String,
      importance: (json['importance']! as num).toDouble(),
      confidence: (json['confidence']! as num).toDouble(),
      updatedAt: DateTime.parse(json['updated_at']! as String),
    );
  }

  final String id;
  final String scope;
  final String kind;
  final String status;
  final String content;
  final double importance;
  final double confidence;
  final DateTime updatedAt;
}

class ConversationMemorySummary {
  const ConversationMemorySummary({
    required this.content,
    required this.sourceMessageCount,
    required this.updatedAt,
  });

  factory ConversationMemorySummary.fromJson(Map<String, Object?> json) {
    return ConversationMemorySummary(
      content: json['content']! as String,
      sourceMessageCount: json['source_message_count']! as int,
      updatedAt: DateTime.parse(json['updated_at']! as String),
    );
  }

  final String content;
  final int sourceMessageCount;
  final DateTime updatedAt;
}

class ConversationMemorySnapshot {
  const ConversationMemorySnapshot({
    required this.memories,
    required this.pendingTasks,
    this.summary,
  });

  factory ConversationMemorySnapshot.fromJson(Map<String, Object?> json) {
    final rawMemories = json['memories'];
    return ConversationMemorySnapshot(
      summary: json['summary'] is Map
          ? ConversationMemorySummary.fromJson(
              Map<String, Object?>.from(json['summary']! as Map),
            )
          : null,
      memories: rawMemories is List
          ? rawMemories
                .map(
                  (item) => MemoryItem.fromJson(
                    Map<String, Object?>.from(item! as Map),
                  ),
                )
                .toList(growable: false)
          : const <MemoryItem>[],
      pendingTasks: (json['pending_tasks'] as int?) ?? 0,
    );
  }

  final ConversationMemorySummary? summary;
  final List<MemoryItem> memories;
  final int pendingTasks;
}
