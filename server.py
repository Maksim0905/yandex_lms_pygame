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
        # Основная платформа
        platforms.append(Platform(0, SCREEN_HEIGHT - 20, SCREEN_WIDTH))

        # Параметры прыжка
        jump_height = (JUMP_FORCE**2) / (2 * GRAVITY)  # ≈ 100px
        jump_time = (2 * abs(JUMP_FORCE)) / GRAVITY
        max_horizontal = MOVEMENT_SPEED * jump_time     # ≈ 200px

        # Стартовая позиция игрока (центр нижней платформы)
        start_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT - PLAYER_SIZE - 0  # 20 - высота платформы

        # Первая обязательная платформа
        platform1_x = start_x - max_horizontal//2
        platform1_y = start_y - jump_height + 20  # 20px запас
        platforms.append(Platform(platform1_x, platform1_y, 120))

        # Вторая обязательная платформа
        platform2_x = platform1_x + max_horizontal//2
        platform2_y = platform1_y - jump_height + 20
        platforms.append(Platform(platform2_x, platform2_y, 120))

        # Дополнительные платформы
        current_x, current_y = platform2_x, platform2_y
        for _ in range(5):
            new_x = current_x + random.randint(-50, 50)
            new_y = current_y - random.randint(60, 80)
            platforms.append(Platform(new_x, new_y, 100))
            current_x, current_y = new_x, new_y

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
