import 'dart:async';

import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/features/auth/application/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    final isSubmitting = ref.watch(authActionInProgressProvider);
    final user = authState.value?.user;

    if (user == null) {
      return const Center(child: CircularProgressIndicator());
    }

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: <Widget>[
          Text(
            'Hồ sơ',
            style: Theme.of(
              context,
            ).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 20),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                children: <Widget>[
                  CircleAvatar(
                    radius: 34,
                    child: Text(
                      user.username.isEmpty
                          ? 'A'
                          : user.username.characters.first.toUpperCase(),
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                  ),
                  const SizedBox(width: 20),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          user.username,
                          style: Theme.of(context).textTheme.titleLarge
                              ?.copyWith(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 4),
                        Text(user.email),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: <Widget>[
                            Chip(
                              avatar: const Icon(Icons.check_circle, size: 18),
                              label: Text(
                                user.isActive
                                    ? 'Đang hoạt động'
                                    : 'Đã vô hiệu hóa',
                              ),
                            ),
                            Chip(
                              avatar: const Icon(Icons.verified, size: 18),
                              label: Text(
                                user.isVerified
                                    ? 'Đã xác minh'
                                    : 'Chưa xác minh',
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Column(
              children: <Widget>[
                ListTile(
                  enabled: !isSubmitting,
                  leading: const Icon(Icons.devices),
                  title: const Text('Đăng xuất khỏi thiết bị này'),
                  subtitle: const Text('Thu hồi refresh session hiện tại.'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    unawaited(
                      ref.read(authControllerProvider.notifier).logout(),
                    );
                  },
                ),
                const Divider(height: 1),
                ListTile(
                  enabled: !isSubmitting,
                  leading: Icon(
                    Icons.phonelink_erase,
                    color: Theme.of(context).colorScheme.error,
                  ),
                  title: const Text('Đăng xuất khỏi tất cả thiết bị'),
                  subtitle: const Text(
                    'Thu hồi toàn bộ phiên đăng nhập đang hoạt động.',
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => unawaited(_confirmLogoutAll(context, ref)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmLogoutAll(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Đăng xuất tất cả thiết bị?'),
          content: const Text(
            'Tất cả refresh session của tài khoản sẽ bị thu hồi.',
          ),
          actions: <Widget>[
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: const Text('Hủy'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(dialogContext).pop(true),
              child: const Text('Đăng xuất tất cả'),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !context.mounted) {
      return;
    }

    try {
      final revokedCount = await ref
          .read(authControllerProvider.notifier)
          .logoutAllDevices();
      if (!context.mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Đã thu hồi $revokedCount phiên đăng nhập.')),
      );
    } catch (error) {
      if (!context.mounted) {
        return;
      }
      final message = error is AppException
          ? error.message
          : 'Không thể đăng xuất khỏi tất cả thiết bị.';
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
    }
  }
}
