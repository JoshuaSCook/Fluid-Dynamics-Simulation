import sys
import numpy as np
import pygame
from dataclasses import dataclass
import random

# ==============================================================================
# CONFIGURATION CONSTANTS
# ==============================================================================
@dataclass(frozen=True)
class SimulationConfig:
    SCREEN_SIZE_X: int = 300
    SCREEN_SIZE_Y: int = 200
    FPS: int = 60
    BLACK: tuple = (0, 0, 0)
    WHITE: tuple = (255, 255, 255)

    CELL_COUNT_X: int = 4
    CELL_COUNT_Y: int = 3
    CELL_SIZE: float = 100.0

CONFIG = SimulationConfig()


# ==============================================================================
# CELL ARRAY SETUP AND PHYSICS CALCULATIONS
# ==============================================================================
class fluidGrid:
    """
    Initializes the boundary velocities. self.velocities are 2d arrays that are
    n-number of cells in rows and columns + 1 to assign a velocity at every
    edge.
    """
    def __init__(self, cell_count_x, cell_count_y, cell_size):
        self.cell_count_x = int(CONFIG.CELL_COUNT_X)
        self.cell_count_y = int(CONFIG.CELL_COUNT_Y)
        self.cell_size = float(CONFIG.CELL_SIZE)

        self.velocities_x = np.zeros((CONFIG.CELL_COUNT_X + 1, CONFIG.CELL_COUNT_Y), dtype=float)
        self.velocities_y = np.zeros((CONFIG.CELL_COUNT_X, CONFIG.CELL_COUNT_Y + 1), dtype=float)

    def randomize_velocities(self):
        """
        Takes the initial arrays of boundary velocities and assigns a random
        value 0.00 <= vel <= 1.00
        """
        for i, row in enumerate(self.velocities_x):
            for j, element in enumerate(row):
                self.velocities_x[i][j] = round(random.uniform(0.0, 1.0), 2)

        return self.velocities_x

    def calculate_cell_velocity_divergence(self, cell_x, cell_y):
        """
        Calculate the divergence of the velocity for a given cell identified by
        interger coordinates (cell_x, cell_y)
        """
        # Get velocities at each edge of cell
        velocity_R = self.velocities_x[cell_x + 1, cell_y + 0]
        velocity_L = self.velocities_x[cell_x + 0, cell_y + 0]
        velocity_T = self.velocities_y[cell_x + 0, cell_y + 1]
        velocity_B = self.velocities_y[cell_x + 0, cell_y + 0]

        # Calculate how fast the fluid's velocity is changing across this cell
        # on either axies
        gradient_x = (velocity_R - velocity_L) / self.cell_size
        gradient_y = (velocity_T - velocity_B) / self.cell_size
        # Sum to calculate if more fluid is entering (div < 0) or exiting the
        # cell (div > 0)
        divergence = gradient_x + gradient_y
        return divergence

# ==============================================================================
# THE MAIN SIMULATION ENGINE
# ==============================================================================
class Simulation:
    """Execution of main loop logic, math operations and rendering."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((CONFIG.SCREEN_SIZE_X, CONFIG.SCREEN_SIZE_Y))
        pygame.display.set_caption("Simulation")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initiate the fluid grid of cells and velocites
        self.state = fluidGrid(3, 2, 100)
        
        # Test printing of values
        self.state.randomize_velocities()
        print(self.state.velocities_x)

        for i in range(len(self.state.velocities_x)):
            for j in range(len(self.state.velocities_y)):
                a = self.state.calculate_cell_velocity_divergence(i-1, j-1)
                print(round(a, 4))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def render(self):
        self.screen.fill(CONFIG.BLACK)

        pygame.draw.rect(
            self.screen,
            CONFIG.WHITE,
            (0,0,100,100)
        )

        pygame.display.flip()

    def run(self):       
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(CONFIG.FPS)
            
        pygame.quit()
        sys.exit()


# ==============================================================================
# EXECUTION ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    # Inject the container into the execution engine and run it!
    simulation = Simulation()
    simulation.run()