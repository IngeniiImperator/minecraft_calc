# AFK Autoclicker (companion tool)

A fixed-interval autoclicker for click-based AFK farms in Minecraft:
Java Edition — fish farms above all. It exists because the popular
downloadable autoclickers are unauditable binaries from ad-supported
sites: this one is a single short Python file you can read top to
bottom before running, it works fully offline, needs no admin rights,
and sends nothing anywhere.

A browser cannot click for you — web pages are sandboxed away from
other applications' input, on purpose — so this script runs locally,
outside the `index.html` app. The app's **AFK Clicker** tab validates
your settings and generates the exact command line for it.

## What it does (and deliberately doesn't)

- Clicks one mouse button at a fixed interval (default: **right click
  every 1,200 ms**, the commonly recommended pacing for click-based AFK
  fish farms).
- **Starts paused.** It never clicks until you press the toggle key
  (**F6** by default). Press it again to pause. The quit key (**F7**)
  or **Ctrl+C** in its terminal exits outright.
- Optional auto-stops: `--max-clicks N` and/or `--max-minutes N`.
- Clicks go to whichever window has focus, at the current cursor
  position — exactly like a human clicking, nothing more. There is
  **no** window targeting, **no** game integration or memory reading,
  and **no** randomized "humanizing" jitter. It is a metronome for
  your mouse.

## Setup

Requires Python 3.8+ and one package, [`pynput`](https://pypi.org/project/pynput/)
(it sends the clicks and listens for the hotkeys):

```sh
python3 -m pip install pynput     # Windows: py -m pip install pynput
```

Platform notes:

- **Windows** — no special permissions. If Minecraft itself runs as
  administrator, run the terminal as administrator too, or Windows
  silently drops synthetic clicks into it.
- **macOS** — the first run triggers a prompt to grant your terminal
  **Accessibility** permission (System Settings → Privacy & Security →
  Accessibility). That prompt is the OS-level gate on synthetic input.
- **Linux** — works under X11/Xorg. Most Wayland sessions block
  synthetic input by design; if nothing clicks, log in with an X11
  session.

## Usage

From the repository root:

```sh
# AFK fish farm defaults: right click every 1200 ms, F6 toggle, F7 quit
python3 tools/autoclicker/autoclicker.py

# everything spelled out, with a 6-hour safety stop
python3 tools/autoclicker/autoclicker.py --interval-ms 1200 --button right \
    --toggle-key f6 --quit-key f7 --max-minutes 360
```

Then focus Minecraft, line up your cast, and press **F6**. The terminal
prints every toggle with a running click count, and a summary (with the
stop reason) on exit.

| Flag | Default | Meaning |
| --- | --- | --- |
| `--interval-ms` | `1200` | Milliseconds between clicks (100–3,600,000) |
| `--button` | `right` | `left`, `right`, or `middle` — fishing rods use the right button |
| `--toggle-key` | `f6` | Global start/stop key |
| `--quit-key` | `f7` | Global exit key (Ctrl+C in the terminal always works too) |
| `--max-clicks` | `0` | Auto-stop after N clicks (`0` = no limit) |
| `--max-minutes` | `0` | Auto-stop N minutes after launch (`0` = no limit) |

Keys accept `f1`–`f24`, `esc`, `insert`, `delete`, `home`, `end`,
`page_up`, `page_down`, `pause`, `scroll_lock`, or any single
character. Prefer F-keys the game leaves unbound — vanilla already uses
F1 (hide GUI), F2 (screenshot), F3 (debug), F5 (perspective), and F11
(fullscreen), which is why the web tab only offers F6–F10. A
single-character key would also fire while typing in chat.

## Fair play

Automation is fine in singleplayer and on your own Realm; many public
servers explicitly ban autoclickers and AFK devices. Check the rules of
wherever you play — that responsibility is yours, not the tool's. Note
that AFK fishing yields also vary by game version and farm design.

## Tests

The scheduling logic and argument validation are unit-tested with only
the standard library (no `pynput`, no display, no real mouse needed):

```sh
python3 -m unittest discover tools/autoclicker
```

The click loop (`AutoClicker`) takes its click function and clock as
injected parameters, which is what makes those tests possible — and
what keeps the part of the code that touches your mouse down to a
handful of obvious lines in `main()`.

Defaults and bounds are mirrored in `ClickerEngine` inside
`../../index.html` (which generates command lines for this script);
its K1–K6 self-tests pin that side. If you change a default here,
change it there too.
