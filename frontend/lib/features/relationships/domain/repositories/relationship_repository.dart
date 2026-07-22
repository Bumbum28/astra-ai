import 'package:astra_ai/features/relationships/domain/entities/relationship.dart';

abstract interface class RelationshipRepository {
  Future<RelationshipProfile?> get(String conversationId);

  Future<RelationshipProfile> update(
    String conversationId,
    Map<String, Object?> data,
  );
}
