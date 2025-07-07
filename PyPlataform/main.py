import pgzrun
import math
import random

# Configurações da tela
WIDTH = 800
HEIGHT = 350

# Configurações do jogo
GROUND = HEIGHT - 50  # Será ajustado quando as imagens forem carregadas
GRAVITY = 0.5
JUMP_STRENGTH = -10
PLAYER_SPEED = 5
ANIMATION_SPEED = 8

# Estados do jogo
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    LEVEL_COMPLETE = 3

# Variáveis globais do jogo
game_state = GameState.MENU
offset = 0
health = 100
is_jumping = False
jump_speed = 0
is_scenario_built = False
background_blocks = []
frame_counter = 0

class BeeEnemy(Actor):
    """Classe para inimigos abelha com movimento e animação"""

    def __init__(self, pos=(0, 0)):
        super().__init__('bee_a', pos)
        self.frames = ['bee_a', 'bee_b']
        self.frame_index = 0
        self.stung = False
        self.animation_timer = 0
        self.animation_speed = 0.2
        self.speed = random.uniform(1.5, 2.5)
        self.direction = 1
        self.start_x = pos[0]
        self.patrol_range = 60
        self.health = 20
        self.damage = 10
        self.falling = False
        self.fall_speed = 0

    def update_animation(self, dt):
        """Atualiza a animação da abelha"""
        if self.health > 0:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.image = self.frames[self.frame_index]

    def update(self, dt):
        """Atualiza posição e animação da abelha"""
        if self.health <= 0:
            if not self.falling:
                self.image = "bee_rest"  # Imagem de abelha caída
                self.falling = True
                self.fall_speed = 2

            # Faz a abelha cair verticalmente
            self.y += self.fall_speed
            self.fall_speed += GRAVITY
            return  # Não executa mais lógica viva

        self.update_animation(dt)

        if not self.stung:
            if self.x > self.start_x + self.patrol_range:
                self.direction = -1
            elif self.x < self.start_x - self.patrol_range:
                self.direction = 1
        else:
            self.direction *= -1
            self.stung = False  # Reset ferroada

        self.x += self.speed * self.direction
        self.x -= offset / 60

    def get_hurt(self):
        """Dano à abelha"""
        if self.health > 0:
            self.image = 'bee_rest'
            self.health -= 5
            if self.health <= 0:
                self.falling = True


class BlockEnemy(Actor):
    """Classe para inimigos bloco que caem"""
    
    def __init__(self, pos=(0, 0)):
        super().__init__('block_rest', pos)
        self.sprites = ['block_rest', 'block_idle', 'block_fall']
        self.state = 'rest'  # 'rest', 'idle', 'falling'
        self.activated = False
        self.damage = 15
        self.fall_speed = 0
        self.original_y = pos[1]

    def activate(self):
        """Ativa o inimigo para cair"""
        if not self.activated:
            self.activated = True
            self.state = 'falling'
            self.image = self.sprites[2]
            self.fall_speed = 2

    def update(self, dt):
        """Atualiza o estado do inimigo bloco"""
        if self.activated and self.state == 'falling':
            self.y += self.fall_speed
            self.fall_speed += GRAVITY
            
            # Verifica se chegou ao chão
            if self.bottom >= GROUND:
                self.bottom = GROUND
                self.state = 'idle'
                self.image = self.sprites[1]

    def reset(self):
        """Reseta o inimigo para o estado inicial"""
        self.activated = False
        self.state = 'rest'
        self.image = self.sprites[0]
        self.fall_speed = 0
        self.y = self.original_y

class Player(Actor):
    """Classe do jogador com animação e estados"""
    
    def __init__(self):
        self.walking_sprites = ["character_purple_idle", "character_purple_walk_a", "character_purple_walk_b"]
        super().__init__(self.walking_sprites[0])
        self.frame_index = 0
        self.animation_counter = 0
        self.is_hurt = False
        self.hurt_timer = 0
        self.max_health = 100
        self.is_crouching = False
        
        # Posição inicial
        self.reset_position()

    def reset_position(self):
        """Reseta a posição do jogador"""
        global GROUND
        try:
            GROUND = HEIGHT - images.character_purple_idle.get_height()
        except:
            GROUND = HEIGHT - 50
        self.bottomleft = (50, GROUND)

    def animate_walking(self):
        """Anima o movimento do jogador"""
        self.animation_counter += 1
        if self.animation_counter >= ANIMATION_SPEED:
            self.animation_counter = 0
            self.frame_index = (self.frame_index + 1) % len(self.walking_sprites)
            self.image = self.walking_sprites[self.frame_index]

    def take_damage(self, damage):
        """Aplica dano ao jogador"""
        global health
        if not self.is_hurt and not self.is_crouching:
            health -= damage
            self.set_hurt()
            try:
                sounds.sfx_hurt.play()
            except:
                pass  # Som não disponível

    def set_hurt(self):
        """Define o estado de ferimento"""
        self.is_hurt = True
        self.hurt_timer = 30  # frames
        try:
            self.image = "character_purple_hit"
        except:
            pass

    def set_normal(self):
        """Volta ao estado normal"""
        self.is_hurt = False
        self.image = self.walking_sprites[0]

    def update(self, dt):
        """Atualiza o estado do jogador"""
        if self.is_hurt:
            self.hurt_timer -= 1
            if self.hurt_timer <= 0:
                self.set_normal()

class GameManager:
    """Gerencia o estado geral do jogo"""
    
    def __init__(self):
        self.player = Player()
        self.bees = []
        self.block_enemies = []
        self.door_top = None
        self.door_bottom = None
        self.buttons = {}
        self.setup_game()

    def setup_game(self):
        """Configura os elementos iniciais do jogo"""
        # Cria abelhas
        num_bees = random.randint(3, 8)
        for i in range(num_bees):
            x = random.randint(WIDTH // 2, WIDTH + 400)
            y = random.randint(50, GROUND - 50)
            self.bees.append(BeeEnemy(pos=(x, y)))

        # Cria inimigos bloco
        for i in range(5):
            enemy = BlockEnemy(pos=(WIDTH + 100 * i, GROUND - 100))
            self.block_enemies.append(enemy)

        # Cria portas
        try:
            self.door_bottom = Actor("door_open")
            self.door_top = Actor("door_open_top")
            self.door_bottom.midbottom = (WIDTH, GROUND)
            self.door_top.midbottom = (WIDTH, GROUND - images.door_open.get_height())
        except:
            pass

        # Cria botões
        self.setup_buttons()

    def setup_buttons(self):
        """Configura os botões da interface"""
        try:
            self.buttons['start'] = Actor("button_normal")
            self.buttons['start'].center = (WIDTH // 2, HEIGHT // 2)
            
            self.buttons['retry'] = Actor("button_normal")
            self.buttons['retry'].center = (WIDTH // 2, HEIGHT // 2 + 50)
            
            self.buttons['sound'] = Actor("volume-on-button-red-icon")
            self.buttons['sound'].topright = (WIDTH - 10, 10)
            
            self.buttons['quit'] = Actor("turn-off-button-red-icon")
            self.buttons['quit'].topright = (WIDTH - 60, 10)
        except:
            pass

    def reset_game(self):
        """Reseta o jogo para o estado inicial"""
        global offset, health, is_jumping, jump_speed, background_blocks, is_scenario_built
        
        offset = 0
        health = 100
        is_jumping = False
        jump_speed = 0
        background_blocks.clear()
        is_scenario_built = False
        
        self.player.reset_position()
        
        # Reset das abelhas
        for bee in self.bees:
            bee.stung = False
            bee.x = bee.start_x
        
        # Reset dos inimigos bloco
        for enemy in self.block_enemies:
            enemy.reset()

    def update(self, dt):
        """Atualiza todos os elementos do jogo"""
        global game_state, offset, is_jumping, jump_speed, health
        
        if game_state != GameState.PLAYING:
            return
        
        # Atualiza o jogador
        self.player.update(dt)
        
        # Verifica game over
        if health <= 0:
            game_state = GameState.GAME_OVER
            return
        
        # Atualiza abelhas
        for bee in self.bees:
            bee.update(dt)
            if bee.health > 0 and self.player.colliderect(bee) and not bee.stung:
                bee.stung = True
                self.player.take_damage(bee.damage)
        
        # Atualiza inimigos bloco
        for i, enemy in enumerate(self.block_enemies):
            enemy.update(dt)
            if abs(self.player.x - enemy.x) < 50 and not enemy.activated:
                enemy.activate()
            
            if self.player.colliderect(enemy) and enemy.activated:
                self.player.take_damage(enemy.damage)
        
        # Controles do jogador
        self.handle_input()
        
        # Física do pulo
        if is_jumping:
            self.player.y += jump_speed
            jump_speed += GRAVITY
            
            if self.player.bottom >= GROUND:
                self.player.bottom = GROUND
                is_jumping = False
                jump_speed = 0
        
        # Verifica conclusão do nível
        if self.door_bottom and self.player.colliderect(self.door_bottom):
            game_state = GameState.LEVEL_COMPLETE

    def handle_input(self):
        global offset, is_jumping, jump_speed

        player_moved = False

        # AGACHAR
        self.player.is_crouching = (
            keyboard.down or keyboard.c or keyboard.lctrl or keyboard.rctrl
        )

        

        if keyboard.right and not self.player.is_crouching:
            player_half = self.player.x + self.player.width // 2

            if player_half <= WIDTH // 2:
                self.player.x += PLAYER_SPEED
            else:
                offset += PLAYER_SPEED
                if self.door_bottom:
                    self.door_bottom.x -= PLAYER_SPEED
                    self.door_top.x -= PLAYER_SPEED

            self.player.animate_walking()
            player_moved = True

        elif keyboard.left and not self.player.is_crouching:
            if self.player.x > 0:
                self.player.x -= PLAYER_SPEED
                self.player.animate_walking()
                player_moved = True

        if keyboard.space and not is_jumping and not self.player.is_crouching:
            try:
                sounds.sfx_jump.play()
            except:
                pass
            is_jumping = True
            jump_speed = JUMP_STRENGTH
        if self.player.is_crouching:
            self.player.image = "character_purple_duck"  # ou um sprite de agachado se tiver
        else:
            self.player.image = self.player.walking_sprites[0]

        if not player_moved and not self.player.is_crouching:
            self.player.set_normal()


def build_scenario():
    """Constrói o cenário de fundo"""
    global background_blocks, is_scenario_built
    
    if is_scenario_built:
        return
    
    try:
        background_width = images.background_fade_mushrooms.get_width()
        screen_ratio = WIDTH / background_width
        num_blocks = math.ceil(screen_ratio) + 5  # Extra para rolagem
        
        background_options = [
            "background_fade_mushrooms",
            "background_fade_trees", 
            "background_fade_hills"
        ]
        
        for i in range(num_blocks):
            background_blocks.append(random.choice(background_options))
        
        is_scenario_built = True
    except:
        # Fallback se as imagens não estiverem disponíveis
        background_blocks = ["background_fade_mushrooms"] * 10
        is_scenario_built = True

# Instância do gerenciador de jogo
game_manager = GameManager()

def update():
    """Função principal de atualização do jogo"""
    global frame_counter
    frame_counter += 1
    dt = 1/60  # 60 FPS
    
    if game_state == GameState.PLAYING:
        game_manager.update(dt)

def draw():
    """Função principal de desenho"""
    screen.clear()
    
    if game_state == GameState.MENU:
        draw_menu()
    elif game_state == GameState.PLAYING:
        draw_game()
    elif game_state == GameState.GAME_OVER:
        draw_game_over()
    elif game_state == GameState.LEVEL_COMPLETE:
        draw_level_complete()

def draw_menu():
    """Desenha o menu principal"""
    screen.fill((50, 50, 100))
    screen.draw.text("Enfrente as abelhas!", center=(WIDTH//2, HEIGHT//2 - 50), 
                    color="white", fontsize=40)
    screen.draw.text("Clique para começar!", center=(WIDTH//2, HEIGHT//2 + 20), 
                    color="yellow", fontsize=20)
    
    # Instruções do jogo
    instructions = [
        "Controles:",
        "← → Mover",
        "ESPAÇO Pular", 
        "C/CTRL/↓ Agachar (evita dano)",
        "ESC Voltar ao menu"
    ]
    
    for i, instruction in enumerate(instructions):
        screen.draw.text(instruction, center=(WIDTH//2, HEIGHT//2 + 80 + i*20), 
                        color="lightblue", fontsize=14)
    
    if 'start' in game_manager.buttons:
        game_manager.buttons['start'].draw()
    if 'quit' in game_manager.buttons:
        game_manager.buttons['quit'].draw()

def draw_game():
    """Desenha o jogo principal"""
    # Constrói o cenário se necessário
    build_scenario()
    
    # Desenha o fundo
    try:
        draw_background()
    except:
        screen.fill((135, 206, 235))  # Cor de céu como fallback
    
    # Desenha elementos do jogo
    game_manager.player.draw()
    
    for bee in game_manager.bees:
        bee.draw()
    
    for enemy in game_manager.block_enemies:
        if enemy.activated:
            enemy.draw()
    
    if game_manager.door_bottom:
        game_manager.door_bottom.draw()
    if game_manager.door_top:
        game_manager.door_top.draw()
    
    # Interface
    screen.draw.text(f"Vida: {health}", topleft=(10, 10), color="red", fontsize=20)
    
    # Mostra status de agachamento
    if game_manager.player.is_crouching:
        screen.draw.text("PROTEGIDO!", center=(WIDTH//2, 50), color="green", fontsize=24)
    
    # Instruções de controle
    screen.draw.text("Controles: ←→ Mover | ESPAÇO Pular | C/CTRL/↓ Agachar", 
                    bottomleft=(10, HEIGHT - 10), color="white", fontsize=12)
    
    if 'sound' in game_manager.buttons:
        game_manager.buttons['sound'].draw()

def draw_background():
    """Desenha o cenário de fundo"""
    try:
        for i, scenario in enumerate(background_blocks):
            # Carrega a imagem correspondente ao cenário
            image_width = images.background_fade_hills.get_width()
            image_height = images.background_fade_hills.get_height()
            grass_image = images.background_solid_grass
            grass_height = grass_image.get_height() / 2

            # Calcula a posição correta com base na largura da imagem
            x_pos = i * image_width - offset % image_width

            # Só desenha se estiver visível na tela
            if x_pos < WIDTH:
                y_pos = 0
                screen.blit(scenario, (x_pos, y_pos))
                screen.blit("background_solid_grass", (x_pos, HEIGHT - grass_height))
    except Exception as e:
        print(f"Erro ao desenhar o fundo: {e}")


def draw_game_over():
    """Desenha a tela de game over"""
    screen.fill((50, 50, 50))
    screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2 - 30), 
                    color="red", fontsize=40)
    screen.draw.text("Click to Retry", center=(WIDTH//2, HEIGHT//2 + 20), 
                    color="white", fontsize=20)
    
    if 'retry' in game_manager.buttons:
        game_manager.buttons['retry'].draw()

def draw_level_complete():
    """Desenha a tela de nível completo"""
    screen.fill((0, 50, 0))
    screen.draw.text("LEVEL COMPLETE!", center=(WIDTH//2, HEIGHT//2), 
                    color="gold", fontsize=40)
    screen.draw.text("Parabéns!", center=(WIDTH//2, HEIGHT//2 + 40), 
                    color="yellow", fontsize=20)

def on_mouse_down(pos):
    """Gerencia cliques do mouse"""
    global game_state, bees
    
    if game_state == GameState.MENU:
        if 'start' in game_manager.buttons and game_manager.buttons['start'].collidepoint(pos):
            game_state = GameState.PLAYING
        elif 'quit' in game_manager.buttons and game_manager.buttons['quit'].collidepoint(pos):
            exit()
    
    elif game_state == GameState.GAME_OVER:
        if 'retry' in game_manager.buttons and game_manager.buttons['retry'].collidepoint(pos):
            game_manager.reset_game()
            game_state = GameState.PLAYING
    
    elif game_state == GameState.PLAYING:
        if 'sound' in game_manager.buttons and game_manager.buttons['sound'].collidepoint(pos):
            try:
                if game_manager.buttons['sound'].image == "volume-mute-button-red-icon":
                    game_manager.buttons['sound'].image = "volume-on-button-red-icon"
                    music.unpause()
                else:
                    game_manager.buttons['sound'].image = "volume-mute-button-red-icon"
                    music.pause()
            except:
                pass
    
    for bee in game_manager.bees:
        if bee.collidepoint(pos):
            bee.get_hurt()
def on_key_down(key):
    """Gerencia teclas pressionadas"""
    global game_state
    
    if key == keys.ESCAPE:
        if game_state == GameState.PLAYING:
            game_state = GameState.MENU
        else:
            exit()
    elif key == keys.R and game_state == GameState.GAME_OVER:
        game_manager.reset_game()
        game_state = GameState.PLAYING

# Inicializa a música
try:
    music.play("background")
except:
    pass

pgzrun.go()