import 'package:astra_ai/core/config/config_providers.dart';
import 'package:astra_ai/core/network/network_providers.dart';
import 'package:astra_ai/features/roleplay/data/datasources/roleplay_remote_data_source.dart';
import 'package:astra_ai/features/roleplay/data/repositories/roleplay_repository_impl.dart';
import 'package:astra_ai/features/roleplay/domain/repositories/roleplay_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final roleplayRemoteDataSourceProvider = Provider<RoleplayRemoteDataSource>((
  ref,
) {
  return RoleplayRemoteDataSource(
    ref.watch(dioProvider),
    ref.watch(appConfigProvider),
  );
});

final roleplayRepositoryProvider = Provider<RoleplayRepository>((ref) {
  return RoleplayRepositoryImpl(ref.watch(roleplayRemoteDataSourceProvider));
});
