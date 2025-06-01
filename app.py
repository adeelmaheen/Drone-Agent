import streamlit as st
import numpy as np
import plotly.graph_objects as go
from typing import List, Tuple
import uuid
import time

# Streamlit page configuration
st.set_page_config(page_title="3D Swarm Simulation", layout="wide")

# Boid class for flocking behavior
class Boid:
    def __init__(self, position: np.ndarray, velocity: np.ndarray):
        self.position = position
        self.velocity = velocity
        self.max_speed = 2.0
        self.perception_radius = 10.0

    def update(self, boids: List['Boid']):
        try:
            separation = self.separate(boids)
            alignment = self.align(boids)
            cohesion = self.cohere(boids)
            self.velocity += separation + alignment + cohesion
            speed = np.linalg.norm(self.velocity)
            if speed > self.max_speed:
                self.velocity = (self.velocity / speed) * self.max_speed
            self.position += self.velocity
            self.position = self.position % 100  # Wrap around a 100x100x100 space
        except Exception as e:
            st.error(f"Error in Boid update: {e}")

    def separate(self, boids: List['Boid']) -> np.ndarray:
        try:
            steering = np.zeros(3)
            total = 0
            for other in boids:
                if other is not self:
                    dist = np.linalg.norm(self.position - other.position)
                    if dist < self.perception_radius:
                        diff = self.position - other.position
                        if dist > 0:
                            diff /= dist
                        steering += diff
                        total += 1
            if total > 0:
                steering /= total
            return steering
        except Exception as e:
            st.error(f"Error in Boid separation: {e}")
            return np.zeros(3)

    def align(self, boids: List['Boid']) -> np.ndarray:
        try:
            steering = np.zeros(3)
            total = 0
            for other in boids:
                if other is not self:
                    dist = np.linalg.norm(self.position - other.position)
                    if dist < self.perception_radius:
                        steering += other.velocity
                        total += 1
            if total > 0:
                steering /= total
                steering = (steering / np.linalg.norm(steering)) * self.max_speed if np.linalg.norm(steering) > 0 else steering
            return steering * 0.5
        except Exception as e:
            st.error(f"Error in Boid alignment: {e}")
            return np.zeros(3)

    def cohere(self, boids: List['Boid']) -> np.ndarray:
        try:
            center = np.zeros(3)
            total = 0
            for other in boids:
                if other is not self:
                    dist = np.linalg.norm(self.position - other.position)
                    if dist < self.perception_radius:
                        center += other.position
                        total += 1
            if total > 0:
                center /= total
                steering = center - self.position
                if np.linalg.norm(steering) > 0:
                    steering = (steering / np.linalg.norm(steering)) * self.max_speed
                return steering * 0.1
            return np.zeros(3)
        except Exception as e:
            st.error(f"Error in Boid cohesion: {e}")
            return np.zeros(3)

# Ant class for path optimization
class Ant:
    def __init__(self, position: np.ndarray):
        self.position = position
        self.velocity = np.random.uniform(-1, 1, 3)
        self.path = [position.copy()]
        self.target = np.array([50, 50, 50])  # Central target in 100x100x100 space

    def update(self, pheromones: np.ndarray):
        try:
            self.velocity = 0.7 * self.velocity + 0.3 * (self.target - self.position)
            speed = np.linalg.norm(self.velocity)
            if speed > 1.5:
                self.velocity = (self.velocity / speed) * 1.5
            self.position += self.velocity
            self.position = np.clip(self.position, 0, 100)
            self.path.append(self.position.copy())
            idx = tuple(self.position.astype(int) // 10)
            if idx[0] < pheromones.shape[0] and idx[1] < pheromones.shape[1] and idx[2] < pheromones.shape[2]:
                pheromones[idx] += 0.1  # Deposit pheromone
        except Exception as e:
            st.error(f"Error in Ant update: {e}")

# Bee class for structure building
class Bee:
    def __init__(self, position: np.ndarray):
        self.position = position
        self.velocity = np.random.uniform(-1, 1, 3)
        self.structure_points: List[np.ndarray] = []

    def update(self, bees: List['Bee']):
        try:
            center = np.mean([b.position for b in bees], axis=0)
            self.velocity = 0.5 * self.velocity + 0.5 * (center - self.position)
            speed = np.linalg.norm(self.velocity)
            if speed > 1.5:
                self.velocity = (self.velocity / speed) * 1.5
            self.position += self.velocity
            self.position = np.clip(self.position, 0, 100)
            if np.random.random() < 0.05:  # Randomly add to structure
                self.structure_points.append(self.position.copy())
        except Exception as e:
            st.error(f"Error in Bee update: {e}")

# Simulation state management
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.boids = []
    st.session_state.ants = []
    st.session_state.bees = []
    st.session_state.pheromones = np.zeros((10, 10, 10))  # 100x100x100 grid scaled down
    st.session_state.frame = 0
    st.session_state.running = False

# Sidebar for simulation selection
with st.sidebar:
    st.header("Swarm Simulation Controls")
    sim_type = st.selectbox("Select Swarm Model", ["Boid Model (Flocking Drones)", "Ant Colony (Path Optimization)", "Bee Colony (Structure Building)"])
    num_agents = st.slider("Number of Agents", 10, 100, 50)
    speed = st.slider("Animation Speed (updates/sec)", 1, 10, 5)
    reset = st.button("Reset Simulation")
    run = st.button("Run/Stop Simulation")

# Toggle simulation running state
if run:
    st.session_state.running = not st.session_state.running

# Reset simulation if requested
if reset or not st.session_state.initialized:
    try:
        st.session_state.boids = [Boid(np.random.uniform(0, 100, 3), np.random.uniform(-1, 1, 3)) for _ in range(num_agents)]
        st.session_state.ants = [Ant(np.random.uniform(0, 100, 3)) for _ in range(num_agents)]
        st.session_state.bees = [Bee(np.random.uniform(0, 100, 3)) for _ in range(num_agents)]
        st.session_state.pheromones = np.zeros((10, 10, 10))
        st.session_state.frame = 0
        st.session_state.initialized = True
        st.session_state.running = False
    except Exception as e:
        st.error(f"Error in initialization: {e}")

# Main simulation logic
def update_simulation():
    try:
        if sim_type == "Boid Model (Flocking Drones)":
            for boid in st.session_state.boids:
                boid.update(st.session_state.boids)
        elif sim_type == "Ant Colony (Path Optimization)":
            st.session_state.pheromones *= 0.95  # Pheromone evaporation
            for ant in st.session_state.ants:
                ant.update(st.session_state.pheromones)
        else:  # Bee Colony
            for bee in st.session_state.bees:
                bee.update(st.session_state.bees)
        st.session_state.frame += 1
    except Exception as e:
        st.error(f"Error in simulation update: {e}")

# 3D Visualization
def create_3d_plot():
    try:
        fig = go.Figure()
        if sim_type == "Boid Model (Flocking Drones)":
            positions = np.array([boid.position for boid in st.session_state.boids])
            fig.add_trace(go.Scatter3d(
                x=positions[:, 0], y=positions[:, 1], z=positions[:, 2],
                mode='markers', marker=dict(size=5, color='blue'),
                name='Drones'
            ))
        elif sim_type == "Ant Colony (Path Optimization)":
            for ant in st.session_state.ants:
                path = np.array(ant.path[-50:])  # Limit path for performance
                fig.add_trace(go.Scatter3d(
                    x=path[:, 0], y=path[:, 1], z=path[:, 2],
                    mode='lines', line=dict(color='green', width=2),
                    name=f'Ant {id(ant)}'
                ))
            fig.add_trace(go.Scatter3d(
                x=[50], y=[50], z=[50],
                mode='markers', marker=dict(size=8, color='red'),
                name='Target'
            ))
        else:  # Bee Colony
            positions = np.array([bee.position for bee in st.session_state.bees])
            fig.add_trace(go.Scatter3d(
                x=positions[:, 0], y=positions[:, 1], z=positions[:, 2],
                mode='markers', marker=dict(size=5, color='yellow'),
                name='Bees'
            ))
            for bee in st.session_state.bees:
                if bee.structure_points:
                    struct = np.array(bee.structure_points)
                    fig.add_trace(go.Scatter3d(
                        x=struct[:, 0], y=struct[:, 1], z=struct[:, 2],
                        mode='markers', marker=dict(size=3, color='orange'),
                        name=f'Structure {id(bee)}'
                    ))
        fig.update_layout(
            title=f"{sim_type} - Frame {st.session_state.frame}",
            scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z',
                       xaxis_range=[0, 100], yaxis_range=[0, 100], zaxis_range=[0, 100]),
            width=800, height=600
        )
        return fig
    except Exception as e:
        st.error(f"Error in 3D plot creation: {e}")
        return go.Figure()

# Main UI and loop
try:
    st.title("Advanced 3D Swarm Simulation")
    plot_placeholder = st.empty()
    if st.session_state.running:
        update_simulation()
        fig = create_3d_plot()
        plot_placeholder.plotly_chart(fig, use_container_width=True)
        time.sleep(1.0 / speed)  # Control animation speed
        st.rerun()
    else:
        fig = create_3d_plot()
        plot_placeholder.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error in main loop: {e}")
