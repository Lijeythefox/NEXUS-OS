-- Keyboard, mouse and touchpad.

hl.config({
    input = {
        kb_layout          = "us",
        follow_mouse       = 1,
        sensitivity        = 0,
        repeat_rate        = 40,
        repeat_delay       = 300,
        numlock_by_default = true,

        touchpad = {
            natural_scroll = true,
        },
    },
})

-- Three-finger swipe left/right changes workspace.
hl.gesture({
    fingers   = 3,
    direction = "horizontal",
    action    = "workspace",
})
