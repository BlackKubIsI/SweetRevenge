import pygame, sys, os, copy


pygame.init()
info = pygame.display.Info()
W, H = info.current_w - 200, info.current_h - 200
clock = pygame.time.Clock()
pygame.quit()

pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=512,
    devicename=None,
    allowedchanges=pygame.AUDIO_ALLOW_FREQUENCY_CHANGE
    | pygame.AUDIO_ALLOW_CHANNELS_CHANGE,
)
pygame.mixer.pre_init(
    frequency=44100, size=-16, channels=2, buffer=512, devicename=None
)
# звуковые эффекты
hit_of_stick = pygame.mixer.Sound(
    os.path.join("data/music/SoundEffects", "hit_stick.ogg")
)
blaster_shot = pygame.mixer.Sound(
    os.path.join("data/music/SoundEffects", "blaster_shot.ogg")
)
damage = pygame.mixer.Sound(os.path.join("data/music/SoundEffects", "damage.ogg"))


def load_image(name, colorkey=-1):
    fullname = os.path.join("data/pictures", name)
    if not os.path.isfile(fullname):
        print(f"Файл с именем {fullname} не найден.")
        sys.exit()
    return pygame.image.load(fullname).convert_alpha()


def load_music(name):
    fullname = os.path.join("data/music", name)
    if not os.path.isfile(fullname):
        print(f"Файл с именем {fullname} не найден.")
        sys.exit()
    pygame.mixer.music.load(fullname)


class Board:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.board = [[0 for g in range(self.x)] for i in range(self.y)]
        self.left, self.top, self.cell_size_1, self.cell_size_2, self.line_size = (
            10,
            10,
            40,
            40,
            1,
        )

    def set_view(self, left, top, cell_size_1, cell_size_2, line_size):
        self.left, self.top, self.cell_size_1, self.cell_size_2, self.line_size = (
            left,
            top,
            cell_size_1,
            cell_size_2,
            line_size,
        )

    def render(self, screen):
        for i in range(self.x):
            for g in range(self.y):
                pygame.draw.rect(
                    screen,
                    "black",
                    (
                        self.left + self.cell_size_1 * g,
                        self.top + self.cell_size_2 * i,
                        self.cell_size_1,
                        self.cell_size_2,
                    ),
                    self.line_size,
                )

    def get_cell(self, mouse_pos):
        if (
            self.left + self.x * (self.cell_size_1) >= mouse_pos[0] >= self.left
            and self.top + self.y * (self.cell_size_2) >= mouse_pos[1] >= self.top
        ):
            return (
                (mouse_pos[0] - self.left) // (self.cell_size_1 + self.line_size) + 1,
                (mouse_pos[1] - self.top) // (self.cell_size_2 + self.line_size) + 1,
            )

    def on_click(self, cell_coords):
        self.board[cell_coords[0]][cell_coords[1]] = int(
            not (self.board[cell_coords[0]][cell_coords[1]])
        )

    def get_click(self, mouse_pos):
        return self.get_cell(mouse_pos), self.on_click(self.get_cell(mouse_pos))

    def upper_left_corner_of_cell(self, mouse_pos):
        if self.get_cell(mouse_pos):
            cell_coord = list(map(lambda n: n - 1, self.get_cell(mouse_pos)))
            return (
                self.left + cell_coord[0] * self.cell_size_1,
                self.top + cell_coord[1] * self.cell_size_2,
            )


class MainWindowOfGame(Board):
    def __init__(self, screen, x=10, y=15):
        super().__init__(x, y)
        self.set_view(0, 0, (W * 0.8) // y, (H * 0.8) // x, 1)
        self.screen = screen

    def update_level(self, level):
        level()

    def render(self):
        super().render(self.screen)


class Hand:
    def in_rect(self, pos_x, pos_y):
        return (self.left + self.x * self.cell_size_1) >= pos_x >= self.left and (
            self.top + self.y * self.cell_size_2
        ) >= pos_y >= self.top


class LeftHand(Board, Hand):
    def __init__(self, screen, x=1, y=1):
        super().__init__(x, y)
        self.set_view(
            0, H * 0.8, (W - 2 * (W // inventory.y)) // (inventory.y), H * 0.2, 1
        )
        self.screen = screen
        self.hand = ""
        self.empty = True

    def render(self):
        super().render(self.screen)
        self.screen.blit(
            pygame.transform.scale(
                load_image("hand_1.png"), (self.cell_size_1, self.cell_size_2)
            ),
            (self.left, self.top),
        )


class RightHand(Board, Hand):
    def __init__(self, screen, x=1, y=1):
        super().__init__(x, y)
        self.set_view(
            W - ((W - 2 * (W // inventory.y)) // (inventory.y)),
            H * 0.8,
            (W - 2 * (W // inventory.y)) // (inventory.y),
            H * 0.2,
            1,
        )
        self.screen = screen
        self.hand = ""
        self.empty = True

    def render(self):
        super().render(self.screen)
        self.screen.blit(
            pygame.transform.scale(
                load_image("hand_2.png"), (self.cell_size_1, self.cell_size_2)
            ),
            (self.left, self.top),
        )


class InventoryElement(pygame.sprite.Sprite):
    def __init__(self, name_of_image, x, y, w, h, name, *k):
        super().__init__(k)
        self.image = pygame.transform.scale(load_image(name_of_image), (w, h))
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.k1, self.k2 = 0, 0
        self.pos_0_x, self.pos_0_y = x, y
        self.f = False
        self.name = name

    def update(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.f:
                self.rect.x = self.rect.x - self.k1 + event.pos[0]
                self.rect.y = self.rect.y - self.k2 + event.pos[1]
            self.k1, self.k2 = event.pos
        if event.type == pygame.MOUSEBUTTONDOWN:
            if (self.rect.x + self.rect[2]) >= event.pos[0] >= self.rect.x and (
                self.rect.y + self.rect[3]
            ) >= event.pos[1] >= self.rect.y:
                self.f = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.f = False
            if left_hand.in_rect(self.rect[0], self.rect[1]):
                if left_hand.empty:
                    left_hand.empty = False
                    left_hand.hand = self.name
            elif right_hand.in_rect(self.rect[0], self.rect[1]):
                if right_hand.empty:
                    right_hand.empty = False
                    right_hand.hand = self.name
            else:
                if right_hand.empty == False and right_hand.hand == self.name:
                    right_hand.empty = True
                    right_hand.hand = ""
                if left_hand.empty == False and left_hand.hand == self.name:
                    left_hand.empty = True
                    left_hand.hand = ""
                self.rect.x, self.rect.y = self.pos_0_x, self.pos_0_y


class Inventory(Board):
    def __init__(self, screen, x=2, y=5):
        super().__init__(x, y)
        self.set_view(
            W // y, int(H * 0.8), (W - 2 * (W // y)) // (y), (H * 0.2) // x, 1
        )
        self.screen = screen
        self.inventory = []

    def render(self):
        super().render(self.screen)
        inventory_group.draw(self.screen)

    def add_element(self, name):
        if name not in self.inventory:
            inventory_group.add(
                InventoryElement(
                    f"Inventory/{name}.png",
                    self.left
                    + int((len(self.inventory) % self.y) * self.cell_size_1)
                    + self.cell_size_1 // 3,
                    self.top + int((len(self.inventory) // self.y) * self.cell_size_2),
                    self.cell_size_1 // 3,
                    self.cell_size_2,
                    name,
                )
            )
            self.inventory.append(name)

    def remove_element(self, name):
        self.inventory = list(filter(lambda m: m != name, self.inventory))
        for elem in inventory_group:
            if elem.name == name:
                elem.kill()


class TextWindow(Board):
    def __init__(self, screen, x=1, y=1):
        super().__init__(x, y)
        self.set_view(int(W * 0.8), 0, (W * 0.2) // y, (H * 0.8) // x, 1)
        self.screen = screen
        self.text_screen = pygame.Surface(
            (
                self.x * self.cell_size_1 - self.line_size,
                self.y * self.cell_size_2 - self.line_size,
            )
        )

    def render(self):
        super().render(self.screen)
        self.text_screen.blit(
            pygame.transform.scale(load_image("parchment.png"), (W * 0.2, H * 0.8)),
            (0, 0),
        )
        self.screen.blit(
            pygame.transform.scale(load_image("parchment.png"), (W * 0.2, H * 0.8)),
            (self.left, self.top),
        )

    def set_text(self, text, color=pygame.Color("brown")):
        self.text_screen.fill("black")
        text_window.render()
        font = pygame.font.SysFont(None, 25)
        words = [word.split(" ") for word in text.splitlines()]
        space = font.size(" ")[0]
        max_width, max_height = (
            self.cell_size_1 - self.line_size,
            self.cell_size_2 - self.line_size,
        )
        pos_ = [self.left + self.line_size, self.top + self.line_size]
        pos = [self.line_size + 10, self.line_size + 70]
        x, y = pos
        for line in words:
            for word in line:
                word_surface = font.render(word, 0, color)
                word_width, word_height = word_surface.get_size()
                if x + word_width >= max_width - 10:
                    x = pos[0]
                    y += word_height
                self.text_screen.blit(word_surface, (x, y))
                x += word_width + space
            x = pos[0]
            y += word_height
        self.screen.blit(self.text_screen, pos_)


pygame.init()
screen = pygame.display.set_mode((W, H))
main_window_of_game = MainWindowOfGame(screen)
inventory = Inventory(screen)
text_window = TextWindow(screen)
inventory_group = pygame.sprite.Group()
left_hand = LeftHand(screen)
right_hand = RightHand(screen)


class Player(pygame.sprite.Sprite):
    def __init__(self, x0=0, y0=0, name="hero.png", delta=[0, 0], *k):
        super().__init__(k)
        self.image = pygame.transform.scale(
            load_image(name),
            (main_window_of_game.cell_size_1, main_window_of_game.cell_size_2),
        )
        self.rect = self.image.get_rect()
        self.rect.x = x0 * main_window_of_game.cell_size_1
        self.rect.y = y0 * main_window_of_game.cell_size_2
        self.mask = pygame.mask.from_surface(self.image)
        self.hp = 4
        if name == "hero.png":
            self.hp = 8
        self.x0, self.y0 = x0, y0
        self.name = name
        self.delta_pos = delta

    def move(self, delta_pos):
        if self.name == "hero.png" and delta_pos != [0, 0]:
            self.delta_pos = delta_pos
        self.rect = self.rect.move(
            main_window_of_game.cell_size_1 * delta_pos[0],
            main_window_of_game.cell_size_2 * delta_pos[1],
        )

    def hp_render(self):
        image_hp = pygame.transform.scale(load_image(f"hp_{self.hp}.png"), (400, 50))
        screen.blit(image_hp, (20, 10))

    def set_image(self, name_of_image):
        self.image = pygame.transform.scale(
            load_image(name_of_image),
            (main_window_of_game.cell_size_1, main_window_of_game.cell_size_2),
        )

    def died(self):
        if self.hp <= 0:
            return self.kill(), True
        return "", False

    def pos_on_board(self):
        pos = [0, 0]
        pos[0] = int(
            (self.rect.x - main_window_of_game.left) // main_window_of_game.cell_size_1
        )
        pos[1] = int(
            (self.rect.y - main_window_of_game.top) // main_window_of_game.cell_size_2
        )
        return pos


player = Player()
players_group = pygame.sprite.Group(player)
plate_group = pygame.sprite.Group()


class Game:
    def __init__(self):
        self.game_surface = pygame.Surface((W * 0.8, H * 0.8), pygame.SRCALPHA, 32)


Game()
pygame.quit()