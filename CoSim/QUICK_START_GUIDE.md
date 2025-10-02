# Quick Start Guide - Workspace Page

## Running the Application

```bash
# Terminal 1 - Start frontend
cd frontend
npm run dev
# Opens at http://localhost:5173

# Terminal 2 - Start backend (if needed)
cd backend
# Follow backend startup instructions
```

## Testing the New Design

### 1. Navigate to Workspace
1. Login to CoSim
2. Click on any project from Projects page
3. You'll be taken to the new enhanced Workspace page

### 2. Explore Header Features
- **Project Name**: See gradient text effect
- **Status Cards**: Hover over each card to see lift animation
  - CPU icon (purple) - Shows status
  - Activity icon (green) - Shows session count
  - Zap icon (yellow) - Shows state
  - Play icon (pink) - Shows engine
- **Workspace Selector**: Click dropdown to change workspace

### 3. Test IDE Panel
- **File Tree**: Select different files
- **Monaco Editor**: Edit code
- **Run Buttons**:
  - Select a `.py` file → See "▶️ Run Python" button
  - Select a `.cpp` file → See "🔨 Build" and "⚡ Build & Run" buttons
- **Terminal**: Check connection status indicator

### 4. Test Simulation Panel

#### Tab Navigation
- Click **"Simulation"** tab (default)
- Click **"Metrics"** tab to see performance dashboard
- Click **"Logs"** tab to see terminal-style logs

#### Simulation Controls
- **Connection Status**: Watch pulsing green indicator
- **Play/Pause**: Click to toggle (button changes color)
- **Reset**: Click to reset simulation
- **Settings**: Click gear icon to expand/collapse settings panel
- **Expand**: Click expand icon (top-right) to maximize simulation

#### Settings Panel
- Change **Frame Rate**: 30/60/120 FPS
- Change **Quality**: Low/Medium/High/Ultra
- Change **Camera Mode**: Fixed/Follow/Free

#### Additional Controls
- **Camera**: Screenshot (not yet wired)
- **Download**: Export (not yet wired)
- **Share**: Share simulation (not yet wired)
- **Fullscreen**: Maximize view (not yet wired)

### 5. Test Responsive Layout

#### Expand Simulation
1. Click expand button (↕️ icon) in simulation header
2. Simulation panel takes full width
3. IDE panel hides
4. Click again to restore

#### Resize Window
- Drag browser window to different sizes
- Layout adapts automatically
- Status cards reflow in grid

## Visual Features Checklist

### Animations
- [ ] Status cards lift on hover
- [ ] Connection indicator pulses
- [ ] Tab switches smoothly
- [ ] Buttons scale slightly on hover
- [ ] Settings panel expands/collapses
- [ ] Loading spinner rotates

### Colors & Gradients
- [ ] Project name has purple gradient
- [ ] Status cards have colored icon backgrounds
- [ ] Play button is green gradient
- [ ] Pause button is yellow gradient
- [ ] Active tab has purple gradient

### Glassmorphism
- [ ] Header card has blur effect
- [ ] Status cards have transparent backgrounds
- [ ] Workspace selector has blur
- [ ] Settings panel has backdrop blur

### Status Indicators
- [ ] Connection shows "CONNECTING..." → "● CONNECTED"
- [ ] FPS counter updates
- [ ] Frame count increments when playing
- [ ] Simulation time updates

## Keyboard Shortcuts

### IDE
- `Ctrl/Cmd + S`: Save file
- `Ctrl/Cmd + Enter`: Run code (when implemented)

### Navigation
- `Tab`: Navigate between elements
- `Enter`: Activate button
- `Escape`: Close panels

## Common Issues & Solutions

### Issue: TypeScript errors
**Solution:** Run `npm install` to ensure all dependencies are installed

### Issue: Animations not smooth
**Solution:** 
- Check browser supports CSS transitions
- Try Chrome/Firefox/Safari latest
- Disable browser extensions

### Issue: Glassmorphism not showing
**Solution:**
- Check browser supports `backdrop-filter`
- Update to latest browser version
- Fallback: solid backgrounds show instead

### Issue: Connection stuck on "Connecting..."
**Solution:**
- This is expected until backend WebSocket is implemented
- Simulation uses fallback placeholder mode
- Controls still work in demo mode

### Issue: Metrics/Logs show placeholder text
**Solution:**
- This is expected until backend integration
- Frontend is ready, waiting for backend

## Next Steps After Testing

### Backend Integration
1. **WebSocket Terminal** (`/v1/sessions/{id}/terminal`)
2. **Python Execution** (`POST /v1/sessions/execute/python`)
3. **C++ Build** (`POST /v1/sessions/build/cpp`)
4. **Metrics Stream** (real-time performance data)
5. **Logs Stream** (real-time system logs)

### Additional Features
- Wire up Screenshot button
- Wire up Export button
- Wire up Share button
- Wire up Fullscreen button
- Add keyboard shortcuts overlay

## File Locations

### Modified Files
```
frontend/src/
├── routes/
│   └── Workspace.tsx         ← Main page (redesigned)
├── components/
│   ├── SessionIDE.tsx        ← Code execution buttons
│   ├── SimulationViewer.tsx  ← Enhanced viewer
│   └── Terminal.tsx          ← WebSocket terminal
└── api/
    └── execution.ts          ← Execution API
```

### Documentation
```
CoSim/
├── WORKSPACE_PAGE_REDESIGN.md    ← Full redesign summary
├── WORKSPACE_LAYOUT_GUIDE.md     ← Visual layout guide
├── BEFORE_AFTER_COMPARISON.md    ← Comparison doc
├── CODE_EXECUTION_IMPLEMENTATION.md  ← Execution system
└── QUICK_START_GUIDE.md          ← This file
```

## Quick CSS Reference

### Colors Used
```css
/* Primary Gradients */
--purple-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--green-gradient: linear-gradient(135deg, #0dbc79 0%, #23d18b 100%);
--yellow-gradient: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
--pink-gradient: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);

/* Status Colors */
--purple: #667eea;
--green: #0dbc79;
--yellow: #f59e0b;
--pink: #ec4899;

/* Neutrals */
--dark-bg: #0a0a0a;
--mid-bg: #1a1a1a;
--light-bg: #2d2d30;
--text-primary: #e2e8f0;
--text-secondary: #94a3b8;
--border: rgba(102, 126, 234, 0.2);
```

### Animation Durations
```css
--transition-fast: 150ms;
--transition-normal: 200ms;
--transition-slow: 300ms;
```

## Browser DevTools Tips

### Inspect Animations
1. Open DevTools (F12)
2. Go to "Animations" tab
3. Trigger hover/click
4. See animation timeline

### Check Performance
1. Open DevTools Performance tab
2. Record while interacting
3. Look for smooth 60fps
4. Check for layout thrashing

### Debug Glassmorphism
1. Inspect element
2. Check `backdrop-filter` property
3. Verify `background` has alpha
4. Check stacking context (z-index)

## Accessibility Testing

### Keyboard Navigation
1. Tab through all elements
2. Verify focus outlines visible
3. Enter activates buttons
4. Escape closes panels

### Screen Reader
1. Enable VoiceOver (Mac) or NVDA (Windows)
2. Navigate with screen reader
3. Verify all labels read correctly
4. Check status announcements

### Color Contrast
1. Use browser extension (axe DevTools)
2. Check text contrast ratios
3. Verify WCAG AA compliance
4. Test with color blindness simulators

## Performance Benchmarks

### Target Metrics
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Animation FPS**: 60fps constant
- **Bundle Size**: < 500KB gzipped

### Monitor With
```javascript
// Add to browser console
performance.mark('workspace-load-start');
// ... page loads ...
performance.mark('workspace-load-end');
performance.measure('workspace-load', 'workspace-load-start', 'workspace-load-end');
```

## Troubleshooting Commands

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev

# Check TypeScript errors
npx tsc --noEmit

# Run linter
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

## Support & Feedback

### Report Issues
- Check browser console for errors
- Note browser version and OS
- Provide steps to reproduce
- Include screenshots if visual issue

### Feature Requests
- Describe the feature
- Explain use case
- Note if urgent or nice-to-have

---

**Quick Start Complete!**
Enjoy the new enhanced workspace experience! 🚀
