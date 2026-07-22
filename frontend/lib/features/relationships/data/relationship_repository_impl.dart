import 'package:astra_ai/features/relationships/data/relationship_remote_data_source.dart';
import 'package:astra_ai/features/relationships/domain/entities/relationship.dart';
import 'package:astra_ai/features/relationships/domain/repositories/relationship_repository.dart';

class RelationshipRepositoryImpl implements RelationshipRepository {
  const RelationshipRepositoryImpl(this._remote);

  final RelationshipRemoteDataSource _remote;

  @override
  Future<RelationshipProfile?> get(String conversationId) =>
      _remote.get(conversationId);

  @override
  Future<RelationshipProfile> update(
    String conversationId,
    Map<String, Object?> data,
  ) => _remote.update(conversationId, data);
}
