import pygame
import sys
import random
import datetime
import math

from pygame.constants import MOUSEBUTTONDOWN
from pygame.locals import *

# ---------- Инициализация ----------
pygame.init()
WIDTH, HEIGHT = 1100, 750
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("VitaCor – забота о сердце")
clock = pygame.time.Clock()

# Цветовая палитра (Telegram + VK style)
BG_TOP = (235, 245, 255)
BG_BOTTOM = (255, 240, 245)
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
GRAY_LIGHT = (245, 245, 245)
GRAY_MED = (200, 200, 200)
GRAY_DARK = (100, 100, 100)
PRIMARY = (0, 136, 204)        # синий Telegram
PRIMARY_HOVER = (0, 160, 230)
SECONDARY = (230, 70, 70)
SECONDARY_HOVER = (255, 100, 100)
ACCENT = (100, 180, 100)
CHAT_BUBBLE_USER = (220, 240, 255)
CHAT_BUBBLE_BOT = (240, 240, 240)
SHADOW = (0, 0, 0, 30)

# Шрифты
font_large = pygame.font.Font(None, 42)
font_default = pygame.font.Font(None, 32)
font_small = pygame.font.Font(None, 24)
font_emoji = pygame.font.Font(None, 32)  # для звёзд

# ---------- Вспомогательные функции ----------
def draw_gradient_background(surface):
    """Градиент от верхнего цвета к нижнему."""
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
        g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
        b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

def draw_shadow_rect(surface, rect, color, radius=12, shadow_alpha=30):
    """Рисует прямоугольник с тенью."""
    shadow_surf = pygame.Surface((rect.width+6, rect.height+6), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (*SHADOW[:3], shadow_alpha), shadow_surf.get_rect(), border_radius=radius+3)
    surface.blit(shadow_surf, (rect.x-3, rect.y-3))
    pygame.draw.rect(surface, color, rect, border_radius=radius)

# ---------- Кнопка с анимацией нажатия ----------
class Button:
    def __init__(self, x, y, w, h, text, color=PRIMARY, text_color=WHITE, font=font_default):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = self._lighten(color)
        self.press_color = self._darken(color)
        self.text_color = text_color
        self.font = font
        self.is_hovered = False
        self.is_pressed = False
        self.anim = 0.0  # 0..1 для плавности
        self.scale = 1.0

    def _lighten(self, color):
        return tuple(min(c+30, 255) for c in color)

    def _darken(self, color):
        return tuple(max(c-30, 0) for c in color)

    def update(self, mouse_pos, mouse_pressed):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.is_pressed = self.is_hovered and mouse_pressed[0]
        target = 1.0 if self.is_hovered else 0.0
        self.anim += (target - self.anim) * 0.2
        self.scale = 1.0 - 0.03 * self.anim if not self.is_pressed else 0.97

    def draw(self, surface):
        current_color = [
            int(self.color[i] + (self.hover_color[i] - self.color[i]) * self.anim)
            for i in range(3)
        ]
        if self.is_pressed:
            current_color = self.press_color
        # Рисуем с тенью и масштабированием
        scaled_rect = self.rect.inflate(-self.rect.w*(1-self.scale), -self.rect.h*(1-self.scale))
        scaled_rect.center = self.rect.center
        draw_shadow_rect(surface, scaled_rect, current_color, radius=12)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event, MOUSEBUTTONDOWN=None):
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            return True
        return False

# ---------- Поле ввода (исправленное: используем TEXTINPUT) ----------
class InputBox:
    def __init__(self, x, y, w, h, placeholder='', font=font_default, password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ''
        self.placeholder = placeholder
        self.font = font
        self.active = False
        self.password = password
        self.cursor_visible = True
        self.cursor_timer = 0
        self.scroll_offset = 0

    def update(self, events):
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos)
            if event.type == KEYDOWN and self.active:
                if event.key == K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == K_RETURN:
                    pass  # Enter обрабатывается отдельно
            if event.type == TEXTINPUT and self.active:
                self.text += event.text  # корректный ввод без дублирования

        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self, surface):
        bg_color = GRAY_LIGHT if self.active else WHITE
        border_color = PRIMARY if self.active else GRAY_MED
        draw_shadow_rect(surface, self.rect, bg_color, radius=8)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)

        display_text = self.text if not self.password else '*' * len(self.text)
        if not display_text:
            text_surf = self.font.render(self.placeholder, True, GRAY_DARK)
        else:
            text_surf = self.font.render(display_text, True, BLACK)

        text_rect = text_surf.get_rect(midleft=(self.rect.x+10, self.rect.centery))
        if text_rect.right > self.rect.right - 10:
            self.scroll_offset = max(0, text_rect.right - (self.rect.right - 10))
        else:
            self.scroll_offset = 0
        clip_rect = self.rect.inflate(-12, -12)
        surface.set_clip(clip_rect)
        surface.blit(text_surf, (text_rect.x - self.scroll_offset, text_rect.y))
        surface.set_clip(None)

        if self.active and self.cursor_visible:
            cursor_x = min(text_rect.right - self.scroll_offset, self.rect.right-10) + 2
            pygame.draw.line(surface, BLACK, (cursor_x, self.rect.y+8), (cursor_x, self.rect.bottom-8), 2)

# ---------- Полоса прокрутки для чата ----------
class ScrollBar:
    def __init__(self, x, y, h, total_height, view_height):
        self.rect = pygame.Rect(x, y, 8, h)
        self.total_height = total_height
        self.view_height = view_height
        self.knob_height = max(20, int(h * view_height / total_height))
        self.knob_y = y
        self.dragging = False
        self.drag_offset = 0

    def update(self, total_height, view_height, events):
        self.total_height = total_height
        self.view_height = view_height
        self.knob_height = max(20, int(self.rect.h * view_height / total_height)) if total_height > view_height else self.rect.h
        max_knob_y = self.rect.y + self.rect.h - self.knob_height
        for event in events:
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                knob_rect = pygame.Rect(self.rect.x, self.knob_y, 8, self.knob_height)
                if knob_rect.collidepoint(event.pos):
                    self.dragging = True
                    self.drag_offset = event.pos[1] - self.knob_y
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == MOUSEMOTION and self.dragging:
                self.knob_y = max(self.rect.y, min(event.pos[1] - self.drag_offset, max_knob_y))

    def get_scroll_ratio(self):
        max_knob_y = self.rect.y + self.rect.h - self.knob_height
        if max_knob_y == self.rect.y:
            return 0
        return (self.knob_y - self.rect.y) / (max_knob_y - self.rect.y)

    def set_scroll_from_ratio(self, ratio):
        max_knob_y = self.rect.y + self.rect.h - self.knob_height
        self.knob_y = self.rect.y + ratio * (max_knob_y - self.rect.y)

    def draw(self, surface):
        pygame.draw.rect(surface, GRAY_LIGHT, self.rect, border_radius=4)
        knob_rect = pygame.Rect(self.rect.x, self.knob_y, 8, self.knob_height)
        pygame.draw.rect(surface, PRIMARY, knob_rect, border_radius=4)

# ---------- Область чата с поддержкой прокрутки и бегунка ----------
class ChatArea:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.messages = []  # (text, is_user, time_str)
        self.line_height = 28
        self.padding = 15
        self.scroll_offset = 0  # пиксели прокрутки
        self.scrollbar = None   # создаётся при отрисовке

    def add_message(self, text, is_user=True):
        time_str = datetime.datetime.now().strftime("%H:%M")
        self.messages.append((text, is_user, time_str))
        self.scroll_offset = 0  # прокрутка вниз

    def handle_event(self, events):
        for event in events:
            if event.type == MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset -= event.y * 30
                self.scroll_offset = max(0, min(self.scroll_offset, self._max_scroll()))
            if self.scrollbar:
                self.scrollbar.update(self._total_height(), self.rect.height, events)
                if self.scrollbar.dragging:
                    self.scroll_offset = self.scrollbar.get_scroll_ratio() * self._max_scroll()

    def _total_height(self):
        y = self.padding
        for msg, is_user, _ in self.messages:
            lines = self._wrap_text(msg, self.rect.width - 100)
            bubble_height = len(lines) * self.line_height + 20
            y += bubble_height + 10
        return y

    def _max_scroll(self):
        return max(0, self._total_height() - self.rect.height + 20)

    def _wrap_text(self, text, max_width):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test = current_line + word + " "
            if font_small.size(test)[0] <= max_width:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
        return lines

    def draw(self, surface):
        # Фон чата
        draw_shadow_rect(surface, self.rect, WHITE, radius=12)
        surface.set_clip(self.rect)
        y = self.rect.y + self.padding - self.scroll_offset
        for msg, is_user, time_str in self.messages:
            lines = self._wrap_text(msg, self.rect.width - 100)
            # Максимальная ширина текста
            max_line_w = max((font_small.size(line)[0] for line in lines), default=0)
            bubble_w = max_line_w + 30
            bubble_h = len(lines) * self.line_height + 20
            bubble_x = self.rect.x + 15 if is_user else self.rect.right - bubble_w - 15
            bubble_rect = pygame.Rect(bubble_x, y, bubble_w, bubble_h)
            bubble_color = CHAT_BUBBLE_USER if is_user else CHAT_BUBBLE_BOT
            draw_shadow_rect(surface, bubble_rect, bubble_color, radius=16)
            # Аватар (простой круг)
            avatar_x = bubble_rect.left - 10 if is_user else bubble_rect.right + 10
            pygame.draw.circle(surface, PRIMARY if is_user else GRAY_MED, (avatar_x, bubble_rect.centery), 12)
            # Текст
            line_y = bubble_rect.y + 10
            for line in lines:
                line_surf = font_small.render(line, True, BLACK)
                surface.blit(line_surf, (bubble_rect.x+15, line_y))
                line_y += self.line_height
            # Время
            time_surf = font_small.render(time_str, True, GRAY_DARK)
            time_rect = time_surf.get_rect(bottomright=(bubble_rect.right-5, bubble_rect.bottom-5))
            surface.blit(time_surf, time_rect)
            y += bubble_h + 10
        surface.set_clip(None)

        # Полоса прокрутки
        total_h = self._total_height()
        if total_h > self.rect.height:
            if not self.scrollbar:
                self.scrollbar = ScrollBar(self.rect.right+5, self.rect.y, self.rect.height, total_h, self.rect.height)
            else:
                self.scrollbar.update(total_h, self.rect.height, [])
                ratio = self.scroll_offset / self._max_scroll() if self._max_scroll() > 0 else 0
                self.scrollbar.set_scroll_from_ratio(ratio)
            self.scrollbar.draw(surface)
        else:
            self.scrollbar = None

# ---------- Основное приложение ----------
class VitaCorApp:
    def __init__(self):
        self.state = 'register'
        self.user = {'phone': '', 'diet': '', 'allergies': '', 'code': '123456'}
        self.chefs = self.generate_chefs(50)
        self.recipes = self.generate_recipes()
        self.current_chef = None
        self.bot_chat = None
        self.chef_chat = None
        self.buttons = []
        self.inputs = []
        self.animation_offset = 0
        self.mouse_pressed = (False, False, False)

    def generate_chefs(self, count):
        names = ["Анна", "Иван", "Елена", "Дмитрий", "Ольга", "Сергей", "Мария", "Алексей", "Наталья", "Павел",
                 "Юлия", "Максим", "Татьяна", "Андрей", "Екатерина", "Владимир", "Ирина", "Роман", "Светлана", "Артём"]
        surnames = ["Смирнов(а)", "Иванов(а)", "Петров(а)", "Сидоров(а)", "Кузнецов(а)", "Попов(а)", "Васильев(а)", "Михайлов(а)"]
        descs = ["Специалист по низкосолевой кухне", "Диетолог с 10-летним стажем", "Эксперт пост-инфарктного питания",
                 "Шеф-повар здоровой кухни", "Нутрициолог и повар", "Автор книги о сердечном питании"]
        chefs = []
        for i in range(count):
            name = f"{random.choice(names)} {random.choice(surnames)}"
            desc = random.choice(descs)
            rating = round(random.uniform(4.0, 5.0), 1)
            price1 = random.randint(1800, 3500)
            price2 = int(price1 * 1.8)
            chefs.append({
                'id': i,
                'name': name,
                'desc': desc,
                'rating': rating,
                'price1': price1,
                'price2': price2
            })
        return chefs

    def generate_recipes(self):
        return [
            {'title': 'Овсяная каша с яблоком и корицей',
             'ingr': 'Овсяные хлопья (50 г), вода (200 мл), яблоко (1 шт.), корица (щепотка), мёд (1 ч.л. опционально)',
             'instr': '1. Вскипятите воду. 2. Добавьте хлопья, варите 5-7 мин. 3. Натрите яблоко, добавьте в кашу. 4. Посыпьте корицей, дайте настояться 2 мин.',
             'diet': 'низкосолевая'},
            {'title': 'Суп-пюре из тыквы с имбирём',
             'ingr': 'Тыква (300 г), морковь (1 шт.), лук (1/2 шт.), имбирь (1 см), оливковое масло (1 ст.л.), вода (500 мл)',
             'instr': '1. Лук и имбирь обжарьте на масле 2 мин. 2. Добавьте нарезанные тыкву и морковь, тушите 5 мин. 3. Залейте водой, варите 20 мин. 4. Измельчите блендером.',
             'diet': 'низкосолевая'},
            {'title': 'Куриная грудка на пару с брокколи',
             'ingr': 'Куриное филе (150 г), брокколи (100 г), лимонный сок (1 ч.л.), чёрный перец',
             'instr': '1. Филе отбейте, сбрызните лимонным соком. 2. Готовьте в пароварке 20 мин. 3. Брокколи отварите отдельно 5-7 мин. 4. Подавайте вместе.',
             'diet': 'постинфарктная'},
            {'title': 'Запечённая треска с овощами',
             'ingr': 'Филе трески (200 г), кабачок (1/2 шт.), помидоры черри (5 шт.), оливковое масло, укроп',
             'instr': '1. Нарежьте кабачок кружками, выложите в форму. 2. Сверху положите рыбу, помидоры. 3. Сбрызните маслом, запекайте 25 мин при 180°C. 4. Посыпьте укропом.',
             'diet': 'постинфарктная'},
        ]

    def set_state(self, new_state):
        self.state = new_state
        self.buttons.clear()
        self.inputs.clear()
        if new_state == 'bot' and not self.bot_chat:
            self.bot_chat = ChatArea(50, 160, WIDTH-100, 400)
            self.show_daily_recipe()
        elif new_state == 'chef_chat' and self.current_chef:
            self.chef_chat = ChatArea(50, 160, WIDTH-100, 400)
            welcome = f"Вы соединились с поваром {self.current_chef['name']}. Расскажите о вашей диете и аллергиях."
            self.chef_chat.add_message(welcome, is_user=False)

    def show_daily_recipe(self):
        suitable = [r for r in self.recipes if self.user.get('diet') and r['diet'] == self.user['diet']] or self.recipes
        recipe = random.choice(suitable)
        msg = f"🍽 **{recipe['title']}**\n\n🛒 Ингредиенты:\n{recipe['ingr']}\n\n👩‍🍳 Приготовление:\n{recipe['instr']}"
        self.bot_chat.add_message(msg, is_user=False)

    def handle_events(self):
        events = pygame.event.get()
        mouse_pos = pygame.mouse.get_pos()
        self.mouse_pressed = pygame.mouse.get_pressed()
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                for btn in self.buttons:
                    if btn.handle_event(event):
                        self.on_button_click(btn.text)
            if self.state in ['bot', 'chef_chat']:
                chat = self.bot_chat if self.state == 'bot' else self.chef_chat
                if chat:
                    chat.handle_event(events)
        # Обновление полей ввода (передаём все события)
        for inp in self.inputs:
            inp.update(events)
        # Анимация кнопок
        for btn in self.buttons:
            btn.update(mouse_pos, self.mouse_pressed)
        return events

    def on_button_click(self, text):
        if self.state == 'register':
            if text == 'Получить код':
                phone = self.inputs[0].text.strip()
                if phone:
                    self.user['phone'] = phone
                    print(f"[SMS] Код 123456 отправлен на {phone}")
                    self.set_state('verify')
        elif self.state == 'verify':
            if text == 'Подтвердить':
                if self.inputs[0].text == self.user['code']:
                    self.set_state('main')
        elif self.state == 'main':
            if text == 'Диета и бот Vita':
                self.set_state('diet')
            elif text == 'Шеф-повара':
                self.set_state('chefs')
            elif text == 'Выход':
                self.set_state('register')
        elif self.state == 'diet':
            if text == 'Сохранить':
                self.user['diet'] = self.inputs[0].text
                self.user['allergies'] = self.inputs[1].text
                self.set_state('bot')
            elif text == 'Назад':
                self.set_state('main')
        elif self.state == 'bot':
            if text == 'Заменить рецепт':
                self.show_daily_recipe()
            elif text == 'Назад':
                self.set_state('main')
        elif self.state == 'chefs':
            if text.startswith('chef_'):
                idx = int(text.split('_')[1])
                self.current_chef = self.chefs[idx]
                self.set_state('chef_chat')
            elif text == 'Назад':
                self.set_state('main')
        elif self.state == 'chef_chat':
            if text == 'Отправить' and self.inputs:
                msg = self.inputs[0].text
                if msg:
                    self.chef_chat.add_message(msg, is_user=True)
                    self.inputs[0].text = ''
                    response = f"Повар {self.current_chef['name']}: Спасибо за заказ! Цена: {self.current_chef['price1']}₽/день. Оплата по ссылке (демо)."
                    self.chef_chat.add_message(response, is_user=False)
            elif text == 'Назад':
                self.set_state('chefs')

    def draw(self):
        draw_gradient_background(screen)
        # Декоративные круги
        for i in range(5):
            radius = 80 + i*30
            alpha = 20 - i*3
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255,255,255, alpha), (radius, radius), radius)
            screen.blit(surf, (WIDTH//2 + i*50 - 200, HEIGHT//2 + i*30 - 100))

        title = font_large.render("VitaCor", True, PRIMARY)
        screen.blit(title, (40, 30))

        if self.state == 'register':
            self.draw_register()
        elif self.state == 'verify':
            self.draw_verify()
        elif self.state == 'main':
            self.draw_main()
        elif self.state == 'diet':
            self.draw_diet()
        elif self.state == 'bot':
            self.draw_bot()
        elif self.state == 'chefs':
            self.draw_chefs()
        elif self.state == 'chef_chat':
            self.draw_chef_chat()

        for btn in self.buttons:
            btn.draw(screen)
        for inp in self.inputs:
            inp.draw(screen)

        pygame.display.flip()

    def draw_register(self):
        if not self.inputs:
            self.inputs.append(InputBox(WIDTH//2-150, 250, 300, 50, "+7 999 123 45 67"))
            self.buttons.append(Button(WIDTH//2-100, 340, 200, 55, "Получить код"))
        text = font_default.render("Введите номер телефона", True, BLACK)
        screen.blit(text, (WIDTH//2-120, 200))
        hint = font_small.render("Тестовый: +79991234567 / 123456", True, GRAY_DARK)
        screen.blit(hint, (WIDTH//2-130, 420))

    def draw_verify(self):
        if not self.inputs:
            self.inputs.append(InputBox(WIDTH//2-60, 250, 120, 50, "Код"))
            self.buttons.append(Button(WIDTH//2-100, 340, 200, 55, "Подтвердить"))
        text = font_default.render("Введите код из SMS", True, BLACK)
        screen.blit(text, (WIDTH//2-120, 200))

    def draw_main(self):
        if not self.buttons:
            btns = [
                ("Диета и бот Vita", WIDTH//2-150, 200),
                ("Шеф-повара", WIDTH//2-150, 280),
                ("Выход", WIDTH//2-150, 360)
            ]
            for txt, x, y in btns:
                col = SECONDARY if "Выход" in txt else PRIMARY
                self.buttons.append(Button(x, y, 300, 60, txt, color=col))
        text = font_large.render("Главное меню", True, BLACK)
        screen.blit(text, (WIDTH//2-120, 100))

    def draw_diet(self):
        if not self.inputs:
            self.inputs.append(InputBox(WIDTH//2-200, 220, 400, 50, "Тип диеты (например, низкосолевая)"))
            self.inputs.append(InputBox(WIDTH//2-200, 290, 400, 50, "Аллергии / что нельзя"))
            self.buttons.extend([
                Button(WIDTH//2-200, 370, 190, 55, "Сохранить"),
                Button(WIDTH//2+10, 370, 190, 55, "Назад", color=SECONDARY)
            ])
        text = font_large.render("Настройка диеты", True, BLACK)
        screen.blit(text, (WIDTH//2-120, 120))

    def draw_bot(self):
        text = font_large.render("Чат с ботом Vita", True, BLACK)
        screen.blit(text, (WIDTH//2-120, 100))
        self.bot_chat.draw(screen)
        if not self.buttons:
            self.buttons.append(Button(50, HEIGHT-80, 200, 50, "Заменить рецепт"))
            self.buttons.append(Button(WIDTH-250, HEIGHT-80, 200, 50, "Назад", color=SECONDARY))

    def draw_chefs(self):
        text = font_large.render("Наши шеф-повара", True, BLACK)
        screen.blit(text, (WIDTH//2-120, 100))
        self.animation_offset = min(1.0, self.animation_offset + 0.05)
        y_start = 160
        visible_count = min(len(self.chefs), 5)
        self.buttons = []  # очищаем старые кнопки поваров
        for i, chef in enumerate(self.chefs[:visible_count]):
            offset_x = (1 - self.animation_offset) * 50 * (i % 2 * 2 - 1)
            card_rect = pygame.Rect(WIDTH//2-350 + offset_x, y_start + i*110, 700, 90)
            draw_shadow_rect(screen, card_rect, WHITE, radius=16)
            name_surf = font_default.render(chef['name'], True, BLACK)
            desc_surf = font_small.render(chef['desc'], True, GRAY_DARK)
            rating_surf = font_emoji.render(f"★ {chef['rating']}", True, PRIMARY)
            screen.blit(name_surf, (card_rect.x+20, card_rect.y+15))
            screen.blit(desc_surf, (card_rect.x+20, card_rect.y+45))
            screen.blit(rating_surf, (card_rect.right-120, card_rect.y+20))
            btn = Button(card_rect.right-140, card_rect.y+50, 120, 35, "Выбрать")
            btn.text = f"chef_{chef['id']}"
            self.buttons.append(btn)
        self.buttons.append(Button(50, HEIGHT-80, 150, 50, "Назад", color=SECONDARY))

    def draw_chef_chat(self):
        chef = self.current_chef
        text = font_large.render(f"Чат с {chef['name']}", True, BLACK)
        screen.blit(text, (WIDTH//2-120, 100))
        self.chef_chat.draw(screen)
        if not self.inputs:
            self.inputs.append(InputBox(50, HEIGHT-80, WIDTH-300, 50, "Сообщение..."))
            self.buttons.extend([
                Button(WIDTH-230, HEIGHT-80, 180, 50, "Отправить"),
                Button(WIDTH-230, HEIGHT-150, 180, 50, "Назад", color=SECONDARY)
            ])

    def run(self):
        while True:
            self.handle_events()
            self.draw()
            clock.tick(FPS)

if __name__ == "__main__":
    app = VitaCorApp()
    app.run()