---
name: lwa-translator
description: Use when the user asks to create a translated version of a Markdown document, typically between English and Chinese. Trigger phrases include "translate X into Chinese/English", "make a Chinese/English version of a doc", or naming a .md file plus a target language (or no language, expecting a default). Output is a language-suffixed sibling file in the same directory, e.g. guide.zh.md or guide.en.md. Also applies when an existing .zh.md/.en.md translation is stale and must be re-generated to match its changed source.
---

# LWA Translator

## Overview

Creates a **sibling translated copy** of a document and saves it in the same directory as the source. The source file is **never modified or deleted**. The default target language flips with the source's language:

- Document written mainly in **Chinese** → translate to **English** → `<title>.en.md`.
- Document written mainly in **English** (or another non-Chinese language) → translate to **Chinese** → `<title>.zh.md`.

The user may override the target language; the output is then `<title>.<lang-code>.md`.

## When to Use

- The user asks to translate a document, or to "create an English/Chinese/Japanese/… version" of one.
- A request mentions a language-suffixed sibling file (`guide.zh.md`, `guide.en.md`, …).
- An existing translation is out of date and the user wants it re-generated from a changed source.

**When not to use:** a single string or snippet translation pasted in chat (no file target); the source is in a language that is neither English nor Chinese *and* no target is given (no default — ask first); or the user only wants a summary/review of a doc, not a translation.

## Workflow

1. **Resolve the target language.**
   - If the user named a target language, translate to it (mapping in Step 3).
   - If no target was given, use the default from the source-language detection (Step 2).
   - Recognize the language however the user names it: its English name, its endonym in its own script, or a name in some other language. Resolve it to one of the codes below.

2. **Detect the source language** from the document's prose:
   - Strip fenced code blocks (```…```), indented code, inline code spans, frontmatter, URLs, and raw HTML before counting.
   - Tally **Han (CJK) characters** vs **Latin letters** in the remaining prose.
   - Han ≥ Latin → treat as a **Chinese** document (default target English).
   - Han < Latin → treat as a **non-Chinese** document (default target Chinese).
   - If the prose is clearly in a language that is neither English nor Chinese (e.g. Japanese, French) and the user named **no** target, ask which language to translate into rather than guessing.

   | Source document is… | Default target | Output |
   |---|---|---|
   | mainly Chinese | English | `<title>.en.md` |
   | mainly English / other non-Chinese | Chinese | `<title>.zh.md` |

   Detection is about the **body prose**, not the filename or frontmatter title.

3. **Map the target to a language code and output path.**

   Use the ISO 639-1 two-letter code as the suffix; if the language has none, use its three-letter code.

   | Language | Code |
   |---|---|
   | English | `en` |
   | Chinese (Simplified) | `zh` |
   | Chinese (Traditional) | `zh-Hant` |
   | Japanese | `ja` |
   | Korean | `ko` |
   | French | `fr` |
   | German | `de` |
   | Spanish | `es` |
   | Russian | `ru` |
   | Portuguese | `pt` |

   **Output path:** keep the filename `<title>` byte-for-byte identical — **never translate, transliterate, or otherwise alter it**, no matter the script (an English source keeps an English title; a Chinese source keeps its Chinese title). Strip only the final `.md` extension, append `.<lang-code>.md`, and keep the source's directory.

   - `guide.md` (EN) → default → `guide.zh.md`
   - `guide.md` (ZH) → default → `guide.en.md`
   - `guide.md` (EN) → user wants Japanese → `guide.ja.md`
   - `my.docs.md` (EN) → `my.docs.zh.md`
   - `guide.zh.md` (ZH) → English → `guide.en.md`

   **If the source already carries a language suffix** (`guide.zh.md`, `README.en.md`, any known `<lang>.md`), strip it before appending the new one so suffixes never nest — `guide.zh.md` (ZH) translated to English becomes `guide.en.md`, not `guide.zh.en.md`. This still preserves the identical `<title>`; only the language suffix changes.

   **Collision check before writing:** if the target path already exists, do not silently overwrite. If the existing file looks like a prior/stale translation of this source (same base name + language), it's fine to replace it — that is the normal "refresh the translation" flow. If it looks like an independently authored document, stop and ask the user.

4. **Translate with fidelity.** Translate the human-readable prose only. Reproduce structure so the two files stay parallel (same headings, paragraphs, list items, table cells). Preserve verbatim — do **not** translate or alter:
   - Code blocks and inline code (`\`code\``); leave code comments as-is too.
   - Wikilinks/embeds `[[Note]]`, `![[file#^block]]`, anchors `#heading`, tags `#tag`.
   - URLs, file paths, image `src`, link destinations `[text](url)` — translate only the display text.
   - YAML frontmatter keys and structure; leave frontmatter values untouched by default (a translated doc may keep its original title/aliases).
   - Template syntax and variables: `{{var}}`, `%s`, `{field}`, `${var}`.
   - Math `$…$`/`$$…$$`, HTML tags and attributes, numbers, units, dates, product/person/org names, and acronyms.
   - Markdown syntax itself: `#` levels, list/quote/table markers, emphasis, footnote-definition IDs (keep footnote ids consistent across the doc).

   Produce a faithful, natural translation in the target language, not a word-for-word calque. Preserve terminology consistently. When translating into Chinese, follow Chinese punctuation conventions (full-width marks); into English, use standard English punctuation.

5. **Verify.** Re-read the output and compare with the source: same directory, filename `<title>` byte-identical to the source with the correct `.<lang>.md` suffix appended, all headings/paragraphs/list items/table cells present, code blocks and links byte-identical to the source, frontmatter intact, and no prose left untranslated. For very large documents, translate the whole file — do not stop early.

To translate several documents (or every `.md` in a folder), apply the same workflow per file.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Overwriting or deleting the source file | Never modify the source — always write a new sibling file |
| Wrong suffix, e.g. writing the translation back into the source name, or nesting suffixes (`guide.zh.en.md`) | Append `<lang>.md` to the base name only; strip an existing language suffix first |
| Translating or transliterating the filename `<title>` (e.g. renaming `guide.md` to a translated or transcribed title) | The title must stay byte-for-byte identical — only the language suffix changes |
| Default target guessed wrong | Flip it on the detected source language: Chinese to en, non-Chinese to zh |
| Translating code, URLs, wikilinks, or frontmatter | These are identifiers/structure — preserve them verbatim |
| Counting code or frontmatter text when detecting language | Strip code/frontmatter/URLs first, then tally Han vs Latin on prose only |
| Silent overwrite of an existing authored document | Check the target path; replace only a prior translation of this source, else ask |
| Doc in a third language (Japanese/French…) with no target given | No default exists — ask the user for the target language |
