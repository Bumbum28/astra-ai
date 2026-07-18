import 'package:astra_ai/core/config/platform_api_base_url_stub.dart'
    if (dart.library.io) 'package:astra_ai/core/config/platform_api_base_url_io.dart'
    as implementation;

String defaultApiBaseUrl() => implementation.defaultApiBaseUrl();
