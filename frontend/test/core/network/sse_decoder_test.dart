import 'package:astra_ai/core/network/sse_decoder.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('decodes SSE frames split across transport chunks', () {
    final decoder = SseDecoder();

    final first = decoder.add(
      'event: message.delta\ndata: {"delta":"Xin',
    );
    final second = decoder.add(' chào"}\n\n');

    expect(first, isEmpty);
    expect(second, hasLength(1));
    expect(second.single.event, 'message.delta');
    expect(second.single.data, '{"delta":"Xin chào"}');
  });
}
