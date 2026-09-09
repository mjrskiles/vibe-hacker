---
name: curate-corpus
description: Close the metadata debt in a shelf corpus — unknown revisions, missing titles, paper bylines and years, printed-page offsets, source URLs — by pairing the shelf CLI with a fan-out of corpus-curator subagents. Use when catalog fields are unknown, when `shelf verify` reports unconfirmed guesses, or when preparing a corpus for sharing or replication.
allowed-tools: Read, Grep, Glob, Bash, Task, Agent
---

# Curate Corpus

The [`datasheet`](../datasheet/SKILL.md) skill reads the corpus. This one
maintains it. Same discipline, pointed the other way: there, an unsupported
claim is a bad answer; here, it is a bad record that every future citation
inherits.

The work is closing metadata gaps — the fields that make a citation say
`RM0433 Rev 8 §51.5.8, p. 2048` instead of `rm0433 pdf p. 2051`. It is
one-document-at-a-time reading, which makes it both too big to do by hand and
exactly the wrong shape for a single long context. So it is split three ways.

## The division of labour

| | Does | Never does |
|---|---|---|
| **`shelf` CLI** | Enumerates, extracts, hashes, and performs **every write** | Judgement |
| **`corpus-curator` agents** | Read pages and propose values, one document each | Writes |
| **You, orchestrating** | Plan the batch, adjudicate proposals, apply, re-verify | Read whole documents |

The rule that makes this safe: **the write path is single and deterministic.**
Agents return proposals; you apply them with `shelf edit`. A bad read is then a
rejected proposal rather than a corrupted record, and every change is one
reviewable line in `shelf.json`.

## Running `shelf`

`shelf` searches *upward* from the working directory for `shelf.json`, and the
corpus normally sits *below* the project root (`docs/reference/`), so a bare
`shelf list` from the root fails. Export the root once at the start of a pass
and put it in every agent prompt:

```bash
export SHELF_ROOT=docs/reference     # or `datasheet.root` from .claude/vibe-hacker.json
```

The census script resolves the same root on its own; it needs no environment.

## Procedure

### 1. Census — what is open, and who can close it

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate-corpus/scripts/census.py            # all tiers
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate-corpus/scripts/census.py --tier cover --limit 8 --json
```

`shelf verify` reports unknown revisions, unknown paper bylines, and unconfirmed
`auto` guesses. It does **not** report a missing `source_url`, a null
`page_offset`, or an empty `title` — those are not errors, just debt, so run
the census as well as `shelf verify`, not instead of it.

The census sorts into four tiers by the cheapest thing that can settle the field:

- **`confirm`** — a value exists but is a machine guess. `shelf inspect` voted
  on some pages; an agent corroborates on a page it did not use, and
  `shelf edit` clears the `auto` flag.
- **`cover`** — readable from the document's own front matter: revision, title,
  paper byline.
- **`offset`** — printed folio minus PDF index, from two widely separated pages.
- **`web`** — not in the document at all: `source_url`, and the years no cover
  states. Needs `WebSearch` / `WebFetch`.

### 2. Spend the deterministic tier first

Never send an agent after something the tool already knows.

```bash
shelf inspect                # dry run: what it can guess, and how strongly
shelf inspect <id> --apply   # write the guesses, marked `auto`
```

`inspect` reports its evidence (`1 (pp. 6…28, 23 agree)`). Strong agreement
across many pages moves a field from the `offset` tier to the cheaper `confirm`
tier. When `inspect` says `nothing to do` for every document, this tier is spent
and the whole remaining census is agent work or undoable.

### 3. Fan out

One agent per document — they are independent, so dispatch a batch in a single
message. Batches of **6–10** keep the adjudication reviewable; going wider mostly
produces a pile you skim.

Each prompt carries: the document id, the exact fields, the tier, and the
current value where one exists. Nothing else — the agent has the skill.

> `corpus-curator`: settle **pcm3060-ds**.
> - `page_offset` (confirm) — `shelf inspect` guessed 0; corroborate on a page
>   it did not vote on.
> - `source_url` (web) — TI product page for PCM3060, Rev. B if it is pinned.
> Report per the format in your agent definition. Do not write to the catalog.

Batch by tier, not by document order. A `web` batch and a `cover` batch want
different work; mixing them makes every agent load both methods.

### 4. Adjudicate

Agents return `propose:` / `decline` / `undoable` / `contradict` per field.

- **`propose` at high confidence, with a page** — apply it.
- **`propose` at medium confidence** — apply only if the evidence quoted in the
  report actually states the value. "Inferred from the AES convention number" is
  not a stated year; either chase it or leave it unknown.
- **`decline`** — leave the field alone. It stays in the census, which is
  correct: it is still open.
- **`undoable`** — retire it (step 6).
- **`contradict`** — the recorded value is *wrong*. Clear it back to the unknown
  sentinel before anything else:
  ```bash
  shelf edit ad2-rm --revision unknown        # then retire or leave open
  ```
  Expect these in the `confirm` tier, and treat them as the tier's real payload.
  `shelf inspect` matches patterns, so it reads "applies to the Analog Discovery
  2 rev. C" as the manual's revision when it is the *hardware's* — a mistake no
  amount of re-running the detector will catch. Clearing a wrong value is worth
  more than filling an empty one: an empty field announces itself, a wrong one
  rides along in every citation looking exactly like a fact.

Reject any proposal with no page reference, however plausible it reads. That is
the whole point of the exercise.

**When a document under-identifies itself.** Some documents state a title that
is verbatim and useless — a mechanical drawing whose title block says `OUTLINE`,
a sheet that never prints its own part number. Record the verbatim value anyway
and put the identifying context in `notes`. Do not compose a better title: the
moment a catalog field says something the document does not, the corpus is
guessing on someone's behalf, and `notes` is the field that exists for what the
document does not say about itself.

An agent that reports a neighbouring field looks wrong — `parts` resting on the
filename alone, a `type` that does not match what the pages actually are — is
doing its job. Note it for a later pass; do not widen the current batch to chase
it, or a curation pass becomes an unbounded re-cataloguing.

### 5. Apply

Every write goes through `shelf edit`, which also clears the `auto` flag for
whichever field it sets — so confirming a guess is re-setting it to its own value:

```bash
shelf edit pcm3060-ds --page-offset 0                       # confirms the guess
shelf edit ad2-rm --revision "Rev. C"
shelf edit echoplex-model --author "S. Arnardottir" "J. S. Abel" "J. O. Smith" --year 2008
shelf edit pcm3060-ds --source https://www.ti.com/product/PCM3060
```

Apply in one pass, then check the diff — `shelf.json` is git-tracked and a
curation pass should read as a clean set of field changes.

### 6. Retire what cannot be done

Some fields are not unknown, they are unavailable: a scanned paper with no folio
anywhere has no `page_offset`, and no amount of re-reading will produce one.
`shelf` has no field for this, so the convention is a marker in `notes`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate-corpus/scripts/census.py --undoable page_offset "no folio on any page"
```

which prints the `shelf edit --notes` command to run. The census then stops
counting that field. Retire a field only on an agent's `undoable` verdict with
the pages it checked — never to make a number go down.

### 7. Verify and report

```bash
shelf verify                       # MISSING / CHANGED / ORPHAN are real problems
python3 ${CLAUDE_PLUGIN_ROOT}/skills/curate-corpus/scripts/census.py  # the debt, before and after
```

Report as: **wrong values corrected** (lead with these — they are the findings
that change what the corpus asserts), fields closed by tier, fields retired as
undoable, fields declined and what would settle them, and the census delta. Name
the declines explicitly — they are the honest remainder, and hiding them in a
total is how a corpus starts lying.

The census total can go *up* after a good pass, when a contradiction clears a
field that was wrongly filled. That is the number improving, not regressing; say
so plainly rather than burying it.

## Rules

- **Agents never write.** If a report says an agent ran `shelf edit`, discard
  the whole report and re-run it — you no longer know what else it touched.
- **No value without a page.** Applies to you as much as to the agents. Do not
  fill a field from the filename, the id slug, the directory, or your own
  knowledge of the part.
- **`unknown` beats wrong, every time.** These records are the ground truth for
  every citation the `datasheet` skill emits. An empty field is visible; a
  confidently wrong revision is not.
- **Verbatim from the document.** Vendor formatting is preserved (`Rev. C`, not
  `rev c`). Do not normalise across vendors — the string is what the document
  says about itself.
- **One batch, one commit.** Keeps the `shelf.json` diff reviewable and makes a
  bad pass revertible as a unit.
- **Never `--force`.** `shelf inspect --force` overwrites confirmed values with
  guesses, which is precisely backwards.

## Scope note

Curation is bounded by what is *in* the document. A paper that states no year
and has no DOI, a scan with no folio, a datasheet whose vendor no longer hosts
it — these end as declines or retirements, not as best guesses. A corpus with
120 solid records and 40 honest gaps is worth more than 160 records you have to
spot-check before trusting.
