import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ApiEnvelope', () {
    test('returns data from a successful response', () {
      final data = ApiEnvelope.requireDataMap(<String, Object?>{
        'success': true,
        'data': <String, Object?>{'value': 42},
        'error': null,
      });

      expect(data['value'], 42);
    });

    test('maps an API error to AppException', () {
      expect(
        () => ApiEnvelope.requireDataMap(<String, Object?>{
          'success': false,
          'data': null,
          'error': <String, Object?>{
            'code': 'AUTH_INVALID_CREDENTIALS',
            'message': 'Invalid credentials.',
          },
        }),
        throwsA(
          isA<AppException>()
              .having((error) => error.code, 'code', 'AUTH_INVALID_CREDENTIALS')
              .having(
                (error) => error.message,
                'message',
                'Invalid credentials.',
              ),
        ),
      );
    });
  });
}
