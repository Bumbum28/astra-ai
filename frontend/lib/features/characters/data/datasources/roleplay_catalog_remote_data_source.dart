import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:astra_ai/core/network/dio_exception_mapper.dart';
import 'package:astra_ai/features/characters/domain/entities/character.dart';
import 'package:astra_ai/features/characters/domain/entities/persona.dart';
import 'package:dio/dio.dart';

class RoleplayCatalogRemoteDataSource {
  const RoleplayCatalogRemoteDataSource(this._dio, this._config);

  final Dio _dio;
  final AppConfig _config;

  Future<List<CharacterProfile>> listCharacters() async {
    return _list(
      'characters',
      CharacterProfile.fromJson,
    );
  }

  Future<CharacterProfile> createCharacter(Map<String, Object?> data) async {
    return _write('characters', data, CharacterProfile.fromJson);
  }

  Future<CharacterProfile> updateCharacter(
    String characterId,
    Map<String, Object?> data,
  ) async {
    return _write(
      'characters/$characterId',
      data,
      CharacterProfile.fromJson,
      patch: true,
    );
  }

  Future<void> archiveCharacter(String characterId) {
    return _archive('characters/$characterId');
  }

  Future<List<PersonaProfile>> listPersonas() async {
    return _list('personas', PersonaProfile.fromJson);
  }

  Future<PersonaProfile> createPersona(Map<String, Object?> data) async {
    return _write('personas', data, PersonaProfile.fromJson);
  }

  Future<PersonaProfile> updatePersona(
    String personaId,
    Map<String, Object?> data,
  ) async {
    return _write(
      'personas/$personaId',
      data,
      PersonaProfile.fromJson,
      patch: true,
    );
  }

  Future<void> archivePersona(String personaId) {
    return _archive('personas/$personaId');
  }

  Future<List<T>> _list<T>(
    String path,
    T Function(Map<String, Object?>) parser,
  ) async {
    try {
      final response = await _dio.get<Object?>(
        _config.endpoint(path),
        queryParameters: const <String, Object?>{'limit': 100},
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      final rawItems = data['items'];
      if (rawItems is! List) {
        throw const FormatException('Missing catalog items.');
      }
      return rawItems
          .map((item) => parser(_map(item)))
          .toList(growable: false);
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(error.message);
    } on TypeError catch (error) {
      throw _invalidResponse(error.toString());
    }
  }

  Future<T> _write<T>(
    String path,
    Map<String, Object?> data,
    T Function(Map<String, Object?>) parser, {
    bool patch = false,
  }) async {
    try {
      final response = patch
          ? await _dio.patch<Object?>(_config.endpoint(path), data: data)
          : await _dio.post<Object?>(_config.endpoint(path), data: data);
      return parser(ApiEnvelope.requireDataMap(response.data));
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(error.message);
    } on TypeError catch (error) {
      throw _invalidResponse(error.toString());
    }
  }

  Future<void> _archive(String path) async {
    try {
      await _dio.delete<Object?>(_config.endpoint(path));
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Map<String, Object?> _map(Object? value) {
    if (value is! Map) {
      throw const FormatException('Expected a JSON object.');
    }
    return Map<String, Object?>.from(value);
  }

  AppException _invalidResponse(Object details) {
    return AppException(
      code: 'INVALID_SERVER_RESPONSE',
      message: 'Dữ liệu Character/Persona từ máy chủ không hợp lệ.',
      details: details,
    );
  }
}
