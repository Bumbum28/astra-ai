// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_tokens.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_AuthTokens _$AuthTokensFromJson(Map<String, dynamic> json) => $checkedCreate(
  '_AuthTokens',
  json,
  ($checkedConvert) {
    final val = _AuthTokens(
      accessToken: $checkedConvert('access_token', (v) => v as String),
      refreshToken: $checkedConvert('refresh_token', (v) => v as String),
      tokenType: $checkedConvert('token_type', (v) => v as String),
      accessExpiresIn: $checkedConvert(
        'access_expires_in',
        (v) => (v as num).toInt(),
      ),
      refreshExpiresIn: $checkedConvert(
        'refresh_expires_in',
        (v) => (v as num).toInt(),
      ),
    );
    return val;
  },
  fieldKeyMap: const {
    'accessToken': 'access_token',
    'refreshToken': 'refresh_token',
    'tokenType': 'token_type',
    'accessExpiresIn': 'access_expires_in',
    'refreshExpiresIn': 'refresh_expires_in',
  },
);

Map<String, dynamic> _$AuthTokensToJson(_AuthTokens instance) =>
    <String, dynamic>{
      'access_token': instance.accessToken,
      'refresh_token': instance.refreshToken,
      'token_type': instance.tokenType,
      'access_expires_in': instance.accessExpiresIn,
      'refresh_expires_in': instance.refreshExpiresIn,
    };
