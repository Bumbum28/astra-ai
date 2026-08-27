class KnowledgeSource {
  const KnowledgeSource({
    required this.id,
    required this.name,
    required this.sourceType,
  });

  factory KnowledgeSource.fromJson(Map<String, Object?> json) {
    return KnowledgeSource(
      id: json['id']! as String,
      name: json['name']! as String,
      sourceType: json['source_type']! as String,
    );
  }

  final String id;
  final String name;
  final String sourceType;
}
