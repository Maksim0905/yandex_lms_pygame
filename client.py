import pygame
import socket
import threading
import json
import random
import os
from pygame.locals import *

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PLAYER_SIZE = 32
BULLET_SIZE = 8
GRAVITY = 0.5
JUMP_FORCE = -10
MOVEMENT_SPEED = 5
BULLET_SPEED = 10
PLATFORM_HEIGHT = 20
MAX_PLAYERS = 4
PORT = 5555
SERVER_IP = "127.0.0.1"
WIN_SCORE = 5  # Количество очков для победы

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

if not os.path.exists("assets"):
    os.makedirs("assets")


def create_player_image(color, player_id):
    player_surface = pygame.Surface(
        (PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(player_surface, color, (8, 8, 16, 24))
    pygame.draw.circle(player_surface, (255, 220, 175), (16, 8), 8)
    pygame.draw.circle(player_surface, BLACK, (14, 6), 2)
    pygame.draw.circle(player_surface, BLACK, (18, 6), 2)
    font = pygame.font.Font(None, 20)
    text = font.render(str(player_id), True, WHITE)
    player_surface.blit(text, (13, 14))
    filename = f"assets/player_{player_id}.png"
    pygame.image.save(player_surface, filename)
    return filename


def create_bullet_image():
    bullet_surface = pygame.Surface(
        (BULLET_SIZE, BULLET_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(bullet_surface, RED, (BULLET_SIZE //
                       2, BULLET_SIZE//2), BULLET_SIZE//2)
    filename = "assets/bullet.png"
    pygame.image.save(bullet_surface, filename)
    return filename


def create_background_image():
    bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg_surface.fill((135, 206, 235))
    pygame.draw.circle(bg_surface, YELLOW, (700, 100), 50)
    for i in range(5):
        x = random.randint(50, SCREEN_WIDTH - 100)
        y = random.randint(50, 200)
        size = random.randint(30, 70)
        pygame.draw.ellipse(bg_surface, WHITE, (x, y, size*2, size))
        pygame.draw.ellipse(bg_surface, WHITE,
                            (x+size//2, y-size//4, size*2, size))
        pygame.draw.ellipse(bg_surface, WHITE, (x+size, y, size*2, size))
    filename = "assets/background.png"
    pygame.image.save(bg_surface, filename)
    return filename


player_images = [create_player_image(
    color, i+1) for i, color in enumerate([BLUE, RED, GREEN, YELLOW])]
bullet_image = create_bullet_image()
background_image = create_background_image()


class Player:
    def __init__(self, player_id, x, y):
        self.id = player_id
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        self.health = 100
        self.score = 0
        self.image = pygame.image.load(
            player_images[player_id % len(player_images)])
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)

    def update(self, platforms):
        self.vel_y += GRAVITY
        self.x += self.vel_x
        self.y += self.vel_y

        if self.x < 0:
            self.x = 0
        if self.x > SCREEN_WIDTH - PLAYER_SIZE:
            self.x = SCREEN_WIDTH - PLAYER_SIZE

        self.rect.x = self.x
        self.rect.y = self.y

        on_ground = False
        for platform in platforms:
            if (self.rect.bottom >= platform.rect.top and
                self.rect.bottom <= platform.rect.top + 10 and
                self.rect.right > platform.rect.left and
                self.rect.left < platform.rect.right and
                    self.vel_y > 0):
                self.rect.bottom = platform.rect.top
                self.y = self.rect.y
                self.vel_y = 0
                on_ground = True

        self.is_jumping = not on_ground

        if self.y > SCREEN_HEIGHT:
            self.x = random.randint(50, SCREEN_WIDTH - 50)
            self.y = 0
            self.vel_y = 0
            self.health -= 25

        if self.y < 10 and self.y > 0:
            self.score += 1
            self.x = random.randint(50, SCREEN_WIDTH - 50)
            self.y = SCREEN_HEIGHT - 100
            self.vel_y = 0

    def jump(self):
        if not self.is_jumping:
            self.vel_y = JUMP_FORCE
            self.is_jumping = True

    def move_left(self):
        self.vel_x = -MOVEMENT_SPEED

    def move_right(self):
        self.vel_x = MOVEMENT_SPEED

    def stop(self):
        self.vel_x = 0

    def shoot(self):
        return Bullet(self.id, self.x + PLAYER_SIZE//2, self.y + PLAYER_SIZE//2)

    def to_dict(self):
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'vel_x': self.vel_x,
            'vel_y': self.vel_y,
            'health': self.health,
            'score': self.score
        }

    @staticmethod
    def from_dict(data):
        player = Player(data['id'], data['x'], data['y'])
        player.vel_x = data['vel_x']
        player.vel_y = data['vel_y']
        player.health = data['health']
        player.score = data['score']
        return player


class Bullet:
    def __init__(self, owner_id, x, y):
        self.owner_id = owner_id
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = -BULLET_SPEED
        self.image = pygame.image.load(bullet_image)
        self.rect = pygame.Rect(x, y, BULLET_SIZE, BULLET_SIZE)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.x = self.x
        self.rect.y = self.y

        if (self.x < 0 or self.x > SCREEN_WIDTH or
                self.y < 0 or self.y > SCREEN_HEIGHT):
            return False
        return True

    def to_dict(self):
        return {
            'owner_id': self.owner_id,
            'x': self.x,
            'y': self.y,
            'vel_x': self.vel_x,
            'vel_y': self.vel_y
        }

    @staticmethod
    def from_dict(data):
        bullet = Bullet(data['owner_id'], data['x'], data['y'])
        bullet.vel_x = data['vel_x']
        bullet.vel_y = data['vel_y']
        return bullet


class Platform:
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width
        self.height = PLATFORM_HEIGHT
        self.rect = pygame.Rect(x, y, width, self.height)

    def draw(self, screen):
        pygame.draw.rect(screen, (101, 67, 33), self.rect)

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width
        }

    @staticmethod
    def from_dict(data):
        return Platform(data['x'], data['y'], data['width'])


class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.Font(None, 32)

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)  # Border

        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, click):
        return self.rect.collidepoint(mouse_pos) and click


class Room:
    def __init__(self, room_id):
        self.id = room_id
        self.players = {}
        self.bullets = []
        self.platforms = []
        self.background = pygame.image.load(background_image)

    @staticmethod
    def from_dict(data):
        room = Room(data['id'])
        room.players = {int(player_id): Player.from_dict(player_data)
                        for player_id, player_data in data['players'].items()}
        room.bullets = [Bullet.from_dict(bullet_data)
                        for bullet_data in data['bullets']]
        room.platforms = [Platform.from_dict(
            platform_data) for platform_data in data['platforms']]
        return room


class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.dead = False
        self.low_health = False
        self.winner = False
        self.socket = None
        self.player_id = None
        self.room_id = None
        self.room = None
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Jump Game")
        self.clock = pygame.time.Clock()
        self.running = False
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.input_state = {
            'left': False,
            'right': False,
            'jump': False,
            'shoot': False
        }
        self.mouse_x = 0
        self.mouse_y = 0
        # Таймеры для показа сообщений
        self.message_timer = 0
        self.message_text = ""
        self.message_color = WHITE
        # Кнопка перезапуска
        self.restart_button = Button(
            SCREEN_WIDTH//2 - 100,
            SCREEN_HEIGHT//2 + 100,
            200, 50,
            "Перезапустить",
            (70, 70, 70),
            (100, 100, 100)
        )
        # Флаг для управления экраном смерти/победы
        self.show_end_screen = False

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"[CLIENT] Подключено к серверу {self.host}:{self.port}")

            receive_thread = threading.Thread(target=self.receive_data)
            receive_thread.daemon = True
            receive_thread.start()

            return True
        except Exception as e:
            print(f"[CLIENT] Ошибка подключения: {e}")
            return False

    def receive_data(self):
        buffer = b''
        while True:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break

                buffer += data

                while len(buffer) >= 4:
                    # Читаем заголовок с длиной сообщения
                    msg_length = int.from_bytes(buffer[:4], byteorder='big')
                    if len(buffer) < 4 + msg_length:
                        break  # Не все данные получены

                    # Извлекаем полное сообщение
                    message_data = buffer[4:4+msg_length]
                    buffer = buffer[4+msg_length:]

                    message = json.loads(message_data.decode('utf-8'))
                    self.process_server_message(message)

            except Exception as e:
                print(f"[CLIENT] Ошибка при получении данных: {e}")
                break

    def process_server_message(self, message):
        if message['type'] == 'init':
            self.player_id = message['player_id']
            self.room_id = message['room_id']
            # Сбрасываем все флаги при инициализации
            self.dead = False
            self.low_health = False
            self.winner = False
            self.show_end_screen = False
            print(
                f"[CLIENT] Инициализирован как игрок {self.player_id} в комнате {self.room_id}")
        elif message['type'] == 'state':
            old_room = self.room
            self.room = Room.from_dict(message['room'])

            # Проверка выигрыша
            if self.player_id in self.room.players:
                player = self.room.players[self.player_id]

                # Проверяем условие победы
                if player.score >= WIN_SCORE and not self.winner:
                    self.winner = True
                    self.show_end_screen = True
                    self.show_message("ВЫ ПОБЕДИЛИ!", GREEN, 3000)

                # Проверяем состояние здоровья
                if player.health <= 30 and not self.low_health and not self.dead:
                    self.low_health = True
                    self.show_message(
                        "ВНИМАНИЕ! КРИТИЧЕСКИ НИЗКОЕ ЗДОРОВЬЕ!", RED, 2000)
                elif player.health > 30:
                    self.low_health = False

            # Проверка если игрок был в комнате, но сейчас его нет (умер или был удален)
            if old_room and self.player_id in old_room.players and self.player_id not in self.room.players:
                self.dead = True
                self.show_end_screen = True
                self.show_message(
                    "ВЫ ПРОИГРАЛИ! Здоровье закончилось", RED, 3000)

        elif message['type'] == 'death':
            self.dead = True
            self.show_end_screen = True
            self.show_message(
                "ВЫ ПОГИБЛИ! Нажмите кнопку для возрождения", RED, 3000)

        elif message['type'] == 'restart_success':
            # Сбрасываем флаги состояния при успешном перезапуске
            self.dead = False
            self.low_health = False
            self.winner = False
            self.show_end_screen = False
            self.show_message("Перезапуск выполнен!", GREEN, 1000)

    def show_message(self, text, color, duration):
        self.message_text = text
        self.message_color = color
        self.message_timer = duration

    def send_input(self):
        if self.socket and self.player_id is not None:
            try:
                message = {'type': 'input', **self.input_state}

                # Добавляем координаты мыши только при выстреле
                if self.input_state.get('shoot'):
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    message.update({
                        'mouse_x': mouse_x,
                        'mouse_y': mouse_y
                    })

                # Отправляем сообщение
                message_data = json.dumps(message).encode('utf-8')
                header = len(message_data).to_bytes(4, byteorder='big')
                self.socket.sendall(header + message_data)

                # Сбрасываем состояние выстрела после отправки
                self.input_state['shoot'] = False

            except Exception as e:
                print(f"[CLIENT] Ошибка при отправке ввода: {e}")

    def send_restart_request(self):
        if self.socket and self.player_id is not None:
            try:
                message = {'type': 'restart'}
                message_data = json.dumps(message).encode('utf-8')
                header = len(message_data).to_bytes(4, byteorder='big')
                self.socket.sendall(header + message_data)
                print(f"[CLIENT] Запрос на перезапуск отправлен")
            except Exception as e:
                print(
                    f"[CLIENT] Ошибка при отправке запроса на перезапуск: {e}")

    def run(self):
        self.running = True

        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False

            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == KEYDOWN:
                    # Движение влево на A
                    if event.key == K_a:
                        self.input_state['left'] = True
                    # Движение вправо на D
                    elif event.key == K_d:
                        self.input_state['right'] = True
                    # Прыжок на SPACE или UP
                    elif event.key == K_UP or event.key == K_SPACE:
                        self.input_state['jump'] = True
                    # Выстрел на LCTRL
                    elif event.key == K_LCTRL:
                        self.input_state['shoot'] = True
                elif event.type == KEYUP:
                    if event.key == K_a:
                        self.input_state['left'] = False
                    elif event.key == K_d:
                        self.input_state['right'] = False
                    elif event.key == K_UP or event.key == K_SPACE:
                        self.input_state['jump'] = False
                    elif event.key == K_LCTRL:
                        self.input_state['shoot'] = False
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # Левая кнопка мыши
                        mouse_clicked = True
                        self.input_state['shoot'] = True
                        self.mouse_x, self.mouse_y = event.pos

            # Обновление кнопки перезапуска
            self.restart_button.update(mouse_pos)

            # Обработка нажатия на кнопку перезапуска
            if mouse_clicked and self.show_end_screen and self.restart_button.is_clicked(mouse_pos, mouse_clicked):
                self.send_restart_request()

            # Только отправляем ввод если игрок жив и не победил
            if not self.show_end_screen:
                self.send_input()

            self.render()

            # Обновляем таймер сообщения
            if self.message_timer > 0:
                self.message_timer -= self.clock.get_time()

            self.clock.tick(60)

        pygame.quit()

    def draw_message_box(self, text, color, size="normal"):
        # Создаем полупрозрачный фон
        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # RGBA: черный с 70% прозрачности
        self.screen.blit(overlay, (0, 0))

        # Выбираем шрифт в зависимости от размера сообщения
        font = self.big_font if size == "big" else self.font

        # Рисуем текст
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(
            center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))

        # Добавляем рамку вокруг сообщения
        padding = 20
        box_rect = pygame.Rect(text_rect.left - padding, text_rect.top - padding,
                               text_rect.width + padding*2, text_rect.height + padding*2)
        pygame.draw.rect(self.screen, (50, 50, 50), box_rect)
        pygame.draw.rect(self.screen, color, box_rect, 3)

        # Добавляем текст
        self.screen.blit(text_surface, text_rect)

    def render(self):
        if not self.room:
            self.screen.fill(BLACK)
            waiting_text = self.font.render(
                "Ожидание данных от сервера...", True, WHITE)
            self.screen.blit(waiting_text, (SCREEN_WIDTH//2 -
                             waiting_text.get_width()//2, SCREEN_HEIGHT//2))
        else:
            # Рисуем игровой мир
            self.screen.blit(self.room.background, (0, 0))

            for platform in self.room.platforms:
                platform.draw(self.screen)
            for bullet in self.room.bullets:
                self.screen.blit(bullet.image, (bullet.x, bullet.y))

            # Рисуем игроков
            for player_id, player in self.room.players.items():
                self.screen.blit(player.image, (player.x, player.y))

                # Здоровье
                health_color = GREEN
                if player.health < 70:
                    health_color = YELLOW
                if player.health < 30:
                    health_color = RED

                health_text = self.font.render(
                    f"{player.health}", True, health_color)
                self.screen.blit(health_text, (player.x, player.y - 20))

                # Выделяем текущего игрока
                if player_id == self.player_id:
                    pygame.draw.rect(self.screen, GREEN, player.rect, 2)

            # Рисуем очки
            y_offset = 10
            for player_id, player in self.room.players.items():
                player_color = GREEN if player_id == self.player_id else WHITE
                score_text = self.font.render(
                    f"Игрок {player_id}: {player.score}/{WIN_SCORE}", True, player_color)
                self.screen.blit(score_text, (10, y_offset))
                y_offset += 30

            # Финишная линия
            pygame.draw.rect(self.screen, RED, (0, 0, SCREEN_WIDTH, 10))
            finish_text = self.font.render("ФИНИШ", True, WHITE)
            self.screen.blit(finish_text, (SCREEN_WIDTH//2 -
                                           finish_text.get_width()//2, 10))

            # Отображаем текущее сообщение, если оно есть
            if self.message_timer > 0:
                self.draw_message_box(
                    self.message_text, self.message_color, "big")

            # Если игрок погиб или победил, показываем соответствующее сообщение
            if self.show_end_screen:
                # Создаем полупрозрачный фон
                overlay = pygame.Surface(
                    (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))  # RGBA: черный с 70% прозрачности
                self.screen.blit(overlay, (0, 0))

                # Рисуем сообщение
                message_text = "ПОЗДРАВЛЯЕМ! ВЫ ПОБЕДИЛИ!" if self.winner else "ВЫ ПРОИГРАЛИ!"
                message_color = GREEN if self.winner else RED

                text_surface = self.big_font.render(
                    message_text, True, message_color)
                text_rect = text_surface.get_rect(
                    center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))

                # Рамка сообщения
                padding = 20
                box_rect = pygame.Rect(text_rect.left - padding, text_rect.top - padding,
                                       text_rect.width + padding*2, text_rect.height + padding*2)
                pygame.draw.rect(self.screen, (50, 50, 50), box_rect)
                pygame.draw.rect(self.screen, message_color, box_rect, 3)

                # Отображаем текст
                self.screen.blit(text_surface, text_rect)

                # Отображаем описание
                description = "Наберите " + \
                    str(WIN_SCORE) + " очков для победы!"
                desc_surface = self.font.render(description, True, WHITE)
                desc_rect = desc_surface.get_rect(
                    center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
                self.screen.blit(desc_surface, desc_rect)

                # Рисуем кнопку перезапуска
                self.restart_button.draw(self.screen)

        pygame.display.flip()

    def cleanup(self):
        if self.socket:
            self.socket.close()


def run_client():
    client = Client(SERVER_IP, PORT)
    if client.connect():
        try:
            client.run()
        finally:
            client.cleanup()


if __name__ == "__main__":
    run_client()
