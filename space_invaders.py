import board, time, random, os, gc
from analogio import AnalogIn
from digitalio import DigitalInOut, Direction, Pull
from simpleio import map_range
import adafruit_rtttl

import rgbmatrix
import framebufferio
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_bitmap_font import bitmap_font

# Init RGB Matrix
displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=64, height=64, bit_depth=4,
    rgb_pins=[board.MTX_R1, board.MTX_G1, board.MTX_B1,
              board.MTX_R2, board.MTX_G2, board.MTX_B2],
    addr_pins=[board.MTX_ADDRA, board.MTX_ADDRB, board.MTX_ADDRC,
               board.MTX_ADDRD, board.MTX_ADDRE],
    clock_pin=board.MTX_CLK, latch_pin=board.MTX_LAT, output_enable_pin=board.MTX_OE,
    doublebuffer=True)

screen = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)

joystick_x = AnalogIn(board.A1)
joystick_y = AnalogIn(board.A2)

trigger = DigitalInOut(board.D0)
trigger.direction = Direction.INPUT
trigger.pull = Pull.UP

# Setup Buzzer. Can be any digital Pin
buzzer = board.A3

# Load Font tom-thumb.pcf in fonts folder
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

# Invader and Player Bitmaps
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

# Player Explosion Animation (4 frames)
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

def get_joystick():
    # Returns -1 0 or 1 depending on joystick position
    x_coord = int(map_range(joystick_x.value, 200, 65535, -2, 2))
    y_coord = int(map_range(joystick_y.value, 200, 65535, -2, 2))
    return x_coord, y_coord

# Rtttl Game Sounds 
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
        self.draw()  # Desenha imediatamente

    def create_sprite(self):
        # Clean Sprite Group
        while len(self.sprite_group) > 0:
            self.sprite_group.pop()
        
        if not self.visible:
            return
            
        # Create Sprite
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
        
        # Check Vertical Limits (Reverse Mode)
        if self.y < 0:
            self.y = 0  
        # Check Vertical Limits (Normal Mode)
        if self.y >= 58:  # 64 - 6 screen.height - 6
            self.y = 57  # screen height - 7
            
        self.sprite_group.x = self.x
        self.sprite_group.y = self.y
        
        # Check Horizontal Limits
        if self.x <= 0 or self.x >= 58:
            return True
        return False

    def hide(self):
        self.visible = False
        self.draw()

    def shoot(self):
        # From Enemy Ship Center
        return Projectile(self.x + 2, self.y + 6, COLORS[1], self.parent_group)

class PlayerShip:
    def __init__(self, parent_group):
        self.x = 29  # Centro horizontal (64/2 - 6/2)
        self.y = 58  # 4 pixels mais baixo (64 - 6 - 2)
        self.lives = 3
        self.exploding = False
        self.explode_timer = 0
        self.explosion_frame = 0
        self.bitmap = PLAYER_BITMAP
        self.sprite_group = displayio.Group()
        self.parent_group = parent_group
        self.visible = True
        self.create_sprite()
        self.draw()  # Desenha imediatamente

    def create_sprite(self):
        while len(self.sprite_group) > 0:
            self.sprite_group.pop()
        
        if not self.visible:
            return
        
        # Choose Frame and Color, based on stage
        if self.exploding:
            current_bitmap = EXPLOSION_BITMAPS[self.explosion_frame]
            explosion_colors = [0xFFFFFF, 0xFFFF00, 0xFF7F00, 0xFF0000]  # White, Yellow, Orange, Red
            color = explosion_colors[self.explosion_frame]
        else:
            current_bitmap = self.bitmap
            color = COLORS[5]  # Blue
            
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
            # Change Frame each 0.2 sec
            self.explosion_frame = min(3, int(elapsed / 0.2))
            self.create_sprite()
            
            # Explosion ends at 1 sec
            if elapsed > 1.0:
                self.exploding = False
                self.explosion_frame = 0
                self.create_sprite()  # Back to normal Ship
                return True  # Animation is over
        return False

    def draw(self):
        if self.visible:
            if self.sprite_group not in self.parent_group:
                self.parent_group.append(self.sprite_group)
        else:
            if self.sprite_group in self.parent_group:
                self.parent_group.remove(self.sprite_group)

    def draw_lives(self, lives_group):
        # Limpa o grupo de vidas apenas se o número de vidas mudou
        if len(lives_group) != self.lives * 4:  # 4 pixels por vida (2x2)
            while len(lives_group) > 0:
                lives_group.pop()
            
            # Draw lifes at Top Right (aligned with score y=6)
            for i in range(self.lives):
                start_x = 58 - i * 4  # Start Right
                for dx in range(2):
                    for dy in range(2):
                        pixel = Rect(start_x + dx, 3 + dy, 1, 1, fill=COLORS[5]) 
                        lives_group.append(pixel)

    def move(self, dx):
        if not self.exploding:  # Move only if not exploding
            self.x += dx
            if self.x < 0:
                self.x = 0
            elif self.x >= 58:  # 64 - 6
                self.x = 57
            self.sprite_group.x = self.x

    def explode(self):
        if not self.exploding:  # Only start if not exploding
            self.exploding = True
            self.explode_timer = time.monotonic()
            self.explosion_frame = 0
            self.create_sprite()  

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
        # Move o projétil
        self.y += speed
        self.sprite.y = self.y
        
        # Verifica se saiu da tela
        if self.y < -2 or self.y >= 66:
            self.active = False
            if self.sprite in self.parent_group:
                self.parent_group.remove(self.sprite)
            return True
        return False

    def draw(self):
        # Update Sprite Position
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
        
        # Score
        self.score_text = label.Label(font, text="0000", color=COLORS[7], x=2, y=6)
        self.main_group.append(self.score_text)
        
        # Lifes Group
        self.lives_group = displayio.Group()
        self.main_group.append(self.lives_group)
        
        # Player Ship
        self.player_ship = PlayerShip(self.main_group)
        
        self.invaders = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.score = 0
        self.level = 1
        self.invader_move_direction = 1
        self.invader_speed = 0.1
        self.game_over = False
        self.reverse = False
        
        # Main Display Group Config
        screen.root_group = self.main_group
        
        self.resetinvaders()
        galaga_sound()

    def resetinvaders(self):
        # Remove old invaders
        for invader in self.invaders:
            invader.hide()
        self.invaders = []
        
        # Crete new invaders: 5 cols x 3 rows
        for i in range(5):  # 5 cols
            for j in range(3):  # 3 rows
                # Reduce Space: 10 pixels between cols, 8 between rows
                x_pos = i * 10 + 4  # 5 ships with 10 pixels space
                y_pos = j * 8 + 11   # 6 pixels bellow
                invader = Invader(x_pos, y_pos, self.main_group)
                self.invaders.append(invader)
        
        # Reset move direction
        self.invader_move_direction = 1
        self.reverse = False  # Reset Reverse Mode

    def draw(self):
        if self.game_over:
            # Remove Enemy Only, keep player, score, lifes (0)
            for invader in self.invaders:
                invader.hide() 
            
            for projectile in self.projectiles + self.enemy_projectiles:
                projectile.active = False
                projectile.draw() 
            
            # Game Over Message
            game_over_count = sum(1 for item in self.main_group if isinstance(item, label.Label) and item.text == "GAME OVER")
            if game_over_count == 0:
                game_over_text = label.Label(font, text="GAME OVER", color=COLORS[1], x=12, y=30)
                self.main_group.append(game_over_text)
            return
        
        # Draw All Game Elements
        for invader in self.invaders:
            invader.draw()
            
        self.player_ship.draw()
        
        for projectile in self.projectiles:
            projectile.draw()
            
        for projectile in self.enemy_projectiles:
            projectile.draw()
        
        # Update Lives
        self.player_ship.draw_lives(self.lives_group)

    def update(self, dt):
        if self.game_over:
            return

        explosion_finished = self.player_ship.update_explosion()

        if explosion_finished and self.player_ship.lives <= 0:
            self.game_over = True
            return
                
        dx, dy = get_joystick()
        # Só move se não estiver explodindo
        if not self.player_ship.exploding:
            self.player_ship.move(dx)
        
        if not trigger.value and not self.player_ship.exploding and len(self.projectiles) < 3:
            self.projectiles.append(Projectile(self.player_ship.x + 3, self.player_ship.y - 2, COLORS[7], self.main_group))
            shoot_sound()
            time.sleep(0.05)

        # Move player projectiles (UP)
        for projectile in self.projectiles[:]:
            if projectile.update(-3):  # Move para cima
                self.projectiles.remove(projectile)
            else:
                # Check for collision with invaders
                for invader in self.invaders[:]:
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

        # Move enemy projectiles (Down)
        for projectile in self.enemy_projectiles[:]:
            if projectile.update(2):  # Move para baixo
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
            # Move invaders depending on mode Normal or Reverse
            for invader in self.invaders:
                if not self.reverse:
                    invader.move(0, 2)  # Down - Normal
                else:
                    invader.move(0, -2)  # Up - Reverse

        # Check Screen End (Bottom)
        if not self.reverse:
            for invader in self.invaders:
                if invader.y >= 58: 
                    # Activate reverse
                    self.reverse = True
                    break
        
        # Check Screen End (Top)
        if self.reverse:
            top_hit = False
            for invader in self.invaders:
                if invader.y <= 0:  
                    top_hit = True
                    break
            
            if top_hit:
                # Disable Reverse and back to normal
                self.reverse = False
                for invader in self.invaders:
                    invader.move(0, 2)

        player_hit = False
        for invader in self.invaders[:]: 
            if (invader.visible and 
                invader.x < self.player_ship.x + 6 and 
                invader.x + 6 > self.player_ship.x and
                invader.y < self.player_ship.y + 6 and 
                invader.y + 6 > self.player_ship.y):
                
                # Remove Invader
                invader.hide()
                self.invaders.remove(invader)
                player_hit = True
                break  

        # Process player damage
        if player_hit and not self.player_ship.exploding:
            self.player_ship.lives -= 1
            self.player_ship.explode()
            
            # Invaders Reverse 
            self.reverse = True

        # Enemy shooting  (8% chance)
        if random.random() < 0.08 and self.invaders and len(self.enemy_projectiles) < 8:
            shooter = random.choice(self.invaders)
            if shooter.visible:
                self.enemy_projectiles.append(shooter.shoot())

        # Remove invaders beyond screen limits
        self.invaders = [invader for invader in self.invaders if invader.y < 70 and invader.y > -10]

        # Remove inactive projectiles
        self.projectiles = [p for p in self.projectiles if p.active]
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.active]

        if not self.invaders and not self.game_over:
            self.level += 1
            self.resetinvaders()
            xevious_sound()

    def play(self):
        self.last_update_time = time.monotonic()
        while not self.game_over:
            current_time = time.monotonic()
            dt = current_time - self.last_update_time
            self.last_update_time = current_time
            
            self.update(dt)
            self.draw()
            time.sleep(0.008)
            
# Start Game
game = Game()
game.play()

