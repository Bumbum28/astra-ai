import 'dart:async';

import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/widgets/app_logo.dart';
import 'package:astra_ai/features/auth/application/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SplashPage extends ConsumerWidget {
  const SplashPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);

    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                const AppLogo(),
                const SizedBox(height: 28),
                if (authState.hasError) ...<Widget>[
                  Icon(
                    Icons.cloud_off_outlined,
                    size: 48,
                    color: Theme.of(context).colorScheme.error,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _messageFor(authState.error),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 20),
                  FilledButton.icon(
                    onPressed: () {
                      unawaited(
                        ref
                            .read(authControllerProvider.notifier)
                            .retryRestore(),
                      );
                    },
                    icon: const Icon(Icons.refresh),
                    label: const Text('Thử kết nối lại'),
                  ),
                ] else
                  const CircularProgressIndicator(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _messageFor(Object? error) {
    if (error is AppException) {
      return error.message;
    }
    return 'Không thể kết nối đến Astra AI Server.';
  }
}
