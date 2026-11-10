-- Keyboard shortcuts. SUPER is the Windows key.
-- Add your own in ~/.config/hypr/hyprland.lua, below the line that loads the defaults.

local mod = "SUPER"

local function run(command)
    return hl.dsp.exec_cmd(command)
end

-- Apps and menus
hl.bind(mod .. " + space",                run("nexus-launcher"))
hl.bind(mod .. " + ALT + space",          run("nexus-menu"))
hl.bind(mod .. " + K",                    run("nexus-keys"))
hl.bind(mod .. " + Return",               run("foot"))
hl.bind(mod .. " + SHIFT + B",            run("nexus-open browser"))
hl.bind(mod .. " + SHIFT + F",            run("nexus-open files"))
hl.bind(mod .. " + SHIFT + C",            run("nexus-open code"))
hl.bind(mod .. " + G",                    run("nexus-open games"))
hl.bind(mod .. " + Escape",               run("nexus-power"))
hl.bind(mod .. " + CTRL + space",         run("nexus-wallpaper next"))
hl.bind(mod .. " + SHIFT + CTRL + space", run("nexus-menu theme"))
hl.bind(mod .. " + SHIFT + K",            run("nexus-open keyboard"))
hl.bind("Print",                          run("nexus-screenshot full"))
hl.bind("SHIFT + Print",                  run("nexus-screenshot area"))

-- Windows
hl.bind(mod .. " + W", hl.dsp.window.close())
hl.bind(mod .. " + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
hl.bind(mod .. " + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mod .. " + J", hl.dsp.layout("togglesplit"))

for _, direction in ipairs({ "left", "right", "up", "down" }) do
    hl.bind(mod .. " + " .. direction,         hl.dsp.focus({ direction = direction }))
    hl.bind(mod .. " + SHIFT + " .. direction, hl.dsp.window.swap({ direction = direction }))
end

-- Workspaces 1 to 5
for number = 1, 5 do
    hl.bind(mod .. " + " .. number,         hl.dsp.focus({ workspace = number }))
    hl.bind(mod .. " + SHIFT + " .. number, hl.dsp.window.move({ workspace = number }))
end
hl.bind(mod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mod .. " + mouse_up",   hl.dsp.focus({ workspace = "e-1" }))

-- Hold SUPER and drag: left button moves a window, right button resizes it.
hl.bind(mod .. " + mouse:272", hl.dsp.window.drag(),   { mouse = true })
hl.bind(mod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Volume, brightness and media keys (these also work on the lock screen).
hl.bind("XF86AudioRaiseVolume",  run("nexus-osd volume up"),       { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume",  run("nexus-osd volume down"),     { locked = true, repeating = true })
hl.bind("XF86AudioMute",         run("nexus-osd volume mute"),     { locked = true })
hl.bind("XF86AudioMicMute",      run("nexus-osd mic mute"),        { locked = true })
hl.bind("XF86MonBrightnessUp",   run("nexus-osd brightness up"),   { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", run("nexus-osd brightness down"), { locked = true, repeating = true })
hl.bind("XF86AudioNext",         run("playerctl next"),            { locked = true })
hl.bind("XF86AudioPrev",         run("playerctl previous"),        { locked = true })
hl.bind("XF86AudioPlay",         run("playerctl play-pause"),      { locked = true })
hl.bind("XF86AudioPause",        run("playerctl play-pause"),      { locked = true })
