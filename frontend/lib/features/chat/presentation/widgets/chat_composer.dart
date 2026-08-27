import 'package:astra_ai/features/chat/domain/entities/chat_execution_mode.dart';
import 'package:flutter/material.dart';

class ChatComposer extends StatefulWidget {
  const ChatComposer({
    required this.isSending,
    required this.executionMode,
    required this.onExecutionModeChanged,
    required this.onSend,
    super.key,
  });

  final bool isSending;
  final ChatExecutionMode executionMode;
  final ValueChanged<ChatExecutionMode> onExecutionModeChanged;
  final ValueChanged<String> onSend;

  @override
  State<ChatComposer> createState() => _ChatComposerState();
}

class _ChatComposerState extends State<ChatComposer> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _submit() {
    final value = _controller.text.trim();
    if (value.isEmpty || widget.isSending) {
      return;
    }
    _controller.clear();
    widget.onSend(value);
    _focusNode.requestFocus();
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 900),
          child: Material(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(22),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 6, 8, 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: <Widget>[
                  Tooltip(
                    message: widget.executionMode == ChatExecutionMode.agent
                        ? 'Agent có thể tự gọi công cụ tìm Knowledge và lịch sử chat.'
                        : 'Bật Agent để Astra có thể tự gọi công cụ khi cần.',
                    child: FilterChip(
                      selected: widget.executionMode == ChatExecutionMode.agent,
                      onSelected: widget.isSending
                          ? null
                          : (selected) => widget.onExecutionModeChanged(
                              selected
                                  ? ChatExecutionMode.agent
                                  : ChatExecutionMode.direct,
                            ),
                      avatar: const Icon(Icons.hub_outlined, size: 18),
                      label: const Text('Agent'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      focusNode: _focusNode,
                      minLines: 1,
                      maxLines: 6,
                      textCapitalization: TextCapitalization.sentences,
                      decoration: InputDecoration(
                        hintText:
                            widget.executionMode == ChatExecutionMode.agent
                            ? 'Giao nhiệm vụ cho Agent…'
                            : 'Nhập tin nhắn…',
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                  IconButton.filled(
                    tooltip: 'Gửi',
                    onPressed: widget.isSending ? null : _submit,
                    icon: widget.isSending
                        ? const SizedBox.square(
                            dimension: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.arrow_upward),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
