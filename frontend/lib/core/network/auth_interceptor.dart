import 'dart:async';

import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:astra_ai/core/network/session_event_bus.dart';
import 'package:astra_ai/core/storage/token_store.dart';
import 'package:astra_ai/features/auth/domain/entities/auth_tokens.dart';
import 'package:dio/dio.dart';

class AuthInterceptor extends Interceptor {
  AuthInterceptor({
    required Dio client,
    required Dio refreshClient,
    required TokenStore tokenStore,
    required SessionEventBus sessionEvents,
    required AppConfig config,
  }) : _client = client,
       _refreshClient = refreshClient,
       _tokenStore = tokenStore,
       _sessionEvents = sessionEvents,
       _config = config;

  static const _retriedKey = 'astra.auth.retried';
  static const _skipAuthKey = 'astra.auth.skip';

  final Dio _client;
  final Dio _refreshClient;
  final TokenStore _tokenStore;
  final SessionEventBus _sessionEvents;
  final AppConfig _config;

  Future<String?>? _refreshInFlight;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    unawaited(_attachToken(options, handler));
  }

  Future<void> _attachToken(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (options.extra[_skipAuthKey] == true) {
      handler.next(options);
      return;
    }

    final tokens = await _tokenStore.read();
    if (tokens != null) {
      options.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    unawaited(_handleUnauthorized(err, handler));
  }

  Future<void> _handleUnauthorized(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    final request = error.requestOptions;
    final isUnauthorized = error.response?.statusCode == 401;
    final wasRetried = request.extra[_retriedKey] == true;
    final skipAuth = request.extra[_skipAuthKey] == true;
    final isRefreshRequest = request.path.endsWith('auth/refresh');

    if (!isUnauthorized || wasRetried || skipAuth || isRefreshRequest) {
      handler.next(error);
      return;
    }

    try {
      final accessToken = await _singleFlightRefresh();
      if (accessToken == null) {
        handler.next(error);
        return;
      }

      request.extra[_retriedKey] = true;
      request.headers['Authorization'] = 'Bearer $accessToken';
      final response = await _client.fetch<Object?>(request);
      handler.resolve(response);
    } on DioException catch (refreshError) {
      handler.next(refreshError);
    } on Object {
      handler.next(error);
    }
  }

  Future<String?> _singleFlightRefresh() {
    final current = _refreshInFlight;
    if (current != null) {
      return current;
    }

    final future = _refreshTokens();
    _refreshInFlight = future;
    return future.whenComplete(() {
      _refreshInFlight = null;
    });
  }

  Future<String?> _refreshTokens() async {
    final currentTokens = await _tokenStore.read();
    if (currentTokens == null) {
      await _expireLocalSession();
      return null;
    }

    try {
      final response = await _refreshClient.post<Object?>(
        _config.endpoint('auth/refresh'),
        data: <String, Object?>{
          'refresh_token': currentTokens.refreshToken,
          'device_name': _config.deviceName,
        },
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      final tokenData = data['tokens'];
      if (tokenData is! Map) {
        throw const FormatException('Missing token payload.');
      }

      final nextTokens = AuthTokens.fromJson(
        Map<String, Object?>.from(tokenData),
      );
      await _tokenStore.write(nextTokens);
      return nextTokens.accessToken;
    } on DioException catch (error) {
      final statusCode = error.response?.statusCode;
      if (statusCode == 401 || statusCode == 403) {
        await _expireLocalSession();
        return null;
      }
      rethrow;
    } on FormatException {
      await _expireLocalSession();
      return null;
    }
  }

  Future<void> _expireLocalSession() async {
    await _tokenStore.clear();
    _sessionEvents.emitExpired();
  }

  static Options skipAuthentication() {
    return Options(extra: <String, Object?>{_skipAuthKey: true});
  }
}
