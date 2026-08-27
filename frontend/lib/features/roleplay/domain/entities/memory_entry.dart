class MemoryEntry {
  const MemoryEntry({
    required this.id,
    required this.scope,
    required this.kind,
    required this.content,
    required this.importance,
  });

  factory MemoryEntry.fromJson(Map<String, Object?> json) {
    return MemoryEntry(
      id: json['id']! as String,
      scope: json['scope']! as String,
      kind: json['kind']! as String,
      content: json['content']! as String,
      importance: (json['importance']! as num).toDouble(),
    );
  }

  final String id;
  final String scope;
  final String kind;
  final String content;
  final double importance;
}
