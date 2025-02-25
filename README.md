# 🎮 Сетевая Платформер-Игра на Pygame

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<div align="center">
  <img src="https://via.placeholder.com/800x400.png?text=Скриншот+Игры" alt="Скриншот игры" width="600"/>
  
  <p><i>Многопользовательская платформер-игра с сетевыми возможностями</i></p>
</div>

## 📋 Содержание

- [📖 Описание проекта](#-описание-проекта)
- [✨ Особенности](#-особенности)
- [🛠️ Технологии](#️-технологии)
- [📁 Структура проекта](#-структура-проекта)
- [🎲 Начало работы](#-начало-работы)
- [🎯 Геймплей и управление](#-геймплей-и-управление)
- [🔧 Особенности реализации](#-особенности-реализации)
- [🔮 Будущие улучшения](#-будущие-улучшения)
- [📜 Лицензия](#-лицензия)

## 📖 Описание проекта

Этот проект представляет собой многопользовательскую сетевую игру-платформер, разработанную с использованием Pygame. Игроки могут перемещаться по платформам, прыгать, стрелять и соревноваться друг с другом. Цель игры - набрать определенное количество очков, добравшись до верхней части экрана или поразив других игроков.

<details>
<summary><b>🖼️ Посмотреть скриншоты</b></summary>
<br>
<img src="https://via.placeholder.com/600x400.png?text=Игровой+процесс" alt="Игровой процесс" width="400"/>
<img src="https://via.placeholder.com/600x400.png?text=Меню+игры" alt="Меню" width="400"/>
<img src="https://via.placeholder.com/600x400.png?text=Многопользовательский+режим" alt="Мультиплеер" width="400"/>
</details>

## ✨ Особенности

| Функция | Описание |
|---------|----------|
| 👥 Многопользовательский режим | Поддержка до 4 игроков в одной игровой сессии |
| 🔄 Клиент-сервер | Надежная сетевая архитектура для синхронизации игры |
| 🏃 Физика движения | Реалистичная гравитация и система прыжков |
| ⚔️ Боевая система | Стрельба с отслеживанием попаданий и здоровья |
| 🏆 Система очков | Получение очков за достижение целей и атаку противников |
| 🏗️ Генерация платформ | Процедурное создание игрового уровня |
| 💬 Визуальные уведомления | Сообщения о событиях (низкое здоровье, победа/поражение) |
| 🔄 Перезапуск | Возможность начать игру заново после завершения |

## 🛠️ Технологии

<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg" alt="Python" width="50" hspace="10"/>
  <img src="https://www.pygame.org/docs/_static/pygame_tiny.png" alt="Pygame" width="50" hspace="10"/>
  <img src="https://cdn-icons-png.flaticon.com/512/5969/5969293.png" alt="Сокеты" width="50" hspace="10"/>
  <img src="https://cdn-icons-png.flaticon.com/512/136/136525.png" alt="JSON" width="50" hspace="10"/>
  <img src="https://cdn-icons-png.flaticon.com/512/2620/2620975.png" alt="Многопоточность" width="50" hspace="10"/>
</div>

- **Python 3** - основной язык программирования
- **Pygame** - библиотека для создания графического интерфейса и игровой логики
- **Сокеты Python** - для сетевого взаимодействия
- **JSON** - формат для обмена данными между клиентом и сервером
- **Многопоточность** - обработка сетевых соединений в отдельных потоках

## 📁 Структура проекта

```
📦 pygame-network-platformer
 ┣ 📜 client.py - клиентская часть игры
 ┣ 📜 server.py - серверная часть игры
 ┣ 📂 assets/ - папка с игровыми ресурсами
 ┃ ┣ 🖼️ player_1.png - спрайт первого игрока
 ┃ ┣ 🖼️ player_2.png - спрайт второго игрока
 ┃ ┣ 🖼️ player_3.png - спрайт третьего игрока
 ┃ ┣ 🖼️ player_4.png - спрайт четвертого игрока
 ┃ ┣ 🖼️ bullet.png - спрайт пули
 ┃ ┗ 🖼️ background.png - фоновое изображение
 ┗ 📜 README.md
```

## 🎲 Начало работы

### Предварительные требования

<details>
<summary>Необходимые зависимости</summary>

```bash
pip install pygame
```
</details>

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/username/pygame-network-platformer.git
cd pygame-network-platformer
```

2. Установите зависимости:
```bash
pip install pygame
```

### Запуск игры

<details>
<summary>Запуск сервера</summary>

```bash
python server.py
```
</details>

<details>
<summary>Запуск клиента</summary>

```bash
python client.py
```
</details>

> **Примечание:** По умолчанию клиент подключается к локальному серверу (127.0.0.1).
> Для подключения к другому серверу измените переменную `SERVER_IP` в `client.py`.

## 🎯 Геймплей и управление

### Управление:

| Клавиша | Действие |
|---------|----------|
| <kbd>A</kbd> | Движение влево |
| <kbd>D</kbd> | Движение вправо |
| <kbd>Пробел</kbd> / <kbd>↑</kbd> | Прыжок |
| <kbd>ЛКМ</kbd> / <kbd>CTRL</kbd> | Стрельба |

### Цели игры:

1. 🏃‍♂️ Доберитесь до верха уровня для получения очка
2. 🎯 Стреляйте в других игроков, чтобы получить очки
3. ❤️ Следите за своим здоровьем - при падении вы теряете здоровье
4. 🏆 Первый игрок, набравший 5 очков, побеждает

## 🔧 Особенности реализации

- 📡 **Протокол передачи данных:** Протокол с заголовком фиксированной длины для определения размера сообщения, что позволяет избежать проблем с фрагментацией
- 💥 **Система коллизий:** Обнаружение столкновений для взаимодействия игроков с платформами и пулями
- 🖼️ **Процедурные спрайты:** Динамическое создание игровых ресурсов при инициализации
- ⚙️ **Настраиваемая физика:** Легко регулируемые параметры физики для различных игровых ощущений
- 🔄 **Структурированные сообщения:** Обмен данными через JSON-объекты с четкой структурой

<details>
<summary>Схема сетевого взаимодействия</summary>
<img src="https://via.placeholder.com/800x400.png?text=Схема+сетевого+взаимодействия" alt="Схема сетевого взаимодействия" width="600"/>
</details>

## 🔮 Будущие улучшения

- [ ] 🔫 Различные типы оружия
- [ ] 🔼 Система улучшений и бонусов
- [ ] 🎲 Дополнительные игровые режимы
- [ ] 🎨 Улучшенная графика и звуки
- [ ] 🏠 Поддержка нескольких игровых комнат
- [ ] 🔐 Система аутентификации и статистики
- [ ] 📱 Кроссплатформенная поддержка

---

<div align="center">
  <p>Нравится проект? Поставьте ⭐️ на GitHub!</p>
  <a href="https://github.com/Maksim0905/yandex_lms_pygame/issues">📢 Сообщить о проблеме</a> •
  <a href="https://github.com/Maksim0905/yandex_lms_pygame/fork">🍴 Fork</a> •
  <a href="https://github.com/Maksim0905/yandex_lms_pygame/pulls">🛠️ Pull Request</a>
</div>
