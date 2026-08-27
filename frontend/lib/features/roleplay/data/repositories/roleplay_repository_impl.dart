import 'package:astra_ai/features/roleplay/data/datasources/roleplay_remote_data_source.dart';
import 'package:astra_ai/features/roleplay/domain/entities/character_profile.dart';
import 'package:astra_ai/features/roleplay/domain/entities/memory_entry.dart';
import 'package:astra_ai/features/roleplay/domain/entities/persona_profile.dart';
import 'package:astra_ai/features/roleplay/domain/repositories/roleplay_repository.dart';

class RoleplayRepositoryImpl implements RoleplayRepository {
  const RoleplayRepositoryImpl(this._remote);

  final RoleplayRemoteDataSource _remote;

  @override
  Future<List<CharacterProfile>> listCharacters() => _remote.listCharacters();

  @override
  Future<CharacterProfile> createCharacter({
    required String name,
    String? description,
    String? personality,
  }) => _remote.createCharacter(
    name: name,
    description: description,
    personality: personality,
  );

  @override
  Future<List<PersonaProfile>> listPersonas() => _remote.listPersonas();

  @override
  Future<PersonaProfile> createPersona({
    required String name,
    String? description,
    String? instructions,
    bool isDefault = false,
  }) => _remote.createPersona(
    name: name,
    description: description,
    instructions: instructions,
    isDefault: isDefault,
  );

  @override
  Future<List<MemoryEntry>> listMemories() => _remote.listMemories();

  @override
  Future<MemoryEntry> createMemory({
    required String content,
    String scope = 'user',
    String kind = 'fact',
    double importance = 0.5,
  }) => _remote.createMemory(
    content: content,
    scope: scope,
    kind: kind,
    importance: importance,
  );

  @override
  Future<void> archiveMemory(String memoryId) =>
      _remote.archiveMemory(memoryId);
}
