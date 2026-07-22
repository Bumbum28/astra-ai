import 'package:astra_ai/core/config/config_providers.dart';
import 'package:astra_ai/core/network/network_providers.dart';
import 'package:astra_ai/features/memories/data/memory_remote_data_source.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final memoryRemoteDataSourceProvider = Provider<MemoryRemoteDataSource>((ref) {
  return MemoryRemoteDataSource(
    ref.watch(dioProvider),
    ref.watch(appConfigProvider),
  );
});
