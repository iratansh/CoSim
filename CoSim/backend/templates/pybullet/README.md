# PyBullet Project Template

Welcome to your PyBullet simulation project!

## What's Included

- **cartpole_demo.py** - Default cartpole simulation with PD control
- Built-in PyBullet models (plane, cartpole, robots, etc.)
- Real-time WebRTC streaming to browser
- Interactive controls and camera

## Quick Start

1. **Run the default demo:**
   - Click the "▶ Run" button in the IDE
   - Watch the cartpole simulation stream in the viewer
   - See console output for simulation statistics

2. **Modify parameters:**
   ```python
   KP = 50.0  # Increase for stiffer control
   KD = 10.0  # Increase for more damping
   SIMULATION_DURATION = 20.0  # Run longer
   ```

3. **Load different models:**
   ```python
   # Use built-in PyBullet models
   import pybullet as p
   import pybullet_data
   
   p.setAdditionalSearchPath(pybullet_data.getDataPath())
   robot_id = p.loadURDF("r2d2.urdf")
   # Or: "humanoid.urdf", "kuka_iiwa/model.urdf", etc.
   ```

## Available Models

PyBullet includes many built-in URDF models:
- `plane.urdf` - Ground plane
- `cartpole.urdf` - Cartpole/inverted pendulum
- `r2d2.urdf` - Simple wheeled robot
- `humanoid.urdf` - Humanoid robot
- `kuka_iiwa/model.urdf` - KUKA robot arm
- `quadruped/quadruped.urdf` - Quadruped robot

## Simulation API

Your code has access to the `sim` object:

```python
# Reset simulation
sim.reset()

# Step simulation with actions
actions = np.array([force1, force2, ...])
state = sim.step(actions)

# Get current state
state = sim.get_state()
# Returns: frame, time, robot position/orientation, velocities

# Control camera
sim.set_camera(distance=3.0, yaw=45, pitch=-30, target=[0, 0, 1])
```

## Writing Custom Controllers

```python
# Example: Simple PID controller
class PIDController:
    def __init__(self, kp, ki, kd):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.integral = 0
        self.prev_error = 0
    
    def compute(self, setpoint, measurement, dt):
        error = setpoint - measurement
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        self.prev_error = error
        return self.kp * error + self.ki * self.integral + self.kd * derivative

# Use in simulation loop
controller = PIDController(kp=10, ki=0.1, kd=5)

while True:
    state = sim.get_state()
    angle = get_pole_angle(state)
    control = controller.compute(target=0, measurement=angle, dt=1/60)
    sim.step(actions=[control])
```

## Custom URDF Files

Create your own robot models:

```xml
<!-- my_robot.urdf -->
<?xml version="1.0"?>
<robot name="my_robot">
  <link name="base">
    <visual>
      <geometry>
        <box size="0.5 0.5 0.1"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 1 1"/>
      </material>
    </visual>
    <!-- Add collision, inertial, etc. -->
  </link>
  <!-- Add more links and joints -->
</robot>
```

Load in your simulation:
```python
robot_id = p.loadURDF("my_robot.urdf", basePosition=[0, 0, 0.5])
```

## Tips

- **Simulation runs at 240 Hz** internally (PyBullet default)
- **Rendering streams at 60 FPS** to browser
- **Use time.sleep()** in control loops to avoid blocking
- **Check sim.get_state()** for detailed robot state
- **PyBullet docs**: https://docs.google.com/document/d/10sXEhzFRSnvFcl3XxNGhnD4N2SedqwdAvK3dsihxVUA

## Next Steps

1. Experiment with different PD gains
2. Implement your own control algorithm
3. Load different robot models
4. Add sensors and perception
5. Create multi-robot scenarios

Happy simulating! 🤖
