import 'package:astra_ai/features/characters/domain/entities/character.dart';
import 'package:astra_ai/features/characters/domain/entities/persona.dart';

abstract interface class RoleplayCatalogRepository {
  Future<List<CharacterProfile>> listCharacters();

  Future<CharacterProfile> createCharacter(Map<String, Object?> data);

  Future<CharacterProfile> updateCharacter(
    String characterId,
    Map<String, Object?> data,
  );

  Future<void> archiveCharacter(String characterId);

  Future<List<PersonaProfile>> listPersonas();

  Future<PersonaProfile> createPersona(Map<String, Object?> data);

  Future<PersonaProfile> updatePersona(
    String personaId,
    Map<String, Object?> data,
  );

  Future<void> archivePersona(String personaId);
}
