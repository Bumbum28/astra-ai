import 'dart:convert';

import 'package:astra_ai/core/storage/token_store.dart';
import 'package:astra_ai/features/auth/domain/entities/auth_tokens.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureTokenStore implements TokenStore {
  SecureTokenStore(this._storage);

  static const _storageKey = 'astra.auth.tokens';

  final FlutterSecureStorage _storage;
  AuthTokens? _memoryCache;
  bool _hasLoaded = false;

  @override
  Future<AuthTokens?> read() async {
    if (_hasLoaded) {
      return _memoryCache;
    }

    final raw = await _storage.read(key: _storageKey);
    _hasLoaded = true;
    if (raw == null || raw.isEmpty) {
      return null;
    }

    try {
      final decoded = jsonDecode(raw);
      if (decoded is! Map) {
        await clear();
        return null;
      }
      _memoryCache = AuthTokens.fromJson(Map<String, Object?>.from(decoded));
      return _memoryCache;
    } on FormatException {
      await clear();
      return null;
    } on TypeError {
      await clear();
      return null;
    }
  }

  @override
  Future<void> write(AuthTokens tokens) async {
    await _storage.write(key: _storageKey, value: jsonEncode(tokens.toJson()));
    _memoryCache = tokens;
    _hasLoaded = true;
  }

  @override
  Future<void> clear() async {
    _memoryCache = null;
    _hasLoaded = true;
    await _storage.delete(key: _storageKey);
  }
}
