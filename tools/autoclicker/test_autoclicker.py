"""Unit tests for the AFK autoclicker's argument parsing and click loop.

Standard library only — pynput is imported lazily inside main(), so
everything here runs on a machine with no pynput, no display, and no
mouse. Run from this directory (or the repo root) with:

    python3 -m unittest discover tools/autoclicker
"""

import argparse
import threading
import time
import unittest

from autoclicker import (AutoClicker, DEFAULTS, INTERVAL_MAX_MS,
                         INTERVAL_MIN_MS, key_name, parse_args)


def wait_until(cond, timeout=2.0):
    """Polls `cond` until true or the deadline passes; returns the result."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if cond():
            return True
        time.sleep(0.005)
    return cond()


class TestKeyName(unittest.TestCase):
    def test_named_keys_normalize(self):
        self.assertEqual(key_name('F6'), 'f6')
        self.assertEqual(key_name(' esc '), 'esc')
        self.assertEqual(key_name('page_up'), 'page_up')

    def test_single_characters_allowed(self):
        self.assertEqual(key_name('A'), 'a')
        self.assertEqual(key_name('.'), '.')

    def test_junk_rejected(self):
        for bad in ('ff', '', '  ', 'control', 'f25'):
            with self.assertRaises(argparse.ArgumentTypeError):
                key_name(bad)


class TestParseArgs(unittest.TestCase):
    def test_defaults_match_documented_fish_farm_setup(self):
        args = parse_args([])
        self.assertEqual(args.interval_ms, DEFAULTS['interval_ms'])
        self.assertEqual(args.interval_ms, 1200)
        self.assertEqual(args.button, 'right')
        self.assertEqual(args.toggle_key, 'f6')
        self.assertEqual(args.quit_key, 'f7')
        self.assertEqual(args.max_clicks, 0)
        self.assertEqual(args.max_minutes, 0)

    def test_explicit_values(self):
        args = parse_args(['--interval-ms', '2500', '--button', 'left',
                           '--toggle-key', 'F8', '--quit-key', 'esc',
                           '--max-clicks', '500', '--max-minutes', '90'])
        self.assertEqual(args.interval_ms, 2500)
        self.assertEqual(args.button, 'left')
        self.assertEqual(args.toggle_key, 'f8')
        self.assertEqual(args.quit_key, 'esc')
        self.assertEqual(args.max_clicks, 500)
        self.assertEqual(args.max_minutes, 90.0)

    def assert_usage_error(self, argv):
        with self.assertRaises(SystemExit) as ctx:
            parse_args(argv)
        self.assertEqual(ctx.exception.code, 2)

    def test_interval_bounds_enforced(self):
        self.assert_usage_error(['--interval-ms', str(INTERVAL_MIN_MS - 1)])
        self.assert_usage_error(['--interval-ms', str(INTERVAL_MAX_MS + 1)])
        parse_args(['--interval-ms', str(INTERVAL_MIN_MS)])   # boundaries OK
        parse_args(['--interval-ms', str(INTERVAL_MAX_MS)])

    def test_bad_values_rejected(self):
        self.assert_usage_error(['--button', 'side4'])
        self.assert_usage_error(['--toggle-key', 'notakey'])
        self.assert_usage_error(['--toggle-key', 'f6', '--quit-key', 'f6'])
        self.assert_usage_error(['--max-clicks', '-1'])
        self.assert_usage_error(['--max-minutes', '-0.5'])


class TestAutoClicker(unittest.TestCase):
    def run_in_thread(self, clicker):
        thread = threading.Thread(target=clicker.run, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 2.0)
        self.addCleanup(clicker.quit, 'test cleanup')
        return thread

    def test_starts_paused_and_toggle_gates_clicking(self):
        clicks = []
        clicker = AutoClicker(0.005, lambda: clicks.append(1))
        self.run_in_thread(clicker)

        time.sleep(0.1)                               # ~20 intervals' worth
        self.assertEqual(len(clicks), 0, 'clicked while paused')
        self.assertFalse(clicker.on)

        self.assertTrue(clicker.toggle())
        self.assertTrue(wait_until(lambda: len(clicks) >= 3),
                        'did not click after toggling on')

        self.assertFalse(clicker.toggle())
        wait_until(lambda: not clicker.on, 0.2)       # let a wait cycle drain
        time.sleep(0.05)
        frozen = len(clicks)
        time.sleep(0.1)
        self.assertLessEqual(len(clicks), frozen + 1,
                             'kept clicking after toggling off')

    def test_quit_stops_run_and_records_reason(self):
        clicker = AutoClicker(0.005, lambda: None)
        thread = self.run_in_thread(clicker)
        clicker.quit('quit key (f7)')
        thread.join(2.0)
        self.assertFalse(thread.is_alive())
        self.assertEqual(clicker.stop_reason, 'quit key (f7)')

    def test_max_clicks_stops_exactly_at_limit(self):
        clicks = []
        clicker = AutoClicker(0.001, lambda: clicks.append(1), max_clicks=5)
        clicker.toggle()
        total = clicker.run()                         # returns when limit trips
        self.assertEqual(total, 5)
        self.assertEqual(len(clicks), 5)
        self.assertEqual(clicker.stop_reason, 'click limit reached')

    def test_max_seconds_uses_injected_clock(self):
        fake_now = [0.0]

        def click():
            fake_now[0] += 30.0                       # each click "takes" 30 s

        clicker = AutoClicker(0.001, click, max_seconds=60.0,
                              monotonic=lambda: fake_now[0])
        clicker.toggle()
        total = clicker.run()
        # t=0: click (→30) · t=30: click (→60) · t=60: limit trips pre-click
        self.assertEqual(total, 2)
        self.assertEqual(clicker.stop_reason, 'time limit reached')

    def test_first_stop_reason_wins(self):
        clicker = AutoClicker(0.001, lambda: None)
        clicker.quit('first')
        clicker.quit('second')
        self.assertEqual(clicker.stop_reason, 'first')


if __name__ == '__main__':
    unittest.main()
