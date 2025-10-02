# 🎮 Simulator Integration - User Guide

## Overview

CoSim now connects your IDE code directly to MuJoCo and PyBullet simulators! Write control scripts in Python, click "Run in Sim", and watch your robot come alive.

---

## 🚀 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Browser                           │
│  ┌──────────────────┐         ┌─────────────────────────────┐  │
│  │   SessionIDE     │         │   SimulationViewer          │  │
│  │  (Monaco Editor) │────────▶│  (WebRTC Canvas/Video)      │  │
│  │                  │         │                             │  │
│  │ [🎮 Run in Sim]  │         │  ┌──────────────────────┐   │  │
│  └────────┬─────────┘         │  │   MuJoCo Render      │   │  │
│           │                   │  │   (Cartpole/Robot)   │   │  │
│           │ HTTP POST         │  └──────────────────────┘   │  │
│           ▼                   └─────────────────────────────┘  │
└───────────┼────────────────────────────────────────────────────┘
            │
            │ /simulations/{session_id}/execute
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (Docker)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Simulation Agent (port 8005)                │  │
│  │                                                          │  │
│  │  POST /simulations/create                               │  │
│  │    - Creates MuJoCo/PyBullet environment                │  │
│  │    - Loads XML/URDF model file                          │  │
│  │                                                          │  │
│  │  POST /simulations/{session_id}/execute                 │  │
│  │    - Runs your Python code                              │  │
│  │    - Injects `sim` object (reset, step, get_state)      │  │
│  │    - Captures stdout/stderr                             │  │
│  │    - Returns execution results                          │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │       MuJoCo Environment                           │ │  │
│  │  │  - Physics simulation (60 FPS)                     │ │  │
│  │  │  - Model loaded from /models/cartpole.xml          │ │  │
│  │  │  - API: reset(), step(actions), get_state()        │ │  │
│  │  │  - Rendering: 800x600 frames                       │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 Writing Control Scripts

### Simulation API

When you click "Run in Sim", your Python code has access to a `sim` object:

```python
# Get simulation object (automatically injected)
sim = get_simulation()

# Reset simulation to initial state
state = sim.reset()
# Returns: {'qpos': [...], 'qvel': [...], 'time': 0.0, 'frame': 0}

# Get current state
state = sim.get_state()
# Returns: {'qpos': [...], 'qvel': [...], 'time': 1.23}

# Step simulation with control actions
action = np.array([5.0])  # Force on cart
state = sim.step(action)
# Returns: updated state after physics step

# Get rendered frame (optional)
frame = sim.render()
# Returns: numpy array (height, width, 3) RGB image
```

### Example: Cartpole Balancing

The default workspace includes `/src/cartpole_sim.py`:

```python
import numpy as np

class CartpoleController:
    """PD controller for cartpole."""
    
    def __init__(self, kp=50.0, kd=10.0):
        self.kp = kp
        self.kd = kd
    
    def compute_action(self, state):
        # Extract state
        pole_angle = state['qpos'][1]  # Pole angle (rad)
        pole_vel = state['qvel'][1]    # Angular velocity
        
        # PD control
        action = -self.kp * pole_angle - self.kd * pole_vel
        
        # Clip to actuator limits
        return np.clip(action, -10.0, 10.0)

def main():
    print("🚀 Starting Simulation...")
    
    controller = CartpoleController()
    sim = get_simulation()  # Injected by CoSim
    
    # Reset
    state = sim.reset()
    
    # Run loop
    for i in range(500):
        state = sim.get_state()
        action = controller.compute_action(state)
        state = sim.step(np.array([action]))
        
        if i % 50 == 0:
            print(f"Step {i} | Pole: {state['qpos'][1]:.3f} rad")
    
    print("✓ Done!")

if __name__ == "__main__":
    main()
```

**How to Run:**
1. Open `/src/cartpole_sim.py` in IDE
2. Click **"🎮 Run in Sim"** button
3. Watch console output
4. See simulation update in SimulationViewer panel

---

## 🏗️ MuJoCo Model Files

### Model Structure

The workspace includes `/models/cartpole.xml`:

```xml
<mujoco model="cartpole">
  <option gravity="0 0 -9.81" integrator="RK4" timestep="0.01"/>
  
  <worldbody>
    <body name="cart" pos="0 0 0">
      <joint name="slider" type="slide" axis="1 0 0" range="-1 1"/>
      <geom name="cart" type="box" size="0.2 0.15 0.1"/>
      
      <body name="pole" pos="0 0 0">
        <joint name="hinge" type="hinge" axis="0 1 0"/>
        <geom name="pole" type="capsule" fromto="0 0 0 0 0 0.6" size="0.045"/>
      </body>
    </body>
  </worldbody>
  
  <actuator>
    <motor joint="slider" gear="100" ctrlrange="-10 10"/>
  </actuator>
</mujoco>
```

### Key Components

- **`<option>`**: Physics settings (gravity, timestep, integrator)
- **`<worldbody>`**: Scene hierarchy (bodies, joints, geoms)
- **`<joint>`**: Degrees of freedom (slider, hinge, ball, etc.)
- **`<geom>`**: Visual/collision geometry (box, sphere, capsule)
- **`<actuator>`**: Motors and forces

### State Mapping

For cartpole model:
- `qpos[0]`: Cart position (m)
- `qpos[1]`: Pole angle (rad)
- `qvel[0]`: Cart velocity (m/s)
- `qvel[1]`: Pole angular velocity (rad/s)
- `ctrl[0]`: Motor force (N)

---

## 🎯 Quick Start Guide

### 1. Open Workspace

```
http://localhost:5173
→ Navigate to "Workspace"
```

### 2. Explore Default Files

Your workspace includes:
```
/src/
  ├── main.py              # General Python starter
  ├── cartpole_sim.py      # ✨ MuJoCo control script
  ├── utils.py             # Helper functions
  └── main.cpp             # C++ starter

/models/
  └── cartpole.xml         # ✨ MuJoCo model

/config/
  └── sim-control.json     # Simulation settings
```

### 3. Run Cartpole Example

1. **Open** `/src/cartpole_sim.py` in IDE
2. **Click** `🎮 Run in Sim` button (purple, next to green "Run")
3. **Watch** console output:
   ```
   🚀 Starting Cartpole Simulation...
   ✓ Initial angle: 0.100 rad
   Step   0 | Pole: +0.100rad
   Step  50 | Pole: +0.023rad
   Step 100 | Pole: -0.005rad
   ...
   ✓ Balanced for 500 steps!
   🏁 Finished at t=5.00s
   ```

### 4. Modify Controller

Try changing the PD gains in `cartpole_sim.py`:

```python
# Original
controller = CartpoleController(kp_pole=50.0, kd_pole=10.0)

# More aggressive
controller = CartpoleController(kp_pole=100.0, kd_pole=20.0)

# Less aggressive (may fail!)
controller = CartpoleController(kp_pole=20.0, kd_pole=5.0)
```

Click `🎮 Run in Sim` again to test!

### 5. Create Your Own Model

**Upload a new MuJoCo XML:**
1. Create `my_robot.xml` locally
2. Click `📤 Files` in Explorer
3. Upload to `/models/my_robot.xml`

**Write control script:**
```python
# /src/my_robot_control.py
import numpy as np

def main():
    sim = get_simulation()
    state = sim.reset()
    
    for i in range(1000):
        # Your control logic
        action = np.array([...])  # Match model's actuators
        state = sim.step(action)
        
        if i % 100 == 0:
            print(f"Step {i}: {state['qpos']}")

if __name__ == "__main__":
    main()
```

**Run it:**
1. Open `/src/my_robot_control.py`
2. Click `🎮 Run in Sim`

---

## 🔧 Advanced Features

### Multi-Actuator Control

For robots with multiple motors:

```python
# Example: Humanoid with 21 actuators
actions = np.zeros(21)
actions[0] = 1.0   # Right hip
actions[1] = -0.5  # Right knee
actions[5] = 0.8   # Left hip
# ... set all 21 actuators

state = sim.step(actions)
```

### Sensor Reading

```python
state = sim.get_state()

# Joint positions
joint_angles = state['qpos']

# Joint velocities
joint_vels = state['qvel']

# Simulation time
current_time = state['time']

# Frame count
frame_num = state['frame']
```

### Rendering & Visualization

```python
# Get RGB frame
frame = sim.render()  # numpy array (H, W, 3)

# Save frame (if PIL available)
from PIL import Image
img = Image.fromarray(frame)
img.save('/workspace/output/frame.png')
```

### Error Handling

```python
try:
    sim = get_simulation()
    state = sim.reset()
    
    for i in range(1000):
        action = compute_action(state)
        state = sim.step(action)
        
except Exception as e:
    print(f"❌ Simulation error: {e}")
    # Cleanup or retry
```

---

## 🐛 Troubleshooting

### Button Not Appearing

**Problem:** "🎮 Run in Sim" button missing

**Solution:**
- Only appears for `.py` files
- Make sure you have a Python file selected
- Check file extension in Explorer

### Simulation Not Found

**Problem:** `404: Simulation not found`

**Solution:**
- Simulation auto-creates on first run
- Check browser console for errors
- Verify simulation-agent service is running:
  ```bash
  docker-compose ps simulation-agent
  ```

### Model File Not Found

**Problem:** `model_path required for MuJoCo`

**Solution:**
- Create or upload `.xml` file to `/models/` folder
- Default model: `/models/cartpole.xml`
- Check file exists in Explorer tree

### Import Errors

**Problem:** `Import "numpy" could not be resolved`

**Solution:**
- numpy is available in simulation environment
- Red squiggles in IDE are cosmetic
- Code will run successfully in simulator
- Install pylance for better IDE experience

### No Output

**Problem:** Code runs but no console output

**Solution:**
- Check browser console (F12)
- Output appears in developer console, not IDE terminal
- TODO: Pipe stdout to IDE terminal (coming soon!)

---

## 📊 State Reference

### Cartpole (2 DOF, 1 Actuator)

| Index | Variable | Description | Range |
|-------|----------|-------------|-------|
| `qpos[0]` | Cart position | Position on rail (m) | -1 to 1 |
| `qpos[1]` | Pole angle | Angle from vertical (rad) | -π to π |
| `qvel[0]` | Cart velocity | Linear velocity (m/s) | Unlimited |
| `qvel[1]` | Pole velocity | Angular velocity (rad/s) | Unlimited |
| `ctrl[0]` | Motor force | Control force (N) | -10 to 10 |

### Adding More Models

**Humanoid:** `/models/humanoid.xml` (MuJoCo built-in)
- 21 actuators
- 27 DOF (degrees of freedom)
- Complex bipedal locomotion

**Custom Robot:** Create your own!
- Define bodies, joints, geoms
- Add actuators for control
- Specify sensors (optional)

---

## 🎓 Learning Resources

### MuJoCo Documentation
- [MuJoCo Docs](https://mujoco.readthedocs.io/)
- [XML Reference](https://mujoco.readthedocs.io/en/stable/XMLreference.html)
- [Python Bindings](https://mujoco.readthedocs.io/en/stable/python.html)

### Example Scripts
- Check `/backend/templates/mujoco/` folder
- `cartpole_control.py` - PD controller example
- `cartpole.xml` - Model structure

### CoSim Docs
- `AGENT.md` - Architecture overview
- `VS_CODE_FEATURES.md` - IDE capabilities
- `QUICK_START.md` - Platform guide

---

## 🚀 What's Next?

### Currently Working
- ✅ Python control scripts
- ✅ MuJoCo model loading
- ✅ `sim.reset()`, `sim.step()`, `sim.get_state()`
- ✅ Code execution in simulation context
- ✅ Console output capture

### Coming Soon
- [ ] WebRTC video stream (replace canvas placeholder)
- [ ] Real-time simulation viewer updates
- [ ] PyBullet support (URDF files)
- [ ] RL training workflows (parallel envs)
- [ ] Trajectory recording & playback
- [ ] SLAM dataset integration

---

## 💡 Tips & Tricks

### Fast Iteration
1. Write control logic in IDE with autocomplete
2. Click `🎮 Run in Sim` to test instantly
3. Check console for results
4. Modify parameters and re-run
5. No need to restart services!

### Debugging
```python
# Add print statements
print(f"State: {state}")
print(f"Action: {action}")

# Check bounds
assert -10 <= action <= 10, f"Action {action} out of range!"

# Log to file
with open('/workspace/logs/sim.log', 'a') as f:
    f.write(f"Step {i}: {state['qpos']}\n")
```

### Performance
- Simulation runs at 60 FPS (0.01s timestep)
- 500 steps = ~8 seconds real time
- Faster than real-time possible (headless mode)
- GPU not required for cartpole (CPU sufficient)

---

**Ready to simulate?** Open `/src/cartpole_sim.py` and click `🎮 Run in Sim`! 🚀
