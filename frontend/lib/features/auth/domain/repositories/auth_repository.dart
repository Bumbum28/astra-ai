import 'package:astra_ai/features/auth/domain/entities/auth_session.dart';

abstract interface class AuthRepository {
  Future<AuthSession?> restoreSession();

  Future<AuthSession> login({
    required String email,
    required String password,
    String? deviceName,
  });

  Future<AuthSession> register({
    required String email,
    required String username,
    required String password,
    String? deviceName,
  });

  Future<void> logout();

  Future<int> logoutAllDevices();
}
