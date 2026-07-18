import 'package:astra_ai/core/widgets/feature_placeholder.dart';
import 'package:flutter/material.dart';

class ChatPlaceholderPage extends StatelessWidget {
  const ChatPlaceholderPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const FeaturePlaceholder(
      icon: Icons.chat_bubble_outline,
      title: 'AI Chat',
      description:
          'Conversation list, message timeline và streaming response '
          'sẽ được triển khai trên nền authentication hiện tại.',
      sprint: 'Dự kiến Sprint 4',
    );
  }
}
