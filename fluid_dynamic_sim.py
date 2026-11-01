import sys
import numpy as np
import pygame
from dataclasses import dataclass
import random


# ==============================================================================
# SIMULATION CONFIGURATION CONSTANTS
# ==============================================================================
@dataclass(frozen=True)
class SimulationConfig:
    """ Sets the global simulation configuation settings. """
    FPS: int = 60
    BLACK: tuple = (0, 0, 0)
    WHITE: tuple = (255, 255, 255)
    RED: tuple = (255, 0, 0)
    GREEN: tuple = (0, 255, 0)
    BLUE: tuple = (0, 0, 255)

    CELL_COUNT_X: int = 6
    CELL_COUNT_Y: int = 4
    CELL_SIZE: float = 100.0

    SCREEN_SIZE_X: int = (CELL_COUNT_X + 2) * CELL_SIZE
    SCREEN_SIZE_Y: int = (CELL_COUNT_Y + 2) * CELL_SIZE

CONFIG = SimulationConfig()


# ==============================================================================
# CELL ARRAY SETUP AND PHYSICS CALCULATIONS
# ==============================================================================
class fluidGrid:
    """ Initializes the boundary velocities. self.velocities are 2d arrays that are
    n-number of cells in rows and columns + 1 to assign a velocity at every
    edge.
    """
    def __init__(self, cell_count_x, cell_count_y, cell_size):
        self.cell_count_x = int(CONFIG.CELL_COUNT_X)
        self.cell_count_y = int(CONFIG.CELL_COUNT_Y)
        self.cell_size = float(CONFIG.CELL_SIZE)

        self.velocities_x = np.zeros((CONFIG.CELL_COUNT_X + 1, CONFIG.CELL_COUNT_Y), dtype=float)
        self.velocities_y = np.zeros((CONFIG.CELL_COUNT_X, CONFIG.CELL_COUNT_Y + 1), dtype=float)

        self.cell_divergence = np.zeros((CONFIG.CELL_COUNT_X, CONFIG.CELL_COUNT_Y), dtype=float)
        self.cell_divergence_color = np.zeros((CONFIG.CELL_COUNT_X, CONFIG.CELL_COUNT_Y), dtype=object)

    def randomize_velocities(self, vel_a):
        """ Takes the initial arrays of boundary velocities and assigns a random
        value 0.00 <= vel <= 1.00.
        """
        for i, row in enumerate(vel_a):
            for j, element in enumerate(row):
                vel_a[i][j] = round(random.uniform(0.0, 1.0), 2)

        return vel_a

    def calculate_cell_velocity_divergence(self, cell_x, cell_y):
        """ Calculate the divergence of the velocity for a given cell identified by
        interger coordinates (cell_x, cell_y).
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

    def update_cell_divergence(self):
        """ Calculates and updates the divergence for each cell. """
        for i in range(CONFIG.CELL_COUNT_X):
            for j in range(CONFIG.CELL_COUNT_Y):
                self.cell_divergence[i][j] = self.calculate_cell_velocity_divergence(i, j)

    def update_cell_devergence_color(self):
        """  """
        for i in range(CONFIG.CELL_COUNT_X):
            for j in range(CONFIG.CELL_COUNT_Y):
                if -0.01 < self.cell_divergence[i][j] < 0.0:
                    self.cell_divergence_color[i][j] = (255 * abs(self.cell_divergence[i][j]) * 100, 0, 0)
                elif self.cell_divergence[i][j] <= -0.01:
                    self.cell_divergence_color[i][j] = CONFIG.RED

                elif 0.01 > self.cell_divergence[i][j] > 0.0:
                    self.cell_divergence_color[i][j] = (0, 0, 255 * abs(self.cell_divergence[i][j]) * 100)
                elif self.cell_divergence[i][j] >= 0.01:
                    self.cell_divergence_color[i][j] = CONFIG.BLUE
                
                else:
                    self.cell_divergence_color[i][j] = CONFIG.BLACK


# ==============================================================================
# THE MAIN SIMULATION ENGINE
# ==============================================================================
class Simulation:
    """ Execution of sim initiation, logic, math operations, rendering and main 
    run loop.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((CONFIG.SCREEN_SIZE_X, CONFIG.SCREEN_SIZE_Y))
        pygame.display.set_caption("Simulation")
        self.clock = pygame.time.Clock()
        self.running = True

        # Create a font object
        self.font = pygame.font.SysFont("Monospace", 14)

        # Initiate the fluid grid of cells and velocites
        self.state = fluidGrid(CONFIG.CELL_COUNT_X, CONFIG.CELL_COUNT_Y, CONFIG.CELL_SIZE)

        # Fill the velocities arrays with random values
        self.state.randomize_velocities(self.state.velocities_x)
        self.state.randomize_velocities(self.state.velocities_y)
        self.state.update_cell_divergence()
        self.state.update_cell_devergence_color()

        # Test printing
        # ======================================================================
        print("x-velocities")
        print(self.state.velocities_x)
        print("\ny-velocities")
        print(self.state.velocities_y)
        print("\ndivergence")
        print(self.state.cell_divergence)
        # ======================================================================

    def handle_events(self):
        """ Event handlers (button presses and mouse clicks). """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()  # Get the mouse position
                print(f'Mouse clicked at: x = {x}, y = {y}')  # Print coordinates

    def render(self):
        """ RENDERED OBJECTS:
            1. Cells
            2. Divergence text
            3. x-velocity buttons
            4. y-velocity buttons
            """
        self.screen.fill(CONFIG.BLACK)

        # 1. Render the cell blocks with colors calculated based on div strength
        for i in range(CONFIG.CELL_COUNT_X):
            for j in range(CONFIG.CELL_COUNT_Y):
                pygame.draw.rect(
                    self.screen,
                    self.state.cell_divergence_color[i][j],
                    (CONFIG.CELL_SIZE + (i * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE + (j * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE, CONFIG.CELL_SIZE)
                )

        # 2. Render divergence text
                text_surface = self.font.render(str(round(self.state.cell_divergence[i][j], 4)), True, CONFIG.WHITE)
                # Blit the text surface onto the screen
                self.screen.blit(text_surface, (CONFIG.CELL_SIZE + (i * CONFIG.CELL_SIZE) + 10, CONFIG.CELL_SIZE + (j * CONFIG.CELL_SIZE) + 10))

        # 3. Render the x-velocity buttons
        for i in range(CONFIG.CELL_COUNT_X + 1):
            for j in range(CONFIG.CELL_COUNT_Y):
                pygame.draw.circle(
                    self.screen,
                    CONFIG.WHITE,
                    (CONFIG.CELL_SIZE + (i * CONFIG.CELL_SIZE), 1.5 * CONFIG.CELL_SIZE + (j * CONFIG.CELL_SIZE)),
                    6
                )

        # 4. render the y-velocity buttons
        for i in range(CONFIG.CELL_COUNT_X):
            for j in range(CONFIG.CELL_COUNT_Y + 1):
                pygame.draw.circle(
                    self.screen,
                    CONFIG.GREEN,
                    (1.5 * CONFIG.CELL_SIZE + (i * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE + (j * CONFIG.CELL_SIZE)),
                    6
                )

        # Updates the screen with all render changes
        pygame.display.update()

    def run(self):
        """ Main run loop. What to do each clock tick. """ 
        while self.running:
            self.handle_events()
            # Physics goes here...
            self.render()
            self.clock.tick(CONFIG.FPS)
            
        pygame.quit()
        sys.exit()


# ==============================================================================
# EXECUTION ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    simulation = Simulation()
    simulation.run()