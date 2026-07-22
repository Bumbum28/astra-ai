import 'package:astra_ai/core/config/config_providers.dart';
import 'package:astra_ai/core/network/network_providers.dart';
import 'package:astra_ai/features/characters/data/datasources/roleplay_catalog_remote_data_source.dart';
import 'package:astra_ai/features/characters/data/repositories/roleplay_catalog_repository_impl.dart';
import 'package:astra_ai/features/characters/domain/repositories/roleplay_catalog_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final roleplayCatalogRemoteDataSourceProvider =
    Provider<RoleplayCatalogRemoteDataSource>((ref) {
      return RoleplayCatalogRemoteDataSource(
        ref.watch(dioProvider),
        ref.watch(appConfigProvider),
      );
    });

final roleplayCatalogRepositoryProvider = Provider<RoleplayCatalogRepository>((
  ref,
) {
  return RoleplayCatalogRepositoryImpl(
    ref.watch(roleplayCatalogRemoteDataSourceProvider),
  );
});
