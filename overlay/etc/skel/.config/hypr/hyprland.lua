-- Your Hyprland settings.
--
-- The first line loads all the NEXUS OS defaults (shortcuts, animations, theme).
-- Anything you add BELOW it wins over the defaults. Save the file and it applies at once.
-- If something breaks, delete your lines or run:  hyprctl configerrors

dofile("/usr/share/nexus/default/hypr/nexus.lua")

-- Examples (remove the two dashes at the start of a line to switch it on):
--
-- hl.bind("SUPER + B", hl.dsp.exec_cmd("chromium"))        -- your own shortcut
-- hl.config({ general = { gaps_in = 8, gaps_out = 16 } })  -- bigger gaps
-- hl.config({ decoration = { rounding = 14 } })            -- rounder corners
-- hl.config({ animations = { enabled = false } })          -- no animations
