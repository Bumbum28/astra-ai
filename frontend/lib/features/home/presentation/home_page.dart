import 'package:astra_ai/app/router/route_paths.dart';
import 'package:astra_ai/features/auth/application/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).value?.user;
    final colorScheme = Theme.of(context).colorScheme;

    return SafeArea(
      child: CustomScrollView(
        slivers: <Widget>[
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(24, 32, 24, 16),
            sliver: SliverToBoxAdapter(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1200),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'Xin chào, ${user?.username ?? 'Astra User'}',
                      style: Theme.of(context).textTheme.headlineMedium
                          ?.copyWith(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Nền tảng đã sẵn sàng cho các tính năng Chat, '
                      'Character và Memory ở những Sprint tiếp theo.',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(24, 12, 24, 36),
            sliver: SliverLayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.crossAxisExtent;
                final crossAxisCount = width >= 1050
                    ? 3
                    : width >= 650
                    ? 2
                    : 1;

                return SliverGrid(
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: crossAxisCount,
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                    childAspectRatio: crossAxisCount == 1 ? 2.1 : 1.45,
                  ),
                  delegate: SliverChildListDelegate(<Widget>[
                    _FeatureCard(
                      icon: Icons.chat_bubble_outline,
                      title: 'AI Chat',
                      description:
                          'Streaming conversation sẽ được triển khai '
                          'trong Sprint 4.',
                      actionLabel: 'Mở khu vực Chat',
                      onTap: () => context.go(RoutePaths.chats),
                    ),
                    _FeatureCard(
                      icon: Icons.groups_outlined,
                      title: 'Character System',
                      description:
                          'Quản lý nhân vật và persona được chuẩn bị '
                          'cho Sprint 5.',
                      actionLabel: 'Xem khu vực nhân vật',
                      onTap: () => context.go(RoutePaths.characters),
                    ),
                    _FeatureCard(
                      icon: Icons.security_outlined,
                      title: 'Phiên đăng nhập an toàn',
                      description:
                          'Access token, refresh rotation và secure storage '
                          'đang hoạt động.',
                      actionLabel: 'Xem hồ sơ',
                      onTap: () => context.go(RoutePaths.profile),
                    ),
                  ]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  const _FeatureCard({
    required this.icon,
    required this.title,
    required this.description,
    required this.actionLabel,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String description;
  final String actionLabel;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(24),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              DecoratedBox(
                decoration: BoxDecoration(
                  color: colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Icon(icon, color: colorScheme.onPrimaryContainer),
                ),
              ),
              const Spacer(),
              Text(
                title,
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              Text(
                description,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: colorScheme.onSurfaceVariant),
              ),
              const SizedBox(height: 14),
              Text(
                actionLabel,
                style: TextStyle(
                  color: colorScheme.primary,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
