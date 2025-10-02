# Workspace Page - Visual Layout Guide

## Page Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TOP NAVIGATION BAR                              │
│  [Logo] CoSim          Projects  Workspaces         [User Menu ▼]      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      ENHANCED HEADER CARD                               │
│  ╔═══════════════════════════════════════════════════════════════════╗  │
│  ║  [🎁] Project Name (Gradient Text)        [Workspace: Main ▼]   ║  │
│  ║       └─ Workspace • Main                                        ║  │
│  ║                                                                   ║  │
│  ║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           ║  │
│  ║  │ [💻] CPU │ │ [📊] ACT │ │ [⚡] ZAP │ │ [▶️] ENG │           ║  │
│  ║  │  Status  │ │ Sessions │ │  State   │ │  Engine  │           ║  │
│  ║  │  active  │ │    2     │ │  idle    │ │  MuJoCo  │           ║  │
│  ║  └──────────┘ └──────────┘ └──────────┘ └──────────┘           ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────┬────────────────────────────────────────┐
│         IDE PANEL (60%)        │    SIMULATION PANEL (40%)              │
│                                │                                        │
│ ┌────────────────────────────┐ │ ┌────────────────────────────────────┐ │
│ │ File Explorer              │ │ │  [📺] Simulation View  [↕ Expand]  │ │
│ │ ├─ src/                    │ │ │  └─ Real-time visualization        │ │
│ │ │  ├─ main.py ✓            │ │ ├────────────────────────────────────┤ │
│ │ │  ├─ utils.py             │ │ │ [Simulation] [Metrics] [Logs]      │ │
│ │ │  └─ main.cpp             │ │ └────────────────────────────────────┘ │
│ │ └─ config/                 │ │                                        │
│ └────────────────────────────┘ │ ╔══════════════════════════════════╗ │
│                                │ ║  SIMULATION VIEWER                ║ │
│ ┌────────────────────────────┐ │ ║                                   ║ │
│ │ main.py          [💾 Save] │ │ ║  ┌─────────────────────────────┐ ║ │
│ │                 [▶️ Run Py] │ │ ║  │ [MuJoCo] • 60 FPS • Frame 0│ ║ │
│ ├────────────────────────────┤ │ ║  └─────────────────────────────┘ ║ │
│ │                            │ │ ║                                   ║ │
│ │  # Python code editor      │ │ ║  [▶️ Play] [🔄 Reset] [...More] ║ │
│ │  import numpy as np        │ │ ║  ┌────────────────────────────┐ ║ │
│ │                            │ │ ║  │    ▶ Settings Panel       │ ║ │
│ │  def main():               │ │ ║  │  FPS: [60▼] Quality: [High▼]║ │
│ │      print("Hello")        │ │ ║  └────────────────────────────┘ ║ │
│ │                            │ │ ║                                   ║ │
│ │  if __name__ == "__main__":│ │ ║     ╔════════════════════╗       ║ │
│ │      main()                │ │ ║     ║   🤖 Robot Icon    ║       ║ │
│ │                            │ │ ║     ║  Simulation Ready  ║       ║ │
│ │                            │ │ ║     ║  Grid Background   ║       ║ │
│ │                            │ │ ║     ╚════════════════════╝       ║ │
│ │                            │ │ ║                                   ║ │
│ │ [Monaco Editor Area]       │ │ ║  [●] Running • Frame 0            ║ │
│ │                            │ │ ╚══════════════════════════════════╝ │
│ └────────────────────────────┘ │                                        │
│                                │                                        │
│ ┌────────────────────────────┐ │ ┌────────────────────────────────────┐ │
│ │ TERMINAL                   │ │ │ METRICS TAB (when selected)        │ │
│ │ [●] CONNECTED              │ │ │                                    │ │
│ │                            │ │ │ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │ │
│ │ $ python main.py           │ │ │ │ FPS │ │ LAT │ │ MEM │ │ CPU │  │ │
│ │ Hello from CoSim           │ │ │ │ 60  │ │12ms │ │1.2G │ │ 45% │  │ │
│ │ $                          │ │ │ │ +5% │ │ -3ms│ │+0.1G│ │ -2% │  │ │
│ │                            │ │ │ └─────┘ └─────┘ └─────┘ └─────┘  │ │
│ └────────────────────────────┘ │ │                                    │ │
│                                │ │ 📊 Real-time metrics dashboard     │ │
└────────────────────────────────┴────────────────────────────────────────┘
```

## Color Scheme

### Header Card
- Background: `linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1))`
- Border: `rgba(102, 126, 234, 0.2)`
- Project Name: Gradient text `#667eea → #764ba2`
- Status Cards: Glassmorphism with colored icons

### Status Card Colors
1. **CPU (Status)** - Purple `#667eea`
2. **Activity (Sessions)** - Green `#0dbc79`
3. **Zap (State)** - Yellow `#f59e0b`
4. **Play (Engine)** - Pink `#ec4899`

### Simulation Viewer
- Background: Radial gradient `#1a1a1a → #0a0a0a`
- Grid Pattern: `rgba(102, 126, 234, 0.05)`
- Toolbar: `linear-gradient(135deg, #1a1a1a, #2d2d30)`
- Connection Badge: Green `#0dbc79` with pulse animation

### Buttons
- **Play Button**: Green gradient `#0dbc79 → #23d18b`
- **Pause Button**: Yellow gradient `#f59e0b → #fbbf24`
- **Secondary Buttons**: Gray with blue tint on active
- **Disabled**: Gray with low opacity

## Interactive States

### Hover Effects
```
┌─────────────┐           ┌─────────────┐
│  StatusCard │  ──────▶  │  StatusCard │ ↑ 2px
│             │  (hover)  │   + shadow  │
└─────────────┘           └─────────────┘
```

### Connection States
```
Disconnected:  ○ Connecting...  (orange, no pulse)
    ↓
Connected:     ● 60 FPS         (green, pulsing)
```

### Tab States
```
Inactive:  [ Simulation ] [ Metrics ] [ Logs ]
              gray         gray        gray

Active:    [✓Simulation✓] [ Metrics ] [ Logs ]
           gradient bg      gray        gray
           + shadow
```

## Responsive Behavior

### Normal Mode (1400px+)
```
┌─────────────────────┬──────────────┐
│   IDE (60%)         │   Sim (40%)  │
│                     │              │
└─────────────────────┴──────────────┘
```

### Expanded Simulation
```
┌──────────────────────────────────────┐
│        Simulation (100%)             │
│                                      │
└──────────────────────────────────────┘
```

### Medium Screen (900-1400px)
```
┌─────────────────────┬──────────────┐
│   IDE (55%)         │   Sim (45%)  │
│                     │              │
└─────────────────────┴──────────────┘
```

### Small Screen (<900px)
```
┌──────────────────────────────────────┐
│              IDE (100%)              │
│                                      │
├──────────────────────────────────────┤
│        Simulation (100%)             │
│                                      │
└──────────────────────────────────────┘
```

## Component Hierarchy

```
WorkspacePage
│
├── Header Card (glassmorphism)
│   ├── Project Info
│   │   ├── Icon Badge (gradient)
│   │   ├── Name (gradient text)
│   │   └── Workspace Name
│   │
│   ├── Workspace Selector (dropdown)
│   │
│   └── Status Cards (grid)
│       ├── StatusCard × 4
│       │   ├── Icon (colored bg)
│       │   ├── Label
│       │   └── Value
│       └── (hover animations)
│
├── Main Content Grid
│   │
│   ├── IDE Panel
│   │   └── SessionIDE
│   │       ├── File Tree
│   │       ├── Monaco Editor
│   │       │   ├── Run Buttons
│   │       │   └── Save Button
│   │       └── Terminal
│   │
│   └── Simulation Panel
│       ├── Panel Header
│       │   ├── Icon Badge
│       │   ├── Title/Subtitle
│       │   └── Expand Button
│       │
│       ├── Tab Navigation
│       │   └── Active Tab (gradient)
│       │
│       └── Tab Content
│           │
│           ├── SimulationViewer
│           │   ├── Enhanced Toolbar
│           │   │   ├── Status Badge (pulsing)
│           │   │   ├── Stats (FPS, Frame, Time)
│           │   │   ├── Action Buttons
│           │   │   └── Settings Button
│           │   │
│           │   ├── Settings Panel (collapsible)
│           │   │   ├── Frame Rate Control
│           │   │   ├── Quality Control
│           │   │   └── Camera Mode Control
│           │   │
│           │   └── Canvas Area
│           │       ├── Grid Background
│           │       ├── Video/Canvas Element
│           │       ├── Placeholder Content
│           │       └── Status Overlay
│           │
│           ├── MetricsPanel
│           │   ├── Metric Cards × 4
│           │   └── Info Panel
│           │
│           └── LogsPanel
│               ├── Log Entries (colored)
│               └── Info Panel
```

## Animation Timeline

### Page Load
```
0ms    ─────────────────────────────────────────
       Header Card fades in (opacity 0 → 1)
       
100ms  ─────────────────────────────────────────
       Status Cards slide up (translateY 20px → 0)
       
200ms  ─────────────────────────────────────────
       IDE Panel fades in
       
300ms  ─────────────────────────────────────────
       Simulation Panel fades in
       Connection indicator starts pulsing
```

### User Interactions
```
Hover Card      : transform translateY(-2px)  + shadow (200ms)
Click Button    : scale(0.95) → scale(1)      (150ms)
Expand Panel    : grid-template-columns       (300ms ease)
Switch Tab      : opacity 0 → 1               (200ms)
Settings Toggle : max-height 0 → auto         (250ms)
```

## Dark Mode Integration

The design uses the existing dark mode system from ThemeContext:

```
Light Mode Colors:
- Background: #ffffff, #f8fafc
- Text: #1e293b, #475569
- Borders: #e2e8f0

Dark Mode Colors:
- Background: #0a0a0a, #1a1a1a, #2d2d30
- Text: #e2e8f0, #94a3b8
- Borders: rgba(102, 126, 234, 0.2)
```

## Accessibility Features

### Keyboard Navigation
- Tab through all interactive elements
- Enter to activate buttons
- Escape to close settings panel
- Arrow keys in dropdowns

### Screen Reader Support
- Semantic HTML (`<button>`, `<select>`, `<label>`)
- ARIA labels on icon-only buttons
- Status announcements for state changes
- Descriptive alt text

### Visual Indicators
- Focus outlines on interactive elements
- High contrast for text (WCAG AA)
- Color not sole indicator of state
- Loading states clearly shown

## Performance Notes

### Optimizations
1. CSS transitions (GPU-accelerated)
2. Virtual scrolling for logs (when many entries)
3. Debounced resize handlers
4. Conditional rendering of panels
5. Memoized computed values

### Bundle Impact
- Added icons: ~2KB (tree-shaken)
- Additional components: ~5KB
- CSS animations: inline (no bundle)
- Total impact: ~7KB gzipped

---

**Layout Tested On:**
- 1920×1080 (Full HD Desktop)
- 1440×900 (MacBook Pro)
- 1366×768 (Laptop)
- 1024×768 (iPad)

**Browser Compatibility:**
✅ Chrome 90+
✅ Firefox 88+
✅ Safari 14+
✅ Edge 90+
