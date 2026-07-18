import 'dart:async';

import 'package:astra_ai/core/widgets/app_logo.dart';
import 'package:astra_ai/features/auth/application/auth_controller.dart';
import 'package:astra_ai/shared/layout/app_destination.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class AppShell extends ConsumerWidget {
  const AppShell({required this.location, required this.child, super.key});

  final String location;
  final Widget child;

  int get _selectedIndex {
    final index = appDestinations.indexWhere(
      (destination) => location.startsWith(destination.route),
    );
    return index < 0 ? 0 : index;
  }

  void _navigate(BuildContext context, int index) {
    context.go(appDestinations[index].route);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).value?.user;

    return LayoutBuilder(
      builder: (context, constraints) {
        final useDesktopNavigation = constraints.maxWidth >= 920;

        if (useDesktopNavigation) {
          final expanded = constraints.maxWidth >= 1180;

          return Scaffold(
            body: Row(
              children: <Widget>[
                SafeArea(
                  right: false,
                  child: _DesktopSidebar(
                    expanded: expanded,
                    selectedIndex: _selectedIndex,
                    username: user?.username ?? 'Astra User',
                    onDestinationSelected: (index) => _navigate(context, index),
                  ),
                ),
                const VerticalDivider(width: 1),
                Expanded(child: child),
              ],
            ),
          );
        }

        return Scaffold(
          appBar: AppBar(title: const AppLogo(), centerTitle: false),
          drawer: NavigationDrawer(
            selectedIndex: _selectedIndex,
            onDestinationSelected: (index) {
              Navigator.of(context).pop();
              _navigate(context, index);
            },
            children: <Widget>[
              Padding(
                padding: const EdgeInsets.fromLTRB(28, 24, 16, 12),
                child: Text(
                  user?.email ?? '',
                  style: Theme.of(context).textTheme.labelLarge,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              ...appDestinations.map(
                (destination) => NavigationDrawerDestination(
                  icon: Icon(destination.icon),
                  selectedIcon: Icon(destination.selectedIcon),
                  label: Text(destination.label),
                ),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.logout),
                title: const Text('Đăng xuất'),
                onTap: () {
                  Navigator.of(context).pop();
                  unawaited(ref.read(authControllerProvider.notifier).logout());
                },
              ),
            ],
          ),
          body: child,
        );
      },
    );
  }
}

class _DesktopSidebar extends ConsumerWidget {
  const _DesktopSidebar({
    required this.expanded,
    required this.selectedIndex,
    required this.username,
    required this.onDestinationSelected,
  });

  final bool expanded;
  final int selectedIndex;
  final String username;
  final ValueChanged<int> onDestinationSelected;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final width = expanded ? 280.0 : 88.0;

    return SizedBox(
      width: width,
      child: Material(
        color: Theme.of(context).colorScheme.surface,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            Padding(
              padding: EdgeInsets.fromLTRB(
                expanded ? 20 : 14,
                16,
                expanded ? 20 : 14,
                24,
              ),
              child: Align(
                alignment: expanded ? Alignment.centerLeft : Alignment.center,
                child: AppLogo(compact: !expanded),
              ),
            ),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                itemCount: appDestinations.length,
                separatorBuilder: (context, index) => const SizedBox(height: 6),
                itemBuilder: (context, index) {
                  final destination = appDestinations[index];
                  return _DesktopDestinationTile(
                    expanded: expanded,
                    selected: selectedIndex == index,
                    destination: destination,
                    onTap: () => onDestinationSelected(index),
                  );
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: _AccountMenu(
                username: username,
                expanded: expanded,
                onLogout: () {
                  unawaited(ref.read(authControllerProvider.notifier).logout());
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DesktopDestinationTile extends StatelessWidget {
  const _DesktopDestinationTile({
    required this.expanded,
    required this.selected,
    required this.destination,
    required this.onTap,
  });

  final bool expanded;
  final bool selected;
  final AppDestination destination;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final icon = selected ? destination.selectedIcon : destination.icon;
    final foregroundColor = selected
        ? colorScheme.onSecondaryContainer
        : colorScheme.onSurfaceVariant;

    if (!expanded) {
      return Tooltip(
        message: destination.label,
        child: Material(
          color: selected ? colorScheme.secondaryContainer : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
          child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: onTap,
            child: SizedBox(
              width: 64,
              height: 56,
              child: Icon(icon, color: foregroundColor),
            ),
          ),
        ),
      );
    }

    return Material(
      color: selected ? colorScheme.secondaryContainer : Colors.transparent,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: <Widget>[
              Icon(icon, color: foregroundColor),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  destination.label,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: foregroundColor,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AccountMenu extends StatelessWidget {
  const _AccountMenu({
    required this.username,
    required this.expanded,
    required this.onLogout,
  });

  final String username;
  final bool expanded;
  final VoidCallback onLogout;

  @override
  Widget build(BuildContext context) {
    if (!expanded) {
      return Tooltip(
        message: 'Đăng xuất',
        child: IconButton(onPressed: onLogout, icon: const Icon(Icons.logout)),
      );
    }

    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onLogout,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          child: Row(
            children: <Widget>[
              CircleAvatar(
                child: Text(
                  username.isEmpty
                      ? 'A'
                      : username.characters.first.toUpperCase(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      username,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      'Đăng xuất',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.logout, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}
