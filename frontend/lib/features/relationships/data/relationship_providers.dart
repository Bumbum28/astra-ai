import 'package:astra_ai/core/config/config_providers.dart';
import 'package:astra_ai/core/network/network_providers.dart';
import 'package:astra_ai/features/relationships/data/relationship_remote_data_source.dart';
import 'package:astra_ai/features/relationships/data/relationship_repository_impl.dart';
import 'package:astra_ai/features/relationships/domain/entities/relationship.dart';
import 'package:astra_ai/features/relationships/domain/repositories/relationship_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final relationshipRemoteDataSourceProvider =
    Provider<RelationshipRemoteDataSource>((ref) {
      return RelationshipRemoteDataSource(
        ref.watch(dioProvider),
        ref.watch(appConfigProvider),
      );
    });

final relationshipRepositoryProvider = Provider<RelationshipRepository>((ref) {
  return RelationshipRepositoryImpl(
    ref.watch(relationshipRemoteDataSourceProvider),
  );
});

final relationshipProvider =
    FutureProvider.family<RelationshipProfile?, String>((ref, conversationId) {
      return ref.watch(relationshipRepositoryProvider).get(conversationId);
    });
