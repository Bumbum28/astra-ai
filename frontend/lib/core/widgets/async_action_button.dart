import 'package:flutter/material.dart';

class AsyncActionButton extends StatelessWidget {
  const AsyncActionButton({
    required this.label,
    required this.onPressed,
    required this.isLoading,
    super.key,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return FilledButton(
      onPressed: isLoading ? null : onPressed,
      style: FilledButton.styleFrom(
        minimumSize: const Size.fromHeight(52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 180),
        child: isLoading
            ? const SizedBox.square(
                key: ValueKey<String>('loading'),
                dimension: 22,
                child: CircularProgressIndicator(strokeWidth: 2.4),
              )
            : Row(
                key: const ValueKey<String>('label'),
                mainAxisAlignment: MainAxisAlignment.center,
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  if (icon != null) ...<Widget>[
                    Icon(icon),
                    const SizedBox(width: 8),
                  ],
                  Text(label),
                ],
              ),
      ),
    );
  }
}
