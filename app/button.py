import pygame

class Button:
    def __init__(self, x, y, width, height, onclickFunction=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.onclickFunction = onclickFunction
        self.fillColors = {
            'normal': (255, 255, 255),  # White
            'hover': (200, 200, 200),    # Light Gray
            'pressed': (255, 0, 0)    # Red
        }
        self.state = 'normal'

    def draw(self, surface):
        pygame.draw.rect(surface, self.fillColors[self.state], self.rect)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self.state = 'hover'
            else:
                self.state = 'normal'
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.state = 'pressed'
                if self.onclickFunction:
                    self.onclickFunction()
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.state == 'pressed':
                self.state = 'hover'




# ==============================================================================
# HOW TO USE
# ==============================================================================
# pygame.init()
# screen = pygame.display.set_mode((400, 300))
# button = Button(100, 100, 200, 50, onclickFunction=lambda: print('Button Pressed'))

# running = True
# while running:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             running = False
#         button.handleEvent(event)

#     screen.fill((0, 0, 0))  # Clear screen
#     button.draw(screen)      # Draw button
#     pygame.display.flip()    # Update display

# pygame.quit()