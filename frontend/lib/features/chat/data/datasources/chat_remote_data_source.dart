import 'dart:convert';

import 'package:astra_ai/core/config/app_config.dart';
import 'package:astra_ai/core/errors/app_exception.dart';
import 'package:astra_ai/core/network/api_envelope.dart';
import 'package:astra_ai/core/network/dio_exception_mapper.dart';
import 'package:astra_ai/core/network/sse_decoder.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_message.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_page_data.dart';
import 'package:astra_ai/features/chat/domain/entities/chat_stream_event.dart';
import 'package:astra_ai/features/chat/domain/entities/conversation.dart';
import 'package:dio/dio.dart';

class ChatRemoteDataSource {
  const ChatRemoteDataSource(this._dio, this._config);

  final Dio _dio;
  final AppConfig _config;

  Future<ConversationPageData> listConversations({String? cursor}) async {
    try {
      final response = await _dio.get<Object?>(
        _config.endpoint('conversations'),
        queryParameters: <String, Object?>{'limit': 30, 'cursor': ?cursor},
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      return ConversationPageData(
        items: _readItems(data, Conversation.fromJson),
        nextCursor: data['next_cursor'] as String?,
      );
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(error.message);
    } on TypeError catch (error) {
      throw _invalidResponse(error.toString());
    }
  }

  Future<Conversation> createConversation({
    String? title,
    String? systemPrompt,
    String? characterId,
    String? personaId,
  }) async {
    try {
      final response = await _dio.post<Object?>(
        _config.endpoint('conversations'),
        data: <String, Object?>{
          'title': ?title,
          'system_prompt': ?systemPrompt,
          'character_id': ?characterId,
          'persona_id': ?personaId,
        },
      );
      return Conversation.fromJson(ApiEnvelope.requireDataMap(response.data));
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(error.message);
    } on TypeError catch (error) {
      throw _invalidResponse(error.toString());
    }
  }

  Future<void> archiveConversation(String conversationId) async {
    try {
      await _dio.delete<Object?>(
        _config.endpoint('conversations/$conversationId'),
      );
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    }
  }

  Future<MessagePageData> listMessages(
    String conversationId, {
    String? cursor,
  }) async {
    try {
      final response = await _dio.get<Object?>(
        _config.endpoint('conversations/$conversationId/messages'),
        queryParameters: <String, Object?>{'limit': 50, 'cursor': ?cursor},
      );
      final data = ApiEnvelope.requireDataMap(response.data);
      return MessagePageData(
        items: _readItems(data, ChatMessage.fromJson),
        nextCursor: data['next_cursor'] as String?,
      );
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(error.message);
    } on TypeError catch (error) {
      throw _invalidResponse(error.toString());
    }
  }

  Stream<ChatStreamEvent> streamMessage({
    required String conversationId,
    required String content,
    required String clientMessageId,
  }) async* {
    try {
      final response = await _dio.post<ResponseBody>(
        _config.endpoint('conversations/$conversationId/messages/stream'),
        data: <String, Object?>{
          'content': content,
          'client_message_id': clientMessageId,
        },
        options: Options(
          responseType: ResponseType.stream,
          headers: const <String, Object?>{'Accept': 'text/event-stream'},
        ),
      );
      final body = response.data;
      if (body == null) {
        throw const FormatException('Missing streaming response body.');
      }

      final decoder = SseDecoder();
      await for (final chunk in utf8.decoder.bind(body.stream)) {
        for (final frame in decoder.add(chunk)) {
          yield _mapFrame(frame);
        }
      }
    } on DioException catch (error) {
      throw DioExceptionMapper.map(error);
    } on FormatException catch (error) {
      throw _invalidResponse(error.message);
    } on TypeError catch (error) {
      throw _invalidResponse(error.toString());
    }
  }

  ChatStreamEvent _mapFrame(SseFrame frame) {
    final decoded = jsonDecode(frame.data);
    if (decoded is! Map) {
      throw const FormatException(
        'Streaming event must contain a JSON object.',
      );
    }
    final data = Map<String, Object?>.from(decoded);
    return switch (frame.event) {
      'message.created' => ChatStreamStartedEvent(
        userMessage: ChatMessage.fromJson(_map(data['user_message'])),
        assistantMessage: ChatMessage.fromJson(_map(data['assistant_message'])),
        reused: data['reused'] == true,
      ),
      'message.delta' => ChatStreamDeltaEvent(
        messageId: data['message_id']! as String,
        delta: data['delta']! as String,
      ),
      'message.completed' => ChatStreamCompletedEvent(
        ChatMessage.fromJson(_map(data['message'])),
      ),
      'error' => ChatStreamFailedEvent(
        messageId: data['message_id']! as String,
        error: AppException(
          code: (data['code'] as String?) ?? 'CHAT_STREAM_FAILED',
          message:
              (data['message'] as String?) ?? 'Phản hồi AI đã bị gián đoạn.',
          details: data['details'],
        ),
      ),
      _ => throw FormatException('Unknown SSE event: ${frame.event}'),
    };
  }

  List<T> _readItems<T>(
    Map<String, Object?> data,
    T Function(Map<String, Object?>) parser,
  ) {
    final rawItems = data['items'];
    if (rawItems is! List) {
      throw const FormatException('Missing paginated items.');
    }
    return rawItems.map((item) => parser(_map(item))).toList(growable: false);
  }

  Map<String, Object?> _map(Object? value) {
    if (value is! Map) {
      throw const FormatException('Expected a JSON object.');
    }
    return Map<String, Object?>.from(value);
  }

  AppException _invalidResponse(Object details) {
    return AppException(
      code: 'INVALID_SERVER_RESPONSE',
      message: 'Dữ liệu Chat từ máy chủ không hợp lệ.',
      details: details,
    );
  }
}
