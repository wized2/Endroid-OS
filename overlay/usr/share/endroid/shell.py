#!/usr/bin/env python3
"""Endroid OS shell — GTK4 UI with Material You 3 styling."""
import os
import math
import time
from datetime import datetime

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib, Pango

NOTE_PATH = "/tmp/notepad.txt"

# Material You 3 — seed green (fern)
CSS = """
window {
  background-color: #131313;
  color: #e5e2e1;
  font-family: "Cantarell", "Segoe UI", sans-serif;
}
.topbar {
  background-color: #1f1f1f;
  padding: 12px 20px;
  border-bottom: 1px solid #2c2c2c;
}
.brand {
  font-size: 18px;
  font-weight: 650;
  color: #4ade80;
}
.clock {
  font-size: 14px;
  color: #cac5c3;
  font-feature-settings: "tnum";
}
.nav {
  background-color: #1a1a1a;
  padding: 10px 12px;
  border-right: 1px solid #2c2c2c;
}
.nav button {
  background: transparent;
  color: #cac5c3;
  border: none;
  border-radius: 28px;
  padding: 12px 18px;
  margin: 4px 0;
  font-size: 14px;
  font-weight: 500;
}
.nav button:hover {
  background-color: #2c2c2c;
}
.nav button.active {
  background-color: #274833;
  color: #b6f2c6;
}
.content {
  background-color: #131313;
  padding: 20px 24px;
}
.title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #e5e2e1;
}
.card {
  background-color: #1f1f1f;
  border-radius: 20px;
  padding: 16px;
  margin-bottom: 12px;
}
.display {
  background-color: #1f1f1f;
  border-radius: 24px;
  padding: 20px 22px;
  font-size: 36px;
  font-weight: 500;
  color: #e5e2e1;
  margin-bottom: 12px;
}
.calc-grid button {
  background-color: #2c2c2c;
  color: #e5e2e1;
  border: none;
  border-radius: 999px;
  min-width: 64px;
  min-height: 56px;
  font-size: 18px;
  font-weight: 500;
  margin: 4px;
}
.calc-grid button.op {
  background-color: #274833;
  color: #b6f2c6;
}
.calc-grid button.muted {
  background-color: #3a3a3a;
  color: #cac5c3;
}
.calc-grid button.eq {
  background-color: #4ade80;
  color: #003919;
}
button.filled {
  background-color: #4ade80;
  color: #003919;
  border: none;
  border-radius: 24px;
  padding: 10px 22px;
  font-weight: 600;
}
button.tonal {
  background-color: #274833;
  color: #b6f2c6;
  border: none;
  border-radius: 24px;
  padding: 10px 22px;
  font-weight: 600;
}
button.text {
  background: transparent;
  color: #4ade80;
  border: none;
  border-radius: 24px;
  padding: 10px 16px;
}
textview, textview text {
  background-color: #1f1f1f;
  color: #e5e2e1;
  border-radius: 16px;
  padding: 12px;
  font-size: 15px;
}
.timer-big {
  font-size: 48px;
  font-weight: 600;
  color: #4ade80;
  padding: 24px;
}
.hint {
  color: #938f8e;
  font-size: 13px;
}
.sysmono {
  font-family: monospace;
  font-size: 13px;
  color: #cac5c3;
}
.app-tile {
  background-color: #1f1f1f;
  border-radius: 24px;
  padding: 18px;
  min-width: 140px;
  min-height: 100px;
  border: none;
}
.app-tile:hover {
  background-color: #2c2c2c;
}
.app-tile label {
  color: #e5e2e1;
  font-weight: 600;
}
"""


def read_sysinfo():
    lines = []
    try:
        with open("/proc/version") as f:
            lines.append("Kernel: " + f.read().strip()[:80])
    except Exception:
        lines.append("Kernel: ?")
    try:
        with open("/proc/uptime") as f:
            sec = int(float(f.read().split()[0]))
            h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
            lines.append(f"Uptime: {h}h {m}m {s}s")
    except Exception:
        pass
    try:
        mt = ma = 0
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    mt = int(line.split()[1]) // 1024
                elif line.startswith("MemAvailable:"):
                    ma = int(line.split()[1]) // 1024
        lines.append(f"Memory: {ma} / {mt} MB free")
    except Exception:
        pass
    try:
        with open("/proc/loadavg") as f:
            lines.append("Load: " + " ".join(f.read().split()[:3]))
    except Exception:
        pass
    try:
        model = "?"
        cpus = 0
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name") and model == "?":
                    model = line.split(":", 1)[1].strip()
                if line.startswith("processor"):
                    cpus += 1
        lines.append(f"CPU: {model}")
        lines.append(f"Cores: {cpus}")
    except Exception:
        pass
    lines.append(f"Host: {os.uname().nodename}")
    return "\n".join(lines)


class Shell(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Endroid OS")
        self.set_default_size(1024, 640)
        self.maximize()

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(root)

        # Top bar
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        top.add_css_class("topbar")
        brand = Gtk.Label(label="Endroid OS", xalign=0)
        brand.add_css_class("brand")
        top.append(brand)
        spacer = Gtk.Box(hexpand=True)
        top.append(spacer)
        self.clock = Gtk.Label(label="--:--:--")
        self.clock.add_css_class("clock")
        top.append(self.clock)
        root.append(top)

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, vexpand=True)
        root.append(body)

        # Nav
        nav = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        nav.add_css_class("nav")
        nav.set_size_request(180, -1)
        self.nav_buttons = {}
        for key, label in [
            ("home", "Home"),
            ("calc", "Calculator"),
            ("notes", "Notepad"),
            ("timer", "Timer"),
            ("sys", "System"),
        ]:
            b = Gtk.Button(label=label)
            b.connect("clicked", self._nav, key)
            nav.append(b)
            self.nav_buttons[key] = b
        body.append(nav)

        # Stack
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        body.append(self.stack)

        self.stack.add_named(self._page_home(), "home")
        self.stack.add_named(self._page_calc(), "calc")
        self.stack.add_named(self._page_notes(), "notes")
        self.stack.add_named(self._page_timer(), "timer")
        self.stack.add_named(self._page_sys(), "sys")
        self._nav(None, "home")

        GLib.timeout_add(1000, self._tick)

    def _nav(self, _btn, key):
        self.stack.set_visible_child_name(key)
        for k, b in self.nav_buttons.items():
            if k == key:
                b.add_css_class("active")
            else:
                b.remove_css_class("active")
        if key == "sys":
            self.sys_label.set_text(read_sysinfo())

    def _tick(self):
        self.clock.set_text(datetime.now().strftime("%H:%M:%S"))
        return True

    def _page_home(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("content")
        t = Gtk.Label(label="Apps", xalign=0)
        t.add_css_class("title")
        box.append(t)
        grid = Gtk.FlowBox(max_children_per_line=3, selection_mode=Gtk.SelectionMode.NONE)
        for key, title, emoji in [
            ("calc", "Calculator", "🔢"),
            ("notes", "Notepad", "📝"),
            ("timer", "Timer", "⏱"),
            ("sys", "System", "💻"),
        ]:
            b = Gtk.Button()
            b.add_css_class("app-tile")
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            inner.append(Gtk.Label(label=emoji, xalign=0))
            inner.append(Gtk.Label(label=title, xalign=0))
            b.set_child(inner)
            b.connect("clicked", self._nav, key)
            grid.append(b)
        box.append(grid)
        hint = Gtk.Label(
            label="Material You 3 · GTK4 · local only",
            xalign=0,
        )
        hint.add_css_class("hint")
        box.append(hint)
        return box

    def _page_calc(self):
        self.calc_cur = "0"
        self.calc_prev = None
        self.calc_op = None
        self.calc_fresh = True

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.add_css_class("content")
        t = Gtk.Label(label="Calculator", xalign=0)
        t.add_css_class("title")
        box.append(t)
        self.calc_display = Gtk.Label(label="0", xalign=1)
        self.calc_display.add_css_class("display")
        box.append(self.calc_display)

        grid = Gtk.Grid()
        grid.add_css_class("calc-grid")
        keys = [
            ("C", 0, 0, "muted"), ("±", 1, 0, "muted"), ("%", 2, 0, "muted"), ("/", 3, 0, "op"),
            ("7", 0, 1, ""), ("8", 1, 1, ""), ("9", 2, 1, ""), ("*", 3, 1, "op"),
            ("4", 0, 2, ""), ("5", 1, 2, ""), ("6", 2, 2, ""), ("-", 3, 2, "op"),
            ("1", 0, 3, ""), ("2", 1, 3, ""), ("3", 2, 3, ""), ("+", 3, 3, "op"),
            ("0", 0, 4, ""), (".", 2, 4, ""), ("=", 3, 4, "eq"),
        ]
        for label, x, y, cls in keys:
            b = Gtk.Button(label=label)
            if cls:
                b.add_css_class(cls)
            b.connect("clicked", self._calc_key, label)
            w = 2 if label == "0" else 1
            grid.attach(b, x, y, w, 1)
        box.append(grid)
        return box

    def _calc_key(self, _b, k):
        def setd(v):
            self.calc_cur = str(v)
            self.calc_display.set_text(self.calc_cur)

        if k == "C":
            self.calc_prev = None
            self.calc_op = None
            self.calc_fresh = True
            setd("0")
            return
        if k == "±":
            try:
                setd(-float(self.calc_cur))
            except Exception:
                pass
            return
        if k == "=":
            self._calc_compute()
            return
        if k in "+-*/%":
            if self.calc_op and not self.calc_fresh:
                self._calc_compute()
            self.calc_prev = self.calc_cur
            self.calc_op = k
            self.calc_fresh = True
            return
        if k == ".":
            if self.calc_fresh:
                setd("0.")
                self.calc_fresh = False
                return
            if "." not in self.calc_cur:
                setd(self.calc_cur + ".")
            return
        if self.calc_fresh or self.calc_cur == "0":
            setd(k)
            self.calc_fresh = False
        else:
            setd(self.calc_cur + k)

    def _calc_compute(self):
        if self.calc_prev is None or self.calc_op is None:
            return
        try:
            a = float(self.calc_prev)
            b = float(self.calc_cur)
            op = self.calc_op
            if op == "+":
                r = a + b
            elif op == "-":
                r = a - b
            elif op == "*":
                r = a * b
            elif op == "/":
                r = "Error" if b == 0 else a / b
            else:
                r = a % b
            if isinstance(r, float) and r == int(r):
                r = int(r)
            self.calc_display.set_text(str(r))
            self.calc_cur = str(r)
        except Exception:
            self.calc_display.set_text("Error")
            self.calc_cur = "0"
        self.calc_prev = None
        self.calc_op = None
        self.calc_fresh = True

    def _page_notes(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add_css_class("content")
        t = Gtk.Label(label="Notepad", xalign=0)
        t.add_css_class("title")
        box.append(t)
        self.notes = Gtk.TextView()
        self.notes.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.notes.set_vexpand(True)
        sc = Gtk.ScrolledWindow()
        sc.set_child(self.notes)
        sc.set_vexpand(True)
        sc.set_min_content_height(280)
        box.append(sc)
        row = Gtk.Box(spacing=8)
        load = Gtk.Button(label="Load")
        load.add_css_class("tonal")
        save = Gtk.Button(label="Save")
        save.add_css_class("filled")
        self.note_status = Gtk.Label(label="", xalign=0)
        self.note_status.add_css_class("hint")
        load.connect("clicked", self._notes_load)
        save.connect("clicked", self._notes_save)
        row.append(load)
        row.append(save)
        row.append(self.note_status)
        box.append(row)
        return box

    def _notes_load(self, _b):
        try:
            with open(NOTE_PATH, "r", encoding="utf-8") as f:
                text = f.read()
            self.notes.get_buffer().set_text(text)
            self.note_status.set_text("loaded")
        except FileNotFoundError:
            self.notes.get_buffer().set_text("")
            self.note_status.set_text("empty")
        except Exception as e:
            self.note_status.set_text(str(e))

    def _notes_save(self, _b):
        buf = self.notes.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
        try:
            with open(NOTE_PATH, "w", encoding="utf-8") as f:
                f.write(text)
            self.note_status.set_text("saved")
        except Exception as e:
            self.note_status.set_text(str(e))

    def _page_timer(self):
        self.timer_left = 300
        self.timer_id = None
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.add_css_class("content")
        t = Gtk.Label(label="Timer", xalign=0)
        t.add_css_class("title")
        box.append(t)
        self.timer_label = Gtk.Label(label="05:00")
        self.timer_label.add_css_class("timer-big")
        box.append(self.timer_label)
        presets = Gtk.Box(spacing=8)
        for sec, lab in [(60, "1m"), (300, "5m"), (600, "10m"), (1500, "25m")]:
            b = Gtk.Button(label=lab)
            b.add_css_class("tonal")
            b.connect("clicked", self._timer_set, sec)
            presets.append(b)
        box.append(presets)
        row = Gtk.Box(spacing=8)
        start = Gtk.Button(label="Start")
        start.add_css_class("filled")
        pause = Gtk.Button(label="Pause")
        pause.add_css_class("tonal")
        reset = Gtk.Button(label="Reset")
        reset.add_css_class("text")
        start.connect("clicked", self._timer_start)
        pause.connect("clicked", self._timer_pause)
        reset.connect("clicked", self._timer_reset)
        row.append(start)
        row.append(pause)
        row.append(reset)
        box.append(row)
        return box

    def _timer_fmt(self):
        m, s = divmod(max(0, self.timer_left), 60)
        self.timer_label.set_text(f"{m:02d}:{s:02d}")

    def _timer_set(self, _b, sec):
        self.timer_left = sec
        self._timer_fmt()

    def _timer_start(self, _b):
        if self.timer_id:
            return
        def tick():
            if self.timer_left <= 0:
                self.timer_label.set_text("Done")
                self.timer_id = None
                return False
            self.timer_left -= 1
            self._timer_fmt()
            return True
        self.timer_id = GLib.timeout_add(1000, tick)

    def _timer_pause(self, _b):
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

    def _timer_reset(self, _b):
        self._timer_pause(None)
        self.timer_left = 300
        self._timer_fmt()

    def _page_sys(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add_css_class("content")
        t = Gtk.Label(label="System", xalign=0)
        t.add_css_class("title")
        box.append(t)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.add_css_class("card")
        self.sys_label = Gtk.Label(label=read_sysinfo(), xalign=0)
        self.sys_label.add_css_class("sysmono")
        self.sys_label.set_wrap(True)
        card.append(self.sys_label)
        box.append(card)
        ref = Gtk.Button(label="Refresh")
        ref.add_css_class("filled")
        ref.connect("clicked", lambda _b: self.sys_label.set_text(read_sysinfo()))
        box.append(ref)
        return box


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="os.endroid.shell")

    def do_activate(self):
        win = Shell(self)
        win.present()


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
