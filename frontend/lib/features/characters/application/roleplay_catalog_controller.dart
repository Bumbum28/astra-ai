import 'package:astra_ai/features/characters/data/roleplay_catalog_providers.dart';
import 'package:astra_ai/features/characters/domain/entities/character.dart';
import 'package:astra_ai/features/characters/domain/entities/persona.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class RoleplayCatalogState {
  const RoleplayCatalogState({
    required this.characters,
    required this.personas,
  });

  final List<CharacterProfile> characters;
  final List<PersonaProfile> personas;

  RoleplayCatalogState copyWith({
    List<CharacterProfile>? characters,
    List<PersonaProfile>? personas,
  }) {
    return RoleplayCatalogState(
      characters: characters ?? this.characters,
      personas: personas ?? this.personas,
    );
  }
}

class RoleplayCatalogController extends AsyncNotifier<RoleplayCatalogState> {
  @override
  Future<RoleplayCatalogState> build() async {
    final repository = ref.watch(roleplayCatalogRepositoryProvider);
    final characters = await repository.listCharacters();
    final personas = await repository.listPersonas();
    return RoleplayCatalogState(characters: characters, personas: personas);
  }

  Future<void> refreshCatalog() async {
    state = const AsyncLoading<RoleplayCatalogState>();
    state = await AsyncValue.guard(build);
  }

  Future<CharacterProfile> saveCharacter({
    CharacterProfile? current,
    required Map<String, Object?> data,
  }) async {
    final repository = ref.read(roleplayCatalogRepositoryProvider);
    final saved = current == null
        ? await repository.createCharacter(data)
        : await repository.updateCharacter(current.id, data);
    final value = state.value;
    if (value != null) {
      final items = <CharacterProfile>[
        saved,
        ...value.characters.where((item) => item.id != saved.id),
      ];
      state = AsyncData(value.copyWith(characters: items));
    }
    return saved;
  }

  Future<void> archiveCharacter(String characterId) async {
    await ref
        .read(roleplayCatalogRepositoryProvider)
        .archiveCharacter(characterId);
    final value = state.value;
    if (value != null) {
      state = AsyncData(
        value.copyWith(
          characters: value.characters
              .where((item) => item.id != characterId)
              .toList(growable: false),
        ),
      );
    }
  }

  Future<PersonaProfile> savePersona({
    PersonaProfile? current,
    required Map<String, Object?> data,
  }) async {
    final repository = ref.read(roleplayCatalogRepositoryProvider);
    final saved = current == null
        ? await repository.createPersona(data)
        : await repository.updatePersona(current.id, data);
    final value = state.value;
    if (value != null) {
      final items = <PersonaProfile>[
        saved,
        ...value.personas.where((item) => item.id != saved.id),
      ];
      state = AsyncData(value.copyWith(personas: items));
    }
    return saved;
  }

  Future<void> archivePersona(String personaId) async {
    await ref.read(roleplayCatalogRepositoryProvider).archivePersona(personaId);
    final value = state.value;
    if (value != null) {
      state = AsyncData(
        value.copyWith(
          personas: value.personas
              .where((item) => item.id != personaId)
              .toList(growable: false),
        ),
      );
    }
  }
}

final roleplayCatalogControllerProvider =
    AsyncNotifierProvider<RoleplayCatalogController, RoleplayCatalogState>(
      RoleplayCatalogController.new,
    );
