import 'package:astra_ai/features/auth/application/auth_controller.dart';
import 'package:astra_ai/features/auth/domain/entities/auth_session.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class RouterRefreshNotifier extends ChangeNotifier {
  RouterRefreshNotifier(Ref ref) {
    _subscription = ref.listen<AsyncValue<AuthSession?>>(
      authControllerProvider,
      (previous, next) {
        notifyListeners();
      },
    );
  }

  late final ProviderSubscription<AsyncValue<AuthSession?>> _subscription;

  @override
  void dispose() {
    _subscription.close();
    super.dispose();
  }
}
