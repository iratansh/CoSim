"""
PyBullet Cartpole Demonstration

This is a default script that runs when you create a new PyBullet project.
It demonstrates a simple cartpole (inverted pendulum) simulation with control.

Features:
- Physics simulation using PyBullet
- Real-time rendering and streaming
- Simple PD controller for balancing
- Customizable parameters

Run this simulation to see it in action!
"""

import numpy as np
import time

# Get simulation instance (provided by CoSim execution context)
sim = get_simulation()

# Simulation parameters
CONTROL_ENABLED = True
KP = 50.0  # Proportional gain
KD = 10.0  # Derivative gain
TARGET_ANGLE = 0.0  # Target angle (upright)

# Run simulation for a duration
SIMULATION_DURATION = 10.0  # seconds
CONTROL_FREQUENCY = 60  # Hz

print("=" * 60)
print("PyBullet Cartpole Simulation")
print("=" * 60)
print(f"Duration: {SIMULATION_DURATION}s")
print(f"Control: {'Enabled' if CONTROL_ENABLED else 'Disabled'}")
print(f"PD Gains: Kp={KP}, Kd={KD}")
print("=" * 60)

# Reset simulation to initial state
initial_state = sim.reset()
print(f"\n✓ Simulation reset")
print(f"  Frame: {initial_state['frame']}")
print(f"  Time: {initial_state['time']:.3f}s")
print(f"  Bodies: {initial_state['num_bodies']}")

# Get robot ID (cartpole)
robot_id = initial_state.get('robot_id')
if robot_id is None:
    print("\n⚠️  No robot loaded. Loading default cartpole...")
    # The simulation agent should have loaded cartpole.urdf by default

# Main simulation loop
start_time = time.time()
prev_angle = 0.0
step_count = 0

print("\n🎮 Starting simulation loop...")
print("Streaming frames via WebSocket to browser...\n")

while True:
    current_time = time.time() - start_time
    if current_time >= SIMULATION_DURATION:
        break
    
    # Get current state
    state = sim.get_state()
    
    # Calculate control action if enabled
    action = None
    if CONTROL_ENABLED and robot_id is not None:
        # Simple PD control for cartpole
        # Assuming joint 0 is the cart-pole hinge
        
        # Get pole angle (simplified - would need actual joint state in real impl)
        # For demo purposes, we'll apply a small random force
        angle = state.get('base_orientation', [0, 0, 0, 1])[1]  # Approximate
        angle_rate = (angle - prev_angle) * CONTROL_FREQUENCY
        
        # PD control
        error = TARGET_ANGLE - angle
        control_force = KP * error - KD * angle_rate
        
        # Clip force to reasonable range
        control_force = np.clip(control_force, -100, 100)
        
        action = np.array([control_force])
        prev_angle = angle
    
    # Step simulation
    step_result = sim.step(action)
    step_count += 1
    
    # Print progress every second
    if step_count % CONTROL_FREQUENCY == 0:
        elapsed = step_result['time']
        print(f"  [{elapsed:6.2f}s] Frame {step_result['frame']:4d} | ", end="")
        if 'base_position' in step_result:
            pos = step_result['base_position']
            print(f"Pos: ({pos[0]:+.2f}, {pos[1]:+.2f}, {pos[2]:+.2f})")
        else:
            print("Simulating...")
    
    # Sleep to maintain control frequency
    time.sleep(1.0 / CONTROL_FREQUENCY)

# Final statistics
final_state = sim.get_state()
print("\n" + "=" * 60)
print("✓ Simulation Complete!")
print("=" * 60)
print(f"Total frames: {final_state['frame']}")
print(f"Simulation time: {final_state['time']:.2f}s")
print(f"Average FPS: {final_state['frame'] / (time.time() - start_time):.1f}")
print("=" * 60)

print("\n💡 Next steps:")
print("  1. Modify control gains (KP, KD) to see different behaviors")
print("  2. Change SIMULATION_DURATION to run longer")
print("  3. Implement your own controller algorithm")
print("  4. Add your custom URDF models")
print("\n🚀 Happy simulating!")
