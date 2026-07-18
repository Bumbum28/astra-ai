import 'dart:async';

enum SessionEvent { expired }

class SessionEventBus {
  final StreamController<SessionEvent> _controller =
      StreamController<SessionEvent>.broadcast();

  Stream<SessionEvent> get stream => _controller.stream;

  void emitExpired() {
    if (!_controller.isClosed) {
      _controller.add(SessionEvent.expired);
    }
  }

  Future<void> dispose() => _controller.close();
}
