import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:astra_ai/core/network/dio_exception_mapper.dart';
import 'package:astra_ai/features/memories/domain/memory.dart';
import 'package:dio/dio.dart';

class MemoryRemoteDataSource {
  const MemoryRemoteDataSource(this._dio, this._config);

  final Dio _dio;
  final AppConfig _config;

  Future<ConversationMemorySnapshot> getSnapshot(String conversationId) async {
    try {
      final response = await _dio.get<Object?>(
        _config.endpoint('conversations/$conversationId/memory'),
      );
      return ConversationMemorySnapshot.fromJson(
        ApiEnvelope.requireDataMap(response.data),
      );
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<bool> refresh(String conversationId) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('conversations/$conversationId/memory/refresh'),
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      return data['queued'] == true;
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<void> archive(String memoryId) async {
    try {
      await _dio.delete<void>(_config.endpoint('memories/$memoryId'));
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }
}
