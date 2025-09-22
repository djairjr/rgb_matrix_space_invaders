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

# Inicializa a RGB Matrix
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

# Carrega a fonte tom-thumb.pcf (tentativa)
try:
    # Tenta carregar a fonte tom-thumb.pcf
    font = bitmap_font.load_font("/fonts/tom-thumb.pcf")
except:
    try:
        # Fallback: tenta carregar de localização alternativa
        font = bitmap_font.load_font("/lib/tom-thumb.pcf")
    except:
        try:
            # Fallback: tenta a fonte 5x8
            font = bitmap_font.load_font("/lib/5x8font.bin")
        except:
            # Fallback final: usa fonte terminal padrão
            font = terminalio.FONT
            print("Usando fonte padrão")

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

# Definindo as naves como bitmaps
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

# Bitmaps da animação de explosão (4 frames)
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

# Sounds - CORRIGIDOS (removidos caracteres inválidos)
def shoot_sound():
    try:
        adafruit_rtttl.play(buzzer, "shoot:d=4,o=5,b=880:8c6")
    except:
        pass
    
def xevious_sound():
    try:
        adafruit_rtttl.play(buzzer, "Xevious:d=4,o=5,b=160:16c,16c6,16b,16c6,16e6,16c6,16b,16c6,16c,16c6,16a#,16c6,16e6,16c6,16a#,16c6,16c,16c6,16a,16c6,16e6,16c6,16a,16c6,16c,16c6,16g#,16c6,16e6,16c6,16g#,16c6")
    except:
        pass

def galaga_sound():
    try:
        adafruit_rtttl.play(buzzer, "Galaga:d=4,o=5,b=125:8g4,32c,32p,8d,32f,32p,8e,32c,32p,8d,32a,32p,8g,32c,32p,8d,32f,32p,8e,32c,32p,8g,32b,32p,8c6,32a#,32p,8g#,32g,32p,8f,32d#,32p,8d,32a#4,32p,8a#,32c6,32p,8a#,32g,32p,16a,16f,16d,16g,16e,16d")
    except:
        pass

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
        # Limpa o grupo atual
        while len(self.sprite_group) > 0:
            self.sprite_group.pop()
        
        if not self.visible:
            return
            
        # Cria os pixels da nave baseado no bitmap
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
        
        # Verifica limites verticais (modo reverso)
        if self.y < 0:
            self.y = 0  # Impede que suba além do topo
        # Verifica limites verticais (modo normal)
        if self.y >= 58:  # 64 - 6
            self.y = 57  # Impede que desça além da base
            
        self.sprite_group.x = self.x
        self.sprite_group.y = self.y
        
        # Verifica se atingiu as bordas laterais
        if self.x <= 0 or self.x >= 58:
            return True
        return False

    def hide(self):
        self.visible = False
        self.draw()

    def shoot(self):
        # Tiro sai do centro da nave inimiga
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
        
        # Escolhe o bitmap e cor baseado no estado
        if self.exploding:
            current_bitmap = EXPLOSION_BITMAPS[self.explosion_frame]
            # Diferentes colors para cada frame da explosão
            explosion_colors = [0xFFFFFF, 0xFFFF00, 0xFF7F00, 0xFF0000]  # Branco, Amarelo, Laranja, Vermelho
            color = explosion_colors[self.explosion_frame]
        else:
            current_bitmap = self.bitmap
            color = COLORS[5]  # Azul para nave normal
            
        for i in range(6):
            for j in range(6):
                if current_bitmap[i][j]:
                    pixel = Rect(j, i, 1, 1, fill=color)
                    self.sprite_group.append(pixel)
        
        self.sprite_group.x = self.x
        self.sprite_group.y = self.y

    def update_explosion(self):
        """Atualiza a animação da explosão e retorna True quando terminar"""
        if self.exploding:
            elapsed = time.monotonic() - self.explode_timer
            # Muda de frame a cada 0.2 segundos
            self.explosion_frame = min(3, int(elapsed / 0.2))
            
            # Recria o sprite com o frame atual da explosão
            self.create_sprite()
            
            # Termina a explosão após 1 segundo
            if elapsed > 1.0:
                self.exploding = False
                self.explosion_frame = 0
                self.create_sprite()  # Volta para a nave normal
                return True  # Indica que a explosão terminou
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
            
            # Desenha vidas no canto superior direito (alinhado com score y=6)
            for i in range(self.lives):
                start_x = 58 - i * 4  # Começa da direita
                for dx in range(2):
                    for dy in range(2):
                        pixel = Rect(start_x + dx, 3 + dy, 1, 1, fill=COLORS[5])  # Azul, alinhado com score
                        lives_group.append(pixel)

    def move(self, dx):
        if not self.exploding:  # Só pode mover se não estiver explodindo
            self.x += dx
            if self.x < 0:
                self.x = 0
            elif self.x >= 58:  # 64 - 6
                self.x = 57
            self.sprite_group.x = self.x

    def explode(self):
        if not self.exploding:  # Só inicia explosão se não estiver já explodindo
            self.exploding = True
            self.explode_timer = time.monotonic()
            self.explosion_frame = 0
            self.create_sprite()  # Inicia com o primeiro frame da explosão
            

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
        # Atualiza a posição do sprite
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
        
        # Score no canto superior esquerdo com fonte menor
        self.score_text = label.Label(font, text="0000", color=COLORS[7], x=2, y=6)
        self.main_group.append(self.score_text)
        
        # Grupo para vidas no canto superior direito
        self.lives_group = displayio.Group()
        self.main_group.append(self.lives_group)
        
        # Cria o player ship primeiro
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
        
        # Configura o display
        screen.root_group = self.main_group
        
        self.resetinvaders()
        galaga_sound()

    def resetinvaders(self):
        # Remove invaders antigos
        for invader in self.invaders:
            invader.hide()
        self.invaders = []
        
        # Cria novos invaders: 5 colunas x 3 linhas com espaçamento reduzido
        for i in range(5):  # 5 colunas
            for j in range(3):  # 3 linhas (reduzido de 4)
                # Espaçamento reduzido: 10 pixels entre colunas, 8 entre linhas
                x_pos = i * 10 + 4  # 5 naves com 10 pixels de espaçamento
                y_pos = j * 8 + 11   # 6 pixels mais abaixo
                invader = Invader(x_pos, y_pos, self.main_group)
                self.invaders.append(invader)
        
        # Reseta direção do movimento
        self.invader_move_direction = 1
        self.reverse = False  # Reseta o modo reverso

    def draw(self):
        if self.game_over:
            # Remove apenas invasores e projéteis, mantendo jogador, score e vidas
            for invader in self.invaders:
                invader.hide()  # Usa o método hide() em vez de remover diretamente
            
            for projectile in self.projectiles + self.enemy_projectiles:
                projectile.active = False
                projectile.draw()  # Isso fará o projétil se remover
            
            # Adiciona texto de game over apenas uma vez
            game_over_count = sum(1 for item in self.main_group if isinstance(item, label.Label) and item.text == "GAME OVER")
            if game_over_count == 0:
                game_over_text = label.Label(font, text="GAME OVER", color=COLORS[1], x=12, y=30)
                self.main_group.append(game_over_text)
            return
        
        # Desenha elementos normais do jogo
        for invader in self.invaders:
            invader.draw()
            
        self.player_ship.draw()
        
        for projectile in self.projectiles:
            projectile.draw()
            
        for projectile in self.enemy_projectiles:
            projectile.draw()
        
        # Atualiza vidas
        self.player_ship.draw_lives(self.lives_group)

    def update(self, dt):
        if self.game_over:
            return
        
        # Atualiza a animação da explosão da nave
        explosion_finished = self.player_ship.update_explosion()
        
        # Se a explosão terminou e as vidas chegaram a zero, mostra Game Over
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

        # Move player projectiles (para cima)
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

        # Move enemy projectiles (para baixo)
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
            # Move todos os invasores para baixo/baixo dependendo do modo
            for invader in self.invaders:
                if not self.reverse:
                    invader.move(0, 2)  # Move para baixo
                else:
                    invader.move(0, -2)  # Move para cima (modo reverso)

        # Verifica se invasores chegaram ao fundo da tela (modo normal)
        if not self.reverse:
            for invader in self.invaders:
                if invader.y >= 58:  # Chegaram perto do fundo
                    # Ativa modo reverso
                    self.reverse = True
                    break
        
        # Verifica se invasores chegaram ao topo da tela (modo reverso)
        if self.reverse:
            top_hit = False
            for invader in self.invaders:
                if invader.y <= 0:  # Chegaram no topo
                    top_hit = True
                    break
            
            if top_hit:
                # Desativa modo reverso e move para baixo
                self.reverse = False
                for invader in self.invaders:
                    invader.move(0, 2)

        # CORREÇÃO: Verificação de colisão com jogador DEVE remover o invasor
        player_hit = False
        for invader in self.invaders[:]:  # Usar cópia da lista para remover durante iteração
            if (invader.visible and 
                invader.x < self.player_ship.x + 6 and 
                invader.x + 6 > self.player_ship.x and
                invader.y < self.player_ship.y + 6 and 
                invader.y + 6 > self.player_ship.y):
                
                # Remove o invasor que colidiu
                invader.hide()
                self.invaders.remove(invader)
                player_hit = True
                break  # Só processa uma colisão por frame

        # Processa o dano APÓS remover o invasor
        if player_hit and not self.player_ship.exploding:
            self.player_ship.lives -= 1
            self.player_ship.explode()
            
            # Ativa modo reverso quando o jogador é atingido
            self.reverse = True

        # Enemy shooting - frequência aumentada (8% de chance)
        if random.random() < 0.08 and self.invaders and len(self.enemy_projectiles) < 8:
            shooter = random.choice(self.invaders)
            if shooter.visible:
                self.enemy_projectiles.append(shooter.shoot())

        # Remove invasores que saíram completamente da tela
        self.invaders = [invader for invader in self.invaders if invader.y < 70 and invader.y > -10]

        # Remove projéteis inativos
        self.projectiles = [p for p in self.projectiles if p.active]
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.active]

        # CORREÇÃO: Level up check DEVE vir por último e verificar game_over
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
            
# Inicia o jogo
game = Game()
game.play()

