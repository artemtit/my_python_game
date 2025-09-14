import pygame
import random
import time
import sys
import json
import atexit
import os
from pathlib import Path
import colorsys

# Инициализация Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Константы
WIDTH, HEIGHT = 400, 600
GRAVITY = 0.5
INITIAL_JUMP_VELOCITY = -12
PLAYER_SIZE = 32
PLATFORM_WIDTH = 80
PLATFORM_HEIGHT = 20
COIN_SIZE = 16
FPS = 90
PLATFORM_GAP = 100
PLAYER_SPEED = 6
INITIAL_JUMP_DELAY = 1.5

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)
GREEN = (0, 255, 0)
PLATFORM_COLOR = (70, 70, 200)
DISAPPEARING_COLOR = (200, 70, 70)
SPRING_COLOR = (100, 255, 100)

# Система сохранений
SAVE_DIR = Path.home() / ".pixel_hopper_pro"
SAVE_DIR.mkdir(exist_ok=True)
SAVE_FILE = SAVE_DIR / "game_data.json"

# Глобальные переменные
current_score = 0
BACKGROUNDS = ["background.jpg", "mountains_bg.png", "space_bg.png"]
high_score = 0
platforms_passed = 0
max_platforms = 0
total_coins = 0  # Initialize to 0, will be loaded from save
sound_enabled = True
music_loaded = False
coins = []
current_trail = "none"
current_skin = "default"
purchased_skins = ["default"]
purchased_trails = ["none"]
trails = ["none", "red", "blue", "rainbow"]

# Музыкальный плейлист
MUSIC_TRACKS = ["Music_background.mp3", "Music_background1.mp3", "Music_background2.mp3"]
current_music_index = 0
MUSIC_END_EVENT = pygame.USEREVENT + 1

# Улучшения (перманентные)
double_coins = False

# Локализация отображаемых названий предметов
NAME_MAP = {
    "default": "По умолчанию",
    "ninja": "Ниндзя",
    "robot": "Робот",
    "zombie": "Зомби",
    "none": "Нет",
    "red": "Красный",
    "blue": "Синий",
    "rainbow": "Радуга"
}

def display_name(name):
    return NAME_MAP.get(name, name)

# Настройка экрана
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixel Hopper Pro")
clock = pygame.time.Clock()

class Player:
    def __init__(self):
        self.game_dir = self._get_game_directory()
        self.current_skin = current_skin
        self.skins = {
            "default": None,
            "ninja": None,
            "robot": None,
            "zombie": None
        }
        self._load_all_skins()
        self.reset()
        self.trail_points = []
        self.trail_colors = {
            "none": None,
            "red": (255, 100, 100),
            "blue": (100, 100, 255),
            "rainbow": None
        }
        self.trail_update_delay = 0.02
        self.last_trail_update = 0
        self.facing_right = True
        self.animation_frame = 0
        self.current_trail = current_trail

    def _get_game_directory(self):
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent

    def _load_all_skins(self):
        self.skins["default"] = self._create_default_sprite()
        self.skins["ninja"] = self._load_skin("ninja.png", self._create_ninja_sprite)
        self.skins["robot"] = self._load_skin("robot.png", self._create_robot_sprite)
        self.skins["zombie"] = self._load_skin("zombie.png", self._create_zombie_sprite)

    def _load_skin(self, filename, fallback_func):
        skin_path = self.game_dir / "assets" / filename
        if skin_path.exists():
            try:
                img = pygame.image.load(str(skin_path)).convert_alpha()
                return pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
            except Exception as e:
                print(f"Ошибка загрузки {filename}: {e}")
        return fallback_func()

    def _create_default_sprite(self):
        surface = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(surface, (40, 200, 40), (0, 0, PLAYER_SIZE, PLAYER_SIZE))
        pygame.draw.circle(surface, WHITE, (PLAYER_SIZE//3, PLAYER_SIZE//3), 6)
        pygame.draw.circle(surface, WHITE, (2*PLAYER_SIZE//3, PLAYER_SIZE//3), 6)
        pygame.draw.circle(surface, BLACK, (PLAYER_SIZE//3, PLAYER_SIZE//3), 3)
        pygame.draw.circle(surface, BLACK, (2*PLAYER_SIZE//3, PLAYER_SIZE//3), 3)
        pygame.draw.arc(surface, BLACK, (PLAYER_SIZE//4, 2*PLAYER_SIZE//3, PLAYER_SIZE//2, 10), 3.5, 6.0, 2)
        return surface

    def _create_ninja_sprite(self):
        surface = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        # Тело
        pygame.draw.rect(surface, (40, 40, 40), (8, 10, 16, 22))
        # Голова
        pygame.draw.ellipse(surface, (70, 50, 40), (10, 4, 12, 10))
        # Маска
        pygame.draw.rect(surface, (20, 20, 20), (10, 8, 12, 4))
        # Глаза
        pygame.draw.line(surface, (255, 0, 0), (14, 10), (18, 10), 2)
        # Пояс
        pygame.draw.rect(surface, (120, 0, 0), (8, 20, 16, 3))
        # Ноги
        pygame.draw.rect(surface, (30, 30, 30), (10, 28, 4, 4))
        pygame.draw.rect(surface, (30, 30, 30), (18, 28, 4, 4))
        # Руки
        pygame.draw.line(surface, (40, 40, 40), (8, 14), (4, 18), 3)
        pygame.draw.line(surface, (40, 40, 40), (24, 14), (28, 18), 3)
        # Меч за спиной
        pygame.draw.line(surface, (150, 150, 150), (6, 12), (6, 24), 2)
        pygame.draw.polygon(surface, (200, 200, 200), [(6, 12), (2, 16), (6, 16)])
        return surface

    def _create_robot_sprite(self):
        surface = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        # Корпус
        pygame.draw.rect(surface, (150, 150, 150), (8, 8, 16, 20), border_radius=3)
        # Голова
        pygame.draw.rect(surface, (180, 180, 180), (10, 4, 12, 6), border_radius=2)
        # Дисплей на голове
        pygame.draw.rect(surface, (0, 200, 200), (12, 5, 8, 4))
        pygame.draw.line(surface, (0, 0, 0), (14, 6), (18, 6), 1)
        pygame.draw.line(surface, (0, 0, 0), (16, 5), (16, 8), 1)
        # Антенна
        pygame.draw.line(surface, (200, 200, 0), (16, 2), (16, 4), 2)
        pygame.draw.circle(surface, (255, 255, 0), (16, 2), 2)
        # Соединительные элементы
        pygame.draw.rect(surface, (100, 100, 100), (12, 14, 8, 2))
        pygame.draw.rect(surface, (100, 100, 100), (12, 20, 8, 2))
        # Ноги (шасси)
        pygame.draw.rect(surface, (80, 80, 80), (10, 28, 4, 4))
        pygame.draw.rect(surface, (80, 80, 80), (18, 28, 4, 4))
        # Руки
        pygame.draw.rect(surface, (120, 120, 120), (6, 12, 4, 8))
        pygame.draw.rect(surface, (120, 120, 120), (22, 12, 4, 8))
        # Кисти
        pygame.draw.rect(surface, (200, 200, 200), (6, 20, 4, 2))
        pygame.draw.rect(surface, (200, 200, 200), (22, 20, 4, 2))
        return surface

    def _create_zombie_sprite(self):
        surface = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        # Тело
        pygame.draw.rect(surface, (80, 120, 80), (8, 10, 16, 20))
        # Голова
        pygame.draw.ellipse(surface, (120, 150, 120), (10, 4, 12, 10))
        # Глаза
        pygame.draw.ellipse(surface, (255, 0, 0), (12, 7, 3, 3))
        pygame.draw.ellipse(surface, (0, 0, 0), (20, 7, 3, 3))
        # Рот
        pygame.draw.line(surface, (0, 0, 0), (14, 12), (18, 12), 2)
        pygame.draw.line(surface, (0, 0, 0), (14, 12), (13, 14), 1)
        pygame.draw.line(surface, (0, 0, 0), (18, 12), (19, 14), 1)
        # Швы
        for i in range(3):
            pygame.draw.line(surface, (0, 80, 0), (8, 14+i*4), (24, 14+i*4), 1)
        # Разорванная одежда
        pygame.draw.line(surface, (40, 40, 40), (8, 25), (12, 28), 1)
        pygame.draw.line(surface, (40, 40, 40), (20, 25), (24, 28), 1)
        # Ноги
        pygame.draw.rect(surface, (60, 100, 60), (10, 28, 4, 4))
        pygame.draw.rect(surface, (60, 100, 60), (18, 28, 4, 4))
        # Кровь
        pygame.draw.circle(surface, (150, 0, 0), (22, 9), 2)
        pygame.draw.line(surface, (150, 0, 0), (8, 18), (10, 20), 2)
        return surface

    def reset(self):
        self.rect = pygame.Rect(WIDTH // 2 - PLAYER_SIZE // 2, HEIGHT - 150, PLAYER_SIZE, PLAYER_SIZE)
        self.velocity_y = 0
        self.velocity_x = 0
        self.on_ground = True
        self.old_y = 0
        self.old_x = 0
        self.game_start_time = time.time()
        self.initial_jump_available = True
        self.jump_count = 0
        self.last_save_score = 0
        self.trail_points = []
        self.last_trail_update = 0

    def draw(self, surface):
        if self.current_trail != "none" and len(self.trail_points) > 1:
            trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            for i in range(1, len(self.trail_points)):
                progress = i / len(self.trail_points)
                alpha = int(220 * (1 - progress))
                if self.current_trail == "rainbow":
                    hue = progress % 1
                    color = (*[int(c*255) for c in colorsys.hsv_to_rgb(hue, 0.9, 1)], alpha)
                else:
                    base_color = self.trail_colors[self.current_trail]
                    color = (*base_color, alpha)
                start_pos = (self.trail_points[i-1]["x"], self.trail_points[i-1]["y"])
                end_pos = (self.trail_points[i]["x"], self.trail_points[i]["y"])
                pygame.draw.line(trail_surface, color, start_pos, end_pos, 12)
            surface.blit(trail_surface, (0, 0))

        current_skin_img = self.skins.get(self.current_skin, self.skins["default"])
        if not self.facing_right:
            current_skin_img = pygame.transform.flip(current_skin_img, True, False)
        surface.blit(current_skin_img, self.rect)

    def jump(self):
        if self.on_ground or (time.time() - self.game_start_time < INITIAL_JUMP_DELAY and self.initial_jump_available):
            self.velocity_y = INITIAL_JUMP_VELOCITY
            self.on_ground = False
            self.initial_jump_available = False
            self.jump_count += 1
            self.check_background_transition()

    def check_background_transition(self):
        global current_bg_index, is_transitioning, next_bg, transition_alpha
        new_bg_index = 0
        if self.jump_count >= 100:
            new_bg_index = 2
        elif self.jump_count >= 40:
            new_bg_index = 1
        if new_bg_index != current_bg_index and not is_transitioning:
            is_transitioning = True
            next_bg = load_background(new_bg_index)
            transition_alpha = 0
            current_bg_index = new_bg_index

    def add_score(self, points):
        global current_score, high_score, total_coins, double_coins
        current_score += points
        coin_gain = points * (2 if double_coins else 1)
        total_coins += coin_gain  # Учитываем апгрейд x2 монеты
        if current_score > high_score:
            high_score = current_score
        save_game()  # Save game state после сбора монет

    def update(self):
        self.old_y = self.rect.y
        self.old_x = self.rect.x
        self.velocity_y += GRAVITY
        self.rect.y += self.velocity_y
        self.rect.x += self.velocity_x
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.velocity_x > 0:
            self.facing_right = True
        elif self.velocity_x < 0:
            self.facing_right = False
        current_time = time.time()
        if (self.current_trail != "none" and
                current_time - self.last_trail_update > self.trail_update_delay):
            self.trail_points.insert(0, {
                "x": self.rect.centerx,
                "y": self.rect.centery,
                "time": current_time
            })
            self.last_trail_update = current_time
        max_trail_points = 50
        if len(self.trail_points) > max_trail_points:
            self.trail_points = self.trail_points[:max_trail_points]

class Platform:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLATFORM_WIDTH, PLATFORM_HEIGHT)
        self.type = random.choices(["normal", "disappearing", "spring"], weights=[0.7, 0.2, 0.1])[0]
        self.disappear_time = None
        self.activated = False
        self.spring_compressed = False
        self.spring_frame = 0
        self.top_surface = pygame.Surface((PLATFORM_WIDTH, 4))
        self.platform_img = pygame.Surface((PLATFORM_WIDTH, PLATFORM_HEIGHT), pygame.SRCALPHA)
        self.counted = False  
        if self.type == "normal":
            for i in range(PLATFORM_HEIGHT):
                alpha = 255 - i*10
                color = (*PLATFORM_COLOR, alpha)
                pygame.draw.rect(self.platform_img, color, (0, i, PLATFORM_WIDTH, 1))
            self.top_surface.fill((150, 150, 255))
        elif self.type == "disappearing":
            for i in range(PLATFORM_HEIGHT):
                alpha = 255 - i*10
                color = (*DISAPPEARING_COLOR, alpha)
                pygame.draw.rect(self.platform_img, color, (0, i, PLATFORM_WIDTH, 1))
            self.top_surface.fill((255, 150, 150))
        else:
            for i in range(PLATFORM_HEIGHT):
                alpha = 255 - i*10
                color = (*SPRING_COLOR, alpha)
                pygame.draw.rect(self.platform_img, color, (0, i, PLATFORM_WIDTH, 1))
            self.top_surface.fill((200, 255, 200))
            spring_color = (50, 200, 50)
            for i in range(3):
                y_pos = PLATFORM_HEIGHT - 5 - i*3
                pygame.draw.line(self.platform_img, spring_color, (5, y_pos), (PLATFORM_WIDTH-5, y_pos), 2)

    def should_disappear(self):
        if self.type == "disappearing" and self.activated:
            return time.time() - self.disappear_time >= 2
        return False

    def compress_spring(self):
        if self.type == "spring":
            self.spring_compressed = True
            self.spring_frame = 0

    def update_spring(self):
        if self.spring_compressed:
            self.spring_frame += 1
            if self.spring_frame >= 10:
                self.spring_compressed = False

    def draw(self, surface):
        if self.type == "disappearing" and self.activated:
            time_passed = time.time() - self.disappear_time
            alpha = max(0, 255 - int(255 * (time_passed / 2)))
            self.platform_img.set_alpha(alpha)
            self.top_surface.set_alpha(alpha)
        if self.type == "spring" and self.spring_compressed:
            compression = 3 * (1 - self.spring_frame / 10)
            compressed_img = pygame.Surface((PLATFORM_WIDTH, PLATFORM_HEIGHT - compression), pygame.SRCALPHA)
            compressed_img.blit(self.platform_img, (0, 0))
            surface.blit(compressed_img, (self.rect.x, self.rect.y + compression))
            surface.blit(self.top_surface, (self.rect.x, self.rect.y + compression))
        else:
            surface.blit(self.platform_img, self.rect)
            surface.blit(self.top_surface, (self.rect.x, self.rect.y))

class Coin:
    def __init__(self, x, y, coin_type="yellow"):
        self.rect = pygame.Rect(x, y, COIN_SIZE, COIN_SIZE)
        self.type = coin_type
        self.value = 1 if coin_type == "yellow" else 3
        self.animation_frame = 0
        self.image = self._create_coin_image()

    def _create_coin_image(self):
        img = pygame.Surface((COIN_SIZE, COIN_SIZE), pygame.SRCALPHA)
        if self.type == "yellow":
            pygame.draw.circle(img, YELLOW, (COIN_SIZE//2, COIN_SIZE//2), COIN_SIZE//2)
            pygame.draw.circle(img, (200, 200, 0), (COIN_SIZE//2, COIN_SIZE//2), COIN_SIZE//2 - 2)
        else:
            diamond_points = [
                (COIN_SIZE//2, 2),
                (COIN_SIZE-2, COIN_SIZE//2),
                (COIN_SIZE//2, COIN_SIZE-2),
                (2, COIN_SIZE//2)
            ]
            pygame.draw.polygon(img, (50, 150, 255), diamond_points)
            pygame.draw.polygon(img, (100, 200, 255), [
                (COIN_SIZE//2, COIN_SIZE//4),
                (3*COIN_SIZE//4, COIN_SIZE//2),
                (COIN_SIZE//2, 3*COIN_SIZE//4)
            ])
        return img

    def update(self):
        self.animation_frame = (self.animation_frame + 0.1) % 4

    def draw(self, surface):
        offset = 0
        if int(self.animation_frame) == 1:
            offset = -1
        if int(self.animation_frame) == 3:
            offset = 1
        if self.type == "blue":
            angle = self.animation_frame * 10
            rotated_img = pygame.transform.rotate(self.image, angle)
            new_rect = rotated_img.get_rect(center=self.rect.center)
            surface.blit(rotated_img, (new_rect.x, new_rect.y + offset))
        else:
            surface.blit(self.image, (self.rect.x, self.rect.y + offset))

def generate_platforms(start_y, count):
    global coins
    platforms = []
    platforms.append(Platform(WIDTH // 2 - PLATFORM_WIDTH // 2, start_y))
    for i in range(1, count):
        x = random.randint(0, WIDTH - PLATFORM_WIDTH)
        y = start_y - i * PLATFORM_GAP
        platforms.append(Platform(x, y))
        if random.random() < 0.4:
            coin_type = "blue" if random.random() < 0.15 else "yellow"
            coins.append(Coin(x + PLATFORM_WIDTH//2 - COIN_SIZE//2, y - COIN_SIZE - 5, coin_type))
    return platforms

def load_background(index):
    try:
        bg = pygame.image.load(str(Path(__file__).parent / BACKGROUNDS[index]))
        return pygame.transform.scale(bg, (WIDTH, HEIGHT))
    except:
        bg = pygame.Surface((WIDTH, HEIGHT))
        colors = [(30, 60, 30), (60, 30, 60), (30, 30, 60)][index]
        bg.fill(colors)
        return bg

def start_music():
    global music_loaded, current_music_index
    try:
        track = MUSIC_TRACKS[current_music_index]
        pygame.mixer.music.load(track)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        music_loaded = True
    except Exception as e:
        print(f"Ошибка загрузки музыки: {e}")
        music_loaded = False

def play_next_track():
    global current_music_index
    current_music_index = (current_music_index + 1) % len(MUSIC_TRACKS)
    if sound_enabled:
        start_music()

def load_music():
    # Запускает плейлист, только если сейчас ничего не играет
    try:
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
    except Exception:
        pass
    if sound_enabled and not pygame.mixer.music.get_busy():
        start_music()

def toggle_sound():
    global sound_enabled, music_loaded
    sound_enabled = not sound_enabled
    if sound_enabled:
        try:
            pygame.mixer.music.unpause()
            if not pygame.mixer.music.get_busy():
                start_music()
        except Exception:
            start_music()
    else:
        pygame.mixer.music.pause()
    save_game()

def load_game():
    global high_score, sound_enabled, max_platforms, total_coins, current_skin, current_trail, purchased_skins, purchased_trails, double_coins
    try:
        if SAVE_FILE.exists():
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                high_score = data.get("high_score", 0)
                sound_enabled = data.get("sound_enabled", True)
                max_platforms = data.get("max_platforms", 0)
                total_coins = data.get("total_coins", 0)  # Load coins from save
                purchased_skins = list(set(data.get("purchased_skins", [])).union({"default"}))
                purchased_trails = list(set(data.get("purchased_trails", [])).union({"none"}))
                current_skin = data.get("current_skin", "default")
                current_trail = data.get("current_trail", "none")
                double_coins = data.get("double_coins", False)
        else:
            total_coins = 0  # Default to 0 if no save file exists
            save_game()
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        total_coins = 0
        purchased_skins = ["default"]
        purchased_trails = ["none"]
        current_skin = "default"
        current_trail = "none"
        save_game()

def save_game():
    global high_score, sound_enabled, max_platforms, total_coins, current_skin, current_trail, purchased_skins, purchased_trails, double_coins
    try:
        data = {
            "high_score": high_score,
            "sound_enabled": sound_enabled,
            "max_platforms": max_platforms,
            "total_coins": total_coins,
            "current_skin": current_skin,
            "current_trail": current_trail,
            "purchased_skins": purchased_skins,
            "purchased_trails": purchased_trails,
            "double_coins": double_coins
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def save_on_exit():
    save_game()

atexit.register(save_on_exit)

def reset_game_state():
    global current_score, current_bg_index, jump_count, is_transitioning, transition_alpha, platforms_passed
    current_score = 0
    platforms_passed = 0
    current_bg_index = 0
    jump_count = 0
    is_transitioning = False
    transition_alpha = 0
    # Музыку не останавливаем, чтобы она играла непрерывно между экранами
    try:
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
    except Exception:
        pass
    if sound_enabled and not pygame.mixer.music.get_busy():
        start_music()

def show_game_over(screen):
    global high_score, max_platforms, platforms_passed, total_coins
    if platforms_passed > max_platforms:
        max_platforms = platforms_passed
        save_game()
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    font = pygame.font.SysFont("Arial", 36, bold=True)
    small_font = pygame.font.SysFont("Arial", 24, bold=True)
    text = font.render("КОНЕЦ ИГРЫ", True, (255, 50, 50))
    platforms_text = font.render(f"Платформы: {platforms_passed}", True, WHITE)
    record_text = font.render(f"Рекорд: {max_platforms}", True, YELLOW)
    coins_text = font.render(f"Всего монет: {total_coins}", True, (255, 200, 100))
    restart_button = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 80, 120, 40)
    pygame.draw.rect(screen, (70, 200, 70), restart_button, border_radius=5)
    pygame.draw.rect(screen, (40, 40, 40), restart_button, 2, border_radius=5)
    restart_text = small_font.render("Заново", True, BLACK)
    screen.blit(restart_text, (restart_button.centerx - restart_text.get_width()//2,
                              restart_button.centery - restart_text.get_height()//2))
    menu_button = pygame.Rect(WIDTH//2 + 30, HEIGHT//2 + 80, 120, 40)
    pygame.draw.rect(screen, (200, 70, 70), menu_button, border_radius=5)
    pygame.draw.rect(screen, (40, 40, 40), menu_button, 2, border_radius=5)
    menu_text = small_font.render("Меню", True, BLACK)
    screen.blit(menu_text, (menu_button.centerx - menu_text.get_width()//2,
                           menu_button.centery - menu_text.get_height()//2))
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 120))
    screen.blit(platforms_text, (WIDTH//2 - platforms_text.get_width()//2, HEIGHT//2 - 60))
    screen.blit(record_text, (WIDTH//2 - record_text.get_width()//2, HEIGHT//2 - 20))
    screen.blit(coins_text, (WIDTH//2 - coins_text.get_width()//2, HEIGHT//2 + 20))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if restart_button.collidepoint(mouse_pos):
                    return "restart"
                elif menu_button.collidepoint(mouse_pos):
                    return "menu"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "restart"
                elif event.key == pygame.K_ESCAPE:
                    return "menu"
            if event.type == MUSIC_END_EVENT:
                play_next_track()
        clock.tick(FPS)

def show_shop_screen(screen, shop_type):
    global current_skin, current_trail, total_coins, purchased_skins, purchased_trails
    skins = ["default", "ninja", "robot", "zombie"]
    try:
        shop_bg = pygame.image.load("store_background.jpg")
        shop_bg = pygame.transform.scale(shop_bg, (WIDTH, HEIGHT))
    except:
        shop_bg = pygame.Surface((WIDTH, HEIGHT))
        shop_bg.fill((50, 50, 70))
    shop_title = "Магазин скинов" if shop_type == "skins" else "Магазин следов"
    items = skins if shop_type == "skins" else trails
    purchased_items = purchased_skins if shop_type == "skins" else purchased_trails
    max_visible_items = 3
    scroll_index = 0
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    font = pygame.font.SysFont("Arial", 36, bold=True)
    item_font = pygame.font.SysFont("Arial", 24, bold=True)
    up_button = pygame.Rect(WIDTH - 45, 185, 40, 40)
    down_button = pygame.Rect(WIDTH - 45, HEIGHT - 145, 40, 40)
    back_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 80, 200, 50)
    while True:
        screen.blit(shop_bg, (0, 0))
        screen.blit(overlay, (0, 0))
        title_text = font.render(shop_title, True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
        coins_text = font.render(f"Монеты: {total_coins}", True, YELLOW)
        screen.blit(coins_text, (WIDTH // 2 - coins_text.get_width() // 2, 100))
        item_buttons = []
        visible_items = items[scroll_index:scroll_index + max_visible_items]
        for i, item in enumerate(visible_items):
            button_y = 180 + i * 120
            button_rect = pygame.Rect(WIDTH // 2 - 150, button_y, 300, 80)
            if (shop_type == "skins" and item == current_skin) or (shop_type == "trails" and item == current_trail):
                color = (204, 255, 204)
            elif item in purchased_items:
                color = (70, 70, 200)
            else:
                color = (100, 100, 100)
            pygame.draw.rect(screen, color, button_rect, border_radius=10)
            pygame.draw.rect(screen, (40, 40, 40), button_rect, 2, border_radius=10)
            item_text = item_font.render(display_name(item), True, WHITE)
            screen.blit(item_text, (button_rect.centerx - item_text.get_width() // 2,
                                   button_rect.centery - item_text.get_height() // 2))
            price = 0 if item in ["none", "default"] else (1000 if item == "rainbow" else 500)
            if item in purchased_items:
                status_text = item_font.render("Куплено", True, GREEN)
            elif price > total_coins:
                status_text = item_font.render(f"{price} монет", True, (255, 100, 100))
            else:
                status_text = item_font.render(f"{price} монет", True, YELLOW)
            screen.blit(status_text, (button_rect.centerx - status_text.get_width() // 2,
                                     button_rect.centery + 10))
            item_buttons.append((button_rect, item, price))
        pygame.draw.rect(screen, (100, 100, 255), up_button, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 255), down_button, border_radius=5)
        pygame.draw.polygon(screen, WHITE, [
            (up_button.centerx - 10, up_button.centery + 5),
            (up_button.centerx + 10, up_button.centery + 5),
            (up_button.centerx, up_button.centery - 10)
        ])
        pygame.draw.polygon(screen, WHITE, [
            (down_button.centerx - 10, down_button.centery - 5),
            (down_button.centerx + 10, down_button.centery - 5),
            (down_button.centerx, down_button.centery + 10)
        ])
        pygame.draw.rect(screen, (200, 70, 70), back_button, border_radius=10)
        pygame.draw.rect(screen, (40, 40, 40), back_button, 2, border_radius=10)
        back_text = font.render("Назад", True, WHITE)
        screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2,
                               back_button.centery - back_text.get_height() // 2))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for button_rect, item, price in item_buttons:
                    if button_rect.collidepoint(mouse_pos):
                        if item in purchased_items:
                            if shop_type == "skins":
                                current_skin = item
                            else:
                                current_trail = item
                            save_game()
                        elif price <= total_coins and price > 0:
                            total_coins -= price  # Deduct coins for purchase
                            if shop_type == "skins":
                                if item not in purchased_skins:
                                    purchased_skins.append(item)
                                current_skin = item
                            else:
                                if item not in purchased_trails:
                                    purchased_trails.append(item)
                                current_trail = item
                            save_game()
                if up_button.collidepoint(mouse_pos) and scroll_index > 0:
                    scroll_index -= 1
                if down_button.collidepoint(mouse_pos) and scroll_index < len(items) - max_visible_items:
                    scroll_index += 1
                if back_button.collidepoint(mouse_pos):
                    return "menu"
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0 and scroll_index > 0:
                    scroll_index -= 1
                elif event.y < 0 and scroll_index < len(items) - max_visible_items:
                    scroll_index += 1
            if event.type == MUSIC_END_EVENT:
                play_next_track()
        clock.tick(FPS)
    return "menu"

def show_upgrades_shop(screen):
    global total_coins, double_coins
    try:
        shop_bg = pygame.image.load("store_background.jpg")
        shop_bg = pygame.transform.scale(shop_bg, (WIDTH, HEIGHT))
    except:
        shop_bg = pygame.Surface((WIDTH, HEIGHT))
        shop_bg.fill((50, 50, 70))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    title_font = pygame.font.SysFont("Arial", 36, bold=True)
    item_font = pygame.font.SysFont("Arial", 24, bold=True)
    price_font = pygame.font.SysFont("Arial", 24, bold=True)

    title_text = title_font.render("Магазин усилений", True, WHITE)

    back_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 80, 200, 50)

    # Апгрейд: x2 монеты
    upgrade_price = 1000
    upgrade_rect = pygame.Rect(WIDTH // 2 - 150, 220, 300, 80)

    while True:
        screen.blit(shop_bg, (0, 0))
        screen.blit(overlay, (0, 0))
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 60))
        coins_text = title_font.render(f"Монеты: {total_coins}", True, YELLOW)
        screen.blit(coins_text, (WIDTH // 2 - coins_text.get_width() // 2, 110))

        # Кнопка апгрейда
        if double_coins:
            color = (204, 255, 204)  # куплено
        elif total_coins >= upgrade_price:
            color = (70, 70, 200)
        else:
            color = (100, 100, 100)
        pygame.draw.rect(screen, color, upgrade_rect, border_radius=10)
        pygame.draw.rect(screen, (40, 40, 40), upgrade_rect, 2, border_radius=10)
        name_text = item_font.render("x2 монеты", True, WHITE)
        screen.blit(name_text, (upgrade_rect.centerx - name_text.get_width() // 2,
                                upgrade_rect.centery - name_text.get_height()))
        if double_coins:
            status_text = item_font.render("Куплено", True, GREEN)
        else:
            status_color = YELLOW if total_coins >= upgrade_price else (255, 100, 100)
            status_text = price_font.render(f"{upgrade_price} монет", True, status_color)
        screen.blit(status_text, (upgrade_rect.centerx - status_text.get_width() // 2,
                                  upgrade_rect.centery))

        # Кнопка Назад
        pygame.draw.rect(screen, (200, 70, 70), back_button, border_radius=10)
        pygame.draw.rect(screen, (40, 40, 40), back_button, 2, border_radius=10)
        back_text = title_font.render("Назад", True, WHITE)
        screen.blit(back_text, (back_button.centerx - back_text.get_width() // 2,
                                back_button.centery - back_text.get_height() // 2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if back_button.collidepoint(mouse_pos):
                    return "menu"
                if upgrade_rect.collidepoint(mouse_pos) and not double_coins and total_coins >= upgrade_price:
                    total_coins -= upgrade_price
                    double_coins = True
                    save_game()
            if event.type == MUSIC_END_EVENT:
                play_next_track()
        clock.tick(FPS)


def show_loading_screen():
    global sound_enabled, high_score, max_platforms, total_coins
    load_game()
    try:
        bg_image = pygame.image.load("background_home_screen.jpg")
        bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
    except:
        bg_image = pygame.Surface((WIDTH, HEIGHT))
        bg_image.fill((30, 30, 50))
    load_music()
    title_font = pygame.font.SysFont("Arial", 48, bold=True)
    instruction_font = pygame.font.SysFont("Arial", 24)
    button_font = pygame.font.SysFont("Arial", 32, bold=True)
    stats_font = pygame.font.SysFont("Arial", 20)
    title_text = title_font.render("PIXEL HOPPER", True, (100, 255, 100))
    controls_text1 = instruction_font.render("Управление:", True, WHITE)
    controls_text2 = instruction_font.render("← → или A D - Движение", True, WHITE)
    controls_text3 = instruction_font.render("ПРОБЕЛ - Прыжок", True, WHITE)
    stats_text1 = stats_font.render(f"Рекорд: {max_platforms}", True, (200, 200, 255))
    stats_text2 = stats_font.render(f"Монеты: {total_coins}", True, (255, 255, 100))
    start_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 10, 200, 50)
    start_color = (70, 200, 70)
    start_hover_color = (100, 255, 100)
    start_text = button_font.render("СТАРТ", True, BLACK)
    skins_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50)
    skins_color = (200, 100, 200)
    skins_hover_color = (255, 150, 255)
    skins_text = button_font.render("Скины", True, BLACK)
    trails_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 150, 200, 50)
    trails_color = (100, 200, 200)
    trails_hover_color = (150, 255, 255)
    trails_text = button_font.render("Следы", True, BLACK)

    upgrades_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 220, 200, 50)
    upgrades_color = (200, 170, 100)
    upgrades_hover_color = (255, 210, 150)
    upgrades_text = button_font.render("Усиления", True, BLACK)
    sound_button_size = 40
    sound_button_rect = pygame.Rect(WIDTH - sound_button_size - 10, 10, sound_button_size, sound_button_size)
    loading = True
    while loading:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
                if sound_button_rect.collidepoint(mouse_pos):
                    toggle_sound()
            if event.type == MUSIC_END_EVENT:
                play_next_track()
        screen.blit(bg_image, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))
        stats_text1 = stats_font.render(f"Рекорд: {max_platforms}", True, (200, 200, 255))
        stats_text2 = stats_font.render(f"Монеты: {total_coins}", True, (255, 255, 100))
        screen.blit(stats_text1, (20, 20))
        screen.blit(stats_text2, (20, 45))
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//5))
        screen.blit(controls_text1, (WIDTH//2 - controls_text1.get_width()//2, HEIGHT//2 - 110))
        screen.blit(controls_text2, (WIDTH//2 - controls_text2.get_width()//2, HEIGHT//2 - 80))
        screen.blit(controls_text3, (WIDTH//2 - controls_text3.get_width()//2, HEIGHT//2 - 50))
        start_hovered = start_button.collidepoint(mouse_pos)
        pygame.draw.rect(screen, start_hover_color if start_hovered else start_color, start_button, border_radius=10)
        pygame.draw.rect(screen, (40, 40, 40), start_button, 2, border_radius=10)
        screen.blit(start_text, (start_button.centerx - start_text.get_width()//2,
                               start_button.centery - start_text.get_height()//2))
        skins_hovered = skins_button.collidepoint(mouse_pos)
        pygame.draw.rect(screen, skins_hover_color if skins_hovered else skins_color, skins_button, border_radius=10)
        pygame.draw.rect(screen, (40, 40, 40), skins_button, 2, border_radius=10)
        screen.blit(skins_text, (skins_button.centerx - skins_text.get_width()//2,
                               skins_button.centery - skins_text.get_height()//2))
        trails_hovered = trails_button.collidepoint(mouse_pos)
        pygame.draw.rect(screen, trails_hover_color if trails_hovered else trails_color, trails_button, border_radius=10)
        pygame.draw.rect(screen, (40, 40, 40), trails_button, 2, border_radius=10)
        screen.blit(trails_text, (trails_button.centerx - trails_text.get_width()//2,
                                trails_button.centery - trails_text.get_height()//2))

        upgrades_hovered = upgrades_button.collidepoint(mouse_pos)
        pygame.draw.rect(screen, upgrades_hover_color if upgrades_hovered else upgrades_color, upgrades_button, border_radius=10)
        pygame.draw.rect(screen, (40, 40, 40), upgrades_button, 2, border_radius=10)
        screen.blit(upgrades_text, (upgrades_button.centerx - upgrades_text.get_width()//2,
                                  upgrades_button.centery - upgrades_text.get_height()//2))
        sound_button_hovered = sound_button_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, (100, 100, 255) if sound_button_hovered else (70, 70, 200), sound_button_rect, border_radius=10)
        if sound_enabled:
            pygame.draw.polygon(screen, WHITE, [
                (sound_button_rect.left + 10, sound_button_rect.centery - 7),
                (sound_button_rect.left + 17, sound_button_rect.centery - 7),
                (sound_button_rect.left + 25, sound_button_rect.centery - 15),
                (sound_button_rect.left + 25, sound_button_rect.centery + 15),
                (sound_button_rect.left + 17, sound_button_rect.centery + 7),
                (sound_button_rect.left + 10, sound_button_rect.centery + 7)
            ])
            for i in range(3):
                start_x = sound_button_rect.left + 28 + i*3
                height = 8 + i*4
                pygame.draw.arc(screen, WHITE, (start_x, sound_button_rect.centery - height//2, 5, height), -0.7, 0.7, 2)
        else:
            pygame.draw.polygon(screen, WHITE, [
                (sound_button_rect.left + 10, sound_button_rect.centery - 7),
                (sound_button_rect.left + 17, sound_button_rect.centery - 7),
                (sound_button_rect.left + 25, sound_button_rect.centery - 15),
                (sound_button_rect.left + 25, sound_button_rect.centery + 15),
                (sound_button_rect.left + 17, sound_button_rect.centery + 7),
                (sound_button_rect.left + 10, sound_button_rect.centery + 7)
            ])
            pygame.draw.line(screen, (255, 70, 70), (sound_button_rect.left + 30, sound_button_rect.top + 10),
                           (sound_button_rect.left + 10, sound_button_rect.bottom - 10), 3)
        if mouse_clicked:
            if start_hovered:
                loading = False
            elif skins_hovered:
                result = show_shop_screen(screen, "skins")
                load_game()
                if result == "quit":
                    pygame.quit()
                    sys.exit()
            elif trails_hovered:
                result = show_shop_screen(screen, "trails")
                load_game()
                if result == "quit":
                    pygame.quit()
                    sys.exit()
            elif upgrades_hovered:
                result = show_upgrades_shop(screen)
                load_game()
                if result == "quit":
                    pygame.quit()
                    sys.exit()
        pygame.display.flip()
        clock.tick(60)

def main():
    global current_score, high_score, is_transitioning, transition_alpha, next_bg, current_bg_index, coins, platforms_passed, max_platforms, total_coins
    assets_dir = Path(__file__).parent / "assets"
    if not assets_dir.exists():
        assets_dir.mkdir()
        print(f"Создана папка assets по пути: {assets_dir}")
        print("Поместите файлы скинов (ninja.png, robot.png, zombie.png) в эту папку")
    while True:
        show_loading_screen()
        reset_game_state()
        current_background = load_background(0)
        player = Player()
        platforms = generate_platforms(HEIGHT - 50, 10)
        coins.clear()
        camera_offset = 0
        if platforms:
            player.rect.bottom = platforms[0].rect.top
            player.on_ground = True
            player.initial_jump_available = True
        running = True
        while running:
            current_time = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        player.jump()
                if event.type == MUSIC_END_EVENT:
                    play_next_track()
            keys = pygame.key.get_pressed()
            player.velocity_x = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player.velocity_x = -PLAYER_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player.velocity_x = PLAYER_SPEED
            player.update()
            if player.rect.top > HEIGHT:
                result = show_game_over(screen)
                if result == "restart":
                    reset_game_state()
                    current_background = load_background(0)
                    player = Player()
                    platforms = generate_platforms(HEIGHT - 50, 10)
                    coins.clear()
                    camera_offset = 0
                    if platforms:
                        player.rect.bottom = platforms[0].rect.top
                        player.on_ground = True
                        player.initial_jump_available = True
                    continue
                elif result == "menu":
                    running = False
                    break
                else:
                    pygame.quit()
                    return
            player.on_ground = False
            for platform in platforms[:]:
                if (player.rect.colliderect(platform.rect) and
                        player.velocity_y > 0 and
                        player.old_y + PLAYER_SIZE <= platform.rect.top):
                    player.rect.bottom = platform.rect.top
                    player.velocity_y = 0
                    player.on_ground = True
                    if platform.type == "spring":
                        player.velocity_y = INITIAL_JUMP_VELOCITY * 1.5
                        platform.compress_spring()
                        player.on_ground = False
                    elif platform.type == "disappearing" and not platform.activated:
                        platform.activated = True
                        platform.disappear_time = current_time
            
            # Удаляем дублирующий подсчет платформ и оставляем только этот блок
            for platform in platforms:
                if not platform.counted and player.rect.bottom < platform.rect.top:
                    platforms_passed += 1
                    platform.counted = True
                    if platforms_passed > max_platforms:
                        max_platforms = platforms_passed
                        save_game()
            
            platforms = [p for p in platforms if not p.should_disappear()]
            
            for coin in coins[:]:
                coin.update()
                if player.rect.colliderect(coin.rect):
                    player.add_score(coin.value)
                    coins.remove(coin)
            
            if player.rect.top < HEIGHT // 3:
                offset = HEIGHT // 3 - player.rect.top
                camera_offset += offset
                player.rect.y += offset
                for platform in platforms:
                    platform.rect.y += offset
                for coin in coins:
                    coin.rect.y += offset
                for point in player.trail_points:
                    point['y'] += offset
            
            # Удаляем платформы, которые вышли за пределы экрана
            platforms = [p for p in platforms if p.rect.top <= HEIGHT]
            
            if platforms:
                highest_platform = min(p.rect.y for p in platforms)
                while highest_platform > 0:
                    new_y = highest_platform - PLATFORM_GAP
                    new_x = random.randint(0, WIDTH - PLATFORM_WIDTH)
                    new_platform = Platform(new_x, new_y)
                    new_platform.counted = False
                    platforms.append(new_platform)
                    if random.random() < 0.4:
                        coin_type = "blue" if random.random() < 0.15 else "yellow"
                        coins.append(Coin(new_x + PLATFORM_WIDTH//2 - COIN_SIZE//2, new_y - COIN_SIZE - 5, coin_type))
                    highest_platform = new_y
            
            if is_transitioning:
                screen.blit(current_background, (0, 0))
                next_bg.set_alpha(transition_alpha)
                screen.blit(next_bg, (0, 0))
                transition_alpha += 5
                if transition_alpha >= 255:
                    is_transitioning = False
                    current_background = next_bg
            else:
                screen.blit(current_background, (0, 0))
            
            for platform in platforms:
                platform.draw(screen)
            for coin in coins:
                coin.draw(screen)
            player.draw(screen)
            
            score_surface = pygame.Surface((250, 80), pygame.SRCALPHA)
            pygame.draw.rect(score_surface, (0, 0, 0, 150), (0, 0, 250, 80), border_radius=5)
            font = pygame.font.SysFont("Arial", 24, bold=True)
            score_text = font.render(f"Платформы: {platforms_passed}", True, WHITE)
            high_text = font.render(f"Рекорд: {max_platforms}", True, YELLOW)
            coins_text = font.render(f"Монеты: {total_coins}", True, (255, 200, 100))
            screen.blit(score_surface, (10, 10))
            screen.blit(score_text, (20, 15))
            screen.blit(high_text, (20, 35))
            screen.blit(coins_text, (20, 55))
            
            pygame.display.flip()
            clock.tick(FPS)

if __name__ == "__main__":
    import sys
    main()
