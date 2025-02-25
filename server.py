import socket
import threading
import json
import random
import os
import pygame
from pygame.locals import *

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
WIN_SCORE = 5


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
        bullet = Bullet(self.id, self.x + PLAYER_SIZE //
                        2, self.y + PLAYER_SIZE//2)
        return bullet

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

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width
        }

    @staticmethod
    def from_dict(data):
        return Platform(data['x'], data['y'], data['width'])


class Room:
    def __init__(self, room_id):
        self.id = room_id
        self.players = {}
        self.bullets = []
        self.platforms = self.generate_platforms()
        self.clients = {}  # Добавлено для хранения связи игроков с их сокетами

    def generate_platforms(self):
        platforms = []
        # Основная платформа (земля)
        platforms.append(Platform(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH))

        # Параметры прыжка
        jump_height = (JUMP_FORCE**2) / (2 * GRAVITY)
        jump_time = (2 * abs(JUMP_FORCE)) / GRAVITY
        max_horizontal = MOVEMENT_SPEED * jump_time

        # Минимальная высота между платформами (половина высоты прыжка)
        min_vertical_distance = jump_height * 0.5

        grid_size = 30
        grid = [[False for _ in range((SCREEN_HEIGHT // grid_size) + 1)]
                for _ in range((SCREEN_WIDTH // grid_size) + 1)]

        for x in range(SCREEN_WIDTH // grid_size):
            for y in range(3):
                if (SCREEN_HEIGHT // grid_size) - y >= 0:
                    grid[x][(SCREEN_HEIGHT // grid_size) - y] = True

        top_target_y = 20 

        # Создаем несколько "путей" наверх
        num_paths = random.randint(2, 3)
        path_starting_points = [random.randint(
            100, SCREEN_WIDTH - 300) for _ in range(num_paths)]

        # Минимальное расстояние между путями
        min_path_distance = 150
        path_starting_points.sort()

        # Обеспечиваем минимальное расстояние между путями
        for i in range(1, len(path_starting_points)):
            if path_starting_points[i] - path_starting_points[i-1] < min_path_distance:
                path_starting_points[i] = path_starting_points[i -
                                                               1] + min_path_distance
                if path_starting_points[i] > SCREEN_WIDTH - 150:
                    path_starting_points[i] = SCREEN_WIDTH - 150

        # Генерируем платформы для каждого пути
        for path_index, start_x in enumerate(path_starting_points):
            current_x = start_x
            current_y = SCREEN_HEIGHT - 20 - jump_height * 0.8

            height_to_top = (SCREEN_HEIGHT - 20) - top_target_y
            step_height = min_vertical_distance * 1.2
            platforms_to_top = int(height_to_top / step_height) + 1

            platforms_in_path = max(4, min(platforms_to_top, 8))

            height_per_platform = height_to_top / (platforms_in_path)
            path_platform_heights = []

            for i in range(platforms_in_path):
                platform_width = random.randint(80, 150)

                current_x = max(
                    10, min(current_x, SCREEN_WIDTH - platform_width - 10))

                if path_platform_heights:
                    too_close = False
                    for existing_y in path_platform_heights:
                        if abs(current_y - existing_y) < min_vertical_distance:
                            too_close = True
                            break

                    if too_close:
                        closest_height = min(
                            path_platform_heights, key=lambda y: abs(y - current_y))
                        if current_y > closest_height:
                            current_y = closest_height + min_vertical_distance
                        else:
                            current_y = closest_height - min_vertical_distance
                new_platform = Platform(current_x, current_y, platform_width)

                platform_cells = []
                for px in range(int(current_x) // grid_size,
                                (int(current_x) + platform_width) // grid_size + 1):
                    if 0 <= px < len(grid):
                        py = int(current_y) // grid_size
                        if 0 <= py < len(grid[0]):
                            platform_cells.append((px, py))

                too_close_to_other_platforms = False
                for platform in platforms[1:]:
                    if abs(platform.y - current_y) < min_vertical_distance:
                        if (current_x < platform.x + platform.width and
                                current_x + platform_width > platform.x):
                            too_close_to_other_platforms = True
                            break

                # Если нет пересечений и соблюдается минимальное расстояние, добавляем платформу
                if (not any(grid[px][py] for px, py in platform_cells if px < len(grid) and py < len(grid[0])) and
                        not too_close_to_other_platforms):
                    platforms.append(new_platform)
                    path_platform_heights.append(current_y)

                    for px, py in platform_cells:
                        if px < len(grid) and py < len(grid[0]):
                            grid[px][py] = True
                if i == platforms_in_path - 2:
                    current_y = top_target_y + jump_height * 0.3
                else:
                    height_change = max(
                        min_vertical_distance, height_per_platform * random.uniform(0.8, 1.2))
                    current_y -= height_change

                max_shift = max_horizontal * 0.85

                # В зависимости от номера пути, смещаем платформы в разных направлениях
                if path_index % 2 == 0:
                    horizontal_shift = random.uniform(-max_shift, max_shift/2)
                else:
                    horizontal_shift = random.uniform(-max_shift/2, max_shift)

                current_x += horizontal_shift

        # Добавляем финальную "верхнюю" платформу для каждого пути
        for path_index, start_x in enumerate(path_starting_points):
            highest_platform = None
            highest_y = SCREEN_HEIGHT

            for platform in platforms[1:]:  # Пропускаем землю
                if platform.y < highest_y:
                    highest_y = platform.y
                    highest_platform = platform

            if highest_platform:
                final_x = highest_platform.x + \
                    random.uniform(-max_horizontal*0.5, max_horizontal*0.5)
                final_y = top_target_y  # Размещаем у самого верха
                # Чуть шире для надежности
                final_width = random.randint(100, 180)

                final_x = max(
                    10, min(final_x, SCREEN_WIDTH - final_width - 10))

                can_place = True
                for platform in platforms:
                    # Проверяем пересечения
                    if (final_x < platform.x + platform.width and
                            final_x + final_width > platform.x):
                        # Если платформы могут пересекаться по горизонтали, проверяем вертикальное расстояние
                        if abs(platform.y - final_y) < min_vertical_distance:
                            can_place = False
                            break

                if can_place:
                    platforms.append(Platform(final_x, final_y, final_width))

        # Добавляем несколько соединительных платформ между путями
        if len(platforms) > 5:
            for _ in range(random.randint(2, 4)):
                if len(platforms) < 3:
                    break

                plat1_index = random.randint(1, len(platforms) - 1)
                plat2_index = random.randint(1, len(platforms) - 1)

                attempts = 0
                while (plat1_index == plat2_index or
                       abs(platforms[plat1_index].y - platforms[plat2_index].y) < min_vertical_distance) and attempts < 10:
                    plat2_index = random.randint(1, len(platforms) - 1)
                    attempts += 1

                if plat1_index == plat2_index or abs(platforms[plat1_index].y - platforms[plat2_index].y) < min_vertical_distance:
                    continue

                plat1 = platforms[plat1_index]
                plat2 = platforms[plat2_index]

                if abs(plat1.y - plat2.y) < jump_height * 0.5 and abs(plat1.y - plat2.y) >= min_vertical_distance:
                    connect_x = (plat1.x + plat2.x) / 2
                    connect_y = (plat1.y + plat2.y) / 2
                    connect_width = random.randint(70, 120)

                    can_place = True
                    for platform in platforms:
                        if (connect_x < platform.x + platform.width and
                                connect_x + connect_width > platform.x):
                            if abs(platform.y - connect_y) < min_vertical_distance:
                                can_place = False
                                break

                    if can_place:
                        platforms.append(
                            Platform(connect_x, connect_y, connect_width))

        return platforms

    def update(self, server):
        # Проверка на победу
        for player_id, player in list(self.players.items()):
            if player.score >= WIN_SCORE:
                # Отправляем сообщение всем игрокам о победителе
                winner_message = {
                    'type': 'winner',
                    'player_id': player_id
                }
                self.broadcast_message(server, winner_message)

        # Обновление игроков
        for player_id, player in list(self.players.items()):
            old_health = player.health
            player.update(self.platforms)

            # Проверка низкого здоровья
            if old_health > 30 and player.health <= 30:
                # Отправляем предупреждение о низком здоровье
                low_health_message = {
                    'type': 'low_health',
                    'player_id': player_id
                }
                if player_id in server.clients:
                    server.send_data(
                        server.clients[player_id]['socket'], low_health_message)

            # Проверка на смерть
            if player.health <= 0:
                # Отправляем сообщение о смерти
                death_message = {
                    'type': 'death',
                    'player_id': player_id
                }
                if player_id in server.clients:
                    server.send_data(
                        server.clients[player_id]['socket'], death_message)

                # Удаляем игрока из комнаты
                del self.players[player_id]

        # Обновление пуль и обработка попаданий
        updated_bullets = []
        for bullet in self.bullets:
            if bullet.update():
                hit = False
                for player_id, player in self.players.items():
                    if player_id != bullet.owner_id and player.rect.colliderect(bullet.rect):
                        player.health -= 10
                        hit = True

                        # Если здоровье игрока стало критическим после попадания
                        if player.health <= 30 and player.health > 0:
                            low_health_message = {
                                'type': 'low_health',
                                'player_id': player_id
                            }
                            if player_id in server.clients:
                                server.send_data(
                                    server.clients[player_id]['socket'], low_health_message)

                        # Если игрок умер от попадания
                        if player.health <= 0:
                            death_message = {
                                'type': 'death',
                                'player_id': player_id
                            }
                            if player_id in server.clients:
                                server.send_data(
                                    server.clients[player_id]['socket'], death_message)

                        # Добавляем очко тому, кто попал
                        if bullet.owner_id in self.players:
                            shooter = self.players[bullet.owner_id]
                            shooter.score += 1

                            # Проверка выиграл ли стрелок
                            if shooter.score >= WIN_SCORE:
                                winner_message = {
                                    'type': 'winner',
                                    'player_id': bullet.owner_id
                                }
                                self.broadcast_message(server, winner_message)

                        break
                if not hit:
                    updated_bullets.append(bullet)
            else:
                # Пуля вышла за пределы экрана
                pass
        self.bullets = updated_bullets

    def broadcast_message(self, server, message):
        """Отправляет сообщение всем игрокам в комнате"""
        for player_id in self.players:
            if player_id in server.clients:
                try:
                    server.send_data(
                        server.clients[player_id]['socket'], message)
                except:
                    pass

    def to_dict(self):
        return {
            'id': self.id,
            'players': {player_id: player.to_dict() for player_id, player in self.players.items()},
            'bullets': [bullet.to_dict() for bullet in self.bullets],
            'platforms': [platform.to_dict() for platform in self.platforms]
        }

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


class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.rooms = {}
        self.next_player_id = 0
        self.next_room_id = 0

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[SERVER] Сервер запущен на {self.host}:{self.port}")

        self.create_room()

        update_thread = threading.Thread(target=self.update_loop)
        update_thread.daemon = True
        update_thread.start()

        try:
            while True:
                client_socket, address = self.server_socket.accept()
                print(f"[SERVER] Новое подключение: {address}")

                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("[SERVER] Сервер остановлен")
        finally:
            self.server_socket.close()

    def create_room(self):
        room_id = self.next_room_id
        self.rooms[room_id] = Room(room_id)
        self.next_room_id += 1
        print(f"[SERVER] Создана комната {room_id}")
        return room_id

    def handle_client(self, client_socket, address):
        player_id = self.next_player_id
        self.next_player_id += 1

        room_id = None
        for rid, room in self.rooms.items():
            if len(room.players) < MAX_PLAYERS:
                room_id = rid
                break

        if room_id is None:
            room_id = self.create_room()

        x = random.randint(50, SCREEN_WIDTH - 50)
        y = SCREEN_HEIGHT - 100
        player = Player(player_id, x, y)

        self.rooms[room_id].players[player_id] = player
        # Сохраняем связь между комнатой и сокетами игроков
        self.rooms[room_id].clients[player_id] = client_socket

        self.clients[player_id] = {
            'socket': client_socket,
            'room_id': room_id
        }

        self.send_data(client_socket, {
            'type': 'init',
            'player_id': player_id,
            'room_id': room_id
        })

        buffer = b''
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break

                buffer += data

                # Обработка фрагментированных данных
                while len(buffer) >= 4:
                    message_length = int.from_bytes(
                        buffer[:4], byteorder='big')

                    # Если полное сообщение еще не получено
                    if len(buffer) < 4 + message_length:
                        break

                    # Извлекаем сообщение
                    message_data = buffer[4:4+message_length]
                    buffer = buffer[4+message_length:]

                    # Обрабатываем сообщение
                    message = json.loads(message_data.decode('utf-8'))
                    self.process_client_message(player_id, message)

        except Exception as e:
            print(f"[SERVER] Ошибка при обработке клиента {player_id}: {e}")
        finally:
            if player_id in self.clients:
                room_id = self.clients[player_id]['room_id']
                if room_id in self.rooms:
                    room = self.rooms[room_id]
                    if player_id in room.players:
                        del room.players[player_id]
                    if player_id in room.clients:
                        del room.clients[player_id]
                    print(
                        f"[SERVER] Игрок {player_id} покинул комнату {room_id}")

                    if len(room.players) == 0:
                        del self.rooms[room_id]
                        print(f"[SERVER] Комната {room_id} удалена")

                del self.clients[player_id]

            client_socket.close()
            print(f"[SERVER] Клиент {address} отключен")

    def process_client_message(self, player_id, message):
        if player_id not in self.clients:
            return

        room_id = self.clients[player_id]['room_id']
        if room_id not in self.rooms:
            return

        room = self.rooms[room_id]
        player = room.players.get(player_id)

        if message['type'] == 'input':
            if not player:
                return

            if message.get('left'):
                player.move_left()
            elif message.get('right'):
                player.move_right()
            else:
                player.stop()

            if message.get('jump'):
                player.jump()

            if message.get('shoot'):
                # Получаем координаты мыши из сообщения
                target_x = message.get('mouse_x', player.x)
                target_y = message.get('mouse_y', player.y - 100)

                # Вычисляем направление
                start_x = player.x + PLAYER_SIZE//2
                start_y = player.y + PLAYER_SIZE//2
                dx = target_x - start_x
                dy = target_y - start_y
                distance = max(1, (dx**2 + dy**2)**0.5)

                # Нормализуем и задаем скорость
                speed = BULLET_SPEED
                bullet_vel_x = (dx / distance) * speed
                bullet_vel_y = (dy / distance) * speed

                bullet = Bullet(player.id, start_x, start_y)
                bullet.vel_x = bullet_vel_x
                bullet.vel_y = bullet_vel_y
                room.bullets.append(bullet)

        elif message['type'] == 'restart':
            # Обработка запроса на перезапуск игрока
            # Если игрок не существует или был удален при смерти
            if player_id not in room.players:
                # Создаем нового игрока
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = SCREEN_HEIGHT - 100
                new_player = Player(player_id, x, y)
                room.players[player_id] = new_player

                # Отправляем подтверждение о успешном перезапуске
                self.send_data(self.clients[player_id]['socket'], {
                    'type': 'restart_success'
                })
                print(
                    f"[SERVER] Игрок {player_id} перезапущен в комнате {room_id}")
            else:
                # Если игрок существует, но выиграл или имеет низкое здоровье
                # Сбрасываем его состояние
                player.health = 100
                player.score = 0
                player.x = random.randint(50, SCREEN_WIDTH - 50)
                player.y = SCREEN_HEIGHT - 100
                player.vel_x = 0
                player.vel_y = 0

                # Отправляем подтверждение о успешном перезапуске
                self.send_data(self.clients[player_id]['socket'], {
                    'type': 'restart_success'
                })
                print(
                    f"[SERVER] Состояние игрока {player_id} сброшено в комнате {room_id}")

        elif message['type'] == 'change_room':
            if not player:
                return

            new_room_id = message.get('room_id')
            if new_room_id is not None and new_room_id in self.rooms:
                if player_id in room.players:
                    del room.players[player_id]
                if player_id in room.clients:
                    del room.clients[player_id]

                self.clients[player_id]['room_id'] = new_room_id
                self.rooms[new_room_id].players[player_id] = player
                self.rooms[new_room_id].clients[player_id] = self.clients[player_id]['socket']
                print(
                    f"[SERVER] Игрок {player_id} перешел в комнату {new_room_id}")

    def update_loop(self):
        while True:
            for room_id, room in list(self.rooms.items()):
                # Обновляем состояние комнаты и передаем ссылку на сервер
                room.update(self)

                # Отправляем состояние комнаты всем игрокам
                room_data = room.to_dict()
                for player_id in list(room.players.keys()):
                    if player_id in self.clients:
                        try:
                            self.send_data(self.clients[player_id]['socket'], {
                                'type': 'state',
                                'room': room_data
                            })
                        except Exception as e:
                            print(
                                f"[SERVER] Ошибка при отправке состояния игроку {player_id}: {e}")

            pygame.time.delay(33)  # ~30 FPS

    def send_data(self, client_socket, data):
        try:
            message = json.dumps(data).encode('utf-8')
            # Добавляем заголовок с длиной сообщения (4 байта)
            header = len(message).to_bytes(4, byteorder='big')
            client_socket.sendall(header + message)
        except Exception as e:
            print(f"[SERVER] Ошибка при отправке данных: {e}")


def run_server():
    pygame.init()  # Инициализируем pygame для расчетов
    server = Server(SERVER_IP, PORT)
    server.start()


if __name__ == "__main__":
    run_server()
