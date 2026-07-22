class RelationshipProfile {
  const RelationshipProfile({
    required this.id,
    required this.conversationId,
    required this.characterId,
    required this.level,
    required this.affectionScore,
    required this.turnCount,
    this.status,
    this.context,
    this.lastChangeReason,
  });

  factory RelationshipProfile.fromJson(Map<String, Object?> json) {
    return RelationshipProfile(
      id: json['id']! as String,
      conversationId: json['conversation_id']! as String,
      characterId: json['character_id']! as String,
      level: json['level']! as String,
      affectionScore: json['affection_score']! as int,
      status: json['status'] as String?,
      turnCount: json['turn_count']! as int,
      context: json['context'] as String?,
      lastChangeReason: json['last_change_reason'] as String?,
    );
  }

  final String id;
  final String conversationId;
  final String characterId;
  final String level;
  final int affectionScore;
  final String? status;
  final int turnCount;
  final String? context;
  final String? lastChangeReason;
}
