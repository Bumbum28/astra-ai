import 'package:astra_ai/features/roleplay/data/roleplay_providers.dart';
import 'package:astra_ai/features/roleplay/domain/entities/character_profile.dart';
import 'package:astra_ai/features/roleplay/domain/entities/memory_entry.dart';
import 'package:astra_ai/features/roleplay/domain/entities/persona_profile.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class RoleplayState {
  const RoleplayState({
    required this.characters,
    required this.personas,
    required this.memories,
  });

  final List<CharacterProfile> characters;
  final List<PersonaProfile> personas;
  final List<MemoryEntry> memories;
}

class RoleplayController extends AsyncNotifier<RoleplayState> {
  @override
  Future<RoleplayState> build() async {
    final repo = ref.watch(roleplayRepositoryProvider);
    final results = await Future.wait<Object>(<Future<Object>>[
      repo.listCharacters(),
      repo.listPersonas(),
      repo.listMemories(),
    ]);
    return RoleplayState(
      characters: results[0] as List<CharacterProfile>,
      personas: results[1] as List<PersonaProfile>,
      memories: results[2] as List<MemoryEntry>,
    );
  }

  Future<void> addCharacter({required String name, String? personality}) async {
    await ref
        .read(roleplayRepositoryProvider)
        .createCharacter(name: name, personality: personality);
    ref.invalidateSelf();
  }

  Future<void> addPersona({required String name, String? description}) async {
    await ref
        .read(roleplayRepositoryProvider)
        .createPersona(name: name, description: description);
    ref.invalidateSelf();
  }

  Future<void> addMemory(String content) async {
    await ref.read(roleplayRepositoryProvider).createMemory(content: content);
    ref.invalidateSelf();
  }

  Future<void> archiveMemory(String id) async {
    await ref.read(roleplayRepositoryProvider).archiveMemory(id);
    ref.invalidateSelf();
  }
}

final roleplayControllerProvider =
    AsyncNotifierProvider<RoleplayController, RoleplayState>(
      RoleplayController.new,
    );
