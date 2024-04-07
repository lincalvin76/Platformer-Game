import os
import pygame
import random
import math
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Platform Game") #name of the window

WIDTH, HEIGHT = 1400, 700 #window size
FPS = 60 #fps
PLAYER_VEL = 6 #player speed

window = pygame.display.set_mode((WIDTH, HEIGHT)) 

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites] #Flip x direction but not y

def load_sprite_sheets(dir, width, height, direction=False):
    path = join("assets", dir) 
    images = [f for f in listdir(path) if isfile(join(path, f))] 

    all_sprites = {}

    for image in images: 
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha() 

        sprites = []
        for i in range(sprite_sheet.get_width() // width): 
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
    
    return all_sprites

def get_block(size1, size2, temp1, temp2):
    path = join("assets", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size1, size2), pygame.SRCALPHA, 32)
    rect = pygame.Rect(temp1, temp2, size1, size2) 
    surface.blit(image, (0,0), rect)
    return pygame.transform.scale2x(surface)

def get_door(size, temp1, temp2):
    path = join("assets", "Door.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(temp1,temp2 ,size, size) 
    surface.blit(image, (0,0), rect)
    return pygame.transform.scale2x(surface)

class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("Player", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0 #how long player's been falling
        self.jump_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy): #move in direction 
        self.rect.x += dx #direction x
        self.rect.y += dy #direction y

    def move_left(self, vel): #move left function
        self.x_vel = -vel #move left
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel): #move right function
        self.x_vel = vel #move right
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps): #frame by frame movement
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY) #kinda realistic gravity-ish with acceleration where the longer you're in the air the faster you fall, at least 1 pixel OR the accelerated gravity per second so we aren't moving .2, .3.. pixels.
        self.move(self.x_vel, self.y_vel) #the actual movement using move function

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft =(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x): #draw player
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x,y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Block(Object):
    def __init__(self, x, y, size1, size2, temp1, temp2):
        super().__init__(x, y, size1, size2)
        block = get_block(size1, size2, temp1, temp2)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

class Door(Object):
    def __init__(self, x, y, size, temp1, temp2):
        super().__init__(x, y, size, size)
        door = get_door(size, temp1, temp2)
        self.image.blit(door, (0,0))
        self.mask = pygame.mask.from_surface(self.image)

class Pill(Object):
    ANIMATION_DELAY = 12

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "pill")
        self.pill = load_sprite_sheets("Pills", width, height, False)
        self.image = self.pill["idle"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0

    def loop(self):
        sprites = self.pill["idle"]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft =(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)
    
    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj) and type(obj) != Door and type(obj) != Pill:
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0 and type(obj) != Door and type(obj) != Pill:
                player.rect.top = obj.rect.bottom
                player.hit_head()
 
        collided_objects.append(obj)
    
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj) and type(obj) != Door and type(obj) != Pill:
            collided_object = obj
            break
    player.move(-dx, 0)
    player.update()
    return collided_object

def doorTouch(player, objects):
    keys = pygame.key.get_pressed()
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj) and type(obj) == Door:
            if keys[pygame.K_UP]:
                obj.kill()
                objects.append(Door(12 * 96, (HEIGHT - 96) - 64, 64, 32, 0))
            break

def pillTouch(player, objects):
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj) and type(obj) == Pill:
                objects.remove(obj)
                objects.append(Door(12 * 96, (HEIGHT - 96) - 64, 64, 0, 0))
                break
    
            
def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)


    if keys[pygame.K_RIGHT] and not collide_right:
        if keys[pygame.K_LEFT] and not collide_left:
            player.move_left(PLAYER_VEL)
        else:
            player.move_right(PLAYER_VEL)
    elif keys[pygame.K_LEFT] and not collide_left:
            if keys[pygame.K_RIGHT] and not collide_right:
                player.move_right(PLAYER_VEL)
            else:
                player.move_left(PLAYER_VEL)

    handle_vertical_collision(player, objects, player.y_vel)
    

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Background.png")
    block_size = 96

    player = Player(100, 500, 50, 50) #posx, posy, size, size
#-------------------------------------------------------------------------------------------------------------------------------------------------------------
    #Block Positions, For some you need to be more precise.
    #(0,0) = Stone bricks | (0, 64) = Wood planks | (0, 128) = Scales
    #(96,0) = Grass | (96, 64) = Sand | (96, 128) = Candy
    #(192, 0) = Brown Poly Bricks(WHOLE - Vertical) | (192, 64) = Grey Poly Bricks(WHOLE - Vertical) | (192, 128) = Orange Poly Bricks(WHOLE - Vertical)
    #(272, 0) = All Platforms | (272, 64) = Red Bricks | (272, 128) = Gold(WHOLE - Vertical)

    #When Creating a new Block() The Params are (X pos, Y Pos, Size(Square Shape), Terrain.png x value, Terrain.png y value as shown above)
#-------------------------------------------------------------------------------------------------------------------------------------------------------------

    objects = []
    pill = Pill((3 * block_size) + 18, (HEIGHT - block_size * 3) - 250, 32, 32)
    for i in range(0, 15):
        objects.append(Block(i * block_size, HEIGHT - block_size, block_size, block_size, 0, 0),) #Floor
    for i in range(2, 9):
        objects.append(Block(0, HEIGHT - block_size * i, block_size, block_size, 0, 0),) #Left Wall
    for i in range(1, 15):
        objects.append(Block(i * block_size, HEIGHT - block_size * 8, block_size, block_size, 0, 0),) #Roof
    for i in range(2, 9):
        objects.append(Block(14 * block_size, HEIGHT - block_size * i, block_size, block_size, 0, 0),) #Right Wall

    objects.append(Block(3 * block_size, (HEIGHT - block_size * 3) + 100, 96, 34, 192, 64),) #Grey Poly Brick Straight
    objects.append(Block(5 * block_size, (HEIGHT - block_size * 3) + 60, 96, 34, 192, 64),) #Grey Poly Brick Straight
    objects.append(Block(8 * block_size, (HEIGHT - block_size * 3) + 10, 96, 34, 192, 64),) #Grey Poly Brick Straight
    objects.append(Block(5.7 * block_size, (HEIGHT - block_size * 3) - 140, 96, 34, 192, 64),) #Grey Poly Brick Straight
    objects.append(Block(3 * block_size, (HEIGHT - block_size * 3) - 180, 96, 34, 192, 64),) #Grey Poly Brick Straight
    objects.append(pill,)
    
    offset_x = 0
    scroll_area_width = 100


    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

            
        player.loop(FPS)
        pill.loop()
        handle_move(player, objects)
        doorTouch(player, objects)
        pillTouch(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)      

        if((player.rect.right - offset_x >= WIDTH - scroll_area_width and player.x_vel > 0)) or ((player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel  
        

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)





