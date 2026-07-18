# Sprint 3 dynamic Flutter Web port CORS patch

Flutter Web uses a random localhost port when `--web-port` is not supplied.
The previous CORS allow-list only included port 8080, so a page such as
`http://localhost:62652` failed its preflight request with HTTP 400.

This patch adds a development-only origin regex that accepts localhost and
127.0.0.1 on any port while continuing to reject non-local origins.

Production should override `CORS_ORIGIN_REGEX` with an empty value and use an
explicit `CORS_ORIGINS` allow-list.
