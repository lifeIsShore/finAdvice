# Project Stability & Encoding Rules

## CRITICAL: No Emojis or Non-ASCII Characters
To ensure cross-platform compatibility and prevent fatal 'charmap' encoding errors on Windows systems, the following rules **MUST** be followed by all AI agents and contributors:

1.  **NO EMOJIS in Code or Logs**: Do not use Unicode emojis (e.g., ✅, ❌, 📈) in Python `print()` statements, logging, or string literals.
2.  **ASCII-Safe Feedback Only**: Use plain text markers for status feedback:
    *   Instead of ✅ use `[OK]` or `SUCCESS`
    *   Instead of ❌ use `[ERROR]` or `FAILED`
    *   Instead of ⚠️ use `[WARNING]`
    *   Instead of 📈/📉 use `+++` / `---` or `UP` / `DOWN`
3.  **Standardized UI Icons**: 
    *   In HTML/JS, use **Font Awesome** classes (e.g., `<i class="fas fa-check"></i>`) instead of raw Unicode symbols.
    *   Dynamic JS sentiment indicators should use CSS classes or plain text symbols (like `=` or `+`) if they need to be injected as text.
4.  **Windows Terminal Tolerance**: Many users run this application in default Windows CMD or PowerShell environments which default to `cp1252` encoding. Any character outside the standard ASCII/Extended ASCII range can cause the entire ML pipeline to crash during consensus generation.

## Enforcement Measurement
*   Any future modification that introduces a character outside the `U+0000` to `U+007F` range (for console output) should be automatically rejected or flagged.
*   Prioritize `utf-8` explicitly when opening files: `open(file, 'r', encoding='utf-8')`.

**DO NOT DEVIATE FROM THESE RULES. THEY ARE ESSENTIAL FOR ENGINE STABILITY.**
