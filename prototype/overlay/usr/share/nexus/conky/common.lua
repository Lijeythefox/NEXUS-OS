local M = {}

local home = os.getenv('HOME') or ''

function M.read(path)
  local handle = io.open(path, 'r')
  if not handle then
    return nil
  end
  local value = handle:read('*l')
  handle:close()
  return value
end

function M.command(cmd)
  local handle = io.popen(cmd .. ' 2>/dev/null')
  if not handle then
    return nil
  end
  local value = handle:read('*l')
  handle:close()
  return value
end

function M.setting(key, default)
  local handle = io.open(home .. '/.config/nexus/settings.conf', 'r')
  if not handle then
    return default
  end
  for line in handle:lines() do
    local found, value = line:match('^([%w_]+)=(.*)$')
    if found == key then
      handle:close()
      return value
    end
  end
  handle:close()
  return default
end

function M.colors()
  local path = home .. '/.config/nexus/conky-colors.lua'
  local ok, colors = pcall(dofile, path)
  if ok and type(colors) == 'table' then
    return colors
  end
  os.execute('nexus-theme apply')
  ok, colors = pcall(dofile, path)
  if ok and type(colors) == 'table' then
    return colors
  end
  error('NEXUS colours are missing; run nexus-theme apply')
end

function M.scale()
  return tonumber(os.getenv('NEXUS_HUD_SCALE') or '1') or 1
end

function M.font(size)
  return '${font Share Tech Mono:size=' .. math.floor(size * M.scale() + 0.5) .. '}'
end

function M.config(width, height)
  local c = M.colors()
  local scale = M.scale()
  local ontop = os.getenv('NEXUS_HUD_ONTOP') == '1'
  return {
    alignment = os.getenv('NEXUS_HUD_ALIGN') or 'top_right',
    gap_x = tonumber(os.getenv('NEXUS_HUD_GAP_X') or '16'),
    gap_y = tonumber(os.getenv('NEXUS_HUD_GAP_Y') or '16'),
    minimum_width = math.floor(width * scale),
    maximum_width = math.floor(width * scale),
    minimum_height = math.floor(height * scale),
    own_window = true,
    own_window_class = 'NexusHUD',
    own_window_title = 'NEXUS HUD',
    own_window_type = 'normal',
    own_window_hints = 'undecorated,sticky,skip_taskbar,skip_pager,' .. (ontop and 'above' or 'below'),
    own_window_argb_visual = true,
    own_window_argb_value = 205,
    own_window_colour = c.bg,
    double_buffer = true,
    use_xft = true,
    font = 'Share Tech Mono:size=' .. math.floor(10 * scale + 0.5),
    override_utf8_locale = true,
    draw_shades = false,
    draw_outline = false,
    draw_borders = true,
    border_width = 1,
    border_inner_margin = math.floor(10 * scale),
    default_color = c.border,
    color0 = c.primary,
    color1 = c.text,
    color2 = c.dim,
    color3 = c.secondary,
    color4 = c.alert,
    color5 = c.grid,
    default_bar_height = math.floor(6 * scale),
    default_graph_height = math.floor(22 * scale),
    update_interval = 2,
    cpu_avg_samples = 2,
    net_avg_samples = 2,
    no_buffers = true,
    text_buffer_size = 512,
    use_spacer = 'none',
  }
end

return M
