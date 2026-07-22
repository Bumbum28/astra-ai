# Sprint 5 adaptive Vietnamese writing style fix

This patch removes the previous global teencode enforcement.

Behavior:

- The assistant always understands common Vietnamese teencode and abbreviations.
- A latest user message written in standard Vietnamese produces a standard, fully written Vietnamese reply.
- A latest user message containing explicit teencode or shorthand enables a moderate matching style.
- Chinese characters, Chinese sentences, pinyin, and translation sections remain forbidden.
- The language-guard fallback now uses standard Vietnamese rather than forced shorthand.
