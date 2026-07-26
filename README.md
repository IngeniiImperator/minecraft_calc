# Minecraft Calc

Four Minecraft **Java Edition 1.21.x** planning tools — an **Anvil
Combiner**, a **Brewing Planner**, a **Book Library & Merge Planner**, and
**Character Profiles** — bundled into one self-contained HTML file. No
build step, no install, no server, no network calls, no dependencies: open
`index.html` in a browser and it works.

*Java Edition 1.21.x · zero dependencies · single HTML file · 30 automated
self-tests · works fully offline*

Not an official Minecraft product. Not approved by or associated with
Mojang or Microsoft.

## Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
  - [Anvil Combiner](#anvil-combiner)
  - [Brewing Planner](#brewing-planner)
  - [Book Library & Merge Planner](#book-library--merge-planner)
  - [Character Profiles](#character-profiles)
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

Minecraft Calc is a set of deterministic, offline "second screen" planning
tools for players who want to work out the cheapest anvil combine order, a
full brewing shopping list, which enchanted books to save for later, or a
persistent record of a character's gear and inventory — *before* spending
XP levels, brewing-stand time, or storage space in game. All four tools
live in a single HTML file with all logic, styling, and even icon assets
embedded inline — there is nothing to install and nothing is ever sent
over the network.

The four modules are switched with a tab bar at the top of the page and
are otherwise unrelated: they share only a CSS theme and a handful of
generic DOM helpers. The Anvil Combiner and Brewing Planner are
single-session calculators with no persistence; the Book Library and
Character Profiles are the two modules that save their data (to the
browser's `localStorage`, still never leaving the device, each under its
own key) so a book collection or character roster survives a page reload
— see [Book Library & Merge Planner](#book-library--merge-planner) and
[Character Profiles](#character-profiles).

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

### Book Library & Merge Planner

A catalog for enchanted-book collections that grow past the point of
hovering over every book in a chest to remember what's in it. Unlike the
other two modules, entries here persist across reloads in the browser's
`localStorage` — still 100% local, nothing is ever sent anywhere.

**Book catalog**

Each catalogued entry records:

- One or more **enchantments and levels** (built the same way as the Anvil
  Combiner's chip lists — add an enchantment, pick its level, repeat).
- **Quantity** — for stacks of identical books.
- **Storage location** — free text with suggestions (Chest, Barrel,
  Shulker Box, Ender Chest, Inventory), so entries like "Chest A" or
  "Shulker Box 3" both work.
- **Notes** — free text.
- **Status** — Available, Reserved, or Used, editable inline per entry
  alongside quantity, location, and notes.

**Merge Planner**

Link two or more catalog entries into a named plan with a planned result
(e.g. two Efficiency IV books → "Efficiency V", or a Sharpness IV book +
a Looting III book → "Future Sword Upgrade"). Plans are reminders, not
automatic crafting — nothing about the actual anvil combine is computed
here; use the Anvil Combiner tab for that.

**Reserved books**

Linking a book into a plan automatically flips its status to Reserved so
it doesn't get double-booked into a second plan or accidentally spent
elsewhere; deleting the plan (or removing the book from it) automatically
releases the book back to Available. A book reserved this way can't be
manually switched back to Available while still linked — the status
snaps back to Reserved on the next change, protecting the plan. A book
marked Used by hand always wins over automatic reservation, and a book
reserved by hand (outside of any plan) is left alone by the automatic
logic.

**Search & filtering**

The catalog can be filtered, in any combination, by:

- Enchantment and a minimum level
- Compatible equipment (derived from the same enchantment/item
  compatibility table the Anvil Combiner uses — e.g. filtering by
  "Pickaxe" surfaces Efficiency, Fortune, Silk Touch, and Unbreaking
  books)
- Storage location
- Reserved/Available/Used status
- Free-text search across notes, location, and enchantment names

**Upgrade projects**

Define a goal (God Pickaxe, God Sword, Netherite Armor, Elytra, a
villager-trading setup, or anything else) as a list of required
enchantment/level/quantity combinations, and the project shows a
completion percentage plus a per-requirement breakdown of how many
matching books (available or reserved, i.e. not already spent) are on
hand versus how many the project still needs.

**Not implemented** — flagged in the feature request as future work and
intentionally out of scope for this pass: automatic merge suggestions, XP
cost estimation for planned merges, enchantment-conflict detection in the
planner itself (the Anvil Combiner already does this for an actual
combine job), wishlist tracking, duplicate detection, and import/export
(the Book Library's own catalog isn't portable yet — see
[Character Profiles](#character-profiles) below for the module that does
have import/export).

### Character Profiles

Persistent character builds — equipped gear, a full inventory, and custom
per-item notes — that live independently of any single book collection or
project. Unlike the Book Library, entries here are portable: a profile can
be exported to a file and imported again in another project, or after a
Book Library merge reorganizes a collection, without losing any of its
custom data.

**Multiple copies, one item type, separate identities**

The problem this module solves: owning several of the same base item for
different purposes (a "Woodcutting" axe and a "Battle Axe," both plain
axes) and losing track of which was for what. Every inventory entry is its
own object with its own id — adding a second axe never merges with or
overwrites the first, no matter how similar their base type or
enchantments are.

**Each inventory item records**

- **Item type and, where relevant, material** — the same 18 item types and
  6-tier material lists as the Anvil Combiner and Gear Engine, reused as
  plain data (see [Architecture](#architecture)).
- **A custom name** — e.g. "Fortune Build" or "Woodcutting," to tell two
  copies of the same base item apart at a glance.
- **Enchantments and levels** — built the same way as the Anvil Combiner's
  and Book Library's chip lists.
- **Custom stats** — an open-ended list of label/value pairs (e.g.
  "Harvest Speed: +15," "Rare Ore Chance: +30") for anything the built-in
  enchantment model doesn't cover.
- **Quantity and free-text notes.**

**Equipped gear**

Six equipment slots — Main Hand, Off Hand, Helmet, Chestplate, Leggings,
Boots — are tracked per character. Equipping an inventory item into a slot
that's already occupied automatically unequips whatever was there;
unequipping (or deleting) an item never disturbs any other slot. A summary
of all six slots is shown above the full inventory list.

**Import & export**

- **Export one character or the whole roster** to a downloaded `.json`
  file (a hidden-`<a>` + `Blob`/`createObjectURL` download — still 100%
  local, no network request is made).
- **Import** from a file picker or by pasting exported JSON directly into
  a text box (useful when a file dialog isn't convenient) — either path
  accepts the single-character or whole-roster export shape.
- Importing **always adds new characters** — it never overwrites or
  merges into an existing one. A name that collides with a character
  already in the roster is imported anyway, with `" (imported)"` appended
  (repeated if needed) so nothing already on the roster is ever lost or
  silently replaced.
- Every export carries a `schemaVersion` field (currently `1`) so a future
  format change has somewhere to branch from — see
  [Scope and Non-Goals](#scope-and-non-goals).

**Persistence**

Like the Book Library, profiles are saved to the browser's `localStorage`
(under a separate key from the book catalog) after every change, wrapped
in the same defensive `try`/`catch` so a full or unavailable store
degrades to a session-only roster instead of throwing. Because Character
Profiles are a wholly separate engine and storage key from the Book
Library, nothing about merging or reorganizing a book collection can ever
touch a character's saved gear or inventory — the "preserve custom data
across book merges" requirement is satisfied by the two modules simply
never sharing state, not by any explicit synchronization code.

**Not implemented** — left for future work: multiple equipment loadouts
per character, character templates, item tags/categories, cloud sync, and
formal version-migration logic for older `schemaVersion` exports (the
field exists today but nothing yet reads or upgrades an old one).

## How the Numbers Work

A quick-reference table of the constants driving the anvil and brewing
engines (the Book Library and Character Profiles have no fixed game
constants of their own — see
[Book Library & Merge Planner](#book-library--merge-planner) and
[Character Profiles](#character-profiles) above):

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
- The Merge Planner is organizational only — it does not compute or
  validate an actual anvil combine (use the Anvil Combiner tab for that),
  and it does not estimate XP cost.
- No accounts, multiplayer/server integration, or sync between devices —
  the Book Library and Character Profiles persist locally via
  `localStorage` on the one device and browser they're used in; the Anvil
  Combiner and Brewing Planner remain single-session with no persistence
  at all. The Book Library itself has no import/export yet (see
  [Book Library & Merge Planner](#book-library--merge-planner) above for
  the full list of features left for later) — only Character Profiles
  does, and that export format has no version-migration logic behind its
  `schemaVersion` field yet (see [Character Profiles](#character-profiles)).
- One fixed dark visual theme; there is no light-mode toggle.

## Architecture

The entire application is one file: `index.html` contains the markup,
CSS, JavaScript engines, UI code, and self-tests. `README.md` is the only
other file in the repository — there is no build config, package
manifest, or CI pipeline, by design.

The JavaScript is organized into five independent, pure-function "engine"
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
- **`LibraryEngine`** — book-catalog filtering (`filterBooks`),
  merge-plan/reservation bookkeeping (`applyReservations`), and
  upgrade-project completion (`projectProgress`). Like `GearEngine`, it
  takes enchantment ids/levels as plain data from the UI layer rather than
  reaching into `AnvilEngine`'s internals — the UI (`bootLibrary()`) is
  what looks up enchantment names, max levels, and compatible equipment
  from `AnvilEngine.ENCH` when building on-screen labels and filters.
- **`CharacterEngine`** — character/inventory-item construction
  (`makeCharacter`, `makeItem`), equip/unequip bookkeeping (`equipItem`,
  `unequipItem`, `equippedItems`), item CRUD (`addItem`, `updateItem`,
  `removeItem`), and JSON import/export (`exportCharacter`,
  `exportCharacters`, `importPayload`). Every inventory item is its own
  object with its own generated id, so two items of the same `itemType`
  never collapse into one — that per-copy identity is the module's core
  guarantee. Like `GearEngine` and `LibraryEngine`, it takes item/
  enchantment ids as plain data and never reaches into `AnvilEngine`'s
  internals directly.

Each engine is DOM-free by construction — none of the five ever
references `document` or `window` — and `Object.freeze()`-d, so it only
exposes its intended public surface. A separate `HAS_DOM` check, defined
after all five engines, gates the DOM-touching UI layer instead. A small
shared UI layer (`el()`, `$()`, `tile()`, `stateChip()`, and similar
helpers) renders every module's DOM purely from those engines' return
values; a `bootTabs()` / `bootAnvil()` / `bootBrew()` / `bootLibrary()` /
`bootCharacters()` sequence wires everything up on `DOMContentLoaded`.

`bootLibrary()` and `bootCharacters()` are the two boot functions that
talk to browser storage: each loads its own state from a single
`localStorage` key (`mc_calc_library_v1` for the Book Library,
`mc_calc_characters_v1` for Character Profiles) on boot and writes back
to it after every mutation (`saveLibrary()` / `saveCharacters()`), each
wrapped in a `try`/`catch` so a full or unavailable store (private
browsing, quota) degrades to a session-only in-memory state instead of
throwing. These are the only two places in the codebase that touch
`localStorage` — the Anvil Combiner and Brewing Planner keep their state
in an in-memory `S` object for the tab's lifetime only, as before. Import
in `bootCharacters()` reads a file via `FileReader` or a pasted textarea
value; export writes a `Blob` through a temporary `<a download>` and
`URL.createObjectURL` — both are local browser APIs, so no network
request is ever made by either path.

All vanilla item and block icons are embedded as base64 PNG data URIs in
an `ICONS` table, and even the favicon is an inline SVG data URI — nothing
is fetched at runtime, so the calculators work with no network connection
at all.

At the bottom of the script:

```js
if (typeof module !== 'undefined' && module.exports)
  module.exports = {AnvilEngine, BrewEngine, GearEngine, LibraryEngine, CharacterEngine, run_self_tests};
```

This is what lets the engines run headlessly under Node for testing, with
no change to the browser code path.

## Testing

`run_self_tests()` runs **30 assertions** across all five engines: 5
anvil cases (T1–T5), 10 gear-stats cases (W1–W10), 5 brewing cases
(B1–B5), 5 library cases (L1–L5), and 5 character cases (C1–C5) —
covering things like the prior-work-penalty formula, the 40-level cap,
the optimizer beating a naive sequential combine order, correct stat
folding vs. separate conditional lines, corruption-effect routing, the
mutually-exclusive Potency/Extended validation error, batch sizes that
don't divide evenly into brew cycles, catalog filtering by
enchantment/level and by compatible-equipment set, merge plans reserving
and releasing books, a manual Used status overriding automatic
reservation, upgrade-project completion percentages, two same-type items
keeping distinct identities, equipping into an occupied slot
auto-unequipping the previous occupant, deleting an item leaving other
slots undisturbed, an export/import round-trip preserving custom
name/enchantments/stats/notes, and import renaming rather than
overwriting on a character-name collision.

The suite runs automatically the moment the page loads: results are
printed with `console.table()`, and the footer shows a live pass/fail
badge (e.g. *"self-tests: 30/30 passing (see console.table)"*).

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
  combine-order and item-stats panels in the Anvil Combiner, the brew-plan
  panel in the Brewing Planner, the catalog/projects panels in the Book
  Library, and the equipment/inventory panel in Character Profiles — so
  recalculated output is announced to assistive technology without manual
  refocus.
- Every interactive control has a visible `:focus-visible` outline, and
  `@media (prefers-reduced-motion: reduce)` disables transitions and
  animations.
- The two-column layout collapses to a single column below 900px width.
- Requires JavaScript (a `<noscript>` message explains this if it's
  disabled); no Internet Explorer support and no polyfills are included.
- Makes **zero outbound network requests** — no external fonts, scripts,
  images, or analytics of any kind. The Book Library's and Character
  Profiles' `localStorage` use is purely local browser storage, not a
  network call, and file import/export in Character Profiles (`FileReader`,
  `Blob`/`createObjectURL`) never leaves the browser either.

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
- `GearEngine`, `LibraryEngine`, and `CharacterEngine` intentionally read
  `AnvilEngine`'s item ids and enchantment maps as plain data (or leave
  that lookup to the UI layer, as `LibraryEngine` and `CharacterEngine`
  both do) rather than importing `AnvilEngine`'s internals — keep that
  separation when extending any engine.
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
