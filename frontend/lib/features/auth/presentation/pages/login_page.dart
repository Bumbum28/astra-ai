import 'dart:async';

import 'package:astra_ai/app/router/route_paths.dart';
import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/widgets/async_action_button.dart';
import 'package:astra_ai/features/auth/application/auth_controller.dart';
import 'package:astra_ai/features/auth/presentation/auth_validators.dart';
import 'package:astra_ai/features/auth/presentation/widgets/auth_scaffold.dart';
import 'package:astra_ai/features/auth/presentation/widgets/password_field.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    FocusScope.of(context).unfocus();
    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    try {
      await ref
          .read(authControllerProvider.notifier)
          .login(
            email: _emailController.text,
            password: _passwordController.text,
          );
    } catch (error) {
      if (!mounted) {
        return;
      }
      _showError(error, fallback: 'Không thể đăng nhập. Hãy thử lại.');
    }
  }

  void _showError(Object error, {required String fallback}) {
    final message = error is AppException ? error.message : fallback;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final isSubmitting = ref.watch(authActionInProgressProvider);

    return AuthScaffold(
      title: 'Chào mừng trở lại',
      subtitle: 'Đăng nhập để tiếp tục vào Astra AI Platform.',
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            TextFormField(
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              autofillHints: const <String>[
                AutofillHints.username,
                AutofillHints.email,
              ],
              validator: AuthValidators.email,
              decoration: const InputDecoration(
                labelText: 'Email',
                prefixIcon: Icon(Icons.alternate_email),
              ),
            ),
            const SizedBox(height: 16),
            PasswordField(
              controller: _passwordController,
              label: 'Mật khẩu',
              validator: AuthValidators.password,
              onFieldSubmitted: (_) => unawaited(_submit()),
            ),
            const SizedBox(height: 24),
            AsyncActionButton(
              label: 'Đăng nhập',
              icon: Icons.login,
              isLoading: isSubmitting,
              onPressed: () => unawaited(_submit()),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: isSubmitting
                  ? null
                  : () => context.go(RoutePaths.register),
              child: const Text('Chưa có tài khoản? Đăng ký'),
            ),
          ],
        ),
      ),
    );
  }
}
