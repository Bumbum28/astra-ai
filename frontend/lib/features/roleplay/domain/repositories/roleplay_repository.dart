import 'package:astra_ai/features/roleplay/domain/entities/character_profile.dart';
import 'package:astra_ai/features/roleplay/domain/entities/memory_entry.dart';
import 'package:astra_ai/features/roleplay/domain/entities/persona_profile.dart';

abstract interface class RoleplayRepository {
  Future<List<CharacterProfile>> listCharacters();
  Future<CharacterProfile> createCharacter({
    required String name,
    String? description,
    String? personality,
  });
  Future<List<PersonaProfile>> listPersonas();
  Future<PersonaProfile> createPersona({
    required String name,
    String? description,
    String? instructions,
    bool isDefault = false,
  });
  Future<List<MemoryEntry>> listMemories();
  Future<MemoryEntry> createMemory({
    required String content,
    String scope = 'user',
    String kind = 'fact',
    double importance = 0.5,
  });
  Future<void> archiveMemory(String memoryId);
}
