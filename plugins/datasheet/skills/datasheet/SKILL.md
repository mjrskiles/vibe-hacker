---
name: datasheet
description: Consult the project's local corpus of datasheets, reference manuals, errata sheets, and schematics for exact register, timing, electrical, pinout, and protocol facts, with page-level citations. Use whenever a claim depends on what a vendor document actually says — driver code, hardware bringup, schematic work, reconciling research against the manual.
allowed-tools: Read, Grep, Glob, Bash
---

# Datasheet Skill

Answer hardware questions from the documents. Cite facts with a document, section, and page. If the corpus can't
answer, say so and name the document that would.

## The corpus

- **Root:** configured in `.claude/vibe-hacker.json` under `datasheet.root`;
  default `docs/manuals/`. Referred to below as `<root>`.
- **Index:** `<root>/index.json` (tracked in git). Maps each document to its
  part numbers, type, revision, page count, text-layer quality, and a table of
  contents (section → page). Start here.
- **PDFs:** `<root>/*.pdf`. The index may list documents that are not on this machine. Entries under
  `wanted` are known-missing; say so rather than substituting.
- **Tools:** poppler (`pdfinfo`, `pdftotext`, `pdftoppm`). If it isn't
  installed, the `Read` tool still reads PDFs by page range; you lose keyword
  search across a document.

## Procedure

1. **Find the document** in `index.json` by part number. Check `type` and
   `revision`. If it isn't there, stop and report "not in corpus".
2. **Locate the section.** Use the index `toc` if populated. Otherwise search
   the text layer:
   ```bash
   pdftotext -layout <root>/<file>.pdf - | grep -n -i "<term>"
   ```
   Line numbers are not page numbers. To map a hit to a page, extract a page
   range and confirm:
   ```bash
   pdftotext -layout -f <first> -l <last> <root>/<file>.pdf -
   ```
   Printed page numbers (in the footer) and PDF page indices usually differ —
   cite the **printed** page and section number, since that is what humans
   and other documents reference. The index's `page_offset` records the
   difference once someone has measured it.
3. **Read the actual page.** A grep hit is a pointer, not evidence. Read the
   surrounding text with the `Read` tool (`pages` parameter, ≤20 pages per
   call) or `pdftotext -f/-l`. Tables need `-layout`; if a table comes out
   garbled, render it and read the image:
   ```bash
   pdftoppm -f <page> -l <page> -r 110 -png <root>/<file>.pdf /tmp/ds
   ```
   then `Read /tmp/ds-<page>.png`.
4. **Check the errata sheet.** For any peripheral or core-feature question,
   search the part's errata sheet before answering. An erratum that applies is
   part of the answer, including which silicon revisions it affects.
5. **Cite.** Format: `<DOC> <Rev> §<section>, p. <printed page>` — for
   example `RM0433 Rev 8 §51.5.8, p. 2048`. One citation per fact, inline.

## Rules

- **Never fill a gap from memory.** If the corpus does not state it, write
  "not stated in <document>" or "not in corpus — needs <document>". A wrong
  register value costs a debugging afternoon; "unknown" costs a download.
- **Quote, don't paraphrase, for anything numeric or normative.** Bit
  positions, reset values, limits, timing, and "must/shall" language are
  quoted verbatim (short). Interpretation goes after the quote, labelled as
  yours.
- **Revision is part of the fact.** Record the document revision you read.
  When an answer depends on silicon revision (errata, some reset values),
  say which revisions and note that the hardware's revision must be checked.
- **Distinguish stated from inferred.** "The manual says X" and "X follows
  from the manual's description of Y" are different sentences. Use both when
  needed; never blur them.
- **Read-only.** Don't edit `index.json` or the PDFs from this skill unless
  the user asked you to add a document. Never edit source code from this
  skill — report what the document says and where the code disagrees.

## When comparing against code

The common request is "does our driver match the manual?" Report as pairs:

```
uart.hpp:292 — comment says "8-byte hardware FIFO"
RM0433 Rev 8 §51.4.x, p. NNNN — "<quoted FIFO depth statement>"
→ agrees / disagrees / manual does not state
```

Cite the code by `file:line` and the document by the citation format above.
Do not fix the code; the user decides.

## When to delegate to the `datasheet-reader` agent

Use the agent instead of reading in-context when:

- the question spans more than ~10 pages or several sections;
- it crosses documents (reference manual + errata + datasheet for one
  peripheral);
- you need a table of contents built for a newly added document;
- you are auditing a whole driver or schematic sheet against the manuals.

Give the agent the exact question, the part numbers, and the code or
schematic files it should compare against. It returns cited findings and an
explicit "not found" list.

## Adding a document

1. Drop the PDF in `<root>/`. Prefer the vendor document number as the
   filename (`rm0433.pdf`, `es0392.pdf`); keep vendor filenames for board
   documents.
2. `pdfinfo <file>` for title and page count; `pdftotext -f 1 -l 3` to find
   the document number and revision on the cover.
3. Add an entry to `index.json` (schema below). Set `text_layer` honestly —
   extract a table page and look.
4. Ask the `datasheet-reader` agent to generate the `toc` (section → printed
   page) so the next lookup jumps instead of searching.
5. If the document was listed under `wanted`, move it to `documents`.

### index.json schema

```jsonc
{
  "documents": [
    {
      "id": "rm0433",                 // short handle used in citations
      "file": "rm0433.pdf",           // filename under <root>
      "type": "reference-manual",     // datasheet | reference-manual | errata |
                                      // programming-manual | app-note |
                                      // board-datasheet | schematic | user-manual
      "vendor": "…",
      "title": "…",
      "parts": ["STM32H750xB"],       // part numbers covered
      "revision": "Rev 8",            // from the cover; "unknown" until checked
      "pages": 3353,                  // PDF page count
      "page_offset": 0,               // printed page = PDF index − page_offset
      "text_layer": "good",           // good | partial | poor
      "toc": [ { "section": "51.5.8", "title": "…", "page": 2048 } ],
      "notes": "what this answers; quirks"
    }
  ],
  "wanted": [
    { "id": "es0392", "title": "…", "why": "…", "source": "where to get it" }
  ]
}
```

## Output format

```
**Q:** <the question, restated precisely>

**A:** <the answer in one or two sentences>

**Evidence**
- `<DOC> <Rev> §<sec>, p. <page>` — "<verbatim quote>"
- ...

**Errata touching this:** <items, revisions affected> | none found in <errata doc>

**Not stated / not in corpus:** <what remains unverified, and where it would be>
```
