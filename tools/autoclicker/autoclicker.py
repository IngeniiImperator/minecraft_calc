#!/usr/bin/env python3
"""AFK autoclicker — the Minecraft Calc companion tool.

Clicks one mouse button at a fixed interval while toggled on with a
global hotkey. Built for click-based AFK farms in Minecraft: Java
Edition (fish farms above all — a right click every ~1,200 ms), but it
is a generic fixed-pace clicker with no game integration of any kind.

Design rules, in order:

  * Starts PAUSED — it never clicks until you press the toggle key.
  * The toggle key (F6 by default) starts and stops clicking; the quit
    key (F7 by default) and Ctrl+C in the terminal both exit outright.
  * Optional --max-clicks / --max-minutes auto-stops for walking away.
  * Clicks go to whatever window has focus, at the current cursor
    position — exactly like a human clicking. No window targeting, no
    memory reading, no randomized "humanizing" jitter: it presses the
    button you chose, at the pace you chose, and nothing else.
  * No network access, no config files, no admin rights.

Requires Python 3.8+ and the `pynput` package:

    python3 -m pip install pynput      (Windows: py -m pip install pynput)

Platform notes: works on Windows and macOS (grant your terminal app
Accessibility permission when macOS asks); on Linux it needs X11 —
most Wayland sessions block synthetic input by design.

Play fair: use it in singleplayer, or on Realms/servers whose rules
allow AFK and automation devices. Many public servers do not.

The AFK Clicker tab in ../../index.html builds a command line for this
script; keep the defaults and limits below in sync with ClickerEngine
there (the K self-tests pin the engine side).
"""

from __future__ import annotations

import argparse
import sys
import threading
import time

# Keep in sync with ClickerEngine.LIMITS / DEFAULTS in index.html.
INTERVAL_MIN_MS = 100
INTERVAL_MAX_MS = 3_600_000
BUTTONS = ('left', 'right', 'middle')
DEFAULTS = {
    'interval_ms': 1200,        # the commonly recommended AFK-fish-farm pacing
    'button': 'right',          # fishing rods cast/reel with the *right* button
    'toggle_key': 'f6',
    'quit_key': 'f7',
}

# Latency ceiling for noticing a toggle while paused (seconds).
IDLE_POLL_S = 0.05

# Named non-character keys the CLI accepts. F1/F2/F3/F5/F11 are listed
# for completeness but vanilla Minecraft already binds them (hide GUI,
# screenshot, debug, perspective, fullscreen) — F6–F10 are free.
NAMED_KEYS = frozenset(
    ['esc', 'insert', 'delete', 'home', 'end', 'page_up', 'page_down',
     'pause', 'scroll_lock'] + [f'f{n}' for n in range(1, 25)])


def key_name(raw):
    """Normalizes and validates a key argument ('F6' → 'f6').

    Accepts the named keys above or any single printable character.
    Raises argparse.ArgumentTypeError otherwise, so it can be used as an
    argparse `type=`.
    """
    name = str(raw).strip().lower()
    if name in NAMED_KEYS:
        return name
    if len(name) == 1 and name.isprintable() and not name.isspace():
        return name
    raise argparse.ArgumentTypeError(
        f'unknown key {raw!r} — use f1…f24, esc, insert, delete, home, end, '
        f'page_up, page_down, pause, scroll_lock, or a single character')


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog='autoclicker.py',
        description='Fixed-interval autoclicker with a global on/off hotkey. '
                    'Starts paused; press the toggle key in-game to begin.',
        epilog='Example (AFK fish farm): '
               '%(prog)s --interval-ms 1200 --button right')
    p.add_argument('--interval-ms', type=int, default=DEFAULTS['interval_ms'],
                   help='milliseconds between clicks, '
                        f'{INTERVAL_MIN_MS}–{INTERVAL_MAX_MS} '
                        '(default: %(default)s)')
    p.add_argument('--button', choices=BUTTONS, default=DEFAULTS['button'],
                   help='mouse button to click (default: %(default)s — '
                        'Minecraft fishing rods use the right button)')
    p.add_argument('--toggle-key', type=key_name, default=DEFAULTS['toggle_key'],
                   metavar='KEY', help='global key that starts/stops clicking '
                                       '(default: %(default)s)')
    p.add_argument('--quit-key', type=key_name, default=DEFAULTS['quit_key'],
                   metavar='KEY', help='global key that exits the program '
                                       '(default: %(default)s; Ctrl+C always works)')
    p.add_argument('--max-clicks', type=int, default=0, metavar='N',
                   help='auto-stop after N clicks (default: 0 = no limit)')
    p.add_argument('--max-minutes', type=float, default=0, metavar='N',
                   help='auto-stop N minutes after launch (default: 0 = no limit)')
    args = p.parse_args(argv)

    if not INTERVAL_MIN_MS <= args.interval_ms <= INTERVAL_MAX_MS:
        p.error(f'--interval-ms must be between {INTERVAL_MIN_MS} and '
                f'{INTERVAL_MAX_MS}')
    if args.toggle_key == args.quit_key:
        p.error('--toggle-key and --quit-key must be different')
    if args.max_clicks < 0:
        p.error('--max-clicks must be 0 (no limit) or a positive number')
    if args.max_minutes < 0:
        p.error('--max-minutes must be 0 (no limit) or a positive number')
    return args


class AutoClicker:
    """The click loop: fires `click_fn` every `interval_s` seconds while
    toggled on, until quit or an optional limit is reached.

    Pure scheduling — the actual mouse press is the injected `click_fn`,
    and `monotonic` is injectable too, so the whole class is unit-testable
    without pynput, a display, or real mouse movement.
    """

    def __init__(self, interval_s, click_fn, *, max_clicks=0, max_seconds=0.0,
                 monotonic=time.monotonic):
        self.interval_s = interval_s
        self.click_fn = click_fn
        self.max_clicks = max_clicks
        self.max_seconds = max_seconds
        self.monotonic = monotonic
        self.clicks = 0
        self.stop_reason = None
        self._on = threading.Event()
        self._quit = threading.Event()

    @property
    def on(self):
        return self._on.is_set()

    def toggle(self):
        """Flips clicking on/off; returns the new state."""
        if self._on.is_set():
            self._on.clear()
        else:
            self._on.set()
        return self._on.is_set()

    def quit(self, reason='stopped'):
        if self.stop_reason is None:
            self.stop_reason = reason
        self._quit.set()

    def run(self):
        """Blocks until quit() is called or a limit trips. Returns total
        clicks. Pacing is click-to-click: each wait starts after the
        click, and toggling on fires the first click immediately."""
        started = self.monotonic()
        while not self._quit.is_set():
            if self.max_seconds and self.monotonic() - started >= self.max_seconds:
                self.quit('time limit reached')
                break
            if not self._on.is_set():
                self._quit.wait(IDLE_POLL_S)
                continue
            self.click_fn()
            self.clicks += 1
            if self.max_clicks and self.clicks >= self.max_clicks:
                self.quit('click limit reached')
                break
            self._quit.wait(self.interval_s)
        return self.clicks


def _resolve_key(keyboard, name):
    """Maps a normalized key name to a pynput key object."""
    if len(name) == 1:
        return keyboard.KeyCode.from_char(name)
    return getattr(keyboard.Key, name)


def _key_matches(pressed, wanted):
    """True when the pressed pynput key is the configured one. Character
    keys compare case-insensitively so Shift doesn't defeat the hotkey."""
    if pressed == wanted:
        return True
    have = getattr(pressed, 'char', None)
    want = getattr(wanted, 'char', None)
    return have is not None and want is not None and have.lower() == want


def _stamp():
    return time.strftime('%H:%M:%S')


def main(argv=None):
    args = parse_args(argv)
    try:
        from pynput import keyboard, mouse
    except ImportError:
        print('This tool needs the pynput package (the one dependency).\n'
              '  Install it with:  python3 -m pip install pynput\n'
              '  (Windows:         py -m pip install pynput)', file=sys.stderr)
        return 2

    controller = mouse.Controller()
    button = getattr(mouse.Button, args.button)
    clicker = AutoClicker(args.interval_ms / 1000.0,
                          lambda: controller.click(button),
                          max_clicks=args.max_clicks,
                          max_seconds=args.max_minutes * 60.0)
    toggle_key = _resolve_key(keyboard, args.toggle_key)
    quit_key = _resolve_key(keyboard, args.quit_key)

    def on_press(key):
        if _key_matches(key, quit_key):
            clicker.quit(f'quit key ({args.quit_key})')
            return False                      # also stops the listener
        if _key_matches(key, toggle_key):
            state = clicker.toggle()
            print(f'[{_stamp()}] {"ON — clicking" if state else "OFF — paused"} '
                  f'({clicker.clicks} click{"s" if clicker.clicks != 1 else ""} so far)',
                  flush=True)
        return None

    limits = []
    if args.max_clicks:
        limits.append(f'after {args.max_clicks} clicks')
    if args.max_minutes:
        limits.append(f'{args.max_minutes:g} minutes after launch')
    print('AFK autoclicker — minecraft_calc companion\n'
          f'  button    : {args.button}\n'
          f'  interval  : {args.interval_ms} ms '
          f'(~{60000 / args.interval_ms:.1f} clicks/minute)\n'
          f'  toggle key: {args.toggle_key}  (start/stop clicking)\n'
          f'  quit key  : {args.quit_key}  (exit — Ctrl+C here also works)\n'
          f'  auto-stop : {" and ".join(limits) if limits else "none — runs until you stop it"}\n'
          'Clicks go to whichever window has focus, at the current cursor\n'
          'position. Starts PAUSED: focus Minecraft, line up your cast, then\n'
          f'press {args.toggle_key}.', flush=True)

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    try:
        clicker.run()
    except KeyboardInterrupt:
        clicker.quit('Ctrl+C')
    finally:
        listener.stop()
    print(f'[{_stamp()}] done — {clicker.clicks} '
          f'click{"s" if clicker.clicks != 1 else ""} total ({clicker.stop_reason}).',
          flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
