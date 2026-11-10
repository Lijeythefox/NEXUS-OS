-- Rules for windows and for the bar, launcher and notifications.

hl.window_rule({
    name  = "suppress-maximize-events",
    match = { class = ".*" },
    suppress_event = "maximize",
})

hl.window_rule({
    name  = "fix-xwayland-drags",
    match = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
    },
    no_focus = true,
})

-- Frosted-glass blur behind the bar, launcher, notifications and volume pop-up.
for _, namespace in ipairs({ "waybar", "launcher", "notifications", "swayosd" }) do
    hl.layer_rule({
        name         = "blur-" .. namespace,
        match        = { namespace = "^" .. namespace .. "$" },
        blur         = true,
        ignore_alpha = 0.2,
    })
end
