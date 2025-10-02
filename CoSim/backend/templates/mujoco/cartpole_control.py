"""
CoSim MuJoCo Cartpole Control Script

This script demonstrates how to control a MuJoCo simulation from Python code.
The cartpole model has 1 actuator (cart slider) and 2 DOFs (cart position, pole angle).

Available API:
- sim.reset() - Reset simulation to initial state
- sim.step(actions) - Step simulation with control actions
- sim.get_state() - Get current state (qpos, qvel, time)
- sim.render() - Get current rendered frame
"""

import numpy as np
import time

class CartpoleController:
    """Simple PD controller for cartpole balancing."""
    
    def __init__(self, kp_cart=10.0, kd_cart=5.0, kp_pole=50.0, kd_pole=10.0):
        self.kp_cart = kp_cart
        self.kd_cart = kd_cart
        self.kp_pole = kp_pole
        self.kd_pole = kd_pole
    
    def compute_action(self, state):
        """Compute control action based on current state.
        
        Args:
            state: Dictionary with 'qpos' and 'qvel' arrays
                   qpos[0] = cart position
                   qpos[1] = pole angle
                   qvel[0] = cart velocity
                   qvel[1] = pole angular velocity
        
        Returns:
            action: Control force for cart slider
        """
        # Extract state
        cart_pos = state['qpos'][0]
        pole_angle = state['qpos'][1]
        cart_vel = state['qvel'][0]
        pole_vel = state['qvel'][1]
        
        # Target: keep cart at origin, pole upright
        target_cart_pos = 0.0
        target_pole_angle = 0.0
        
        # PD control
        cart_error = cart_pos - target_cart_pos
        pole_error = pole_angle - target_pole_angle
        
        # Control law: push cart to balance pole
        action = (
            - self.kp_cart * cart_error 
            - self.kd_cart * cart_vel
            - self.kp_pole * pole_error
            - self.kd_pole * pole_vel
        )
        
        # Clip to actuator limits
        action = np.clip(action, -10.0, 10.0)
        
        return action


def main():
    """Main simulation loop."""
    print("🚀 Starting Cartpole Simulation...")
    
    # Initialize controller
    controller = CartpoleController()
    
    # Connect to simulation (this will be injected by CoSim)
    # sim = get_simulation()  # Provided by CoSim runtime
    
    # For testing without CoSim, use dummy simulation
    class DummySimulation:
        def __init__(self):
            self.qpos = np.array([0.0, 0.1])  # Start with small pole tilt
            self.qvel = np.array([0.0, 0.0])
            self.time = 0.0
            self.dt = 0.01
        
        def reset(self):
            self.qpos = np.array([0.0, 0.1])
            self.qvel = np.array([0.0, 0.0])
            self.time = 0.0
            return self.get_state()
        
        def get_state(self):
            return {
                'qpos': self.qpos.copy(),
                'qvel': self.qvel.copy(),
                'time': self.time
            }
        
        def step(self, action):
            # Simplified cartpole dynamics
            m_cart = 1.0
            m_pole = 0.1
            l = 0.3  # pole half-length
            g = 9.81
            
            force = action[0] if isinstance(action, np.ndarray) else action
            
            x, theta = self.qpos
            x_dot, theta_dot = self.qvel
            
            sin_theta = np.sin(theta)
            cos_theta = np.cos(theta)
            
            # Equations of motion (simplified)
            theta_acc = (g * sin_theta - cos_theta * (force + m_pole * l * theta_dot**2 * sin_theta) / (m_cart + m_pole)) / \
                        (l * (4/3 - m_pole * cos_theta**2 / (m_cart + m_pole)))
            
            x_acc = (force + m_pole * l * (theta_dot**2 * sin_theta - theta_acc * cos_theta)) / (m_cart + m_pole)
            
            # Euler integration
            self.qvel[0] += x_acc * self.dt
            self.qvel[1] += theta_acc * self.dt
            self.qpos[0] += self.qvel[0] * self.dt
            self.qpos[1] += self.qvel[1] * self.dt
            self.time += self.dt
            
            return self.get_state()
    
    sim = DummySimulation()
    
    # Reset simulation
    state = sim.reset()
    print(f"✓ Simulation reset. Initial pole angle: {state['qpos'][1]:.3f} rad")
    
    # Run simulation loop
    steps = 500
    for i in range(steps):
        # Get current state
        state = sim.get_state()
        
        # Compute control action
        action = controller.compute_action(state)
        
        # Step simulation
        state = sim.step(np.array([action]))
        
        # Print status every 50 steps
        if i % 50 == 0:
            cart_pos = state['qpos'][0]
            pole_angle = state['qpos'][1]
            print(f"Step {i:3d} | Cart: {cart_pos:+.3f}m | Pole: {pole_angle:+.3f}rad | Action: {action:+.2f}N")
        
        # Check if pole fell
        if abs(state['qpos'][1]) > 0.5:
            print(f"❌ Pole fell at step {i}!")
            break
    else:
        print(f"✓ Successfully balanced pole for {steps} steps!")
    
    print(f"🏁 Simulation finished at t={state['time']:.2f}s")


if __name__ == "__main__":
    main()
