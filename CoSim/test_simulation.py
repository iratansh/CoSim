import numpy as np

print("🚀 Testing cartpole simulation...")

# Get simulation object
sim = get_simulation()

# Reset to initial state
state = sim.reset()
print(f"Initial state:")
print(f"  Cart position: {state['qpos'][0]:.3f} m")
print(f"  Pole angle: {state['qpos'][1]:.3f} rad")

# Apply constant force for 10 steps
print("\nApplying force to cart...")
for i in range(10):
    action = np.array([2.0])  # Push cart to the right
    state = sim.step(action)

print(f"\nFinal state after 10 steps:")
print(f"  Cart position: {state['qpos'][0]:.3f} m")
print(f"  Pole angle: {state['qpos'][1]:.3f} rad")

print("\n✅ Simulation test complete!")
