import 'package:freezed_annotation/freezed_annotation.dart';

part 'auth_tokens.freezed.dart';
part 'auth_tokens.g.dart';

@freezed
abstract class AuthTokens with _$AuthTokens {
  const factory AuthTokens({
    @JsonKey(name: 'access_token') required String accessToken,
    @JsonKey(name: 'refresh_token') required String refreshToken,
    @JsonKey(name: 'token_type') required String tokenType,
    @JsonKey(name: 'access_expires_in') required int accessExpiresIn,
    @JsonKey(name: 'refresh_expires_in') required int refreshExpiresIn,
  }) = _AuthTokens;

  factory AuthTokens.fromJson(Map<String, Object?> json) =>
      _$AuthTokensFromJson(json);
}
