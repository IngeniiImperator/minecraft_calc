# minecraft_calc

Two Minecraft (Java Edition 1.21.x) planning calculators in **one self-contained
HTML file** — no build step, no network, no dependencies. Open `index.html` in a
browser.

## Modules (tab switcher)

- **Anvil Combiner** — finds the cheapest order to combine enchanted books onto an
  item. Exhaustive search over every combine tree (item + up to 7 books), with
  prior-work penalties, book/item multipliers, conflict handling, and the 40-level
  "Too Expensive" cap. Enchantment combining only; repairs and renames are out of
  scope.
- **Brewing Planner** — builds shopping lists of potions (including splash,
  lingering, and tipped arrows), pools bottles across all targets into shared brew
  cycles, and outputs total cycles, elapsed time, blaze-powder fuel, a consolidated
  bill of materials, and spare-slot hints. Brewing involves no XP and no anvil
  interaction; potion durations shown are display-only flavor.

Each module's engine is an independent pure-function namespace (`AnvilEngine`,
`BrewEngine`); they share only the CSS theme and generic UI helpers.

## Self-tests

`run_self_tests()` runs on page load, executes both suites (anvil T1–T5 and
brewing B1–B5), and `console.table`s all results. The footer shows a pass/fail
badge. Headless run:

```sh
node -e "const m=require('fs').readFileSync('index.html','utf8').match(/<script>\n([\s\S]*?)<\/script>/);
require('fs').writeFileSync('/tmp/mc.js',m[1]);
const r=require('/tmp/mc.js').run_self_tests();
process.exit(r.every(x=>x.pass==='PASS')?0:1)"
```
