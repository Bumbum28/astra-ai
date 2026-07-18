import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/storage/token_store.dart';
import 'package:astra_ai/features/auth/data/datasources/auth_remote_data_source.dart';
import 'package:astra_ai/features/auth/domain/entities/auth_session.dart';
import 'package:astra_ai/features/auth/domain/repositories/auth_repository.dart';

class AuthRepositoryImpl implements AuthRepository {
  const AuthRepositoryImpl({
    required AuthRemoteDataSource remoteDataSource,
    required TokenStore tokenStore,
    required AppConfig config,
  }) : _remoteDataSource = remoteDataSource,
       _tokenStore = tokenStore,
       _config = config;

  final AuthRemoteDataSource _remoteDataSource;
  final TokenStore _tokenStore;
  final AppConfig _config;

  @override
  Future<AuthSession?> restoreSession() async {
    final tokens = await _tokenStore.read();
    if (tokens == null) {
      return null;
    }

    try {
      final user = await _remoteDataSource.getCurrentUser();
      return AuthSession(user: user);
    } on AppException catch (error) {
      if (error.statusCode == 401 || error.statusCode == 403) {
        await _tokenStore.clear();
        return null;
      }
      rethrow;
    }
  }

  @override
  Future<AuthSession> login({
    required String email,
    required String password,
    String? deviceName,
  }) async {
    final result = await _remoteDataSource.login(
      email: email.trim().toLowerCase(),
      password: password,
      deviceName: deviceName ?? _config.deviceName,
    );
    await _tokenStore.write(result.tokens);
    return AuthSession(user: result.user);
  }

  @override
  Future<AuthSession> register({
    required String email,
    required String username,
    required String password,
    String? deviceName,
  }) async {
    final result = await _remoteDataSource.register(
      email: email.trim().toLowerCase(),
      username: username.trim(),
      password: password,
      deviceName: deviceName ?? _config.deviceName,
    );
    await _tokenStore.write(result.tokens);
    return AuthSession(user: result.user);
  }

  @override
  Future<void> logout() async {
    final tokens = await _tokenStore.read();
    try {
      if (tokens != null) {
        await _remoteDataSource.logout(tokens.refreshToken);
      }
    } finally {
      await _tokenStore.clear();
    }
  }

  @override
  Future<int> logoutAllDevices() async {
    final revokedCount = await _remoteDataSource.logoutAllDevices();
    await _tokenStore.clear();
    return revokedCount;
  }
}
