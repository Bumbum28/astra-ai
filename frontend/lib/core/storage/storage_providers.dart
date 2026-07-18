import 'package:astra_ai/core/storage/secure_token_store.dart';
import 'package:astra_ai/core/storage/token_store.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

final tokenStoreProvider = Provider<TokenStore>((ref) {
  return SecureTokenStore(ref.watch(secureStorageProvider));
});
