import os
import socket
import sys

from nexus.common import Settings, notify, runtime_dir

LAYOUTS = {
    "stack": ("Stack", "Windows style: windows overlap. Drag one to a screen edge to snap it."),
    "split": ("Split", "Omarchy style: windows tile side by side automatically, the newest one gets the big space."),
}
COMMANDS = ("reload", "layout", "left", "right", "up", "down",
            "swap-left", "swap-right", "swap-up", "swap-down", "main", "float", "close")
ALWAYS_FLOAT = {"onboard", "conky", "xfce4-panel", "wrapper-2.0", "xfce4-notifyd", "nexus-quick-settings",
                "xfce4-screenshooter", "pavucontrol", "lightdm-gtk-greeter"}


def socket_path():
    return str(runtime_dir() / "tiler.sock")


def layout():
    value = Settings().get("WINDOW_LAYOUT", "stack")
    return value if value in LAYOUTS else "stack"


def split_enabled():
    return layout() == "split"


def set_layout(value):
    Settings().set("WINDOW_LAYOUT", value if value in LAYOUTS else "stack")
    send("reload")
    return True


def set_split(value):
    return set_layout("split" if value else "stack")


def send(command):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        client.sendto(command.encode("utf-8"), socket_path())
        return True
    except OSError:
        return False
    finally:
        client.close()


def toggle_layout():
    new = "stack" if split_enabled() else "split"
    set_layout(new)
    notify(f"Window layout: {LAYOUTS[new][0]}", LAYOUTS[new][1], icon="view-dual-symbolic")


def send_main(argv):
    if not argv or argv[0] not in COMMANDS:
        print("usage: nexus-tile " + "|".join(COMMANDS), file=sys.stderr)
        return 2
    if argv[0] == "layout":
        toggle_layout()
        return 0
    return 0 if send(argv[0]) else 1


def split_rects(count, area, gap, ratio):
    x, y, width, height = area
    if count <= 0:
        return []
    if count == 1:
        return [(x + gap, y + gap, width - 2 * gap, height - 2 * gap)]
    main_width = round((width - 3 * gap) * ratio)
    rects = [(x + gap, y + gap, main_width, height - 2 * gap)]
    stack_x = x + 2 * gap + main_width
    stack_width = width - 3 * gap - main_width
    rows = count - 1
    row_height = (height - gap * (rows + 1)) / rows
    for index in range(rows):
        top = y + gap + round(index * (row_height + gap))
        rects.append((stack_x, top, stack_width, round(row_height)))
    return rects


def neighbour(current, others, direction):
    cx, cy, cw, ch = current
    centre = (cx + cw / 2, cy + ch / 2)
    best, best_score = None, None
    for key, (x, y, w, h) in others:
        dx = x + w / 2 - centre[0]
        dy = y + h / 2 - centre[1]
        ahead = {"left": -dx, "right": dx, "up": -dy, "down": dy}[direction]
        if ahead <= 1:
            continue
        side = abs(dy) if direction in ("left", "right") else abs(dx)
        score = ahead + side * 2
        if best_score is None or score < best_score:
            best, best_score = key, score
    return best


class Tiler:
    def __init__(self):
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        gi.require_version("GdkX11", "3.0")
        gi.require_version("Wnck", "3.0")
        from gi.repository import Gdk, GdkX11, Gio, GLib, Gtk, Wnck

        self.Gdk, self.GdkX11, self.GLib, self.Wnck = Gdk, GdkX11, GLib, Wnck
        Wnck.set_client_type(Wnck.ClientType.PAGER)
        self.screen = Wnck.Screen.get_default()
        self.screen.force_update()
        self.order = []
        self.floating = set()
        self.fresh = set()
        self.pending = 0
        self.settings = Settings()
        self.layout = "stack"
        self.load_settings()
        self.screen.connect("window-opened", self.on_opened)
        self.screen.connect("window-closed", self.on_closed)
        self.screen.connect("active-workspace-changed", lambda *_: self.schedule())
        for window in self.screen.get_windows():
            self.watch(window)
            self.order.append(window.get_xid())
        self.monitor = Gio.File.new_for_path(str(self.settings.path)).monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.monitor.connect("changed", lambda *_: self.reload())
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        path = socket_path()
        if os.path.exists(path):
            os.unlink(path)
        self.server.bind(path)
        GLib.io_add_watch(self.server.fileno(), GLib.PRIORITY_DEFAULT, GLib.IO_IN, self.on_command)
        if self.layout == "split":
            self.fresh = set(self.order)
            self.schedule()

    def load_settings(self):
        self.settings.load()
        self.layout = layout()
        self.gap = max(0, min(32, self.settings.get_int("TILE_GAP", 6)))
        self.ratio = max(0.3, min(0.75, self.settings.get_int("TILE_MAIN", 55) / 100))

    def reload(self):
        before = self.layout
        self.load_settings()
        if self.layout == "split" and before != "split":
            self.fresh = {window.get_xid() for window in self.screen.get_windows()}
        self.schedule()

    def watch(self, window):
        window.connect("state-changed", lambda *_: self.schedule())
        window.connect("workspace-changed", lambda *_: self.schedule())

    def on_opened(self, screen, window):
        self.watch(window)
        xid = window.get_xid()
        if xid not in self.order:
            self.order.insert(0, xid)
        self.fresh.add(xid)
        self.schedule()

    def on_closed(self, screen, window):
        xid = window.get_xid()
        self.order = [item for item in self.order if item != xid]
        self.floating.discard(xid)
        self.fresh.discard(xid)
        self.schedule()

    def schedule(self):
        if self.pending:
            self.GLib.source_remove(self.pending)
        self.pending = self.GLib.timeout_add(200, self.retile)

    def timestamp(self):
        return self.GdkX11.x11_get_server_time(self.Gdk.get_default_root_window())

    def workarea(self):
        display = self.Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        area = monitor.get_workarea()
        return area.x, area.y, area.width, area.height

    def tileable(self, window, workspace):
        Wnck = self.Wnck
        if window.get_window_type() != Wnck.WindowType.NORMAL or window.is_skip_tasklist():
            return False
        if window.is_minimized() or window.is_fullscreen() or window.get_transient() is not None:
            return False
        if workspace is not None and not window.is_on_workspace(workspace):
            return False
        names = {(window.get_class_instance_name() or "").lower(), (window.get_class_group_name() or "").lower()}
        if names & ALWAYS_FLOAT or window.get_xid() in self.floating:
            return False
        if window.is_maximized() and window.get_xid() not in self.fresh:
            return False
        return True

    def tiled_windows(self):
        workspace = self.screen.get_active_workspace()
        windows = {window.get_xid(): window for window in self.screen.get_windows() if self.tileable(window, workspace)}
        for xid in windows:
            if xid not in self.order:
                self.order.append(xid)
        return [windows[xid] for xid in self.order if xid in windows]

    def place(self, window, rect):
        Wnck = self.Wnck
        if window.is_maximized():
            window.unmaximize()
        x, y, width, height = rect
        mask = (Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y
                | Wnck.WindowMoveResizeMask.WIDTH | Wnck.WindowMoveResizeMask.HEIGHT)
        window.set_geometry(Wnck.WindowGravity.STATIC, mask, x, y, max(120, width), max(90, height))

    def retile(self):
        self.pending = 0
        if self.layout != "split":
            self.fresh.clear()
            return False
        windows = self.tiled_windows()
        for window, rect in zip(windows, split_rects(len(windows), self.workarea(), self.gap, self.ratio)):
            self.place(window, rect)
        self.fresh.clear()
        return False

    def on_command(self, fd, condition):
        try:
            command = self.server.recv(64).decode("utf-8", "replace").strip()
        except OSError:
            return True
        try:
            self.handle(command)
        except Exception as error:
            print(f"nexus-tiler: {command}: {error}", file=sys.stderr)
        return True

    def handle(self, command):
        if command == "reload":
            self.reload()
            return
        active = self.screen.get_active_window()
        if active is None:
            return
        if command == "close":
            active.close(self.timestamp())
        elif command in ("left", "right", "up", "down"):
            if self.layout == "split":
                self.focus(active, command)
            else:
                self.snap(active, command)
        elif command.startswith("swap-") and self.layout == "split":
            self.swap(active, command[5:])
        elif command == "main" and self.layout == "split":
            xid = active.get_xid()
            self.floating.discard(xid)
            self.order = [xid] + [item for item in self.order if item != xid]
            self.retile()
        elif command == "float" and self.layout == "split":
            xid = active.get_xid()
            if xid in self.floating:
                self.floating.discard(xid)
                active.unmake_above()
            else:
                self.floating.add(xid)
                x, y, width, height = self.workarea()
                self.place(active, (x + width // 6, y + height // 8, width * 2 // 3, height * 3 // 4))
                active.make_above()
            self.retile()

    def others(self, active):
        workspace = self.screen.get_active_workspace()
        return [(window, window.get_geometry()) for window in self.screen.get_windows()
                if window is not active and self.tileable(window, workspace)]

    def focus(self, active, direction):
        target = neighbour(active.get_geometry(), self.others(active), direction)
        if target is not None:
            target.activate(self.timestamp())

    def swap(self, active, direction):
        target = neighbour(active.get_geometry(), self.others(active), direction)
        if target is None:
            return
        a, b = active.get_xid(), target.get_xid()
        if a in self.order and b in self.order:
            i, j = self.order.index(a), self.order.index(b)
            self.order[i], self.order[j] = b, a
            self.retile()

    def snap(self, window, direction):
        x, y, width, height = self.workarea()
        if direction == "up":
            window.maximize()
        elif direction == "down":
            if window.is_maximized():
                window.unmaximize()
            else:
                window.minimize()
        elif direction == "left":
            self.place(window, (x, y, width // 2, height))
        else:
            self.place(window, (x + width // 2, y, width - width // 2, height))


def main(argv=None):
    import gi

    gi.require_version("GLib", "2.0")
    from gi.repository import GLib

    if send("reload"):
        print("nexus-tiler is already running", file=sys.stderr)
        return 0
    Tiler()
    GLib.MainLoop().run()
    return 0
