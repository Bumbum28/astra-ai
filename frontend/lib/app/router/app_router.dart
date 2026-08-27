import 'package:astra_ai/app/router/route_paths.dart';
import 'package:astra_ai/app/router/router_refresh_notifier.dart';
import 'package:astra_ai/features/auth/application/auth_controller.dart';
import 'package:astra_ai/features/auth/presentation/pages/login_page.dart';
import 'package:astra_ai/features/auth/presentation/pages/register_page.dart';
import 'package:astra_ai/features/auth/presentation/pages/splash_page.dart';
import 'package:astra_ai/features/chat/presentation/pages/chat_page.dart';
import 'package:astra_ai/features/home/presentation/home_page.dart';
import 'package:astra_ai/features/knowledge/presentation/knowledge_page.dart';
import 'package:astra_ai/features/profile/presentation/profile_page.dart';
import 'package:astra_ai/features/roleplay/presentation/roleplay_context_page.dart';
import 'package:astra_ai/features/settings/presentation/settings_page.dart';
import 'package:astra_ai/shared/layout/app_shell.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final refreshNotifier = RouterRefreshNotifier(ref);
  ref.onDispose(refreshNotifier.dispose);

  return GoRouter(
    initialLocation: RoutePaths.splash,
    refreshListenable: refreshNotifier,
    redirect: (context, state) {
      final authState = ref.read(authControllerProvider);
      final location = state.matchedLocation;
      final isPublicRoute =
          location == RoutePaths.login ||
          location == RoutePaths.register ||
          location == RoutePaths.splash;

      if (authState.isLoading || authState.hasError) {
        return location == RoutePaths.splash ? null : RoutePaths.splash;
      }

      final isAuthenticated = authState.value != null;
      if (!isAuthenticated) {
        return isPublicRoute && location != RoutePaths.splash
            ? null
            : RoutePaths.login;
      }

      if (isPublicRoute) {
        return RoutePaths.home;
      }

      return null;
    },
    routes: <RouteBase>[
      GoRoute(
        path: RoutePaths.splash,
        builder: (context, state) => const SplashPage(),
      ),
      GoRoute(
        path: RoutePaths.login,
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: RoutePaths.register,
        builder: (context, state) => const RegisterPage(),
      ),
      ShellRoute(
        builder: (context, state, child) {
          return AppShell(location: state.matchedLocation, child: child);
        },
        routes: <RouteBase>[
          GoRoute(
            path: RoutePaths.home,
            builder: (context, state) => const HomePage(),
          ),
          GoRoute(
            path: RoutePaths.chats,
            builder: (context, state) => const ChatPage(),
            routes: <RouteBase>[
              GoRoute(
                path: ':conversationId',
                builder: (context, state) => ChatPage(
                  conversationId: state.pathParameters['conversationId'],
                ),
              ),
            ],
          ),
          GoRoute(
            path: RoutePaths.characters,
            builder: (context, state) => const RoleplayContextPage(),
          ),
          GoRoute(
            path: RoutePaths.knowledge,
            builder: (context, state) => const KnowledgePage(),
          ),
          GoRoute(
            path: RoutePaths.profile,
            builder: (context, state) => const ProfilePage(),
          ),
          GoRoute(
            path: RoutePaths.settings,
            builder: (context, state) => const SettingsPage(),
          ),
        ],
      ),
    ],
  );
});
