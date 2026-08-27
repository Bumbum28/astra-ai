import 'package:astra_ai/core/config/config_providers.dart';
import 'package:astra_ai/core/network/network_providers.dart';
import 'package:astra_ai/features/knowledge/data/knowledge_remote_data_source.dart';
import 'package:astra_ai/features/knowledge/domain/entities/knowledge_hit.dart';
import 'package:astra_ai/features/knowledge/domain/entities/knowledge_source.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final knowledgeRemoteProvider = Provider<KnowledgeRemoteDataSource>((ref) {
  return KnowledgeRemoteDataSource(
    ref.watch(dioProvider),
    ref.watch(appConfigProvider),
  );
});

class KnowledgeState {
  const KnowledgeState({
    required this.sources,
    this.hits = const <KnowledgeHit>[],
  });

  final List<KnowledgeSource> sources;
  final List<KnowledgeHit> hits;
}

class KnowledgeController extends AsyncNotifier<KnowledgeState> {
  @override
  Future<KnowledgeState> build() async {
    final sources = await ref.watch(knowledgeRemoteProvider).listSources();
    return KnowledgeState(sources: sources);
  }

  Future<void> addSource({
    required String name,
    required String content,
  }) async {
    await ref
        .read(knowledgeRemoteProvider)
        .createSource(name: name, content: content);
    ref.invalidateSelf();
  }

  Future<void> search(String query) async {
    final current = state.asData?.value;
    if (current == null) return;
    final hits = await ref.read(knowledgeRemoteProvider).search(query);
    state = AsyncData(KnowledgeState(sources: current.sources, hits: hits));
  }
}

final knowledgeControllerProvider =
    AsyncNotifierProvider<KnowledgeController, KnowledgeState>(
      KnowledgeController.new,
    );
