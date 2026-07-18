import 'package:astra_ai/core/widgets/feature_placeholder.dart';
import 'package:flutter/material.dart';

class CharactersPlaceholderPage extends StatelessWidget {
  const CharactersPlaceholderPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const FeaturePlaceholder(
      icon: Icons.groups_outlined,
      title: 'Character System',
      description:
          'Character, Persona, Prompt composition và Memory integration '
          'sẽ được xây trên module riêng.',
      sprint: 'Dự kiến Sprint 5',
    );
  }
}
