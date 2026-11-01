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
    FPS: int = 1
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
# CELL ARRAY SETUP AND PHYSICS CALCULATIONS METHODS
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

        self.cell_pressure = np.zeros((CONFIG.CELL_COUNT_X, CONFIG.CELL_COUNT_Y), dtype=float)
        self.time_step = 1 / 60
        self.density = 1

    def randomize_velocities(self, velocity):
        """ Takes the initial arrays of boundary velocities and assigns a random
        value -1.00 <= vel <= 1.00.
        """
        for x, row in enumerate(velocity):
            for y, element in enumerate(row):
                velocity[x][y] = round(random.uniform(-1.0, 1.0), 2)

        return velocity

    # UPDATE DIVERGENCE
    # ==========================================================================
    def calculate_cell_velocity_divergence(self, x, y):
        """ Calculate the divergence of the velocity for a given cell identified by
        interger coordinates (cell_x, cell_y).
        """
        # Get velocities at each edge of cell
        velocity_R = self.velocities_x[x + 1, y + 0]
        velocity_L = self.velocities_x[x + 0, y + 0]
        velocity_T = self.velocities_y[x + 0, y + 1]
        velocity_B = self.velocities_y[x + 0, y + 0]

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
        for x in range(CONFIG.CELL_COUNT_X):
            for y in range(CONFIG.CELL_COUNT_Y):
                self.cell_divergence[x][y] = self.calculate_cell_velocity_divergence(x, y)

    def update_cell_devergence_color(self):
        """  """
        for x in range(CONFIG.CELL_COUNT_X):
            for y in range(CONFIG.CELL_COUNT_Y):
                if -0.01 < self.cell_divergence[x][y] < 0.0:
                    self.cell_divergence_color[x][y] = (255 * abs(self.cell_divergence[x][y]) * 100, 0, 0)
                elif self.cell_divergence[x][y] <= -0.01:
                    self.cell_divergence_color[x][y] = CONFIG.RED

                elif 0.01 > self.cell_divergence[x][y] > 0.0:
                    self.cell_divergence_color[x][y] = (0, 0, 255 * abs(self.cell_divergence[x][y]) * 100)
                elif self.cell_divergence[x][y] >= 0.01:
                    self.cell_divergence_color[x][y] = CONFIG.BLUE
                
                else:
                    self.cell_divergence_color[x][y] = CONFIG.BLACK

    # UPDATE PRESSURE
    # ==========================================================================
    def get_pressure(self, x, y):
        """ Retrieves the currently calculated pressure for a single cell at
        coordinates x, y. Assigns pressure to 0.0 if adjacent 'cell' in question
        is outside the border. 
        """
        if x < 0 or x >= CONFIG.CELL_COUNT_X or y < 0 or y >= CONFIG.CELL_COUNT_Y:
            return 0
        else:
            return self.cell_pressure[x][y]

    def update_cell_pressure(self, x, y):
        """ Calculates the pressure for a cell at coordinates x, y based on the
        surrounding pressures and velcocities. Updates the pressure array with
        the newly calculated pressure value.
        """
        pressure_R = self.get_pressure(x + 1, y + 0)
        pressure_L = self.get_pressure(x - 1, y + 0)
        pressure_T = self.get_pressure(x + 0, y + 1)
        pressure_B = self.get_pressure(x + 0, y - 1)
        velocity_R = self.velocities_x[x + 1, y + 0]
        velocity_L = self.velocities_x[x + 0, y + 0]
        velocity_T = self.velocities_y[x + 0, y + 1]
        velocity_B = self.velocities_y[x + 0, y + 0]

        pressure_sum = pressure_R + pressure_L + pressure_T + pressure_B
        delta_velocities_sum = velocity_R - velocity_L + velocity_T - velocity_B
        self.cell_pressure[x][y] = (pressure_sum - (self.density * CONFIG.CELL_SIZE * delta_velocities_sum / self.time_step)) / 4

    def update_pressures(self, n_iterations):
        """ Iterates through the entire pressure array and calculates the value
        of each cell. Because the calulation to find pressure requires us to
        know the pressures, we use the Gauss-Seidel method as an approximation
        to converge on the correct values. This works by iterating through the
        calulations for each all cells repeatedly n-number of times.
        """
        for n in range(n_iterations):
            for x in range(CONFIG.CELL_COUNT_X):
                for y in range(CONFIG.CELL_COUNT_Y):
                    self.update_cell_pressure(x, y)

    # UPDATE VELOCITIES
    # ==========================================================================
    def update_velocities(self):
        """ v_i = u_i - K * (P_i - P_c)    or    (P_c - Pi)
        where K is a constant: (density * cell size) / timestep
        and i is which cell you are referenceing. There are 4 total:
        R, L, T, B
        """
        K = self.time_step / (self.density * CONFIG.CELL_SIZE)

        for x, row in enumerate(self.velocities_x):
            for y, element in enumerate(row):
                pressure_R = self.get_pressure(x, y)
                pressure_L = self.get_pressure(x - 1, y)
                self.velocities_x[x][y] -= K * (pressure_R - pressure_L)

        for x, row in enumerate(self.velocities_y):
            for y, element in enumerate(row):
                pressure_T = self.get_pressure(x, y)
                pressure_B = self.get_pressure(x , y - 1)
                self.velocities_y[x][y] -= K * (pressure_T - pressure_B)


# ==============================================================================
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

        # Initiate empty fluid grid of cells and velocites
        self.state = fluidGrid(CONFIG.CELL_COUNT_X, CONFIG.CELL_COUNT_Y, CONFIG.CELL_SIZE)

        # Fill the velocities arrays with random values
        self.state.randomize_velocities(self.state.velocities_x)
        self.state.randomize_velocities(self.state.velocities_y)

        # TEST PRINTING
        # ======================================================================
        # print("x-velocities")
        # print(self.state.velocities_x)
        # print("\ny-velocities")
        # print(self.state.velocities_y)
        # print("\ndivergence")
        # print(self.state.cell_divergence)

    # EVENT HANDLERS
    # ==========================================================================
    def handle_events(self):
        """ Event handlers (button presses and mouse clicks). """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()  # Get the mouse position
                print(f'Mouse clicked at: x = {x}, y = {y}')  # Print coordinates

    # UPDATING PHYSICS
    # ==========================================================================
    def update_physics(self):
        """ Order of operations to update all the physical parameters.
            1. Cell divergence
            2. Cell divergence color
            3. Pressures
            4. Velocities 
        """
        self.state.update_cell_divergence()
        self.state.update_cell_devergence_color()
        self.state.update_pressures(1) # Higher number --> more accurate. => 8
        self.state.update_velocities()

    # RENDERING
    # ==========================================================================
    def render(self):
        """ RENDERED OBJECTS:
            1. Cells blocks and borders
            2. Divergence text
            3. x-velocity vectors
            4. y-velocity vectors
            """
        self.screen.fill(CONFIG.BLACK)

        # 1. Render cell blocks with colors calculated based on div strength
        for x in range(CONFIG.CELL_COUNT_X):
            for y in range(CONFIG.CELL_COUNT_Y):
                pygame.draw.rect(
                    self.screen,
                    self.state.cell_divergence_color[x][y],
                    (CONFIG.CELL_SIZE + (x * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE + (y * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE, CONFIG.CELL_SIZE),
                )
                # Renders the white border
                pygame.draw.rect(
                    self.screen,
                    CONFIG.WHITE,
                    (CONFIG.CELL_SIZE + (x * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE + (y * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE, CONFIG.CELL_SIZE),
                    width=1,
                )

        # 2. Render divergence text
                text_surface = self.font.render(str(round(self.state.cell_divergence[x][y], 4)), True, CONFIG.WHITE)
                # Blit the text surface onto the screen
                self.screen.blit(text_surface, (CONFIG.CELL_SIZE + (x * CONFIG.CELL_SIZE) + 10, CONFIG.CELL_SIZE + (y * CONFIG.CELL_SIZE) + 10))

        # 3. Render the x-velocity vectors
        for x, row in enumerate(self.state.velocities_x):
            for y, element in enumerate(row):
                pygame.draw.line(
                    self.screen,
                    CONFIG.GREEN,
                    (CONFIG.CELL_SIZE + (x * CONFIG.CELL_SIZE), 1.5 * CONFIG.CELL_SIZE + (y * CONFIG.CELL_SIZE)),
                    (CONFIG.CELL_SIZE + (x * CONFIG.CELL_SIZE) + (40 * self.state.velocities_x[x][y]), 1.5 * CONFIG.CELL_SIZE + (y * CONFIG.CELL_SIZE)),
                    3
                )

        # 4. Render the y-velocity vectors
        for x, row in enumerate(self.state.velocities_y):
            for y, element in enumerate(row):
                pygame.draw.line(
                    self.screen,
                    CONFIG.GREEN,
                    (1.5 * CONFIG.CELL_SIZE + (x * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE + (y * CONFIG.CELL_SIZE)),
                    (1.5 * CONFIG.CELL_SIZE + (x * CONFIG.CELL_SIZE), CONFIG.CELL_SIZE + (y * CONFIG.CELL_SIZE) + (40 * self.state.velocities_y[x][y])),
                    3
                )

        # Updates the screen with all render changes
        pygame.display.update()

    # RUN SIMULATION
    # ==========================================================================
    def run(self):
        """ Main run loop. What to do each clock tick. """ 
        while self.running:
            self.handle_events()
            self.update_physics()
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