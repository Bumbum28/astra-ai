import 'dart:convert';

class SseFrame {
  const SseFrame({required this.event, required this.data});

  final String event;
  final String data;
}

class SseDecoder {
  String _buffer = '';

  List<SseFrame> add(String chunk) {
    _buffer += chunk.replaceAll('\r\n', '\n');
    final frames = <SseFrame>[];

    while (true) {
      final boundary = _buffer.indexOf('\n\n');
      if (boundary < 0) {
        break;
      }

      final block = _buffer.substring(0, boundary);
      _buffer = _buffer.substring(boundary + 2);
      final frame = _parseBlock(block);
      if (frame != null) {
        frames.add(frame);
      }
    }

    return frames;
  }

  SseFrame? _parseBlock(String block) {
    String event = 'message';
    final dataLines = <String>[];
    for (final line in const LineSplitter().convert(block)) {
      if (line.startsWith(':')) {
        continue;
      }
      if (line.startsWith('event:')) {
        event = line.substring(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.add(line.substring(5).trimLeft());
      }
    }
    if (dataLines.isEmpty) {
      return null;
    }
    return SseFrame(event: event, data: dataLines.join('\n'));
  }
}
