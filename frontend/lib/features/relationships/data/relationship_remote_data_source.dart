import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:astra_ai/core/network/dio_exception_mapper.dart';
import 'package:astra_ai/features/relationships/domain/entities/relationship.dart';
import 'package:dio/dio.dart';

class RelationshipRemoteDataSource {
  const RelationshipRemoteDataSource(this._dio, this._config);

  final Dio _dio;
  final AppConfig _config;

  Future<RelationshipProfile?> get(String conversationId) async {
    try {
      final response = await _dio.get<Object?>(
        _config.endpoint('conversations/$conversationId/relationship'),
      );
      return RelationshipProfile.fromJson(
        ApiEnvelope.requireDataMap(response.data),
      );
    } on DioException catch (error) {
      final mapped = DioExceptionMapper.map(error);
      if (mapped.code == 'RELATIONSHIP_NOT_FOUND') {
        return null;
      }
      throw mapped;
    } on FormatException catch (error) {
      throw _invalid(error.message);
    } on TypeError catch (error) {
      throw _invalid(error.toString());
    }
  }

  Future<RelationshipProfile> update(
    String conversationId,
    Map<String, Object?> data,
  ) async {
    try {
      final response = await _dio.patch<Object?>(
        _config.endpoint('conversations/$conversationId/relationship'),
        data: data,
      );
      return RelationshipProfile.fromJson(
        ApiEnvelope.requireDataMap(response.data),
      );
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalid(error.message);
    } on TypeError catch (error) {
      throw _invalid(error.toString());
    }
  }

  AppException _invalid(Object details) {
    return AppException(
      code: 'INVALID_SERVER_RESPONSE',
      message: 'Dữ liệu Relationship từ máy chủ không hợp lệ.',
      details: details,
    );
  }
}
