import 'package:astra_ai/app/router/route_paths.dart';
import 'package:flutter/material.dart';

class AppDestination {
  const AppDestination({
    required this.label,
    required this.route,
    required this.icon,
    required this.selectedIcon,
  });

  final String label;
  final String route;
  final IconData icon;
  final IconData selectedIcon;
}

const appDestinations = <AppDestination>[
  AppDestination(
    label: 'Trang chủ',
    route: RoutePaths.home,
    icon: Icons.home_outlined,
    selectedIcon: Icons.home,
  ),
  AppDestination(
    label: 'Trò chuyện',
    route: RoutePaths.chats,
    icon: Icons.chat_bubble_outline,
    selectedIcon: Icons.chat_bubble,
  ),
  AppDestination(
    label: 'Nhân vật',
    route: RoutePaths.characters,
    icon: Icons.groups_outlined,
    selectedIcon: Icons.groups,
  ),
  AppDestination(
    label: 'Kiến thức',
    route: RoutePaths.knowledge,
    icon: Icons.library_books_outlined,
    selectedIcon: Icons.library_books,
  ),
  AppDestination(
    label: 'Hồ sơ',
    route: RoutePaths.profile,
    icon: Icons.person_outline,
    selectedIcon: Icons.person,
  ),
  AppDestination(
    label: 'Cài đặt',
    route: RoutePaths.settings,
    icon: Icons.settings_outlined,
    selectedIcon: Icons.settings,
  ),
];
