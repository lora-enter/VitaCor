# -*- coding: utf-8 -*-
import pygame
import sys
import random
import datetime
import math
from pygame.locals import (
    QUIT, VIDEORESIZE, RESIZABLE,
    MOUSEBUTTONDOWN, MOUSEWHEEL,
    KEYDOWN, KEYUP, K_BACKSPACE,
    TEXTINPUT
)

# ---------- Инициализация ----------
pygame.init()
WIDTH, HEIGHT = 1100, 750
MIN_WIDTH, MIN_HEIGHT = 800, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT), RESIZABLE)
pygame.display.set_caption("VitaCor – забота о сердце")
clock = pygame.time.Clock()

# ---------- Больничная цветовая палитра (красный + белый) ----------
BG_TOP = (255, 240, 240)       # светло-красный
BG_BOTTOM = (255, 220, 220)    # ещё более светлый красный
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
GRAY_LIGHT = (245, 245, 245)
GRAY_MED = (220, 220, 220)
GRAY_DARK = (100, 100, 100)
PRIMARY = (200, 50, 50)        # медицинский красный
PRIMARY_HOVER = (220, 80, 80)
SECONDARY = (180, 180, 180)    # серый для второстепенных кнопок
SECONDARY_HOVER = (200, 200, 200)
ACCENT = (150, 30, 30)         # тёмно-красный для акцентов
CHAT_BUBBLE_USER = (255, 230, 230)  # пузырёк пользователя – светло-красный
CHAT_BUBBLE_BOT = (255, 255, 255)   # пузырёк бота – белый
SHADOW = (0, 0, 0, 30)

# Шрифты
font_large = None
font_default = None
font_small = None

def init_fonts():
    global font_large, font_default, font_small
    scale = min(screen.get_width() / WIDTH, screen.get_height() / HEIGHT)
    font_large = pygame.font.Font(None, int(42 * scale))
    font_default = pygame.font.Font(None, int(32 * scale))
    font_small = pygame.font.Font(None, int(24 * scale))

def scale_factor():
    return min(screen.get_width() / WIDTH, screen.get_height() / HEIGHT)

# ---------- Функции рисования ----------
def draw_gradient_background(surface):
    w, h = surface.get_size()
    for y in range(h):
        ratio = y / h
        r = int(BG_TOP[0] * (1 - ratio) + BG_BOTTOM[0] * ratio)
        g = int(BG_TOP[1] * (1 - ratio) + BG_BOTTOM[1] * ratio)
        b = int(BG_TOP[2] * (1 - ratio) + BG_BOTTOM[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

def draw_shadow_rect(surface, rect, color, radius=12, shadow_alpha=30):
    shadow_surf = pygame.Surface((rect.width+6, rect.height+6), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surf, (*SHADOW[:3], shadow_alpha),
                     shadow_surf.get_rect(), border_radius=radius+3)
    surface.blit(shadow_surf, (rect.x-3, rect.y-3))
    pygame.draw.rect(surface, color, rect, border_radius=radius)

# ---------- Декоративные элементы (пульсирующие кресты вместо кругов) ----------
class FloatingCross:
    """Медицинский крест, плавающий на фоне."""
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.base_y = y
        self.size = size
        self.speed = speed
        self.phase = random.uniform(0, 2*math.pi)

    def update(self):
        self.phase += 0.02
        self.y = self.base_y + math.sin(self.phase) * 15

    def draw(self, surface):
        alpha = int(15 + 10 * math.sin(self.phase))
        color = (200, 50, 50, alpha)  # красный с прозрачностью
        # Рисуем крест: вертикальная и горизонтальная линии
        thickness = max(4, self.size // 5)
        rect_v = pygame.Rect(self.x - thickness//2, self.y - self.size//2,
                             thickness, self.size)
        rect_h = pygame.Rect(self.x - self.size//2, self.y - thickness//2,
                             self.size, thickness)
        # Используем временную поверхность для прозрачности
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(surf, color, (self.size//2 - thickness//2, 0,
                                       thickness, self.size))
        pygame.draw.rect(surf, color, (0, self.size//2 - thickness//2,
                                       self.size, thickness))
        surface.blit(surf, (self.x - self.size//2, self.y - self.size//2))

# ---------- Кнопка ----------
class Button:
    def __init__(self, x, y, w, h, text, color=PRIMARY, text_color=WHITE, font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = tuple(min(c+30, 255) for c in color)
        self.press_color = tuple(max(c-30, 0) for c in color)
        self.text_color = text_color
        self.font = font or font_default
        self.is_hovered = False
        self.is_pressed = False
        self.anim = 0.0
        self.scale = 1.0

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
        scaled_rect = self.rect.inflate(-self.rect.w*(1-self.scale),
                                        -self.rect.h*(1-self.scale))
        scaled_rect.center = self.rect.center
        draw_shadow_rect(surface, scaled_rect, current_color, radius=12)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=scaled_rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            return True
        return False

# ---------- Поле ввода ----------
class InputBox:
    def __init__(self, x, y, w, h, placeholder='', font=None, password=False, read_only=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ''
        self.placeholder = placeholder
        self.font = font or font_default
        self.active = False
        self.password = password
        self.read_only = read_only
        self.cursor_visible = True
        self.cursor_timer = 0
        self.scroll_offset = 0
        self.backspace_pressed = False
        self.backspace_timer = 0
        self.backspace_initial_delay = 30
        self.backspace_repeat_rate = 3

    def update(self, events):
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos) and not self.read_only
            if event.type == KEYDOWN and self.active:
                if event.key == K_BACKSPACE:
                    self.text = self.text[:-1]
                    self.backspace_pressed = True
                    self.backspace_timer = 0
            if event.type == KEYUP:
                if event.key == K_BACKSPACE:
                    self.backspace_pressed = False
            if event.type == TEXTINPUT and self.active and not self.read_only:
                self.text += event.text

        if self.backspace_pressed and self.active:
            self.backspace_timer += 1
            if self.backspace_timer >= self.backspace_initial_delay:
                if (self.backspace_timer - self.backspace_initial_delay) % self.backspace_repeat_rate == 0:
                    self.text = self.text[:-1]

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
            pygame.draw.line(surface, BLACK, (cursor_x, self.rect.y+8),
                             (cursor_x, self.rect.bottom-8), 2)

# ---------- Список поваров ----------
class ChefList:
    def __init__(self, x, y, w, h, chefs, on_detail_callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.chefs = chefs
        self.on_detail = on_detail_callback
        self.item_height = int(100 * scale_factor())
        self.spacing = int(15 * scale_factor())
        self.scroll_offset = 0
        self.buttons = []
        self._update_buttons()

    def _update_buttons(self):
        self.buttons.clear()
        y = self.rect.y + 10 - self.scroll_offset
        for chef in self.chefs:
            item_rect = pygame.Rect(self.rect.x+10, y, self.rect.width-20, self.item_height)
            if item_rect.bottom >= self.rect.top and item_rect.top <= self.rect.bottom:
                detail_btn = pygame.Rect(item_rect.right - 150,
                                         item_rect.y + self.item_height - 40, 130, 30)
                self.buttons.append((item_rect, chef, detail_btn))
            y += self.item_height + self.spacing

    def total_height(self):
        return len(self.chefs) * (self.item_height + self.spacing)

    def handle_event(self, events):
        for event in events:
            if event.type == MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset -= event.y * 40
                max_scroll = max(0, self.total_height() - self.rect.height + 20)
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
                self._update_buttons()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                for item_rect, chef, detail_btn in self.buttons:
                    if detail_btn.collidepoint(event.pos):
                        self.on_detail(chef)
                        return

    def draw(self, surface):
        draw_shadow_rect(surface, self.rect, WHITE, radius=12)
        surface.set_clip(self.rect)
        for item_rect, chef, detail_btn in self.buttons:
            draw_shadow_rect(surface, item_rect, WHITE, radius=12)
            name_surf = font_default.render(chef['name'], True, BLACK)
            surface.blit(name_surf, (item_rect.x+15, item_rect.y+15))
            desc_surf = font_small.render(chef['desc'], True, GRAY_DARK)
            surface.blit(desc_surf, (item_rect.x+15, item_rect.y+45))
            rating_surf = font_default.render(f"★ {chef['rating']}", True, PRIMARY)
            surface.blit(rating_surf, (item_rect.right-120, item_rect.y+20))
            pygame.draw.rect(surface, PRIMARY, detail_btn, border_radius=8)
            detail_text = font_small.render("Подробнее", True, WHITE)
            detail_rect = detail_text.get_rect(center=detail_btn.center)
            surface.blit(detail_text, detail_rect)
        surface.set_clip(None)

        total_h = self.total_height()
        if total_h > self.rect.height:
            bar_x = self.rect.right + 5
            bar_h = self.rect.height
            knob_h = max(20, bar_h * self.rect.height / total_h)
            max_knob_y = self.rect.y + bar_h - knob_h
            ratio = self.scroll_offset / (total_h - self.rect.height) if total_h > self.rect.height else 0
            knob_y = self.rect.y + ratio * (bar_h - knob_h)
            pygame.draw.rect(surface, GRAY_LIGHT, (bar_x, self.rect.y, 8, bar_h), border_radius=4)
            pygame.draw.rect(surface, PRIMARY, (bar_x, knob_y, 8, knob_h), border_radius=4)

# ---------- Чат ----------
class ChatArea:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.messages = []
        self.line_height = int(28 * scale_factor())
        self.padding = int(15 * scale_factor())
        self.scroll_offset = 0

    def add_message(self, text, is_user=True):
        time_str = datetime.datetime.now().strftime("%H:%M")
        self.messages.append((text, is_user, time_str))
        self.scroll_offset = 0

    def scroll_to_bottom(self):
        self.scroll_offset = 0

    def handle_event(self, events):
        for event in events:
            if event.type == MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset -= event.y * 30
                max_scroll = max(0, self._total_height() - self.rect.height + 20)
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def _total_height(self):
        y = self.padding
        for msg, is_user, _ in self.messages:
            lines = self._wrap_text(msg, self.rect.width - 100)
            bubble_height = len(lines) * self.line_height + 20
            y += bubble_height + 10
        return y

    def _wrap_text(self, text, max_width):
        words = text.split(' ')
        lines = []
        current = ""
        for word in words:
            test = current + word + " "
            if font_small.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current.strip())
                current = word + " "
        if current:
            lines.append(current.strip())
        return lines

    def draw(self, surface):
        draw_shadow_rect(surface, self.rect, WHITE, radius=12)
        surface.set_clip(self.rect)
        y = self.rect.y + self.padding - self.scroll_offset
        for msg, is_user, time_str in self.messages:
            lines = self._wrap_text(msg, self.rect.width - 100)
            max_line_w = max((font_small.size(line)[0] for line in lines), default=0)
            bubble_w = max_line_w + 30
            bubble_h = len(lines) * self.line_height + 20
            bubble_x = self.rect.x + 15 if is_user else self.rect.right - bubble_w - 15
            bubble_rect = pygame.Rect(bubble_x, y, bubble_w, bubble_h)
            bubble_color = CHAT_BUBBLE_USER if is_user else CHAT_BUBBLE_BOT
            draw_shadow_rect(surface, bubble_rect, bubble_color, radius=16)
            avatar_x = bubble_rect.left - 10 if is_user else bubble_rect.right + 10
            pygame.draw.circle(surface, PRIMARY if is_user else GRAY_MED,
                               (avatar_x, bubble_rect.centery), 12)
            line_y = bubble_rect.y + 10
            for line in lines:
                line_surf = font_small.render(line, True, BLACK)
                surface.blit(line_surf, (bubble_rect.x+15, line_y))
                line_y += self.line_height
            time_surf = font_small.render(time_str, True, GRAY_DARK)
            time_rect = time_surf.get_rect(bottomright=(bubble_rect.right-5, bubble_rect.bottom-5))
            surface.blit(time_surf, time_rect)
            y += bubble_h + 10
        surface.set_clip(None)

# ---------- Основное приложение ----------
class VitaCorApp:
    def __init__(self):
        init_fonts()
        self.state = 'register'
        self.user = {
            'phone': '',
            'code': '123456',
            'first_name': '',
            'last_name': '',
            'diet': '',
            'allergies': ''
        }
        self.chefs = self.generate_chefs(50)
        self.recipes = self.generate_recipes(100)
        self.current_chef = None
        self.bot_chat = None
        self.chef_chat = None
        self.chef_list = None
        self.buttons = []
        self.inputs = []
        self.mouse_pressed = (False, False, False)
        self.loading = False
        self.loading_timer = 0
        self.order_placed = False
        self.last_recipe_time = 0
        self.health_tip_sent_today = False
        self.health_tips = [
            "Следите за давлением, избегайте стрессов.",
            "Употребляйте больше овощей и фруктов.",
            "Ежедневная лёгкая прогулка улучшает работу сердца.",
            "Ограничьте потребление соли до 5 г в день.",
            "Пейте достаточно воды, но не переусердствуйте."
        ]
        self.sent_recipes_today = set()
        self.last_recipe_date = None
        self.settings_open = False
        # Декоративные кресты
        self.decorations = []
        for i in range(6):
            x = random.randint(50, screen.get_width()-50)
            y = random.randint(50, screen.get_height()-50)
            size = random.randint(30, 60)
            speed = random.uniform(0.5, 2.0)
            self.decorations.append(FloatingCross(x, y, size, speed))

    def generate_chefs(self, count):
        names = ["Анна", "Иван", "Елена", "Дмитрий", "Ольга", "Сергей", "Мария", "Алексей", "Наталья", "Павел",
                 "Юлия", "Максим", "Татьяна", "Андрей", "Екатерина", "Владимир", "Ирина", "Роман", "Светлана", "Артём"]
        surnames = ["Смирнов", "Иванов", "Петров", "Сидоров", "Кузнецов", "Попов", "Васильев", "Михайлов"]
        descs = ["Кардиолог-диетолог", "Специалист по лечебному питанию", "Эксперт пост-инфарктной диеты",
                 "Шеф-повар кардио-кухни", "Нутрициолог", "Автор методики сердечного питания"]
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
                'price2': price2,
                'bio': f"Опыт более 8 лет. {desc}. Индивидуальный подход."
            })
        return chefs

    def generate_recipes(self, count):
        base_recipes = [
            {'title': 'Овсяная каша с яблоком',
             'ingr': 'Овсяные хлопья (50 г), вода (200 мл), яблоко (1 шт.), корица',
             'instr': '1. Вскипятите воду. 2. Добавьте хлопья, варите 5-7 мин. 3. Натрите яблоко, добавьте в кашу. 4. Посыпьте корицей.',
             'diet': 'низкосолевая'},
            {'title': 'Тыквенный суп-пюре',
             'ingr': 'Тыква (300 г), морковь (1 шт.), лук (1/2 шт.), имбирь, оливковое масло, вода (500 мл)',
             'instr': '1. Обжарьте лук и имбирь. 2. Добавьте тыкву и морковь, тушите 5 мин. 3. Залейте водой, варите 20 мин. 4. Измельчите блендером.',
             'diet': 'низкосолевая'},
            {'title': 'Куриная грудка с брокколи',
             'ingr': 'Куриное филе (150 г), брокколи (100 г), лимонный сок, перец',
             'instr': '1. Филе отбейте, сбрызните лимонным соком. 2. Готовьте на пару 20 мин. 3. Брокколи отварите 5-7 мин. 4. Подавайте вместе.',
             'diet': 'постинфарктная'},
            {'title': 'Запечённая треска',
             'ingr': 'Филе трески (200 г), кабачок (1/2 шт.), помидоры черри, оливковое масло, укроп',
             'instr': '1. Нарежьте кабачок, выложите в форму. 2. Сверху положите рыбу и помидоры. 3. Запекайте 25 мин при 180°C. 4. Посыпьте укропом.',
             'diet': 'постинфарктная'},
        ]
        recipes = []
        for i in range(count):
            base = random.choice(base_recipes).copy()
            base['title'] = f"{base['title']} (вариант {i+1})"
            base['ingr'] += f", секретный ингредиент №{i}"
            base['diet'] = random.choice(['низкосолевая', 'постинфарктная'])
            recipes.append(base)
        return recipes

    def set_state(self, new_state):
        self.state = new_state
        self.buttons.clear()
        self.inputs.clear()
        self.chef_list = None
        self.loading = False
        self.order_placed = False
        self.settings_open = False
        if new_state == 'bot' and not self.bot_chat:
            self.bot_chat = ChatArea(50, 160, screen.get_width()-100, 400)
            self.show_daily_recipe()
        elif new_state == 'chef_chat' and self.current_chef:
            self.chef_chat = ChatArea(50, 160, screen.get_width()-100, 400)
            welcome = f"Вы соединились с поваром {self.current_chef['name']}. Расскажите о вашей диете и аллергиях."
            self.chef_chat.add_message(welcome, is_user=False)
        elif new_state == 'chefs':
            self.chef_list = ChefList(50, 160, screen.get_width()-100, 450,
                                      self.chefs, self.on_chef_detail)

    def on_chef_detail(self, chef):
        self.current_chef = chef
        self.set_state('chef_detail')

    def show_daily_recipe(self):
        today = datetime.date.today()
        if self.last_recipe_date != today:
            self.sent_recipes_today.clear()
            self.last_recipe_date = today
        suitable = [r for r in self.recipes if self.user.get('diet') and r['diet'] == self.user['diet']] or self.recipes
        available = [r for r in suitable if r['title'] not in self.sent_recipes_today]
        if not available:
            available = suitable
        recipe = random.choice(available)
        self.sent_recipes_today.add(recipe['title'])
        msg = f"**{recipe['title']}**\n\nИнгредиенты:\n{recipe['ingr']}\n\nПриготовление:\n{recipe['instr']}"
        self.bot_chat.add_message(msg, is_user=False)
        self.bot_chat.scroll_to_bottom()
        self.last_recipe_time = pygame.time.get_ticks()
        self.health_tip_sent_today = False

    def check_health_tip(self):
        if self.state == 'bot' and not self.health_tip_sent_today:
            now = pygame.time.get_ticks()
            if now - self.last_recipe_time > 15 * 60 * 1000:
                tip = random.choice(self.health_tips)
                self.bot_chat.add_message(f"💡 Совет дня: {tip}", is_user=False)
                self.health_tip_sent_today = True

    def handle_events(self):
        global screen
        events = pygame.event.get()
        mouse_pos = pygame.mouse.get_pos()
        self.mouse_pressed = pygame.mouse.get_pressed()
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), RESIZABLE)
                init_fonts()
                self.relayout()
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                # Кнопка настроек (крест)
                if not self.settings_open and pygame.Rect(screen.get_width()-60, 20, 40, 40).collidepoint(event.pos):
                    self.settings_open = True
                    self.inputs.clear()
                    self.buttons.clear()
                    return
                if self.settings_open:
                    settings_rect = pygame.Rect(screen.get_width()//2-150,
                                                screen.get_height()//2-125, 300, 250)
                    if not settings_rect.collidepoint(event.pos):
                        self.settings_open = False
                        self.set_state(self.state)
                for btn in self.buttons:
                    if btn.handle_event(event):
                        self.on_button_click(btn.text)
            if self.state in ['bot', 'chef_chat']:
                chat = self.bot_chat if self.state == 'bot' else self.chef_chat
                if chat:
                    chat.handle_event(events)
            if self.chef_list:
                self.chef_list.handle_event(events)

        if not self.settings_open:
            for inp in self.inputs:
                inp.update(events)
        else:
            for inp in self.inputs:
                if not inp.read_only:
                    inp.update(events)

        for btn in self.buttons:
            btn.update(mouse_pos, self.mouse_pressed)

        self.check_health_tip()

        if self.loading:
            self.loading_timer += 1
            if self.loading_timer > 60:
                self.loading = False
                self.order_placed = True

        for dec in self.decorations:
            dec.update()
        return events

    def relayout(self):
        if self.state == 'chefs' and self.chef_list:
            self.chef_list.rect.width = screen.get_width() - 100
            self.chef_list._update_buttons()
        elif self.state == 'bot' and self.bot_chat:
            self.bot_chat.rect.width = screen.get_width() - 100
        elif self.state == 'chef_chat' and self.chef_chat:
            self.chef_chat.rect.width = screen.get_width() - 100
        self.decorations.clear()
        for i in range(6):
            x = random.randint(50, screen.get_width()-50)
            y = random.randint(50, screen.get_height()-50)
            size = random.randint(30, 60)
            speed = random.uniform(0.5, 2.0)
            self.decorations.append(FloatingCross(x, y, size, speed))

    def on_button_click(self, text):
        if self.settings_open:
            if text == 'Сохранить':
                if len(self.inputs) >= 3:
                    self.user['first_name'] = self.inputs[0].text
                    self.user['last_name'] = self.inputs[1].text
                self.settings_open = False
                self.set_state(self.state)
            return

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
            if text == 'Новый рецепт':
                self.show_daily_recipe()
            elif text == 'Назад':
                self.set_state('main')
        elif self.state == 'chefs':
            if text == 'Назад':
                self.set_state('main')
        elif self.state == 'chef_detail':
            if text == 'Заказать':
                self.loading = True
                self.loading_timer = 0
            elif text == 'Назад':
                self.set_state('chefs')
        elif self.state == 'chef_chat':
            if text == 'Отправить' and self.inputs:
                msg = self.inputs[0].text
                if msg:
                    self.chef_chat.add_message(msg, is_user=True)
                    self.inputs[0].text = ''
                    response = f"Повар {self.current_chef['name']}: Спасибо за заказ! Цена: {self.current_chef['price1']} руб./день. Оплата по ссылке (демо)."
                    self.chef_chat.add_message(response, is_user=False)
            elif text == 'Назад':
                self.set_state('chefs')
        elif self.state == 'order_success':
            if text == 'OK':
                self.order_placed = False
                self.set_state('chefs')

    def draw(self):
        draw_gradient_background(screen)
        for dec in self.decorations:
            dec.draw(screen)

        title = font_large.render("VitaCor", True, PRIMARY)
        screen.blit(title, (40, 30))
        # Кнопка настроек (красный крест)
        gear_rect = pygame.Rect(screen.get_width()-60, 20, 40, 40)
        pygame.draw.circle(screen, GRAY_LIGHT, gear_rect.center, 20)
        # Рисуем маленький крестик
        cross_color = PRIMARY
        pygame.draw.rect(screen, cross_color, (gear_rect.x+18, gear_rect.y+10, 4, 20))
        pygame.draw.rect(screen, cross_color, (gear_rect.x+10, gear_rect.y+18, 20, 4))

        if not self.settings_open:
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
            elif self.state == 'chef_detail':
                self.draw_chef_detail()
            elif self.state == 'chef_chat':
                self.draw_chef_chat()
        else:
            self.draw_settings()

        for btn in self.buttons:
            btn.draw(screen)
        for inp in self.inputs:
            inp.draw(screen)

        if self.loading:
            self.draw_loading()
        elif self.order_placed:
            self.draw_order_success()

        pygame.display.flip()

    def draw_settings(self):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0,0,0, 128))
        screen.blit(overlay, (0,0))
        rect = pygame.Rect(screen.get_width()//2-150, screen.get_height()//2-125, 300, 250)
        draw_shadow_rect(screen, rect, WHITE, radius=16)
        title = font_default.render("Настройки профиля", True, BLACK)
        screen.blit(title, (rect.x+60, rect.y+20))
        if not self.inputs:
            self.inputs.append(InputBox(rect.x+30, rect.y+60, 240, 35, "Имя", font_small))
            self.inputs.append(InputBox(rect.x+30, rect.y+105, 240, 35, "Фамилия", font_small))
            self.inputs.append(InputBox(rect.x+30, rect.y+150, 240, 35, "Телефон", font_small, read_only=True))
            self.inputs[0].text = self.user.get('first_name', '')
            self.inputs[1].text = self.user.get('last_name', '')
            self.inputs[2].text = self.user.get('phone', '')
            self.buttons.append(Button(rect.x+75, rect.y+195, 150, 40, "Сохранить", font=font_small))
        for inp in self.inputs:
            inp.draw(screen)

    def draw_register(self):
        if not self.inputs:
            self.inputs.append(InputBox(screen.get_width()//2-150, 250, 300, 50, "+7 999 123 45 67"))
            self.buttons.append(Button(screen.get_width()//2-100, 340, 200, 55, "Получить код"))
        text = font_default.render("Введите номер телефона", True, BLACK)
        screen.blit(text, (screen.get_width()//2-120, 200))
        hint = font_small.render("Тестовый: +79991234567 / 123456", True, GRAY_DARK)
        screen.blit(hint, (screen.get_width()//2-130, 420))

    def draw_verify(self):
        if not self.inputs:
            self.inputs.append(InputBox(screen.get_width()//2-60, 250, 120, 50, "Код"))
            self.buttons.append(Button(screen.get_width()//2-100, 340, 200, 55, "Подтвердить"))
        text = font_default.render("Введите код из SMS", True, BLACK)
        screen.blit(text, (screen.get_width()//2-120, 200))

    def draw_main(self):
        if not self.buttons:
            btns = [
                ("Диета и бот Vita", screen.get_width()//2-150, 200),
                ("Шеф-повара", screen.get_width()//2-150, 280),
                ("Выход", screen.get_width()//2-150, 360)
            ]
            for txt, x, y in btns:
                col = SECONDARY if "Выход" in txt else PRIMARY
                self.buttons.append(Button(x, y, 300, 60, txt, color=col))
        text = font_large.render("Главное меню", True, BLACK)
        screen.blit(text, (screen.get_width()//2-100, 100))

    def draw_diet(self):
        if not self.inputs:
            self.inputs.append(InputBox(screen.get_width()//2-200, 220, 400, 50, "Тип диеты (например, низкосолевая)"))
            self.inputs.append(InputBox(screen.get_width()//2-200, 290, 400, 50, "Аллергии / что нельзя"))
            self.buttons.extend([
                Button(screen.get_width()//2-200, 370, 190, 55, "Сохранить"),
                Button(screen.get_width()//2+10, 370, 190, 55, "Назад", color=SECONDARY)
            ])
        text = font_large.render("Настройка диеты", True, BLACK)
        screen.blit(text, (screen.get_width()//2-100, 120))

    def draw_bot(self):
        text = font_large.render("Чат с ботом Vita", True, BLACK)
        screen.blit(text, (screen.get_width()//2-120, 100))
        self.bot_chat.draw(screen)
        if not self.buttons:
            self.buttons.append(Button(50, screen.get_height()-80, 200, 50, "Новый рецепт"))
            self.buttons.append(Button(screen.get_width()-250, screen.get_height()-80, 200, 50, "Назад", color=SECONDARY))

    def draw_chefs(self):
        text = font_large.render("Наши шеф-повара", True, BLACK)
        screen.blit(text, (screen.get_width()//2-120, 100))
        self.chef_list.draw(screen)
        if not self.buttons:
            self.buttons.append(Button(50, screen.get_height()-80, 150, 50, "Назад", color=SECONDARY))

    def draw_chef_detail(self):
        chef = self.current_chef
        text = font_large.render(chef['name'], True, BLACK)
        screen.blit(text, (screen.get_width()//2-100, 100))
        card_rect = pygame.Rect(50, 160, screen.get_width()-100, 400)
        draw_shadow_rect(screen, card_rect, WHITE, radius=16)
        y = card_rect.y + 20
        lines = [
            f"★ {chef['rating']}",
            chef['desc'],
            f"Цена за 1 день: {chef['price1']} руб.",
            f"Цена за 2 дня: {chef['price2']} руб.",
            chef['bio']
        ]
        for line in lines:
            surf = font_default.render(line, True, BLACK)
            screen.blit(surf, (card_rect.x+30, y))
            y += 40
        if not self.buttons:
            self.buttons.append(Button(screen.get_width()//2-100, screen.get_height()-150, 200, 55, "Заказать", color=ACCENT))
            self.buttons.append(Button(50, screen.get_height()-80, 150, 50, "Назад", color=SECONDARY))

    def draw_chef_chat(self):
        chef = self.current_chef
        text = font_large.render(f"Чат с {chef['name']}", True, BLACK)
        screen.blit(text, (screen.get_width()//2-120, 100))
        self.chef_chat.draw(screen)
        if not self.inputs:
            self.inputs.append(InputBox(50, screen.get_height()-80, screen.get_width()-300, 50, "Сообщение..."))
            self.buttons.extend([
                Button(screen.get_width()-230, screen.get_height()-80, 180, 50, "Отправить"),
                Button(screen.get_width()-230, screen.get_height()-150, 180, 50, "Назад", color=SECONDARY)
            ])

    def draw_loading(self):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0,0,0, 128))
        screen.blit(overlay, (0,0))
        text = font_large.render("Загрузка...", True, WHITE)
        rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
        screen.blit(text, rect)

    def draw_order_success(self):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0,0,0, 128))
        screen.blit(overlay, (0,0))
        text = font_large.render("Заказ оформлен!", True, WHITE)
        rect = text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
        screen.blit(text, rect)
        ok_btn = Button(screen.get_width()//2-50, screen.get_height()//2+50, 100, 40, "OK")
        ok_btn.update(pygame.mouse.get_pos(), self.mouse_pressed)
        ok_btn.draw(screen)
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN and event.button == 1 and ok_btn.is_hovered:
                self.order_placed = False
                self.set_state('chefs')

    def run(self):
        while True:
            self.handle_events()
            self.draw()
            clock.tick(FPS)

if __name__ == "__main__":
    app = VitaCorApp()
    app.run()