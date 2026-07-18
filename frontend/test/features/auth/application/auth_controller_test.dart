import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/features/auth/application/auth_controller.dart';
import 'package:astra_ai/features/auth/data/auth_providers.dart';
import 'package:astra_ai/features/auth/domain/entities/auth_session.dart';
import 'package:astra_ai/features/auth/domain/entities/user.dart';
import 'package:astra_ai/features/auth/domain/repositories/auth_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('restores, logs in, and logs out through the repository', () async {
    final repository = _FakeAuthRepository();
    final container = ProviderContainer(
      overrides: [authRepositoryProvider.overrideWithValue(repository)],
    );
    addTearDown(container.dispose);

    expect(await container.read(authControllerProvider.future), isNull);

    await container
        .read(authControllerProvider.notifier)
        .login(email: 'user@example.com', password: 'secure-password');

    expect(
      container.read(authControllerProvider).value?.user.email,
      'user@example.com',
    );
    expect(repository.loginCalls, 1);
    expect(container.read(authActionInProgressProvider), isFalse);

    await container.read(authControllerProvider.notifier).logout();

    expect(container.read(authControllerProvider).value, isNull);
    expect(repository.logoutCalls, 1);
  });

  test('failed login keeps the unauthenticated route state stable', () async {
    final repository = _FakeAuthRepository(failLogin: true);
    final container = ProviderContainer(
      overrides: [authRepositoryProvider.overrideWithValue(repository)],
    );
    addTearDown(container.dispose);

    expect(await container.read(authControllerProvider.future), isNull);

    await expectLater(
      container
          .read(authControllerProvider.notifier)
          .login(email: 'user@example.com', password: 'wrong-password'),
      throwsA(isA<AppException>()),
    );

    final authState = container.read(authControllerProvider);
    expect(authState.hasError, isFalse);
    expect(authState.value, isNull);
    expect(container.read(authActionInProgressProvider), isFalse);
  });

  test(
    'failed logout-all preserves the current authenticated session',
    () async {
      final repository = _FakeAuthRepository(failLogoutAll: true);
      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      await container.read(authControllerProvider.future);
      await container
          .read(authControllerProvider.notifier)
          .login(email: 'user@example.com', password: 'secure-password');

      await expectLater(
        container.read(authControllerProvider.notifier).logoutAllDevices(),
        throwsA(isA<AppException>()),
      );

      expect(
        container.read(authControllerProvider).value?.user.email,
        'user@example.com',
      );
      expect(container.read(authActionInProgressProvider), isFalse);
    },
  );
}

class _FakeAuthRepository implements AuthRepository {
  _FakeAuthRepository({this.failLogin = false, this.failLogoutAll = false});

  final bool failLogin;
  final bool failLogoutAll;
  int loginCalls = 0;
  int logoutCalls = 0;

  static final _user = User(
    id: '77f26755-64e2-4d28-bb36-6731e0f58a91',
    email: 'user@example.com',
    username: 'astra_user',
    isActive: true,
    isVerified: false,
    createdAt: DateTime.utc(2026, 7, 18),
    updatedAt: DateTime.utc(2026, 7, 18),
  );

  @override
  Future<AuthSession?> restoreSession() async => null;

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
    String? deviceName,
  }) async {
    loginCalls += 1;
    if (failLogin) {
      throw const AppException(
        code: 'AUTH_INVALID_CREDENTIALS',
        message: 'Email or password is incorrect.',
        statusCode: 401,
      );
    }
    return AuthSession(user: _user);
  }

  @override
  Future<AuthSession> register({
    required String email,
    required String username,
    required String password,
    String? deviceName,
  }) async {
    return AuthSession(user: _user);
  }

  @override
  Future<void> logout() async {
    logoutCalls += 1;
  }

  @override
  Future<int> logoutAllDevices() async {
    if (failLogoutAll) {
      throw const AppException(
        code: 'NETWORK_ERROR',
        message: 'Server unavailable.',
      );
    }
    return 1;
  }
}
