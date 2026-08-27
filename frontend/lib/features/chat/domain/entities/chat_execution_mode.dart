enum ChatExecutionMode { direct, agent }

extension ChatExecutionModeX on ChatExecutionMode {
  String get apiValue => name;

  String get label => switch (this) {
    ChatExecutionMode.direct => 'Chat',
    ChatExecutionMode.agent => 'Agent',
  };
}
