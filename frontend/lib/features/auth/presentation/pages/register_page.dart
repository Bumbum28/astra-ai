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

class RegisterPage extends ConsumerStatefulWidget {
  const RegisterPage({super.key});

  @override
  ConsumerState<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends ConsumerState<RegisterPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
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
          .register(
            email: _emailController.text,
            username: _usernameController.text,
            password: _passwordController.text,
          );
    } catch (error) {
      if (!mounted) {
        return;
      }
      _showError(error, fallback: 'Không thể đăng ký. Hãy thử lại.');
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
      title: 'Tạo tài khoản Astra',
      subtitle: 'Tài khoản sẽ được đồng bộ an toàn giữa các thiết bị.',
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            TextFormField(
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              autofillHints: const <String>[AutofillHints.newUsername],
              validator: AuthValidators.email,
              decoration: const InputDecoration(
                labelText: 'Email',
                prefixIcon: Icon(Icons.alternate_email),
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _usernameController,
              textInputAction: TextInputAction.next,
              validator: AuthValidators.username,
              decoration: const InputDecoration(
                labelText: 'Tên người dùng',
                prefixIcon: Icon(Icons.person_outline),
              ),
            ),
            const SizedBox(height: 16),
            PasswordField(
              controller: _passwordController,
              label: 'Mật khẩu',
              validator: AuthValidators.password,
              textInputAction: TextInputAction.next,
              autofillHints: const <String>[AutofillHints.newPassword],
            ),
            const SizedBox(height: 16),
            PasswordField(
              controller: _confirmPasswordController,
              label: 'Xác nhận mật khẩu',
              validator: (value) => AuthValidators.confirmPassword(
                value,
                _passwordController.text,
              ),
              onFieldSubmitted: (_) => unawaited(_submit()),
              autofillHints: const <String>[AutofillHints.newPassword],
            ),
            const SizedBox(height: 24),
            AsyncActionButton(
              label: 'Tạo tài khoản',
              icon: Icons.person_add_alt_1,
              isLoading: isSubmitting,
              onPressed: () => unawaited(_submit()),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: isSubmitting
                  ? null
                  : () => context.go(RoutePaths.login),
              child: const Text('Đã có tài khoản? Đăng nhập'),
            ),
          ],
        ),
      ),
    );
  }
}
