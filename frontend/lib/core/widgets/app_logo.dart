import 'package:flutter/material.dart';

class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.compact = false});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: <Color>[colorScheme.primary, colorScheme.tertiary],
            ),
            borderRadius: BorderRadius.circular(14),
          ),
          child: const SizedBox(
            width: 42,
            height: 42,
            child: Icon(Icons.auto_awesome, color: Colors.white),
          ),
        ),
        if (!compact) ...<Widget>[
          const SizedBox(width: 12),
          Text(
            'Astra AI',
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
          ),
        ],
      ],
    );
  }
}
