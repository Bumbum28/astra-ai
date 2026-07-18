import 'package:astra_ai/features/auth/data/auth_providers.dart';
import 'package:astra_ai/features/auth/domain/entities/auth_session.dart';
import 'package:astra_ai/features/auth/domain/repositories/auth_repository.dart';
import 'package:astra_ai/features/auth/presentation/pages/login_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('validates an invalid email before calling the repository', (
    tester,
  ) async {
    final repository = _CountingAuthRepository();

    await tester.pumpWidget(
      ProviderScope(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
        child: const MaterialApp(home: LoginPage()),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextFormField).first, 'not-an-email');
    await tester.enterText(find.byType(TextFormField).last, 'secure-password');
    await tester.tap(find.text('Đăng nhập'));
    await tester.pump();

    expect(find.text('Email không đúng định dạng.'), findsOneWidget);
    expect(repository.loginCalls, 0);
  });
}

class _CountingAuthRepository implements AuthRepository {
  int loginCalls = 0;

  @override
  Future<AuthSession?> restoreSession() async => null;

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
    String? deviceName,
  }) {
    loginCalls += 1;
    throw UnimplementedError();
  }

  @override
  Future<AuthSession> register({
    required String email,
    required String username,
    required String password,
    String? deviceName,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<void> logout() async {}

  @override
  Future<int> logoutAllDevices() async => 0;
}
