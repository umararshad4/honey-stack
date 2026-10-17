# Unslop pass

Read after drafting any doc, README, changelog, ADR, PR body or commit message. Condensed from cursor/plugins pstack 0.15.25 `skills/unslop` and `skills/technical-writing` (MIT).

Scan the text for the patterns below and rewrite what you find. Keep the meaning and the intended tone. If a rule makes a sentence worse, fix the sentence another way or leave it.

## Filler

- **Filler phrases.** "In order to" becomes "to". "Due to the fact that" becomes "because". Delete "It is important to note that" and "It's worth mentioning".
- **Hedging.** "Could potentially possibly be argued that it might" becomes "may". In reference docs, state facts without hedges.
- **Generic conclusions.** "The future looks bright", "This makes X more robust". Replace them with the specific plan or fact, or delete them.
- **Chatbot phrases.** "I hope this helps", "Let me know if", "Certainly!", "Great question". Delete.
- **Pre-announcing.** "We will soon support…". Document what exists.

## Vague over concrete

- **Say what it does, not how it feels.** "SQL you can read" names a feeling. "`.toSQL()` returns the exact string sent to the database" names the mechanism. If a sentence could appear unchanged in another project's docs, it says nothing about this one: cut it.
- **Vague attributions.** "Experts believe", "Industry reports suggest". Name the source or delete the claim.
- **Adverbs on weak verbs.** "Runs quickly" becomes the number. "Significantly improves" becomes the measured delta.
- **Superficial -ing tails.** "…, ensuring reliability", "…, highlighting the need for". Delete them, or state the actual consequence as its own sentence.

## AI vocabulary

- **Words to replace:** additionally, crucial, delve, enhance, fostering, garner, interplay, intricate, landscape, pivotal, robust, seamless, showcase, tapestry, testament, underscore, vibrant. Use the plain word or nothing.
- **Fancy "is".** "Serves as", "stands as", "boasts", "features". Write "is" or "has".
- **Long words.** "Utilize" and "leverage" become "use", "facilitate" becomes "help", "numerous" becomes "many", "in the event that" becomes "if".
- **Abstract metaphor nouns.** Substrate, wedge, vector (for "way"), nexus, paradigm, north star, flywheel, bedrock, "surface" for an API, "harness" or "scaffolding" as metaphors, "ratchet" for a limit that only tightens. Write the concrete word.
- **Mannered prose.** Aphorisms, rhetorical fragments, personified code ("the plan holds it"), figurative verbs ("rides along"). Say it literally.

## Structure tells

- **"Not just X, but Y."** State Y.
- **Forced threes.** Use the natural number of items.
- **Synonym cycling.** One thing gets one name everywhere. Three names teach the reader three things.
- **False ranges.** "From setup to scale" where the ends aren't on one scale. List the topics.
- **Inline-header lists.** "**Performance:** Performance improved…" restates its label. Make it prose. A bold lead-in that ends in a period and is followed by new detail is fine.

## Punctuation and formatting

- **Em dashes.** Use a period or a comma instead.
- **Mid-sentence colons** used as connectors. Keep colons for introducing a list or an example.
- **Bold** on every term. Bold only what a skimming reader must not miss.
- **Title Case Headings.** Use sentence case.
- **Decorative emoji** in headings and bullets. Remove.
- **Curly quotes.** Use straight quotes.
- **Slashes and "(s)".** "a/b" becomes "a, b, or both". Pick singular or plural.

## Clarity

- **Passive voice.** "Queries are validated" becomes "the compiler validates queries". Keep passive only when the actor is unknown or irrelevant.
- **Dense sentences.** If the reader has to backtrack, split the sentence or drop a clause.
- **Over-compression.** Dropped articles, arrows and symbol-speak make the reader decode. "Parser rejects bad date → exit 2" becomes "The parser rejects a bad date and exits with code 2."
- **Loose pointers.** Every "it", "this" and "they" points at one obvious noun. Repeat the noun when in doubt.
- **Misplaced "only" and "not".** Keep them next to the word they change: "fails only on growth".
- **Noun stacks.** "The proto import budget check script" becomes "the script that checks the proto-import budget".

## Before and after

> Configuration of the budget script parameters is performed via budget.json. Note that it's important to remember that running with --write should only be done when lowering it. If exceeded, CI fails.

> `budget.mjs` reads the budget from `budget.json` and counts the files that import protos. If the count exceeds the budget, CI fails. Run `budget.mjs --write` only to lower the budget.
