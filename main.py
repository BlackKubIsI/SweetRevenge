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
    return pygame.image.load(fullname)


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
    def __init__(self, screen, game, x=10, y=15):
        super().__init__(x, y)
        self.game = game
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
    def __init__(self, screen, game, x=1, y=1):
        super().__init__(x, y)
        self.set_view(
            0,
            H * 0.8,
            (W - 2 * (W // game.inventory.y)) // (game.inventory.y),
            H * 0.2,
            1,
        )
        self.screen = screen
        self.game = game
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
    def __init__(self, screen, game, x=1, y=1):
        super().__init__(x, y)
        self.game = game
        self.set_view(
            W - ((W - 2 * (W // self.game.inventory.y)) // (self.game.inventory.y)),
            H * 0.8,
            (W - 2 * (W // self.game.inventory.y)) // (self.game.inventory.y),
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
    def __init__(self, game, name_of_image, x, y, w, h, name, *k):
        super().__init__(k)
        self.game = game
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
            if self.game.left_hand.in_rect(self.rect[0], self.rect[1]):
                if self.game.left_hand.empty:
                    self.game.left_hand.empty = False
                    self.game.left_hand.hand = self.name
            elif self.game.right_hand.in_rect(self.rect[0], self.rect[1]):
                if self.game.right_hand.empty:
                    self.game.right_hand.empty = False
                    self.game.right_hand.hand = self.name
            else:
                if (
                    self.game.right_hand.empty == False
                    and self.game.right_hand.hand == self.name
                ):
                    self.game.right_hand.empty = True
                    self.game.right_hand.hand = ""
                if (
                    self.game.left_hand.empty == False
                    and self.game.left_hand.hand == self.name
                ):
                    self.game.left_hand.empty = True
                    self.game.left_hand.hand = ""
                self.rect.x, self.rect.y = self.pos_0_x, self.pos_0_y


class Inventory(Board):
    def __init__(self, screen, game, x=2, y=5):
        super().__init__(x, y)
        self.game = game
        self.set_view(
            W // y, int(H * 0.8), (W - 2 * (W // y)) // (y), (H * 0.2) // x, 1
        )
        self.screen = screen
        self.inventory = []

    def render(self):
        super().render(self.screen)
        self.game.inventory_group.draw(self.screen)

    def add_element(self, name):
        if name not in self.inventory:
            self.game.inventory_group.add(
                InventoryElement(
                    self.game,
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
        for elem in self.game.inventory_group:
            if elem.name == name:
                elem.kill()


class TextWindow(Board):
    def __init__(self, screen, game, x=1, y=1):
        super().__init__(x, y)
        self.game = game
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
        self.game.text_window.render()
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


class Plate(pygame.sprite.Sprite):
    def __init__(self, game, type, x0, y0, *k):
        super().__init__(k)
        self.game = game
        self.game = game
        if type == "s":
            self.image = pygame.transform.scale(
                load_image("Teaching/stone_path.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "g":
            self.image = pygame.transform.scale(
                load_image("Teaching/grass.jpeg"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "t":
            self.image = pygame.transform.scale(
                load_image("Teaching/tree.jpg"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
            self.image.set_colorkey((255, 255, 255))
        elif type == "b":
            self.image = pygame.transform.scale(
                load_image("Teaching/bush.jpg"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
            self.image.set_colorkey((255, 255, 255))
        elif type == "2":
            self.image = pygame.transform.scale(
                load_image("Level_1/2.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "1":
            self.image = pygame.transform.scale(
                load_image("Level_1/1.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "3":
            self.image = pygame.transform.scale(
                load_image("Level_1/3.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "kust":
            self.image = pygame.transform.scale(
                load_image("Level_1/kust.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "dv":
            self.image = pygame.transform.scale(
                load_image("Level_1/dv_1.jpg"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
            self.image.set_colorkey((255, 255, 255))
        elif type == "dv_2":
            self.image = pygame.transform.scale(
                load_image("Level_1/dv_2.jpg"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
            self.image.set_colorkey((255, 255, 255))
        elif type == "glaz":
            self.image = pygame.transform.scale(
                load_image("Level_1/glaz.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "ab":
            self.image = pygame.transform.scale(
                load_image("Level_1/ab.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "chest":
            self.image = pygame.transform.scale(
                load_image("Level_1/chest_1.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "chest_1":
            self.image = pygame.transform.scale(
                load_image("Level_1/chest_2.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "kr":
            self.image = pygame.transform.scale(
                load_image("Level_1/kr.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "gr":
            self.image = pygame.transform.scale(
                load_image("Level_1/grib.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "k":
            self.image = pygame.transform.scale(
                load_image("Level_1/kam.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        elif type == "c":
            self.image = pygame.transform.scale(
                load_image("Level_1/cv.png"),
                (
                    self.game.main_window_of_game.cell_size_1,
                    self.game.main_window_of_game.cell_size_2,
                ),
            )
        self.rect = self.image.get_rect()
        self.rect.x = x0 * self.game.main_window_of_game.cell_size_1
        self.rect.y = y0 * self.game.main_window_of_game.cell_size_2
        self.mask = pygame.mask.from_surface(self.image)


class Player(pygame.sprite.Sprite):
    def __init__(self, game, x0=0, y0=0, name="hero.png", delta=[0, 0], *k):
        super().__init__(k)
        self.game = game
        self.image = pygame.transform.scale(
            load_image(name),
            (
                self.game.main_window_of_game.cell_size_1,
                self.game.main_window_of_game.cell_size_2,
            ),
        )
        self.rect = self.image.get_rect()
        self.rect.x = x0 * self.game.main_window_of_game.cell_size_1
        self.rect.y = y0 * self.game.main_window_of_game.cell_size_2
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
            self.game.main_window_of_game.cell_size_1 * delta_pos[0],
            self.game.main_window_of_game.cell_size_2 * delta_pos[1],
        )

    def hp_render(self):
        if self.hp == 0:
            return
        image_hp = pygame.transform.scale(load_image(f"hp_{self.hp}.png"), (400, 50))
        self.game.screen.blit(image_hp, (20, 10))

    def set_image(self, name_of_image):
        self.image = pygame.transform.scale(
            load_image(name_of_image),
            (
                self.game.main_window_of_game.cell_size_1,
                self.game.main_window_of_game.cell_size_2,
            ),
        )

    def died(self):
        if self.hp <= 0:
            return self.kill(), True
        return "", False

    def pos_on_board(self):
        pos = [0, 0]
        pos[0] = int(
            (self.rect.x - self.game.main_window_of_game.left)
            // self.game.main_window_of_game.cell_size_1
        )
        pos[1] = int(
            (self.rect.y - self.game.main_window_of_game.top)
            // self.game.main_window_of_game.cell_size_2
        )
        return pos


class Game:
    def __init__(self):
        self.game_surface = pygame.Surface((W * 0.8, H * 0.8), pygame.SRCALPHA, 32)

        self.screen = pygame.display.set_mode((W, H))
        self.main_window_of_game = MainWindowOfGame(self.screen, self)
        self.inventory = Inventory(self.screen, self)
        self.text_window = TextWindow(self.screen, self)
        self.inventory_group = pygame.sprite.Group()
        self.left_hand = LeftHand(self.screen, self)
        self.right_hand = RightHand(self.screen, self)

    def start_game(self):
        self.start()
        self.introduction()
        self.teaching()

    def start(self):
        running = True

        fon_image = pygame.transform.scale(
            load_image("Start/fon.jpeg"), (W * 0.8, H * 0.8)
        )
        self.game_surface.blit(fon_image, (0, 0))

        font = pygame.font.Font(None, 100)
        text = font.render("Start", True, [0, 0, 0])
        self.game_surface.blit(
            text, (W * 0.8 // 2 - W * 0.8 // 10, H * 0.8 // 2 - H * 0.8 // 20)
        )

        while running:
            self.screen.fill((127, 72, 41))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if W * 0.8 >= event.pos[0] >= 0 and H * 0.8 >= event.pos[1] >= 0:
                        running = False
            self.main_window_of_game.render()
            self.inventory.render()
            self.text_window.render()
            self.left_hand.render()
            self.right_hand.render()
            self.screen.blit(self.game_surface, (0, 0))
            pygame.time.delay(100)
            pygame.display.flip()

    def game_over(self):
        running = True
        self.game_surface.fill("black")
        fon_image = pygame.transform.scale(
            load_image("GameOver/game_over.jpg"), (W * 0.8, H * 0.8)
        )
        self.game_surface.blit(fon_image, (0, 0))

        while running:
            self.screen.fill((127, 72, 41))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if W * 0.8 >= event.pos[0] >= 0 and H * 0.8 >= event.pos[1] >= 0:
                        running = False
            self.main_window_of_game.render()
            self.inventory.render()
            self.text_window.render()
            self.left_hand.render()
            self.right_hand.render()
            self.screen.blit(self.game_surface, (0, 0))
            pygame.time.delay(100)
            pygame.display.flip()
        self.start_game()
    
    def introduction(self): 
        running = True

        zamok = pygame.transform.scale(load_image("Introduction/zamok.jpg"), (W * 0.8, H * 0.8))
        king = pygame.transform.scale(load_image("Introduction/king.jpg"), (W * 0.8, H * 0.8))
        poxod = pygame.transform.scale(load_image("Introduction/poxod.jpg"), (W * 0.8, H * 0.8))
        voin = pygame.transform.scale(load_image("Introduction/voin.jpg"), (W * 0.8, H * 0.8))

        load_music("Introduction/war.mp3")
        pygame.mixer.music.play(-1, fade_ms=15000)

        self.game_surface.blit(zamok, (0, 0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        
        self.main_window_of_game.render()
        self.inventory.render()
        self.text_window.render()
        self.left_hand.render()
        self.right_hand.render()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        self.text_window.set_text("""Когда-то его называли Победоносным. Освободивший народ от тирании своего кровожадного дяди король Эрих стал надеждой Ланд Бесатт на светлое будущее.Однако шли годы, и вот уже тот, кто раньше вел народ за собой, стал новым проклятием для своей страны. И те, кто некогда звали Эриха Победоносным, нарекли его Жадным королем.""")
        self.screen.blit(self.game_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(5000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pygame.time.delay(5000)

        self.text_window.set_text("""Новый правитель моментально развязал очередную войну с варграми – кочевниками, обитающими в степях к югу от Ланд Бесатт. И грозился начать противостояние и с Ланд Меннескер – королевством людей, самым большим на всем континенте.""")
        self.screen.blit(king, (0, 0))
        pygame.display.flip()
        pygame.time.delay(5000)
        self.text_window.set_text("""Его боялись и поначалу даже уважали, пока не осознали, что король Арнгейр Кровавый безумен. Он убирал со своего пути всех, кого мог заподозрить в неверности, а после взялся и за тех, кто ему просто не нравился. Вскоре дело дошло до одной причины: желания развлечь себя очередной кровавой жертвой.""")
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pygame.time.delay(5000)

        self.text_window.set_text("""Но вот, появился за горами, в далекой стране, вдруг доблестный и смелый рыцарь. Был он очень сильным и отважным. С малых лет упражнялся он в воинской отваге и был во множестве сражений. Никто не мог победить его в открытом бою.""")
        self.screen.blit(poxod, (0, 0))
        pygame.display.flip()
        pygame.time.delay(5000)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pygame.time.delay(5000)

        self.text_window.set_text("""Узнал рыцарь о том, что злой король угнетает свой народ, оседлал своего верного коня, позвал оруженосца, взял длинное копье и дедовский меч и отправился в дальнюю дорогу, в тридевятое государство, в тридесятое царство.""")
        self.screen.blit(voin, (0, 0))
        pygame.display.flip()
        pygame.time.delay(5000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pygame.time.delay(5000)

        pygame.mixer.music.stop()
    
    def teaching(self):
        running = True
        with open(os.path.join("", "teaching_1.txt")) as f:
            board = list(map(lambda x: x.split("-"), f.read().split("\n")))
        player_y = board.index(list(filter(lambda x: "@" in x, board))[0])
        player_x = "".join(board[player_y]).index("@")
        player = Player(self, player_x, player_y)
        players_group = pygame.sprite.Group(player)
        plate_group = pygame.sprite.Group()

        for i in range(len(board)):
            for g in range(len(board[0])):
                plate_group.add(Plate(self, "g", g, i))
        for i in range(len(board)):
            for g in range(len(board[0])):
                if board[i][g] in ["s", "@"]:
                    plate_group.add(Plate(self, "s", g, i))
                elif board[i][g] == "t":
                    plate_group.add(Plate(self, "t", g, i))
                elif board[i][g] == "b":
                    plate_group.add(Plate(self, "b", g, i))
        
        load_music("Teaching/teaching.mp3")
        pygame.mixer.music.play(-1, fade_ms=15000)

        while running:
            self.screen.fill((127, 72, 41))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    delta = [0, 0]
                    pos_now_pl = [0, 0]
                    pos_now_pl[0] = int((player.rect.x - self.main_window_of_game.left) // self.main_window_of_game.cell_size_1)
                    pos_now_pl[1] = int((player.rect.y - self.main_window_of_game.top) // self.main_window_of_game.cell_size_2)
                    if event.key == pygame.K_DOWN:
                        if (H * 0.8 - self.main_window_of_game.cell_size_2) >= (player.rect.y + self.main_window_of_game.cell_size_2) >= 0:
                            delta = [0, 1]
                    if event.key == pygame.K_UP:
                        if (H * 0.8 - self.main_window_of_game.cell_size_2) >= (player.rect.y - self.main_window_of_game.cell_size_2) >= 0:
                            delta = [0, -1]
                    if event.key == pygame.K_LEFT:
                        if (W * 0.8 - self.main_window_of_game.cell_size_1) >= (player.rect.x - self.main_window_of_game.cell_size_1) >= 0:
                            delta = [-1, 0]
                    if event.key == pygame.K_RIGHT:
                        if (W * 0.8 - self.main_window_of_game.cell_size_1) >= (player.rect.x + self.main_window_of_game.cell_size_1) >= 0:
                            delta = [1, 0]
                    if board[pos_now_pl[1] + delta[1]][pos_now_pl[0] + delta[0]] in ["s", "@"]:
                        player.move(delta)
                    if event.key == pygame.K_RETURN:
                        for _1 in (-1, 0, 1):
                            for _2 in (-1, 0, 1):
                                if (pos_now_pl[1] + _2 < 0 or pos_now_pl[1] + _2 > len(board)) or\
                                    (pos_now_pl[0] + _1 < 0 or pos_now_pl[0] + _1 > len(board[0])):
                                    continue
                                if board[pos_now_pl[1] + _2][pos_now_pl[0] + _1] == "t":
                                    running = False
            self.main_window_of_game.render()
            self.inventory.render()
            self.text_window.render()
            self.left_hand.render()
            self.right_hand.render()
            plate_group.draw(self.screen)
            players_group.draw(self.screen)
            self.text_window.set_text("Дойдите до дерева используя клавиши: <<вверх>>,\
             <<вниз>>, <<вправо>>, <<влево>>.")
            pygame.time.delay(100)
            pygame.display.flip()
        
        pygame.mixer.music.stop()


game = Game()
player = Player(game)
players_group = pygame.sprite.Group(player)
plate_group = pygame.sprite.Group()
game.start_game()
pygame.quit()
