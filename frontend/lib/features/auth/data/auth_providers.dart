import 'package:astra_ai/core/config/config_providers.dart';
import 'package:astra_ai/core/network/network_providers.dart';
import 'package:astra_ai/core/storage/storage_providers.dart';
import 'package:astra_ai/features/auth/data/datasources/auth_remote_data_source.dart';
import 'package:astra_ai/features/auth/data/repositories/auth_repository_impl.dart';
import 'package:astra_ai/features/auth/domain/repositories/auth_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final authRemoteDataSourceProvider = Provider<AuthRemoteDataSource>((ref) {
  return AuthRemoteDataSource(
    ref.watch(dioProvider),
    ref.watch(appConfigProvider),
  );
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(
    remoteDataSource: ref.watch(authRemoteDataSourceProvider),
    tokenStore: ref.watch(tokenStoreProvider),
    config: ref.watch(appConfigProvider),
  );
});
