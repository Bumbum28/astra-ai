import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:astra_ai/core/network/dio_exception_mapper.dart';
import 'package:astra_ai/features/knowledge/domain/entities/knowledge_hit.dart';
import 'package:astra_ai/features/knowledge/domain/entities/knowledge_source.dart';
import 'package:dio/dio.dart';

class KnowledgeRemoteDataSource {
  const KnowledgeRemoteDataSource(this._dio, this._config);

  final Dio _dio;
  final AppConfig _config;

  Future<List<KnowledgeSource>> listSources() async {
    try {
      final response = await _dio.get<Object?>(
        _config.endpoint('knowledge/sources'),
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      final raw = data['items'] as List? ?? const <Object?>[];
      return raw
          .map(
            (item) => KnowledgeSource.fromJson(
              Map<String, Object?>.from(item! as Map),
            ),
          )
          .toList(growable: false);
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<KnowledgeSource> createSource({
    required String name,
    required String content,
  }) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('knowledge/sources'),
        data: <String, Object?>{'name': name, 'content': content},
      );
      return KnowledgeSource.fromJson(
        ApiEnvelope.requireDataMap(response.data),
      );
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<List<KnowledgeHit>> search(String query) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('knowledge/search'),
        data: <String, Object?>{'query': query, 'top_k': 8},
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      final raw = data['items'] as List? ?? const <Object?>[];
      return raw
          .map(
            (item) =>
                KnowledgeHit.fromJson(Map<String, Object?>.from(item! as Map)),
          )
          .toList(growable: false);
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }
}
