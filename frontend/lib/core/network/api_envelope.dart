import 'package:astra_ai/core/errors/app_exception.dart';

class ApiEnvelope {
  const ApiEnvelope._();

  static Map<String, Object?> requireDataMap(Object? body) {
    final root = _asStringObjectMap(body);
    final success = root['success'];

    if (success != true) {
      throw _toException(root);
    }

    return _asStringObjectMap(root['data']);
  }

  static void requireSuccess(Object? body) {
    final root = _asStringObjectMap(body);
    if (root['success'] != true) {
      throw _toException(root);
    }
  }

  static AppException exceptionFromBody(
    Object? body, {
    int? statusCode,
    String fallbackCode = 'NETWORK_REQUEST_FAILED',
    String fallbackMessage = 'Không thể hoàn tất yêu cầu.',
  }) {
    try {
      final root = _asStringObjectMap(body);
      return _toException(root, statusCode: statusCode);
    } on FormatException {
      return AppException(
        code: fallbackCode,
        message: fallbackMessage,
        statusCode: statusCode,
      );
    }
  }

  static AppException _toException(
    Map<String, Object?> root, {
    int? statusCode,
  }) {
    final errorValue = root['error'];
    final error = errorValue is Map
        ? _asStringObjectMap(errorValue)
        : <String, Object?>{};

    return AppException(
      code: error['code']?.toString() ?? 'UNKNOWN_API_ERROR',
      message: error['message']?.toString() ?? 'Đã xảy ra lỗi không xác định.',
      statusCode: statusCode,
      details: error['details'],
    );
  }

  static Map<String, Object?> _asStringObjectMap(Object? value) {
    if (value is Map<String, Object?>) {
      return value;
    }
    if (value is Map) {
      try {
        return Map<String, Object?>.from(value);
      } on Object {
        throw const FormatException('Expected a JSON object with string keys.');
      }
    }
    throw const FormatException('Expected a JSON object.');
  }
}
