import board, time, random, os, gc
from analogio import AnalogIn
from digitalio import DigitalInOut, Direction, Pull
from simpleio import map_range

# Adding ringtone sound type
import adafruit_rtttl

# Init Matrix Display
import rgbmatrix
import framebufferio
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_bitmap_font import bitmap_font

'''
# Adding Accelerometer support
import adafruit_lis3dh

# Acelerometer config
i2c = board.I2C()
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, address=0x19)
lis3dh.range = adafruit_lis3dh.RANGE_2_G
'''

# Init RGB Matrix as Display
displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=64, height=64, bit_depth=4,
    rgb_pins=[board.MTX_R1, board.MTX_G1, board.MTX_B1,
              board.MTX_R2, board.MTX_G2, board.MTX_B2],
    addr_pins=[board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC,
               board.MTX_ADDRD, board.MTX_ADDRE],
    clock_pin=board.MTX_CLK, latch_pin=board.MTX_LAT, output_enable_pin=board.MTX_OE,
    doublebuffer=True)

# Keep name Screen just to keep easy porting from Neopixel
screen = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)

# Not used if using Accelerometer
joystick_x = AnalogIn(board.A1)
joystick_y = AnalogIn(board.A2)

# Changed to Button UP for use with Accelerometer 
trigger = DigitalInOut(board.BUTTON_UP)
trigger.direction = Direction.INPUT
trigger.pull = Pull.UP

# Setup Buzzer. Can be any digital Pin
buzzer = board.A4

font = bitmap_font.load_font("/fonts/tom-thumb.pcf")

# Creating colors
COLORS = [
    0x000000,  # Black
    0xFF0000,  # Red
    0xFF7F00,  # Orange
    0xFFFF00,  # Yellow
    0x00FF00,  # Green
    0x0000FF,  # Blue
    0x4B0082,  # Indigo
    0x8B00FF   # Violet
]

# Ship Bitmaps - simple list with 0s and 1s
INVADER_BITMAP = [
    [0, 1, 0, 1, 0, 0],
    [1, 1, 1, 1, 1, 0],
    [1, 1, 0, 1, 1, 0],
    [1, 0, 1, 0, 1, 0],
    [0, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0]
]

PLAYER_BITMAP = [
    [0, 0, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 0, 0],
    [0, 1, 0, 1, 0, 0],
    [1, 1, 1, 1, 1, 0]
]

# Player Ship Explosion
EXPLOSION_BITMAPS = [
    # Frame 1
    [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0],
        [0, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0]
    ],
    # Frame 2
    [
        [0, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0]
    ],
    # Frame 3
    [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 1, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0]
    ],
    # Frame 4
    [
        [0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 0]
    ]
]


def get_joystick(): # With Analog Joystick
    # Returns -1 0 or 1 depending on joystick position
    x_coord = int(map_range(joystick_x.value, 200, 65535, -2, 2))
    y_coord = int(map_range(joystick_y.value, 200, 65535, -2, 2))
    return x_coord, y_coord

'''
def get_joystick(): # Using Accelerometer
    # Reads accelerometer values ​​and converts them to G
    x, y, z = (value / adafruit_lis3dh.STANDARD_GRAVITY for value in lis3dh.acceleration)
    
    # Calculates the magnitude of the tilt on each axis
    x_mag = abs(x)
    y_mag = abs(y)
    
    # Determine which axis has the greatest inclination
    if x_mag > y_mag:
        # X Axis (Left/Right)
        if x > 0.1:
            dx = 2  # Right
        elif x < -0.01:
            dx = -2  # Left
        else:
            dx = 0
        dy = 0  # Block Y
    else:
        # Y Axis (UP/Down)
        if y > 0.2:
            dy = 2  # Down
        elif y < -0.2:
            dy = -2  # UP
        else:
            dy = 0
        dx = 0  # Block X
    
    return dx, dy
'''

def shoot_sound():
    adafruit_rtttl.play(buzzer, "shoot:d=4,o=5,b=880:8c6")
    
def xevious_sound():
    adafruit_rtttl.play(buzzer, "Xevious:d=4,o=5,b=160:16c,16c6,16b,16c6,16e6,16c6,16b,16c6,16c,16c6,16a#,16c6,16e6,16c6,16a#,16c6,16c,16c6,16a,16c6,16e6,16c6,16a,16c6,16c,16c6,16g#,16c6,16e6,16c6,16g#,16c6")

def galaga_sound():
    adafruit_rtttl.play(buzzer, "Galaga:d=4,o=5,b=125:8g4,32c,32p,8d,32f,32p,8e,32c,32p,8d,32a,32p,8g,32c,32p,8d,32f,32p,8e,32c,32p,8g,32b,32p,8c6,32a#,32p,8g#,32g,32p,8f,32d#,32p,8d,32a#4,32p,8a#,32c6,32p,8a#,32g,32p,16a,16f,16d,16g,16e,16d")


class Invader:
    def __init__(self, x, y, parent_group):
        self.x = x
        self.y = y
        self.width = 6
        self.height = 6
        self.color = random.choice(COLORS[1:])
        self.bitmap = INVADER_BITMAP
        self.sprite_group = displayio.Group()
        self.parent_group = parent_group
        self.visible = True
        self.create_sprite()
        self.draw()  # Draw Imediatelly

    def create_sprite(self):
        # Clean actual group
        while len(self.sprite_group) > 0:
            self.sprite_group.pop()
        
        if not self.visible:
            return
            
        # Read Bitmap and draw pixels
        for i in range(self.height):
            for j in range(self.width):
                if self.bitmap[i][j]:
                    pixel = Rect(j, i, 1, 1, fill=self.color)
                    self.sprite_group.append(pixel)
        
        self.sprite_group.x = self.x
        self.sprite_group.y = self.y

    def draw(self):
        if self.visible:
            if self.sprite_group not in self.parent_group:
                self.parent_group.append(self.sprite_group)
        else:
            if self.sprite_group in self.parent_group:
                self.parent_group.remove(self.sprite_group)

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        
        # Check Vertical Limits. Reverse
        if self.y < 0:
            self.y = 0  # TOP
        # Check Vertical Limits. Normal
        if self.y >= 58:  # 64 - 6
            self.y = 57  # Base
            
        self.sprite_group.x = self.x
        self.sprite_group.y = self.y
        
        # Lateral Limits
        if self.x <= 0 or self.x >= 58:
            return True
        return False

    def hide(self):
        self.visible = False
        self.draw()

    def shoot(self):
        # Projectile Origin from center of enemy ship
        return Projectile(self.x + 2, self.y + 6, COLORS[1], self.parent_group)

class PlayerShip:
    def __init__(self, parent_group):
        self.x = 29  # Horizontal Center
        self.y = 58  # Vertical Position
        self.lives = 3
        self.exploding = False
        self.explode_timer = 0
        self.explosion_frame = 0
        self.bitmap = PLAYER_BITMAP
        self.sprite_group = displayio.Group()
        self.parent_group = parent_group
        self.visible = True
        self.create_sprite()
        self.draw()  

    def create_sprite(self):
        while len(self.sprite_group) > 0:
            self.sprite_group.pop()
        
        if not self.visible:
            return
        
        # Choose Each Frame and Attribute a different Collor
        if self.exploding:
            current_bitmap = EXPLOSION_BITMAPS[self.explosion_frame]
            explosion_colors = [0xFFFFFF, 0xFFFF00, 0xFF7F00, 0xFF0000]  # White, Yellow, Orange, Red
            color = explosion_colors[self.explosion_frame]
        else:
            current_bitmap = self.bitmap
            color = COLORS[5]  # Blue, for normal ship
            
        for i in range(6):
            for j in range(6):
                if current_bitmap[i][j]:
                    pixel = Rect(j, i, 1, 1, fill=color)
                    self.sprite_group.append(pixel)
        
        self.sprite_group.x = self.x
        self.sprite_group.y = self.y

    def update_explosion(self):
        if self.exploding:
            elapsed = time.monotonic() - self.explode_timer
            # Change Frame each 0.2 secs
            self.explosion_frame = min(3, int(elapsed / 0.2))
            
            # Recreate Sprite
            self.create_sprite()
            
            # End Explosion after 1s
            if elapsed > 1.0:
                self.exploding = False
                self.explosion_frame = 0
                self.create_sprite()  # Back to normal Ship
                return True  # Explosion is over
        return False

    def draw(self):
        if self.visible:
            if self.sprite_group not in self.parent_group:
                self.parent_group.append(self.sprite_group)
        else:
            if self.sprite_group in self.parent_group:
                self.parent_group.remove(self.sprite_group)

    def draw_lives(self, lives_group):
        # Clean Group only if lives changed
        if len(lives_group) != self.lives * 4:  # 4 pixels for life (2x2)
            while len(lives_group) > 0:
                lives_group.pop()
            
            # Drwa Lives top Right (aligned with score y=6)
            for i in range(self.lives):
                start_x = 58 - i * 4  # Draw from right
                for dx in range(2):
                    for dy in range(2):
                        pixel = Rect(start_x + dx, 3 + dy, 1, 1, fill=COLORS[5])  # Blue, aligned with score
                        lives_group.append(pixel)

    def move(self, dx):
        if not self.exploding:  # Move if not exploding
            self.x += dx
            if self.x < 0:
                self.x = 0
            elif self.x >= 58:  # 64 - 6
                self.x = 57
            self.sprite_group.x = self.x

    def explode(self):
        if not self.exploding:  # Explode only if not exploding already
            self.exploding = True
            self.explode_timer = time.monotonic()
            self.explosion_frame = 0
            self.create_sprite()  # First frame for explosion
            

class Projectile:
    def __init__(self, x, y, color, parent_group):
        self.x = x
        self.y = y
        self.color = color
        self.sprite = Rect(x, y, 1, 2, fill=color)
        self.parent_group = parent_group
        self.active = True
        self.parent_group.append(self.sprite)

    def update(self, speed):
        # Move projectile
        self.y += speed
        self.sprite.y = self.y
        
        # Check screen limits, and remove projectile
        if self.y < -2 or self.y >= 66:
            self.active = False
            if self.sprite in self.parent_group:
                self.parent_group.remove(self.sprite)
            return True
        return False

    def draw(self):
        # Update sprite position
        self.sprite.x = self.x
        self.sprite.y = self.y
        if self.active:
            if self.sprite not in self.parent_group:
                self.parent_group.append(self.sprite)
        else:
            if self.sprite in self.parent_group:
                self.parent_group.remove(self.sprite)

class Game:
    def __init__(self):
        self.main_group = displayio.Group()
        
        # Draw Score
        self.score_text = label.Label(font, text="0000", color=COLORS[7], x=2, y=6)
        self.main_group.append(self.score_text)
        
        # Draw Lives
        self.lives_group = displayio.Group()
        self.main_group.append(self.lives_group)
        
        # Draw Player Ship
        self.player_ship = PlayerShip(self.main_group)
        
        self.invaders = [] # Clean Invaders list
        self.projectiles = [] # Clean player projectiles list
        self.enemy_projectiles = [] # Clean enemy projectiles list
        self.score = 0 # Initial Score
        self.level = 1 # Initial Level
        self.invader_move_direction = 1 # Top Down
        self.invader_speed = 0.1 
        self.game_over = False
        self.reverse = False
        
        # Configure Display Group
        screen.root_group = self.main_group
        
        self.resetinvaders()
        galaga_sound()
    
    def resetlevel():
        self.invaders = [] # Clean Invaders list
        self.projectiles = [] # Clean player projectiles list
        self.enemy_projectiles = [] # Clean enemy projectiles list
        self.invader_move_direction = 1 # Top Down
        self.invader_speed = 0.1
        self.reverse = False

    def resetinvaders(self):
        # Hide old invaders
        for invader in self.invaders:
            invader.hide()
        self.invaders = [] # Clean list
        
        # Create new invaders
        for i in range(5):  # 5 cols
            for j in range(3):  # 3 rows
                # 10 pixels between cols, 8 between rows
                x_pos = i * 10 + 4  
                y_pos = j * 8 + 11 
                invader = Invader(x_pos, y_pos, self.main_group)
                self.invaders.append(invader)
        
        # Reset direction
        self.invader_move_direction = 1
        self.reverse = False 

    def draw(self):
        if self.game_over:
            # Remove only invaders and enemy projectiles
            for invader in self.invaders:
                invader.hide()  
            
            for projectile in self.projectiles + self.enemy_projectiles:
                projectile.active = False
                projectile.draw()  
            
            # Game Over
            game_over_count = sum(1 for item in self.main_group if isinstance(item, label.Label) and item.text == "GAME OVER")
            if game_over_count == 0:
                game_over_text = label.Label(font, text="GAME OVER", color=COLORS[1], x=12, y=30)
                self.main_group.append(game_over_text)
            return
        
        # Draw Enemy
        for invader in self.invaders:
            invader.draw()
            
        # Draw Player  
        self.player_ship.draw()
        
        
        # Draw Projectiles and Enemy Projectiles
        for projectile in self.projectiles:
            projectile.draw()
                        
        for projectile in self.enemy_projectiles:
            projectile.draw()
        
        # Update Lives
        self.player_ship.draw_lives(self.lives_group)

    def update(self, dt):
        if self.game_over:
            # Wait for button press to restart game
            if not trigger.value:  # Button pressed
                time.sleep(0.2)  # Debounce
                self.reset_game()
                return
            return

        explosion_finished = self.player_ship.update_explosion()
        
        if explosion_finished and self.player_ship.lives <= 0:
            self.game_over = True
            return
                
        dx, dy = get_joystick() # Accelerometer

        if not self.player_ship.exploding:
            self.player_ship.move(dx)
        
        if not trigger.value and not self.player_ship.exploding and len(self.projectiles) < 3:
            self.projectiles.append(Projectile(self.player_ship.x + 3, self.player_ship.y - 2, COLORS[7], self.main_group))
            shoot_sound()
            time.sleep(0.05)

        # Move player projectiles (UP)
        for projectile in self.projectiles[:]:  # Use list copy for safe removal
            if projectile.update(-3):  # UP
                self.projectiles.remove(projectile)
            else:
                # Check for collision with invaders
                for invader in self.invaders[:]:  # Use list copy for safe removal
                    if (invader.visible and 
                        invader.x <= projectile.x < invader.x + 6 and 
                        invader.y <= projectile.y < invader.y + 6):
                        invader.hide()
                        self.invaders.remove(invader)
                        shoot_sound()
                        projectile.active = False
                        projectile.draw()
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)
                        self.score += 10
                        self.score_text.text = f"{self.score:04d}"
                        if self.score % 100 == 0:
                            self.player_ship.lives += 1
                        break

        # Move enemy projectiles (DOWN)
        for projectile in self.enemy_projectiles[:]:  # Use list copy for safe removal
            if projectile.update(2):  # Move down
                self.enemy_projectiles.remove(projectile)
            else:
                # Check for collision with player ship
                if (self.player_ship.x <= projectile.x < self.player_ship.x + 6 and 
                    self.player_ship.y <= projectile.y < self.player_ship.y + 6):
                    self.player_ship.lives -= 1
                    self.player_ship.explode()
                    projectile.active = False
                    projectile.draw()
                    if projectile in self.enemy_projectiles:
                        self.enemy_projectiles.remove(projectile)

        # Move invaders and check edge collision
        edge_hit = False
        for invader in self.invaders:
            if invader.move(self.invader_move_direction, 0):
                edge_hit = True

        if edge_hit:
            self.invader_move_direction *= -1
            # Move Invaders
            for invader in self.invaders:
                if not self.reverse:
                    invader.move(0, 2)  # DOWN
                else:
                    invader.move(0, -2)  # UP (Reverse)

        # Check Screen Limits
        if not self.reverse:
            for invader in self.invaders:
                if invader.y >= 58:  # Bottom
                    # Activate Reverse Mode
                    self.reverse = True
                    break
        
        if self.reverse:
            top_hit = False
            for invader in self.invaders:
                if invader.y <= 0:  # Top
                    top_hit = True
                    break
            
            if top_hit:
                # Disable Reverse Mode
                self.reverse = False
                for invader in self.invaders:
                    invader.move(0, 2)

        player_hit = False
        for invader in self.invaders[:]:  # Use list copy for safe removal
            if (invader.visible and 
                invader.x < self.player_ship.x + 6 and 
                invader.x + 6 > self.player_ship.x and
                invader.y < self.player_ship.y + 6 and 
                invader.y + 6 > self.player_ship.y):
                
                # Remove colliding invader
                invader.hide()
                self.invaders.remove(invader)
                player_hit = True
                break  

        if player_hit and not self.player_ship.exploding:
            self.player_ship.lives -= 1
            self.player_ship.explode()
            
            self.reverse = True

        # Enemy shooting - (8% chance)
        if random.random() < 0.08 and self.invaders and len(self.enemy_projectiles) < 8:
            shooter = random.choice(self.invaders)
            if shooter.visible:
                self.enemy_projectiles.append(shooter.shoot())

        # Remove invaders outside boundaries (using list comprehension)
        self.invaders = [invader for invader in self.invaders if invader.y < 70 and invader.y > -10]

        # Remove inactive projectiles (using list comprehension)
        self.projectiles = [p for p in self.projectiles if p.active]
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.active]

        # Level completion check - clear all projectiles when all invaders are defeated
        if not self.invaders and not self.game_over:
            # Clear all projectiles when level is completed
            for projectile in list(self.projectiles):  # Convert to list for safe iteration
                projectile.active = False
                projectile.draw()
            self.projectiles = []
            
            for projectile in list(self.enemy_projectiles):  # Convert to list for safe iteration
                projectile.active = False
                projectile.draw()
            self.enemy_projectiles = []
            
            self.level += 1
            self.resetinvaders()
            xevious_sound()

    def reset_game(self):
        """Reset the game to initial state"""
        # Clear all game objects using safe iteration
        for invader in list(self.invaders):  # Convert to list for safe iteration
            invader.hide()
        self.invaders = []
        
        for projectile in list(self.projectiles):  # Convert to list for safe iteration
            projectile.active = False
            projectile.draw()
        self.projectiles = []
        
        for projectile in list(self.enemy_projectiles):  # Convert to list for safe iteration
            projectile.active = False
            projectile.draw()
        self.enemy_projectiles = []
        
        # Reset game state
        self.score = 0
        self.level = 1
        self.game_over = False
        self.reverse = False
        self.invader_move_direction = 1
        
        # Reset player
        self.player_ship.lives = 3
        self.player_ship.x = 29
        self.player_ship.y = 58
        self.player_ship.exploding = False
        self.player_ship.explosion_frame = 0
        self.player_ship.create_sprite()
        
        # Update UI
        self.score_text.text = "0000"
        
        # Remove game over text if present
        for i in range(len(self.main_group) - 1, -1, -1):  # Iterate backwards for safe removal
            item = self.main_group[i]
            if isinstance(item, label.Label) and item.text == "GAME OVER":
                self.main_group.pop(i)
                break
        
        # Reset invaders
        self.resetinvaders()
        
        # Play start sound
        galaga_sound()

    def play(self):
        self.last_update_time = time.monotonic()
        while True:  # Changed to infinite loop to allow restarting
            current_time = time.monotonic()
            dt = current_time - self.last_update_time
            self.last_update_time = current_time
            
            self.update(dt)
            self.draw()
            time.sleep(0.008)


            
# Start Game as Class
game = Game()
game.play()


