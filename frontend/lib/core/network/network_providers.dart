import 'dart:async';
import 'dart:developer' as developer;

import 'package:astra_ai/core/config/config_providers.dart';
import 'package:astra_ai/core/network/auth_interceptor.dart';
import 'package:astra_ai/core/network/session_event_bus.dart';
import 'package:astra_ai/core/storage/storage_providers.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final sessionEventBusProvider = Provider<SessionEventBus>((ref) {
  final bus = SessionEventBus();
  ref.onDispose(() {
    unawaited(bus.dispose());
  });
  return bus;
});

final refreshDioProvider = Provider<Dio>((ref) {
  final config = ref.watch(appConfigProvider);
  return Dio(
    BaseOptions(
      baseUrl: config.apiBaseUrl,
      connectTimeout: config.connectTimeout,
      receiveTimeout: config.receiveTimeout,
      headers: const <String, Object?>{
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ),
  );
});

final dioProvider = Provider<Dio>((ref) {
  final config = ref.watch(appConfigProvider);
  final dio = Dio(
    BaseOptions(
      baseUrl: config.apiBaseUrl,
      connectTimeout: config.connectTimeout,
      receiveTimeout: config.receiveTimeout,
      headers: const <String, Object?>{
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ),
  );

  dio.interceptors.add(
    AuthInterceptor(
      client: dio,
      refreshClient: ref.watch(refreshDioProvider),
      tokenStore: ref.watch(tokenStoreProvider),
      sessionEvents: ref.watch(sessionEventBusProvider),
      config: config,
    ),
  );

  if (kDebugMode) {
    dio.interceptors.add(
      LogInterceptor(
        requestBody: false,
        responseBody: false,
        logPrint: (message) {
          developer.log(message.toString(), name: 'astra.network');
        },
      ),
    );
  }

  ref.onDispose(() {
    dio.close(force: true);
  });
  return dio;
});
