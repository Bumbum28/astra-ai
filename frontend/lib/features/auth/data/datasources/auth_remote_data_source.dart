import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:astra_ai/core/network/auth_interceptor.dart';
import 'package:astra_ai/core/network/dio_exception_mapper.dart';
import 'package:astra_ai/features/auth/domain/entities/auth_tokens.dart';
import 'package:astra_ai/features/auth/domain/entities/user.dart';
import 'package:dio/dio.dart';

class AuthRemoteResult {
  const AuthRemoteResult({required this.user, required this.tokens});

  final User user;
  final AuthTokens tokens;
}

class AuthRemoteDataSource {
  const AuthRemoteDataSource(this._dio, this._config);

  final Dio _dio;
  final AppConfig _config;

  Future<AuthRemoteResult> login({
    required String email,
    required String password,
    String? deviceName,
  }) {
    return _authenticate(
      path: 'auth/login',
      payload: <String, Object?>{
        'email': email,
        'password': password,
        'device_name': ?deviceName,
      },
    );
  }

  Future<AuthRemoteResult> register({
    required String email,
    required String username,
    required String password,
    String? deviceName,
  }) {
    return _authenticate(
      path: 'auth/register',
      payload: <String, Object?>{
        'email': email,
        'username': username,
        'password': password,
        'device_name': ?deviceName,
      },
    );
  }

  Future<User> getCurrentUser() async {
    try {
      final response = await _dio.get<Object?>(_config.endpoint('auth/me'));
      final data = ApiEnvelope.requireDataMap(response.data);
      return User.fromJson(data);
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(
        message: 'Dữ liệu người dùng từ máy chủ không hợp lệ.',
        details: error.message,
      );
    } on TypeError catch (error) {
      throw _invalidResponse(
        message: 'Dữ liệu người dùng từ máy chủ không hợp lệ.',
        details: error.toString(),
      );
    }
  }

  Future<void> logout(String refreshToken) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('auth/logout'),
        data: <String, Object?>{'refresh_token': refreshToken},
      );
      ApiEnvelope.requireSuccess(response.data);
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<int> logoutAllDevices() async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('auth/logout-all'),
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      final count = data['revoked_sessions'];
      return switch (count) {
        final int value => value,
        final num value => value.toInt(),
        _ => throw const FormatException('Missing revoked session count.'),
      };
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(
        message: 'Phản hồi đăng xuất từ máy chủ không hợp lệ.',
        details: error.message,
      );
    }
  }

  Future<AuthRemoteResult> _authenticate({
    required String path,
    required Map<String, Object?> payload,
  }) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint(path),
        data: payload,
        options: AuthInterceptor.skipAuthentication(),
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      final userData = data['user'];
      final tokenData = data['tokens'];

      if (userData is! Map || tokenData is! Map) {
        throw const FormatException('Missing authentication payload.');
      }

      return AuthRemoteResult(
        user: User.fromJson(Map<String, Object?>.from(userData)),
        tokens: AuthTokens.fromJson(Map<String, Object?>.from(tokenData)),
      );
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(
        message: 'Phản hồi đăng nhập từ máy chủ không hợp lệ.',
        details: error.message,
      );
    } on TypeError catch (error) {
      throw _invalidResponse(
        message: 'Phản hồi đăng nhập từ máy chủ không hợp lệ.',
        details: error.toString(),
      );
    }
  }

  AppException _invalidResponse({
    required String message,
    required Object details,
  }) {
    return AppException(
      code: 'INVALID_SERVER_RESPONSE',
      message: message,
      details: details,
    );
  }
}
