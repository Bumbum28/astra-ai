import 'package:astra_ai/features/auth/domain/entities/auth_tokens.dart';

abstract interface class TokenStore {
  Future<AuthTokens?> read();

  Future<void> write(AuthTokens tokens);

  Future<void> clear();
}
