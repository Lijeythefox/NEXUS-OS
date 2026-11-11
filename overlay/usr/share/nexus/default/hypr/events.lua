-- Keeps the workspace dots in the top bar up to date: whenever a workspace or
-- window changes, the bar is told to redraw them. Nothing runs in between.

local function refresh_bar()
    hl.exec_cmd("pkill -RTMIN+8 -x waybar")
end

for _, event in ipairs({
    "workspace.active",
    "window.open",
    "window.close",
    "window.move_to_workspace",
    "monitor.focused",
}) do
    hl.on(event, refresh_bar)
end
