import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:dio/dio.dart';

abstract final class DioExceptionMapper {
  static AppException map(DioException exception) {
    final response = exception.response;
    if (response != null) {
      return ApiEnvelope.exceptionFromBody(
        response.data,
        statusCode: response.statusCode,
        fallbackMessage: 'Máy chủ từ chối yêu cầu.',
      );
    }

    final message = switch (exception.type) {
      DioExceptionType.connectionTimeout ||
      DioExceptionType.sendTimeout ||
      DioExceptionType.receiveTimeout =>
        'Kết nối đến máy chủ đã hết thời gian.',
      DioExceptionType.connectionError =>
        'Không thể kết nối đến Astra AI Server.',
      DioExceptionType.cancel => 'Yêu cầu đã bị hủy.',
      _ => 'Đã xảy ra lỗi mạng.',
    };

    return AppException(
      code: 'NETWORK_ERROR',
      message: message,
      details: exception.message,
    );
  }
}
