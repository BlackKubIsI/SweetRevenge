import pygame
import sys
import os
import copy


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
damage = pygame.mixer.Sound(os.path.join(
    "data/music/SoundEffects", "damage.ogg"))


def load_image(name, colorkey=-1):
    fullname = os.path.join("data/pictures", name)
    if not os.path.isfile(fullname):
        print(f"Файл с именем {fullname} не найден.")
        sys.exit()
    if game.status == "level_3":
        return pygame.image.load(fullname).convert()
    else:
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
            self.left + self.x *
                (self.cell_size_1) >= mouse_pos[0] >= self.left
            and self.top + self.y * (self.cell_size_2) >= mouse_pos[1] >= self.top
        ):
            return (
                (mouse_pos[0] - self.left) // (self.cell_size_1 +
                                               self.line_size) + 1,
                (mouse_pos[1] - self.top) // (self.cell_size_2 +
                                              self.line_size) + 1,
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
        image = load_image("hand_1.png")
        image.set_colorkey((255, 255, 255))
        self.screen.blit(
            pygame.transform.scale(
                image, (self.cell_size_1, self.cell_size_2)),
            (self.left, self.top),
        )


class RightHand(Board, Hand):
    def __init__(self, screen, game, x=1, y=1):
        super().__init__(x, y)
        self.game = game
        self.set_view(
            W - ((W - 2 * (W // self.game.inventory.y)) //
                 (self.game.inventory.y)),
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
        image = load_image("hand_2.png")
        image.set_colorkey((255, 255, 255))
        self.screen.blit(
            pygame.transform.scale(
                image, (self.cell_size_1, self.cell_size_2)),
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
                    self.top + int((len(self.inventory) // self.y)
                                   * self.cell_size_2),
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
    
    def remove_all(self):
        self.inventory = []
        for elem in self.game.inventory_group:
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
            pygame.transform.scale(load_image(
                "parchment.png"), (W * 0.2, H * 0.8)),
            (0, 0),
        )
        self.screen.blit(
            pygame.transform.scale(load_image(
                "parchment.png"), (W * 0.2, H * 0.8)),
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
        image_hp = pygame.transform.scale(
            load_image(f"hp_{self.hp}.png"), (400, 50))
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


class RectForСollisionСhecks(pygame.sprite.Sprite):
    def __init__(self, pos_1, pos_2, *k):
        super().__init__(k)
        self.image = pygame.Surface((abs(pos_2[0]), abs(pos_2[1])))
        self.image.fill("green")
        self.rect = self.image.get_rect()
        self.rect.x = pos_1[0]
        self.rect.y = pos_1[1]
        self.mask = pygame.mask.from_surface(self.image)


class PlayerForPlatform(pygame.sprite.Sprite):
    def __init__(self, game, screen, x0=0, y0=0, *k):
        super().__init__(k)
        self.screen = screen
        self.image = pygame.transform.scale(load_image("hero.png"), (20, 40))
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.x = x0
        self.rect.y = y0
        self.game = game
        self.run = 0
        self.v = 0
        self.hp = 8
        self.in_water = False
        self.mask = pygame.mask.from_surface(self.image)

    def update(
        self, delta, l=None, t=None, wall=None, j=None, barrier=None, water=None
    ):
        if wall is not None:
            rect_for_collision_checks = RectForСollisionСhecks(
                [self.rect.x, self.rect.y + delta[1] * 10], [self.rect[2], self.rect[3] + delta[1] * 10])
            if ((not pygame.sprite.collide_mask(rect_for_collision_checks, t)) or pygame.sprite.collide_mask(self, l)) and not pygame.sprite.collide_mask(rect_for_collision_checks, wall):
                self.rect.y += delta[1] * 10
            rect_for_collision_checks = RectForСollisionСhecks(
                [self.rect.x + delta[0] * 10, self.rect.y], [self.rect[2] + delta[0] * 10, self.rect[3]])
            if not pygame.sprite.collide_mask(rect_for_collision_checks, wall) and not pygame.sprite.collide_mask(rect_for_collision_checks, t):
                self.rect.x += delta[0] * 10
            else:
                if pygame.sprite.collide_mask(rect_for_collision_checks, wall) is not None:
                    mask = pygame.sprite.collide_mask(
                        rect_for_collision_checks, wall)
                    if delta[0] * 10 <= 0:
                        mask = pygame.sprite.collide_mask(
                            wall, rect_for_collision_checks)
                        self.rect.x -= (abs(abs(mask[0] -
                                        self.rect.x) - abs(delta[0] * 10)))
                    elif delta[0] * 10 > 0:
                        self.rect.x += abs(abs(delta[0] * 10) - mask[0])
                if pygame.sprite.collide_mask(rect_for_collision_checks, t) is not None:
                    mask = pygame.sprite.collide_mask(
                        rect_for_collision_checks, t)
                    if delta[0] * 10 <= 0:
                        mask = pygame.sprite.collide_mask(
                            t, rect_for_collision_checks)
                        self.rect.x -= (abs(abs(mask[0] -
                                        self.rect.x) - abs(delta[0] * 10)))
                    elif delta[0] * 10 > 0:
                        self.rect.x += abs(abs(delta[0] * 10) - mask[0])

            # image update
            if delta[0] != 0:
                self.run = (self.run + 1) % 3 + 1
                if delta[0] == 1:
                    self.set_image(f"Level_3/mario_run_{self.run}.png")
                elif delta[0] == -1:
                    self.set_image(
                        f"Level_3/mario_run_{self.run}.png", reverse=True)
            else:
                self.run = 0
                self.set_image(f"hero_1.png")
            # image update quit

            if delta[1] == 0:
                if t is not None:
                    if pygame.sprite.collide_mask(self, j):
                        self.rect.y -= 2
                        self.v -= 20
                    if pygame.sprite.collide_mask(self, water):
                        self.in_water = True
                    else:
                        self.in_water = False
                    if pygame.sprite.collide_mask(self, barrier):
                        self.hp -= 1
                        damage.play()
                    elif not pygame.sprite.collide_mask(self, t) and not (
                        pygame.sprite.collide_mask(self, wall)
                    ):
                        rect_for_collision_checks = RectForСollisionСhecks(
                            [self.rect.x, self.rect.y + 1], [self.rect[2], self.rect[3] + 1])
                        if pygame.sprite.collide_mask(
                            rect_for_collision_checks, t
                        ) or pygame.sprite.collide_mask(rect_for_collision_checks, wall):
                            self.v = 0
                        elif not self.in_water:
                            self.v += 1
                    rect_for_collision_checks = RectForСollisionСhecks(
                        [self.rect.x, self.rect.y + self.v], [self.rect[2], self.rect[3] + self.v])
                    if pygame.sprite.collide_mask(
                        rect_for_collision_checks, t
                    ) or pygame.sprite.collide_mask(rect_for_collision_checks, wall):
                        if pygame.sprite.collide_mask(rect_for_collision_checks, wall) is not None:
                            mask = pygame.sprite.collide_mask(
                                rect_for_collision_checks, wall)
                            if self.v >= 0:
                                self.rect.y += self.v + \
                                    abs(mask[1] - self.mask.get_rect()[3])
                            elif self.v < 0:
                                self.rect.y += abs(abs(self.v) - mask[1])
                        if pygame.sprite.collide_mask(rect_for_collision_checks, t) is not None:
                            mask = pygame.sprite.collide_mask(
                                rect_for_collision_checks, t)
                            if self.v > 0:
                                self.rect.y += self.v + \
                                    abs(mask[1] - self.mask.get_rect()[3])
                            elif self.v < 0:
                                self.rect.y += abs(abs(self.v) - mask[1])
                        self.v = 0
                    else:
                        self.rect.y += self.v

    def died(self):
        if self.hp <= 0:
            return self.kill(), True
        return "", False

    def hp_render(self):
        if self.hp == 0:
            return
        image_hp = pygame.transform.scale(
            load_image(f"hp_{self.hp}.png"), (400, 50))
        image_hp.set_colorkey((0, 0, 0))
        self.game.screen.blit(image_hp, (20, 10))

    def set_image(self, name_of_image, reverse=False):
        self.image = pygame.transform.scale(
            load_image(name_of_image), (20, 40))
        if name_of_image in ["Level_3/mario_run_3.png", "Level_3/mario_run_1.png"]:
            self.image.set_colorkey((0, 0, 0))
        else:
            self.image.set_colorkey((255, 255, 255))
        if reverse:
            self.image = pygame.transform.flip(
                self.image, flip_x=True, flip_y=False)
        self.mask = pygame.mask.from_surface(self.image)


class Ladder(pygame.sprite.Sprite):
    def __init__(self, game, screen, *k):
        super().__init__(k)
        self.screen = screen
        self.image = load_image("Level_3/l.png")
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)


class Platform(pygame.sprite.Sprite):
    def __init__(self, game, screen, *k):
        super().__init__(k)
        self.screen = screen
        self.image = load_image("Level_3/t.png")
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.game = game
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)


class Wall(pygame.sprite.Sprite):
    def __init__(self, game, screen, *k):
        super().__init__(k)
        self.screen = screen
        self.image = load_image("Level_3/gran.png")
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.game = game
        self.rect.x = 0
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)


class JumpButton(pygame.sprite.Sprite):
    def __init__(self, game, screen, *k):
        super().__init__(k)
        self.screen = screen
        self.game = game
        self.image = load_image("Level_3/jump.png")
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)


class Barrier(pygame.sprite.Sprite):
    def __init__(self, game, screen, *k):
        super().__init__(k)
        self.screen = screen
        self.game = game
        self.image = load_image("Level_3/bomb.png")
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)


class Water(pygame.sprite.Sprite):
    def __init__(self, game, screen, *k):
        super().__init__(k)
        self.screen = screen
        self.image = load_image("Level_3/water.png")
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)


class Portal(pygame.sprite.Sprite):
    def __init__(self, game, screen, *k):
        super().__init__(k)
        self.screen = screen
        self.image = load_image("Level_3/pr.png")
        self.image.set_colorkey((255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)


class Game:
    def __init__(self):
        self.game_surface = pygame.Surface(
            (W * 0.8, H * 0.8), pygame.SRCALPHA, 32)

        self.status = ""
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
        self.level_1()
        self.level_3()
        self.game_over()

    def start(self):
        self.status = "start"
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
        self.status = ""

    def game_over(self):
        self.status = "game_over"
        self.screen = pygame.display.set_mode((W, H))
        self.main_window_of_game = MainWindowOfGame(self.screen, self)
        self.inventory = Inventory(self.screen, self)
        self.text_window = TextWindow(self.screen, self)
        self.inventory_group = pygame.sprite.Group()
        self.left_hand = LeftHand(self.screen, self)
        self.right_hand = RightHand(self.screen, self)

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
        self.status = ""
        self.start_game()

    def introduction(self):
        self.status = "introduction"
        running = True

        zamok = pygame.transform.scale(
            load_image("Introduction/zamok.jpg"), (W * 0.8, H * 0.8)
        )
        king = pygame.transform.scale(
            load_image("Introduction/king.jpg"), (W * 0.8, H * 0.8)
        )
        poxod = pygame.transform.scale(
            load_image("Introduction/poxod.jpg"), (W * 0.8, H * 0.8)
        )
        voin = pygame.transform.scale(
            load_image("Introduction/voin.jpg"), (W * 0.8, H * 0.8)
        )

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

        self.text_window.set_text(
            """Когда-то его называли Победоносным. Освободивший народ от тирании\
своего кровожадного дяди король Эрих стал надеждой Ланд Бесатт \
на светлое будущее.Однако шли годы, и вот уже тот, кто раньше \
вел народ за собой, стал новым проклятием для своей страны.\
И те, кто некогда звали Эриха Победоносным, нарекли его\
Жадным королем."""
        )
        self.screen.blit(self.game_surface, (0, 0))
        pygame.display.flip()
        pygame.time.delay(5000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pygame.time.delay(5000)

        self.text_window.set_text(
            """Новый правитель моментально развязал очередную войну с варграми\
– кочевниками, обитающими в степях к югу от Ланд Бесатт. И грозился \
начать противостояние и с Ланд Меннескер – королевством людей, \
самым большим на всем континенте."""
        )
        self.screen.blit(king, (0, 0))
        pygame.display.flip()
        pygame.time.delay(5000)
        self.text_window.set_text(
            """Его боялись и поначалу даже уважали, пока не осознали,\
что король Арнгейр Кровавый безумен. Он убирал со своего пути всех, \
кого мог заподозрить в неверности, а после взялся и \
за тех, кто ему просто не нравился. Вскоре дело дошло \
до одной причины: желания развлечь себя \
очередной кровавой жертвой."""
        )
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pygame.time.delay(5000)

        self.text_window.set_text(
            """Но вот, появился за горами, в далекой стране, вдруг доблестный и \
смелый рыцарь. Был он очень сильным и отважным. С малых лет \
упражнялся он в воинской отваге и был во множестве сражений. \
Никто не мог победить его в открытом бою."""
        )
        self.screen.blit(poxod, (0, 0))
        pygame.display.flip()
        pygame.time.delay(5000)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pygame.time.delay(5000)

        self.text_window.set_text(
            """Узнал рыцарь о том, что злой король угнетает свой народ, оседлал своего \
верного коня, позвал оруженосца, взял длинное копье и дедовский меч \
и отправился в дальнюю дорогу, в тридевятое государство, \
в тридесятое царство."""
        )
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
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    delta = [0, 0]
                    pos_now_pl = [0, 0]
                    pos_now_pl[0] = int(
                        (player.rect.x - self.main_window_of_game.left)
                        // self.main_window_of_game.cell_size_1
                    )
                    pos_now_pl[1] = int(
                        (player.rect.y - self.main_window_of_game.top)
                        // self.main_window_of_game.cell_size_2
                    )
                    if event.key == pygame.K_DOWN:
                        if (
                            (H * 0.8 - self.main_window_of_game.cell_size_2)
                            >= (player.rect.y + self.main_window_of_game.cell_size_2)
                            >= 0
                        ):
                            delta = [0, 1]
                    if event.key == pygame.K_UP:
                        if (
                            (H * 0.8 - self.main_window_of_game.cell_size_2)
                            >= (player.rect.y - self.main_window_of_game.cell_size_2)
                            >= 0
                        ):
                            delta = [0, -1]
                    if event.key == pygame.K_LEFT:
                        if (
                            (W * 0.8 - self.main_window_of_game.cell_size_1)
                            >= (player.rect.x - self.main_window_of_game.cell_size_1)
                            >= 0
                        ):
                            delta = [-1, 0]
                    if event.key == pygame.K_RIGHT:
                        if (
                            (W * 0.8 - self.main_window_of_game.cell_size_1)
                            >= (player.rect.x + self.main_window_of_game.cell_size_1)
                            >= 0
                        ):
                            delta = [1, 0]
                    if board[pos_now_pl[1] + delta[1]][pos_now_pl[0] + delta[0]] in [
                        "s",
                        "@",
                    ]:
                        player.move(delta)
                    if event.key == pygame.K_RETURN:
                        for _1 in (-1, 0, 1):
                            for _2 in (-1, 0, 1):
                                if (
                                    pos_now_pl[1] + _2 < 0
                                    or pos_now_pl[1] + _2 > len(board)
                                ) or (
                                    pos_now_pl[0] + _1 < 0
                                    or pos_now_pl[0] + _1 > len(board[0])
                                ):
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
            self.text_window.set_text(
                "Дойдите до дерева используя клавиши: <<вверх>>,\
             <<вниз>>, <<вправо>>, <<влево>>."
            )
            pygame.time.delay(100)
            pygame.display.flip()
        self.status = ""

        pygame.mixer.music.stop()

    def level_1(self):
        self.status = "level_1"

        def near_plates(pos_now_pl):
            k = []
            for i in (-1, 0, 1):
                for g in (-1, 0, 1):
                    if (i == 0 or g == 0) and (g != 0 or i != 0):
                        k.append(board[pos_now_pl[1] + i][pos_now_pl[0] + g])
            return k

        def near_mobs(pos_now_pl, group):
            k = []
            for i in (-1, 0, 1):
                for g in (-1, 0, 1):
                    if i != 0 or g != 0:
                        for mob in group:
                            pos_now_mob = mob.pos_on_board()
                            if (
                                pos_now_mob[0] == pos_now_pl[0] + i
                                and pos_now_mob[1] == pos_now_pl[1] + g
                            ):
                                k.append(mob)
            return k

        running = True
        with open(os.path.join("", "level_1.txt")) as f:
            board = list(map(lambda x: x.split(), f.read().split("\n")))
        player_y = board.index(list(filter(lambda x: "@" in x, board))[0])
        player_x = "".join(board[player_y]).index("@")
        player = Player(self, player_x, player_y)
        players_group = pygame.sprite.Group()
        players_group.add(player)
        balls_group = pygame.sprite.Group()
        plate_group = pygame.sprite.Group()
        kam_group = pygame.sprite.Group()
        screen_level_1 = pygame.Surface(
            (
                int(len(board[0]) * self.main_window_of_game.cell_size_1),
                int(len(board) * self.main_window_of_game.cell_size_2),
            )
        )
        delta_kam = 1

        def update_board():
            for i in range(len(board)):
                for g in range(len(board[0])):
                    if board[i][g] in ["1", "@"]:
                        plate_group.add(Plate(self, "1", g, i))
                    elif board[i][g] == "2":
                        plate_group.add(Plate(self, "2", g, i))
                    elif board[i][g] == "3":
                        plate_group.add(Plate(self, "3", g, i))
                    elif board[i][g] == "ab":
                        plate_group.add(Plate(self, "1", g, i))
                        plate_group.add(Plate(self, "ab", g, i))
                    elif board[i][g] == "kust":
                        plate_group.add(Plate(self, "1", g, i))
                        plate_group.add(Plate(self, "kust", g, i))
                    elif board[i][g] == "glaz":
                        plate_group.add(Plate(self, "kust", g, i))
                        plate_group.add(Plate(self, "glaz", g, i))
                    elif board[i][g] == "dv":
                        plate_group.add(Plate(self, "1", g, i))
                        plate_group.add(Plate(self, "dv", g, i))
                    elif board[i][g] == "dv_2":
                        plate_group.add(Plate(self, "1", g, i))
                        plate_group.add(Plate(self, "dv_2", g, i))
                    elif board[i][g] == "chest":
                        plate_group.add(Plate(self, "1", g, i))
                        plate_group.add(Plate(self, "chest", g, i))
                    elif board[i][g] == "chest_1":
                        plate_group.add(Plate(self, "1", g, i))
                        plate_group.add(Plate(self, "chest_1", g, i))
                    elif board[i][g] == "k":
                        plate_group.add(Plate(self, "1", g, i))
                        kam_group.add(Player(self, g, i, "Level_1/kam.png"))
                    elif board[i][g] == "gr":
                        plate_group.add(Plate(self, "1", g, i))
                        players_group.add(
                            Player(self, g, i, "Level_1/grib.png"))
                    elif board[i][g] == "kr":
                        plate_group.add(Plate(self, "1", g, i))
                        plate_group.add(Plate(self, "kr", g, i))
                    elif board[i][g] == "c":
                        plate_group.add(Plate(self, "1", g, i))
                        plate_group.add(Plate(self, "c", g, i))

        update_board()

        load_music("Teaching/teaching.mp3")
        pygame.mixer.music.play(-1, fade_ms=15000)
        text = ""

        while running:
            clock.tick(70)
            self.screen.fill((127, 72, 41))
            screen_level_1.fill("black")
            self.text_window.render()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    delta = [0, 0]
                    pos_now_pl = [0, 0]
                    pos_now_pl[0] = int(
                        (player.rect.x - self.main_window_of_game.left)
                        // self.main_window_of_game.cell_size_1
                    )
                    pos_now_pl[1] = int(
                        (player.rect.y - self.main_window_of_game.top)
                        // self.main_window_of_game.cell_size_2
                    )
                    if event.key == pygame.K_DOWN:
                        delta = [0, 1]
                    if event.key == pygame.K_UP:
                        delta = [0, -1]
                    if event.key == pygame.K_LEFT:
                        delta = [-1, 0]
                    if event.key == pygame.K_RIGHT:
                        delta = [1, 0]
                    if board[pos_now_pl[1] + delta[1]][pos_now_pl[0] + delta[0]] in [
                        "1",
                        "@",
                        "3",
                        "dv_2",
                    ]:
                        player.move(delta)
                    if event.key == pygame.K_RETURN:
                        if "chest" in near_plates(pos_now_pl):
                            self.inventory.add_element("stick")
                            board[19][39] = "chest_1"
                            kam_group = pygame.sprite.Group()
                            update_board()
                            text = "Вы открыли сундук!! Теперь у вас есть палка! Для того, чтобы \
воспользоваться палкой, перетащите её мышкой в одну из рук.\
Теперь нажмите enter!"
                        if "dv" in near_plates(pos_now_pl) and (
                            self.left_hand.hand == "key"
                            or self.right_hand.hand == "key"
                            or self.left_hand.hand == "key_1"
                            or self.right_hand.hand == "key_1"
                        ):
                            self.inventory.add_element("stick")
                            board[player.pos_on_board()[1] - 1][
                                player.pos_on_board()[0]
                            ] = "dv_2"
                            kam_group = pygame.sprite.Group()
                            if "key" in self.inventory.inventory:
                                self.inventory.remove_element("key")
                                self.left_hand.empty, self.right_hand.empty = True, True
                                self.left_hand.hand, self.right_hand.hand = "", ""
                            update_board()
                        if "kr" in near_plates(pos_now_pl):
                            text = "Привет!Меня зовут Крот. Я и мои друзья живём в этом \
подземелье уже очень давно, но недавно здесь поселились \
эти противные камни! Они заточили моих друзей в \
комнате неподалёку оттуда. Я дам тебе этот бластер. \
С помощью него ты сможень одолеть эти камни и \
спасти моих друзей. Ах, да! Я чуть не забыл! \
Держи. Это ключ от комнаты."
                            self.inventory.add_element("gun")
                            self.inventory.add_element("key")
                        if "ab" in near_plates(pos_now_pl):
                            text = "Привет! Меня зовут Сосиска! Я ждал тебя. Держи. Этот \
ключ поможет тебе открыть следующую дверь."
                            self.inventory.add_element("key_1")
                        if "glaz" in near_plates(pos_now_pl):
                            text = "Вот ты и прошёл первое испытание... Впереди тебя ожидает \
ещё много трудностей. Следующая - тёмный лес, полный опасностей."
                        if "kust" in near_plates(pos_now_pl):
                            running = False
                        if not (self.right_hand.empty and self.left_hand.empty):
                            if not (self.right_hand.empty):
                                if self.right_hand.hand in ["stick", "sword"]:
                                    hit_of_stick.play()
                                    for mob in near_mobs(pos_now_pl, players_group):
                                        if mob.hp == 1:
                                            board[mob.pos_on_board()[0]][
                                                mob.pos_on_board()[1]
                                            ] = "1"
                                        mob.hp -= 1
                                if self.right_hand.hand in ["gun"]:
                                    balls_group.add(
                                        Player(
                                            self,
                                            mob.pos_on_board()[
                                                0] + player.delta_pos[0],
                                            mob.pos_on_board()[
                                                1] + player.delta_pos[1],
                                            name="Inventory/ball.png",
                                            delta=player.delta_pos,
                                        )
                                    )

                            if not (self.left_hand.empty):
                                if self.left_hand.hand in ["stick", "sword"]:
                                    hit_of_stick.play()
                                    for mob in near_mobs(pos_now_pl, players_group):
                                        if mob.hp == 1:
                                            board[mob.pos_on_board()[1]][
                                                mob.pos_on_board()[0]
                                            ] = "1"
                                        mob.hp -= 1
                                if self.left_hand.hand in ["gun"]:
                                    blaster_shot.play()
                                    balls_group.add(
                                        Player(
                                            self,
                                            player.pos_on_board()[0]
                                            + player.delta_pos[0],
                                            player.pos_on_board()[1]
                                            + player.delta_pos[1],
                                            name="Inventory/ball.png",
                                            delta=player.delta_pos,
                                        )
                                    )
                self.inventory_group.update(event)
            if len(near_mobs(player.pos_on_board(), kam_group)) != 0:
                player.hp -= 1
                damage.play()
            for m in balls_group:
                m.move(m.delta_pos)
                for mob in players_group:
                    if mob.pos_on_board() == m.pos_on_board():
                        if mob.hp <= 1:
                            board[mob.pos_on_board()[1]][mob.pos_on_board()[
                                0]] = "1"
                        mob.hp -= 1
                        m.kill()
                for mob in kam_group:
                    if mob.pos_on_board() == m.pos_on_board():
                        if mob.hp <= 1:
                            board[mob.pos_on_board()[1]][mob.pos_on_board()[
                                0]] = "1"
                        mob.hp -= 1
                        m.kill()
                if board[m.pos_on_board()[1]][m.pos_on_board()[0]] not in [
                    "1",
                    "@",
                    "gr",
                    "dv_2",
                ]:
                    m.kill()
            for m in kam_group:
                if board[m.pos_on_board()[1]][m.pos_on_board()[0] + delta_kam] not in [
                    "1",
                    "@",
                    "k",
                ]:
                    delta_kam = -delta_kam
            for m in kam_group:
                m.move([delta_kam, 0])
            for pl in players_group:
                pl.died()
            for pl in kam_group:
                if pl.died()[1]:
                    board[pl.y0][pl.x0] = "1"
            if (
                self.right_hand.empty == False
                and self.right_hand.hand != "key"
                and self.right_hand.hand != "key_1"
            ):
                player.set_image(f"mario_and_{self.right_hand.hand}.png")
            if (
                self.left_hand.empty == False
                and self.left_hand.hand != "key"
                and self.left_hand.hand != "key_1"
            ):
                player.set_image(f"mario_and_{self.left_hand.hand}.png")
            if self.left_hand.hand == "" and self.right_hand.hand == "":
                player.set_image(f"hero.png")
            if player.hp == 0:
                pygame.mixer.music.stop()
                self.game_over()
                break
            self.main_window_of_game.render()
            self.text_window.render()
            self.inventory.render()
            self.left_hand.render()
            self.right_hand.render()
            self.text_window.set_text(text)
            plate_group.draw(screen_level_1)
            players_group.draw(screen_level_1)
            balls_group.draw(screen_level_1)
            kam_group.draw(screen_level_1)
            self.screen.blit(
                screen_level_1,
                (0, 0),
                area=(
                    (player.rect.x - self.main_window_of_game.cell_size_1 * 5),
                    (player.rect.y - self.main_window_of_game.cell_size_2 * 5),
                    (player.rect.x - self.main_window_of_game.cell_size_1 * 5)
                    + W * 0.8
                    - self.main_window_of_game.cell_size_1
                    * (int(player.rect.x // self.main_window_of_game.cell_size_1) - 5),
                    (player.rect.y - self.main_window_of_game.cell_size_2 * 5)
                    + H * 0.8
                    - self.main_window_of_game.cell_size_2
                    * (int(player.rect.y // self.main_window_of_game.cell_size_2) - 5),
                ),
            )
            player.hp_render()
            pygame.time.delay(100)
            pygame.display.flip()

        self.status = ""
        pygame.mixer.music.stop()

    def level_3(self):
        self.status = "level_3"
        running = True
        self.inventory.remove_all()
        fon_image = pygame.transform.scale(
            load_image("Level_3/fon.png"), (2750, 5000))
        platform = Platform(self, self.screen)
        ladder = Ladder(self, self.screen)
        wall = Wall(self, self.screen)
        jump_button = JumpButton(self, self.screen)
        barrier = Barrier(self, self.screen)
        water = Water(self, self.screen)
        portal = Portal(self, self.screen)

        self.screen.fill((127, 72, 41))
        self.text_window.set_text("")
        screen_level_3 = pygame.Surface((2750, 5000))
        player = PlayerForPlatform(self, self.screen, x0=30, y0=4840)

        all_group = pygame.sprite.Group()
        all_group.add(platform)
        all_group.add(ladder)
        all_group.add(water)
        all_group.add(player)
        all_group.add(wall)
        all_group.add(jump_button)
        all_group.add(barrier)
        all_group.add(portal)

        delta = [0, 0]

        load_music("Teaching/teaching.mp3")
        pygame.mixer.music.play(-1, fade_ms=15000)

        while running:
            self.screen.fill((127, 72, 41))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    delta = [0, 0]
                    if event.key == pygame.K_LEFT:
                        delta = [-1, 0]
                    if event.key == pygame.K_RIGHT:
                        delta = [1, 0]
                    if event.key == pygame.K_DOWN and (
                        pygame.sprite.collide_mask(
                            player, ladder) or player.in_water
                    ):
                        delta = [0, 1]
                    if event.key == pygame.K_UP and (
                        pygame.sprite.collide_mask(
                            player, ladder) or player.in_water
                    ):
                        delta = [0, -1]
                    if event.key == pygame.K_SPACE:
                        if player.v == 0 and not player.in_water:
                            player.rect.y -= 2
                            player.v -= 11
                    player.update(delta)
                if event.type == pygame.KEYUP:
                    delta = [0, 0]
            player.update(
                delta,
                t=platform,
                l=ladder,
                wall=wall,
                j=jump_button,
                barrier=barrier,
                water=water,
            )
            if pygame.sprite.collide_mask(player, portal):
                running = False
                pygame.mixer.music.stop()
            if player.hp == 0:
                pygame.mixer.music.stop()
                self.game_over()
                break

            self.inventory.render()
            self.text_window.render()
            self.left_hand.render()
            self.right_hand.render()

            screen_level_3.blit(fon_image, (0, 0))
            all_group.draw(screen_level_3)

            self.screen.blit(
                screen_level_3,
                (0, 0),
                area=(
                    (player.rect.x - W * 0.3),
                    (player.rect.y - H * 0.3),
                    W * 0.8,
                    H * 0.8,
                ),
            )
            player.hp_render()
            pygame.display.flip()
        pygame.mixer.music.stop()
        self.status = ""


game = Game()
player = Player(game)
players_group = pygame.sprite.Group(player)
plate_group = pygame.sprite.Group()
game.start_game()
pygame.quit()
