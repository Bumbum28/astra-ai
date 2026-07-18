import 'package:astra_ai/core/config/platform_api_base_url.dart';

class AppConfig {
  const AppConfig({
    required this.apiBaseUrl,
    required this.connectTimeout,
    required this.receiveTimeout,
    required this.deviceName,
  });

  factory AppConfig.fromEnvironment() {
    const configuredBaseUrl = String.fromEnvironment('API_BASE_URL');
    final rawBaseUrl = configuredBaseUrl.isEmpty
        ? defaultApiBaseUrl()
        : configuredBaseUrl;

    return AppConfig(
      apiBaseUrl: _normalizeBaseUrl(rawBaseUrl),
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      deviceName: const String.fromEnvironment(
        'DEVICE_NAME',
        defaultValue: 'astra-flutter',
      ),
    );
  }

  final String apiBaseUrl;
  final Duration connectTimeout;
  final Duration receiveTimeout;
  final String deviceName;

  String endpoint(String relativePath) {
    final normalizedPath = relativePath.startsWith('/')
        ? relativePath.substring(1)
        : relativePath;
    return Uri.parse(apiBaseUrl).resolve(normalizedPath).toString();
  }

  static String _normalizeBaseUrl(String value) {
    final trimmed = value.trim();
    return trimmed.endsWith('/') ? trimmed : '$trimmed/';
  }
}
