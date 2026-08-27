import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:astra_ai/core/network/dio_exception_mapper.dart';
import 'package:astra_ai/features/roleplay/domain/entities/character_profile.dart';
import 'package:astra_ai/features/roleplay/domain/entities/memory_entry.dart';
import 'package:astra_ai/features/roleplay/domain/entities/persona_profile.dart';
import 'package:dio/dio.dart';

class RoleplayRemoteDataSource {
  const RoleplayRemoteDataSource(this._dio, this._config);

  final Dio _dio;
  final AppConfig _config;

  Future<List<CharacterProfile>> listCharacters() async {
    final data = await _getList('characters');
    return data.map(CharacterProfile.fromJson).toList(growable: false);
  }

  Future<CharacterProfile> createCharacter({
    required String name,
    String? description,
    String? personality,
  }) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('characters'),
        data: <String, Object?>{
          'name': name,
          'description': ?description,
          'personality': ?personality,
        },
      );
      return CharacterProfile.fromJson(
        ApiEnvelope.requireDataMap(response.data),
      );
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<List<PersonaProfile>> listPersonas() async {
    final data = await _getList('personas');
    return data.map(PersonaProfile.fromJson).toList(growable: false);
  }

  Future<PersonaProfile> createPersona({
    required String name,
    String? description,
    String? instructions,
    bool isDefault = false,
  }) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('personas'),
        data: <String, Object?>{
          'name': name,
          'description': ?description,
          'instructions': ?instructions,
          'is_default': isDefault,
        },
      );
      return PersonaProfile.fromJson(ApiEnvelope.requireDataMap(response.data));
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<List<MemoryEntry>> listMemories() async {
    final data = await _getList('memories');
    return data.map(MemoryEntry.fromJson).toList(growable: false);
  }

  Future<MemoryEntry> createMemory({
    required String content,
    String scope = 'user',
    String kind = 'fact',
    double importance = 0.5,
  }) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('memories'),
        data: <String, Object?>{
          'content': content,
          'scope': scope,
          'kind': kind,
          'importance': importance,
        },
      );
      return MemoryEntry.fromJson(ApiEnvelope.requireDataMap(response.data));
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<void> archiveMemory(String memoryId) async {
    try {
      await _dio.delete<Object?>(_config.endpoint('memories/$memoryId'));
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<List<Map<String, Object?>>> _getList(String path) async {
    try {
      final response = await _dio.get<Object?>(_config.endpoint(path));
      final data = ApiEnvelope.requireDataMap(response.data);
      final rawItems = data['items'];
      if (rawItems is! List) {
        throw const FormatException('Missing list items.');
      }
      return rawItems
          .map((item) => Map<String, Object?>.from(item! as Map))
          .toList(growable: false);
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }
}
