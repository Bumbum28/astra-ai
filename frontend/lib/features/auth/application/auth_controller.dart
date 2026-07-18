import 'dart:async';
import 'dart:developer' as developer;

import 'package:astra_ai/core/network/network_providers.dart';
import 'package:astra_ai/features/auth/data/auth_providers.dart';
import 'package:astra_ai/features/auth/domain/entities/auth_session.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AuthActionController extends Notifier<bool> {
  @override
  bool build() => false;

  void setInProgress({required bool value}) {
    state = value;
  }
}

final authActionInProgressProvider =
    NotifierProvider<AuthActionController, bool>(AuthActionController.new);

class AuthController extends AsyncNotifier<AuthSession?> {
  @override
  Future<AuthSession?> build() async {
    final events = ref.watch(sessionEventBusProvider);
    final subscription = events.stream.listen((event) {
      state = const AsyncData<AuthSession?>(null);
    });
    ref.onDispose(() {
      unawaited(subscription.cancel());
    });

    return ref.watch(authRepositoryProvider).restoreSession();
  }

  Future<void> login({required String email, required String password}) async {
    _setActionInProgress(value: true);
    try {
      final session = await ref
          .read(authRepositoryProvider)
          .login(email: email, password: password);
      state = AsyncData<AuthSession?>(session);
    } finally {
      _setActionInProgress(value: false);
    }
  }

  Future<void> register({
    required String email,
    required String username,
    required String password,
  }) async {
    _setActionInProgress(value: true);
    try {
      final session = await ref
          .read(authRepositoryProvider)
          .register(email: email, username: username, password: password);
      state = AsyncData<AuthSession?>(session);
    } finally {
      _setActionInProgress(value: false);
    }
  }

  Future<void> logout() async {
    _setActionInProgress(value: true);
    try {
      await ref.read(authRepositoryProvider).logout();
    } on Object catch (error, stackTrace) {
      developer.log(
        'Remote session revoke failed during local logout.',
        name: 'astra.auth',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      state = const AsyncData<AuthSession?>(null);
      _setActionInProgress(value: false);
    }
  }

  Future<int> logoutAllDevices() async {
    _setActionInProgress(value: true);
    try {
      final revokedCount = await ref
          .read(authRepositoryProvider)
          .logoutAllDevices();
      state = const AsyncData<AuthSession?>(null);
      return revokedCount;
    } finally {
      _setActionInProgress(value: false);
    }
  }

  Future<void> retryRestore() async {
    state = const AsyncLoading<AuthSession?>();
    state = await AsyncValue.guard<AuthSession?>(() {
      return ref.read(authRepositoryProvider).restoreSession();
    });
  }

  void _setActionInProgress({required bool value}) {
    ref.read(authActionInProgressProvider.notifier).setInProgress(value: value);
  }
}

final authControllerProvider =
    AsyncNotifierProvider<AuthController, AuthSession?>(AuthController.new);
