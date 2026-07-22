import 'package:astra_ai/features/characters/data/datasources/roleplay_catalog_remote_data_source.dart';
import 'package:astra_ai/features/characters/domain/entities/character.dart';
import 'package:astra_ai/features/characters/domain/entities/persona.dart';
import 'package:astra_ai/features/characters/domain/repositories/roleplay_catalog_repository.dart';

class RoleplayCatalogRepositoryImpl implements RoleplayCatalogRepository {
  const RoleplayCatalogRepositoryImpl(this._remote);

  final RoleplayCatalogRemoteDataSource _remote;

  @override
  Future<void> archiveCharacter(String characterId) =>
      _remote.archiveCharacter(characterId);

  @override
  Future<void> archivePersona(String personaId) =>
      _remote.archivePersona(personaId);

  @override
  Future<CharacterProfile> createCharacter(Map<String, Object?> data) =>
      _remote.createCharacter(data);

  @override
  Future<PersonaProfile> createPersona(Map<String, Object?> data) =>
      _remote.createPersona(data);

  @override
  Future<List<CharacterProfile>> listCharacters() => _remote.listCharacters();

  @override
  Future<List<PersonaProfile>> listPersonas() => _remote.listPersonas();

  @override
  Future<CharacterProfile> updateCharacter(
    String characterId,
    Map<String, Object?> data,
  ) => _remote.updateCharacter(characterId, data);

  @override
  Future<PersonaProfile> updatePersona(
    String personaId,
    Map<String, Object?> data,
  ) => _remote.updatePersona(personaId, data);
}
