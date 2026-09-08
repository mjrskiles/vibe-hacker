---
name: datasheet
description: Consult the project's local corpus of datasheets, reference manuals, errata sheets, and schematics for exact register, timing, electrical, pinout, and protocol facts, with page-level citations. Use whenever a claim depends on what a vendor document actually says — driver code, hardware bringup, schematic work, reconciling research against the manual.
allowed-tools: Read, Grep, Glob, Bash
---

# Datasheet Skill

Answer hardware questions from the documents. Cite facts with a document, section, and page. If the corpus can't
answer, say so and name the document that would.

## The corpus

The corpus is a [shelf](https://github.com/mjrskiles/shelf): a directory holding `shelf.json`
(the catalog, git-tracked), the PDFs (usually gitignored), and a derived full-text index.

- **Root:** `datasheet.root` in `.claude/vibe-hacker.json`, default `docs/reference/`.
  `shelf` finds `shelf.json` by searching upward from the working directory; from elsewhere
  pass `--root <root>`.
- **Catalog:** `shelf list` — every document by id, type, parts, revision, page count, and
  whether it is on disk. The `wanted` section lists documents known to be missing; say so
  rather than substituting another part's manual.
- **Without shelf:** the `Read` tool still reads a PDF by page range, and poppler
  (`pdftotext -layout`, `pdftoppm`) still works on individual files. You lose search across
  the corpus and the printed-page mapping.

## Procedure

1. **Find the document.** `shelf list`, or `shelf search <term> --part <part>` to let the
   index pick. Note the id and revision. If it isn't there, stop and report "not in corpus".
2. **Locate the section.**
   ```bash
   shelf search usart fifo size --doc rm0433      # phrase-ANDed full text; hits show page + snippet
   shelf grep 'ADCSEL\[1:0\]' --doc rm0433        # regex, for tokens FTS mangles (bit ranges, §2.2.21, 0x81A)
   shelf toc rm0433 --grep 'clock generator'      # section by title, when the doc has a TOC
   ```
   Pages in the output are **printed** page numbers (footer), which is what you cite and
   what other documents reference. `shelf show <id>` reports `page_offset` and whether the
   TOC exists; when the offset is unknown the tool says so and pages are PDF indices.
3. **Read the page.** A hit is a pointer, not evidence.
   ```bash
   shelf read rm0433 2020-2021          # printed pages, with a citation header
   shelf read rm0433 §48.5.4            # a whole section, via the TOC
   ```
   Tables that come out garbled: render and read the image.
   ```bash
   pdftoppm -f <pdf-page> -l <pdf-page> -r 110 -png <root>/<file>.pdf /tmp/ds
   ```
   then `Read /tmp/ds-<page>.png`. (`shelf read --pdf` takes PDF indices if you need them.)
4. **Check the errata sheet.** For any peripheral or core-feature question, `shelf search`
   the errata document before answering. An erratum that applies is part of the answer,
   including which silicon revisions it affects.
5. **Cite.** `<id> <Rev> §<section>, p. <printed page>` — for example
   `RM0433 Rev 8 §51.5.8, p. 2048`. One citation per fact, inline. Copy the header that
   `shelf read` prints.

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
- **Read-only.** Don't run `shelf add`, `edit`, `ingest --apply`, or `inspect --apply`
  from this skill unless the user asked you to change the catalog. Never edit
  source code from this skill — report what the document says and where the code disagrees.

## When comparing against code

The common request is "does our driver match the manual?" Report as pairs:

```
uart.hpp:292 — comment says "8-byte hardware FIFO"
RM0433 Rev 8 Table 399, p. 2020 — "Tx/Rx FIFO size 16"
→ agrees / disagrees / manual does not state
```

Cite the code by `file:line` and the document by the citation format above.
Do not fix the code; the user decides.

## When to delegate to the `datasheet-reader` agent

Use the agent instead of reading in-context when:

- the question spans more than ~10 pages or several sections;
- it crosses documents (reference manual + errata + datasheet for one
  peripheral);
- you are auditing a whole driver or schematic sheet against the manuals;
- you are cataloguing new PDFs and checking the guessed metadata.

Give the agent the exact question, the part numbers, and the code or
schematic files it should compare against. It returns cited findings and an
explicit "not found" list.

## Adding a document

```bash
shelf add <file>.pdf --id rm0433 --type reference-manual \
      --parts STM32H750xB --revision "Rev 8" --source <url>     # copies in, hashes, indexes
shelf toc rm0433 --build                                        # TOC from the PDF outline
shelf inspect rm0433 --apply                                    # guess page_offset if unknown
shelf show rm0433                                               # confirm; fix with `shelf edit`
```

Prefer the vendor document number as the id (`rm0433`, `es0392`). For a batch of PDFs
already dropped under the root: `shelf ingest` (dry run), then `shelf ingest --apply`;
metadata it guesses is marked `auto` in the catalog until confirmed. `shelf wanted add <id>`
records a document you need but don't have. `shelf verify` checks the catalog against disk.

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
