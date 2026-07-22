import 'package:astra_ai/features/chat/data/chat_providers.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ConversationListState {
  const ConversationListState({
    required this.items,
    this.nextCursor,
    this.isLoadingMore = false,
  });

  final List<Conversation> items;
  final String? nextCursor;
  final bool isLoadingMore;

  ConversationListState copyWith({
    List<Conversation>? items,
    String? nextCursor,
    bool clearNextCursor = false,
    bool? isLoadingMore,
  }) {
    return ConversationListState(
      items: items ?? this.items,
      nextCursor: clearNextCursor ? null : nextCursor ?? this.nextCursor,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    );
  }
}

class ConversationListController extends AsyncNotifier<ConversationListState> {
  @override
  Future<ConversationListState> build() async {
    final page = await ref.watch(chatRepositoryProvider).listConversations();
    return ConversationListState(
      items: page.items,
      nextCursor: page.nextCursor,
    );
  }

  Future<Conversation> createConversation() async {
    final conversation = await ref
        .read(chatRepositoryProvider)
        .createConversation();
    final current = state.value;
    if (current != null) {
      state = AsyncData(
        current.copyWith(items: <Conversation>[conversation, ...current.items]),
      );
    } else {
      ref.invalidateSelf();
    }
    return conversation;
  }

  Future<void> archiveConversation(String conversationId) async {
    await ref.read(chatRepositoryProvider).archiveConversation(conversationId);
    final current = state.value;
    if (current == null) {
      return;
    }
    state = AsyncData(
      current.copyWith(
        items: current.items
            .where((item) => item.id != conversationId)
            .toList(growable: false),
      ),
    );
  }

  Future<void> loadMore() async {
    final current = state.value;
    if (current == null ||
        current.isLoadingMore ||
        current.nextCursor == null) {
      return;
    }
    state = AsyncData(current.copyWith(isLoadingMore: true));
    try {
      final page = await ref
          .read(chatRepositoryProvider)
          .listConversations(cursor: current.nextCursor);
      state = AsyncData(
        current.copyWith(
          items: <Conversation>[...current.items, ...page.items],
          nextCursor: page.nextCursor,
          clearNextCursor: page.nextCursor == null,
          isLoadingMore: false,
        ),
      );
    } on Object catch (error, stackTrace) {
      state = AsyncError(error, stackTrace);
    }
  }

  Future<void> refreshList() async {
    state = const AsyncLoading<ConversationListState>();
    state = await AsyncValue.guard(() async {
      final page = await ref.read(chatRepositoryProvider).listConversations();
      return ConversationListState(
        items: page.items,
        nextCursor: page.nextCursor,
      );
    });
  }
}

final conversationListControllerProvider =
    AsyncNotifierProvider<ConversationListController, ConversationListState>(
      ConversationListController.new,
    );
