class KnowledgeHit {
  const KnowledgeHit({
    required this.sourceId,
    required this.chunkId,
    required this.content,
    required this.score,
  });

  factory KnowledgeHit.fromJson(Map<String, Object?> json) {
    return KnowledgeHit(
      sourceId: json['source_id']! as String,
      chunkId: json['chunk_id']! as String,
      content: json['content']! as String,
      score: (json['score']! as num).toDouble(),
    );
  }

  final String sourceId;
  final String chunkId;
  final String content;
  final double score;
}
