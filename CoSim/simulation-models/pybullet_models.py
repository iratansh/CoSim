"""
PyBullet URDF Models

These are references to built-in PyBullet models.
PyBullet comes with many pre-built URDF files in pybullet_data.

Available models include:
- plane.urdf (ground plane)
- r2d2.urdf (simple robot)
- cartpole.urdf (cartpole/inverted pendulum)
- humanoid.urdf (humanoid robot)
- kuka_iiwa/model.urdf (KUKA robot arm)
- quadruped/quadruped.urdf (quadruped robot)

Usage in simulation agent:
```python
import pybullet as p
import pybullet_data

# Set search path
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# Load model
robot_id = p.loadURDF("r2d2.urdf", basePosition=[0, 0, 1])
```

Custom URDF files can be added to this directory and referenced
by absolute path when creating simulations.
"""

# Example: Simple pendulum URDF
PENDULUM_URDF = """
<?xml version="1.0"?>
<robot name="simple_pendulum">
  <link name="base">
    <visual>
      <geometry>
        <sphere radius="0.05"/>
      </geometry>
      <material name="gray">
        <color rgba="0.5 0.5 0.5 1"/>
      </material>
    </visual>
    <inertial>
      <mass value="0.1"/>
      <inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.001"/>
    </inertial>
  </link>

  <link name="pole">
    <visual>
      <geometry>
        <cylinder radius="0.03" length="1.0"/>
      </geometry>
      <origin xyz="0 0 -0.5"/>
      <material name="blue">
        <color rgba="0.2 0.6 0.9 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <cylinder radius="0.03" length="1.0"/>
      </geometry>
      <origin xyz="0 0 -0.5"/>
    </collision>
    <inertial>
      <mass value="0.5"/>
      <inertia ixx="0.042" ixy="0" ixz="0" iyy="0.042" iyz="0" izz="0.001"/>
      <origin xyz="0 0 -0.5"/>
    </inertial>
  </link>

  <joint name="hinge" type="continuous">
    <parent link="base"/>
    <child link="pole"/>
    <axis xyz="0 1 0"/>
    <origin xyz="0 0 0"/>
    <dynamics damping="0.01"/>
  </joint>

  <link name="bob">
    <visual>
      <geometry>
        <sphere radius="0.12"/>
      </geometry>
      <material name="red">
        <color rgba="0.9 0.4 0.2 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <sphere radius="0.12"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="1.0"/>
      <inertia ixx="0.006" ixy="0" ixz="0" iyy="0.006" iyz="0" izz="0.006"/>
    </inertial>
  </link>

  <joint name="bob_joint" type="fixed">
    <parent link="pole"/>
    <child link="bob"/>
    <origin xyz="0 0 -1.0"/>
  </joint>
</robot>
"""

# Save to file if needed
if __name__ == "__main__":
    with open("pendulum.urdf", "w") as f:
        f.write(PENDULUM_URDF)
    print("Created pendulum.urdf")
