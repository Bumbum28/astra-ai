class SseFrame {
  const SseFrame({required this.event, required this.data});

  final String event;
  final String data;
}

class SseDecoder {
  final StringBuffer _lineBuffer = StringBuffer();
  final List<String> _dataLines = <String>[];

  String _event = 'message';
  bool _pendingCarriageReturn = false;

  /// Adds a transport chunk and eagerly returns every complete SSE frame.
  ///
  /// This method is intentionally not a `sync*` generator. A lazy generator
  /// would not consume the chunk until its returned iterable is iterated,
  /// which can silently drop earlier chunks when callers ignore an empty
  /// intermediate result.
  List<SseFrame> add(String chunk) {
    final frames = <SseFrame>[];

    for (final codeUnit in chunk.codeUnits) {
      final character = String.fromCharCode(codeUnit);

      if (_pendingCarriageReturn) {
        _pendingCarriageReturn = false;
        _finishLine(frames);

        // CRLF is one line ending. The LF has already been consumed by the
        // preceding CR, so do not process it a second time.
        if (character == '\n') {
          continue;
        }
      }

      if (character == '\r') {
        _pendingCarriageReturn = true;
      } else if (character == '\n') {
        _finishLine(frames);
      } else {
        _lineBuffer.write(character);
      }
    }

    return frames;
  }

  void _finishLine(List<SseFrame> frames) {
    final line = _lineBuffer.toString();
    _lineBuffer.clear();

    if (line.isEmpty) {
      if (_dataLines.isNotEmpty) {
        frames.add(SseFrame(event: _event, data: _dataLines.join('\n')));
      }
      _event = 'message';
      _dataLines.clear();
      return;
    }

    if (line.startsWith(':')) {
      return;
    }

    final separator = line.indexOf(':');
    final field = separator < 0 ? line : line.substring(0, separator);
    var value = separator < 0 ? '' : line.substring(separator + 1);
    if (value.startsWith(' ')) {
      value = value.substring(1);
    }

    switch (field) {
      case 'event':
        _event = value.isEmpty ? 'message' : value;
      case 'data':
        _dataLines.add(value);
    }
  }
}
