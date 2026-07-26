# Minecraft Calc

Two Minecraft **Java Edition 1.21.x** planning calculators — an **Anvil
Combiner** and a **Brewing Planner** — bundled into one self-contained HTML
file. No build step, no install, no server, no network calls, no
dependencies: open `index.html` in a browser and it works.

*Java Edition 1.21.x · zero dependencies · single ~114 KB HTML file · 20
automated self-tests · works fully offline*

Not an official Minecraft product. Not approved by or associated with
Mojang or Microsoft.

## Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
  - [Anvil Combiner](#anvil-combiner)
  - [Brewing Planner](#brewing-planner)
- [How the Numbers Work](#how-the-numbers-work)
- [Scope and Non-Goals](#scope-and-non-goals)
- [Architecture](#architecture)
- [Testing](#testing)
- [Accessibility and Browser Support](#accessibility-and-browser-support)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Attribution](#attribution)
- [License](#license)

## Overview

Minecraft Calc is a pair of deterministic, offline "second screen" planning
tools for players who want to work out the cheapest anvil combine order or
a full brewing shopping list *before* spending XP levels or brewing-stand
time in game. Both calculators live in a single HTML file with all logic,
styling, and even icon assets embedded inline — there is nothing to
install and nothing is ever sent over the network.

The two modules are switched with a tab bar at the top of the page and are
otherwise unrelated: they share only a CSS theme and a handful of generic
DOM helpers.

## Quick Start

No installation, build step, or server is required.

- **Double-click** `index.html`, or drag it into an open browser window, or
- From a terminal:
  ```sh
  open index.html          # macOS
  xdg-open index.html      # Linux
  start index.html         # Windows (cmd/PowerShell)
  ```
- Or, if you'd rather serve it over HTTP than open it directly from disk,
  any static file server works, e.g. `python3 -m http.server` from this
  directory, then visit `http://localhost:8000`. This makes no functional
  difference — the app behaves identically under `file://` and `http://`.

Any modern evergreen desktop or mobile browser with JavaScript enabled
(Chrome, Firefox, Safari, Edge) is sufficient. Node.js is **not** needed to
use the calculators — it's only used for the optional headless test run
described in [Testing](#testing).

## Features

### Anvil Combiner

Given a target item and a pool of enchanted books, the Anvil Combiner finds
the cheapest possible order to combine them all at an anvil — pairing the
target with a **sacrifice** (the book or item consumed in each step to
transfer its enchantments) — and shows the resulting item's real combat or
defense stats.

**Inputs**

- **Target item** — one of 18 item types (tools, weapons, armor, elytra,
  bow/crossbow, trident, fishing rod, shears, shield, or a bare enchanted
  book), each with a short in-app description of what it's for.
- **Material**, for the item types that have one — see
  [material tiers](#material-tiers-and-stats) below.
- **Prior anvil uses on the item** — the work-penalty counter (0–8).
- **Enchantments already on the item**, added one at a time with a level.
- **Enchanted books to combine in** — up to 7 books per job (8 units total
  including the target item).

**The optimizer**

Rather than greedily combining books in list order, the engine performs an
exhaustive search: it explores *every* possible binary combine tree over
the target item and its books (dynamic programming across all subsets),
keeping only the cheapest path to each distinct resulting enchantment
state, and returns a guaranteed-minimum-total-level order. The output
panel also shows how many levels that saves compared with sacrificing the
books one after another in the order you added them.

**Cost model**

| Term | Rule |
| --- | --- |
| Prior-work penalty | `2^(prior anvil uses) − 1` XP levels, charged for *both* the target and the sacrifice in every operation |
| Enchantment cost | `final level × per-level multiplier` — the multiplier depends on the enchantment; a book sacrifice is never more expensive than an item sacrifice, and is cheaper for most enchantments (a handful, like Sharpness and Protection, cost the same either way) |
| Leveling a duplicate | Combining two copies of the same enchantment at the same level raises it by one, up to that enchantment's max level; combining different levels keeps the higher one |
| Conflict penalty | A sacrifice enchantment that conflicts with one already present (e.g. Sharpness vs. Smite) still costs **+1 level** but is dropped rather than applied |
| Inapplicable enchantments | An enchantment a book carries that doesn't fit the target item type is skipped for free (no cost, no effect) |
| "Too Expensive" cap | Any single operation whose total cost reaches **40 levels** is rejected outright — the optimizer never routes through it, matching survival mode's anvil cap |

42 enchantments are modeled in total, with 20 mutually-exclusive pairs
(the four Protection variants against each other, Sharpness/Smite/Bane of
Arthropods against each other, Silk Touch vs. Fortune, Infinity vs.
Mending, and so on) enforced automatically.

**Output**

- The full ordered list of anvil operations, each showing the target
  (with its prior-work count), the sacrifice, the result, and the level
  cost of that step, with dropped conflicts called out.
- Summary tiles: total levels spent, number of operations, the priciest
  single step, and levels saved versus a naive one-by-one order.

<a id="material-tiers-and-stats"></a>
**Resulting item stats** *(referred to elsewhere in this document as the
"gear-stats" panel — `GearEngine` in the source)*

Alongside the combine order, the panel also shows the finished item's real
stats:

- **Tiered tools and weapons** (sword, axe, pickaxe, shovel, hoe) across
  6 material tiers — wood, stone, iron, gold, diamond, netherite — with
  attack damage, attacks per second, computed DPS, and durability.
- **Tiered armor** (helmet, chestplate, leggings, boots) across 6 material
  tiers — leather, chainmail, iron, gold, diamond, netherite — with armor
  points, toughness, knockback resistance, and durability.
- **8 fixed single-tier items** with no material select (mace, elytra,
  bow, crossbow, trident, fishing rod, shears, shield). Where vanilla has
  no clean, unconditional number for a stat — ranged weapons' damage, for
  instance — the tile is left blank with an explanatory note instead of
  guessing.
- A bounded, explicit set of enchantments is **folded into the headline
  tiles**: Sharpness increases the Damage tile, Unbreaking multiplies the
  Durability tile. Everything else that has a real numeric effect but only
  applies conditionally — Smite and Bane of Arthropods (target-type
  only), the four Protection variants (per-piece, not summed across a
  full set), Feather Falling (fall damage only), Knockback, Power, Punch,
  Density, Breach, and Wind Burst — is shown as a **separate labeled
  line** explaining exactly what it does, rather than being blended into
  a single misleading number.

Enchantment combining only: **repairing items and renaming at the anvil
are out of scope.**

### Brewing Planner

Given a list of desired potions — including splash, lingering, and tipped
arrows — the Brewing Planner works out the minimal brewing-stand pipeline
for each one, then pools every target's bottles together into shared brew
cycles and totals up the cost.

**Inputs**

- **Effect** — 19 potion effects: 16 are brewed directly, and 3
  (Slowness, Harming, Invisibility) are corruption-only and reachable only
  by corrupting a related potion with a fermented spider eye.
- **Potency II** (glowstone dust — Slowness becomes Potency **IV**
  instead, per its special case) and **Extended** (redstone dust) toggles.
  These are mutually exclusive — checking one automatically unchecks the
  other — and each is also disabled with an explanation when the selected
  effect has no such variant (or, for Extended, when the effect is
  instant).
- **Form** — Potion, Splash, Lingering, or Tipped Arrow.
- **Quantity** (or arrow count, for tipped arrows).
- **Brewing stands available**, used for the elapsed-time estimate.

**The ingredient chain**

Each target follows Minecraft's brewing state machine: Water Bottle →
(nether wart) → Awkward Potion → (effect ingredient) → base potion →
optional Potency/Extended → optional Splash (gunpowder) → optional
Lingering (dragon's breath, Splash only) → optional tipped-arrow crafting.
Weakness is the one exception, made by applying a fermented spider eye
directly to a Water Bottle rather than an Awkward Potion.

For the 3 corruption-only effects, the planner automatically inserts the
correct source potion and a fermented spider eye. When more than one
source potion reaches the same corrupted effect in the same number of
steps (e.g. Harming, reachable via either Healing or Poison), it picks the
route alphabetically by ingredient and notes the equally-valid alternate.

**Batch pooling**

This is the planner's key feature: instead of planning each target in
isolation, it pools every bottle across every queued target and groups
identical transitions (same starting state, same next ingredient)
together, since a brewing stand processes up to **3 bottles per cycle**
regardless of how many different final potions they'll become. Two
different potions that both start with a Water → Awkward step, for
example, share those cycles instead of repeating them.

**Output**

- Summary tiles: total brew cycles, elapsed time, blaze powder needed, and
  total bottles.
- A per-target step-by-step chain, annotated with which shared cycle(s)
  each transition runs in.
- **Spare-slot hints** — whenever a shared cycle's bottle count isn't a
  multiple of 3, the leftover slots are called out as free capacity for
  more bottles at no extra time or fuel.
- A consolidated **bill of materials** (every ingredient, glass bottles,
  arrows for tipped-arrow crafting, and blaze powder fuel, each with its
  role).
- A surplus note when tipped-arrow crafting (which always happens in
  batches of 8) yields more arrows than requested.

Under the hood, the planning engine also rejects Potency II + Extended as
a validation error if both are ever requested together. The shopping-list
checkboxes already prevent selecting both at once, so in practice this is
a defensive guard exercised by the self-test suite rather than something
you'll see triggered on screen.

Brewing involves **no XP and no anvil interaction**; the base potion
durations shown next to each effect are reference/flavor text only and are
not recomputed per potency or extension level.

## How the Numbers Work

A quick-reference table of the constants driving both engines:

| Constant | Value | Meaning |
| --- | --- | --- |
| "Too Expensive" cap | 40 levels | Anvil operation cost at/above this is rejected |
| Prior-work penalty | `2^uses − 1` | XP levels added per unit, per prior anvil use |
| Combine job size | 8 units | Target item + up to 7 books, per Anvil Combiner job |
| Brew cycle | 20 seconds | Time for one brewing-stand cycle |
| Bottles per cycle | 3 | Bottles a stand brews at once |
| Fuel per blaze powder | 20 cycles | Brewing-stand charges from one blaze powder |
| Tipped-arrow batch | 8 arrows | Arrows produced per lingering potion consumed |
| Enchantments modeled | 42 | All usable in the Anvil Combiner; 15 also affect gear stats (2 folded into headline tiles, 13 shown as separate lines) |
| Potion effects modeled | 19 | 16 direct + 3 corruption-only |
| Item types | 18 | 17 wearable/wieldable items + the enchanted book carrier |

## Scope and Non-Goals

- The Anvil Combiner models **enchantment combining only** — item repairs
  and renaming at the anvil are not implemented.
- The Brewing Planner has **no XP cost and no anvil interaction**; on-screen
  potion durations are flavor text, not a fully modeled timer system.
- The gear-stats panel **never invents a number the base game doesn't
  define** — items like the bow and crossbow show no melee "damage"
  figure, only an explanatory note, because vanilla doesn't define one.
- Situational or target-specific enchantment bonuses (Smite, Bane of
  Arthropods, the Protection family, Feather Falling, Knockback, Power,
  Punch, Density, Breach, Wind Burst) are always shown as separate,
  labeled, conditional lines — never silently folded into the headline
  Damage, Armor, or Durability tiles.
- Choosing a material tier never changes enchanting cost — the gear-stats
  engine and the anvil-cost engine are independent and only share plain
  item identifiers and enchantment maps, never each other's internals.
- No save/export, accounts, or multiplayer/server integration — this is a
  single-session, client-side planning tool with no persistence.
- One fixed dark visual theme; there is no light-mode toggle.

## Architecture

The entire application is one file: `index.html` contains the markup,
CSS, JavaScript engines, UI code, and self-tests. `README.md` is the only
other file in the repository — there is no build config, package
manifest, or CI pipeline, by design.

The JavaScript is organized into three independent, pure-function "engine"
namespaces, each an IIFE that returns a frozen object of functions and
constants:

- **`AnvilEngine`** — enchantment-combining rules (`combine`) and the
  combine-order optimizer (`optimize`).
- **`GearEngine`** — material tiers and the bounded enchantment-to-stat
  modifier table (`resultingStats`). It takes `AnvilEngine`'s item ids and
  a plain enchantment map as input and never reaches into `AnvilEngine`'s
  internals, so the two stay fully decoupled.
- **`BrewEngine`** — the brewing-stand state machine (`applyIngredient`)
  and the batch/cycle planner (`planBatch`).

Each engine is DOM-free by construction — none of the three ever
references `document` or `window` — and `Object.freeze()`-d, so it only
exposes its intended public surface. A separate `HAS_DOM` check, defined
after all three engines, gates the DOM-touching UI layer instead. A small
shared UI layer (`el()`, `$()`, `tile()`, `stateChip()`, and similar
helpers) renders both modules' DOM purely from those engines' return
values; a `bootTabs()` / `bootAnvil()` / `bootBrew()` sequence wires
everything up on `DOMContentLoaded`.

All vanilla item and block icons are embedded as base64 PNG data URIs in
an `ICONS` table, and even the favicon is an inline SVG data URI — nothing
is fetched at runtime, so the calculators work with no network connection
at all.

At the bottom of the script:

```js
if (typeof module !== 'undefined' && module.exports)
  module.exports = {AnvilEngine, BrewEngine, GearEngine, run_self_tests};
```

This is what lets the engines run headlessly under Node for testing, with
no change to the browser code path.

## Testing

`run_self_tests()` runs **20 assertions** across all three engines: 5
anvil cases (T1–T5), 10 gear-stats cases (W1–W10), and 5 brewing cases
(B1–B5) — covering things like the prior-work-penalty formula, the
40-level cap, the optimizer beating a naive sequential combine order,
correct stat folding vs. separate conditional lines, corruption-effect
routing, the mutually-exclusive Potency/Extended validation error, and
batch sizes that don't divide evenly into brew cycles.

The suite runs automatically the moment the page loads: results are
printed with `console.table()`, and the footer shows a live pass/fail
badge (e.g. *"self-tests: 20/20 passing (see console.table)"*).

It can also run headlessly with only Node.js — no browser, no
dependencies:

```sh
node -e "
const src = require('fs').readFileSync('index.html', 'utf8');
const script = src.match(/<script>\n([\s\S]*?)<\/script>/)[1];
require('fs').writeFileSync('/tmp/mc.js', script);
const rows = require('/tmp/mc.js').run_self_tests();
process.exit(rows.every(r => r.pass === 'PASS') ? 0 : 1);
"
```

The process exit code reflects the result (`0` = all passing), which
makes this a natural fit for a CI check — none is currently wired up in
this repository. If you add or change a mechanic, add a matching
`t(...)` case to the relevant suite in `run_self_tests()` and confirm the
badge (or the command above) still shows everything passing.

## Accessibility and Browser Support

- Tabs implement the full ARIA tabs pattern (`role="tablist"`/`"tab"`/
  `"tabpanel"`, `aria-selected`, `aria-controls`) with Left/Right/Home/End
  keyboard navigation and a roving `tabindex`.
- Every dynamic output card is an `aria-live="polite"` region — the
  combine-order and item-stats panels in the Anvil Combiner, plus the
  brew-plan panel in the Brewing Planner — so recalculated output is
  announced to assistive technology without manual refocus.
- Every interactive control has a visible `:focus-visible` outline, and
  `@media (prefers-reduced-motion: reduce)` disables transitions and
  animations.
- The two-column layout collapses to a single column below 900px width.
- Requires JavaScript (a `<noscript>` message explains this if it's
  disabled); no Internet Explorer support and no polyfills are included.
- Makes **zero outbound network requests** — no external fonts, scripts,
  images, or analytics of any kind.

## Project Structure

```text
minecraft_calc/
├── README.md    — this file
└── index.html   — the entire application: markup, styles, engines, UI, and self-tests
```

## Contributing

- There's no build step: edit `index.html` directly and reload it in a
  browser to see changes immediately.
- Keep new game-mechanic logic inside the relevant engine's IIFE and pure
  (no DOM access) — the UI layer should only ever read engine outputs,
  never contain calculation logic itself.
- Add or update a `run_self_tests()` case for any new or changed
  mechanic, and confirm all tests still pass (see [Testing](#testing))
  before submitting changes.
- `GearEngine` intentionally reads `AnvilEngine`'s item ids and
  enchantment maps as plain data rather than importing its internals —
  keep that separation when extending either engine.
- Keep the project dependency-free: no build tooling, no external
  requests, and no added libraries or frameworks.

## Attribution

Item and block icons are embedded inline as base64 PNG data URIs, sourced
from [misode/mcmeta](https://github.com/misode/mcmeta) (a mirror of
Mojang's own generated assets), and used here solely for item
identification.

**Not an official Minecraft product. Not approved by or associated with
Mojang or Microsoft.**

Game mechanics — anvil combination rules, brewing-stand behavior, and item
material stats — reflect Minecraft: Java Edition 1.21.x, as transcribed
into the inline code comments alongside each engine.

## License

This repository does not currently include a `LICENSE` file, so default
copyright applies: all rights are reserved unless and until the repository
owner adds explicit license terms. Regardless of this repository's own
licensing, the embedded Minecraft icon assets remain the property of
Mojang/Microsoft and are used here only as permitted for identification
purposes.
