import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
GRID_SIZE = 40
PLAY_AREA_WIDTH = 600 
HUD_WIDTH = 400

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (30, 30, 30)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 255)
YELLOW = (200, 200, 0)
ORANGE = (255, 150, 0)

# Block Types: (Name, BaseColor, MaxHP, Value, Fuel_Given, Grav_Affected, FluidType)
# FluidType: None, Liquid, Gas
BLOCK_TYPES = {
    "Air": ("Air", BLACK, 0, 0, 0, False, None),
    "Bedrock": ("Bedrock", (20, 20, 20), 9999, 0, 0, False, None),
    "Dirt": ("Dirt", (134, 87, 62), 1, 1, 0, True, None),
    "Sandstone": ("Sandstone", (194, 178, 128), 2, 2, 0, True, None),
    "Limestone": ("Limestone", (211, 211, 211), 4, 3, 0, False, None),
    "Granite": ("Granite", (80, 80, 80), 6, 5, 0, False, None),
    "Basalt": ("Basalt", (40, 40, 40), 10, 8, 0, False, None),
    "Obsidian": ("Obsidian", (75, 0, 130), 15, 150, 0, False, None),
    "Coal": ("Coal", (10, 10, 10), 3, 10, 25, True, None),
    "Iron": ("Iron", (180, 100, 50), 5, 30, 0, False, None),
    "Gold": ("Gold", (255, 215, 0), 6, 80, 0, False, None),
    "Diamond": ("Diamond", (0, 255, 255), 10, 200, 0, False, None),
    "Uranium": ("Uranium", (50, 255, 50), 7, 500, 0, False, None),
    "Water": ("Water", (50, 100, 255), 1, 0, 0, True, "Liquid"),
    "Oil": ("Oil", (50, 50, 50), 1, 50, 0, True, "Liquid"),
    "Gas": ("Gas", (200, 200, 0), 1, 10, 0, True, "Gas"), # Pressurized Methane
    "Magma": ("Magma", (255, 69, 0), 0, -50, 0, False, "Liquid"),
    "Core": ("Core", (255, 255, 255), 50, 10000, 0, False, None) # Win Block
}

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Journey to the Core: V5 - Thermodynamics & Textures")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22, bold=True)
large_font = pygame.font.SysFont("Arial", 48, bold=True)
title_font = pygame.font.SysFont("Arial", 32, bold=True)

def generate_block_texture(color, b_type):
    """Generates a procedural pixel-art texture for each block type."""
    surf = pygame.Surface((GRID_SIZE, GRID_SIZE))
    surf.fill(color)
    
    if b_type in ["Dirt", "Sandstone", "Basalt", "Bedrock"]:
        for _ in range(15):
            rx = random.randint(0, GRID_SIZE-4)
            ry = random.randint(0, GRID_SIZE-4)
            shade = random.randint(-20, 20)
            new_color = (max(0,min(255,color[0]+shade)), max(0,min(255,color[1]+shade)), max(0,min(255,color[2]+shade)))
            pygame.draw.rect(surf, new_color, (rx, ry, 4, 4))
    elif b_type in ["Granite", "Limestone"]:
        for _ in range(5):
            pygame.draw.line(surf, (max(0,color[0]-30), max(0,color[1]-30), max(0,color[2]-30)), 
                             (random.randint(0, GRID_SIZE), random.randint(0, GRID_SIZE)),
                             (random.randint(0, GRID_SIZE), random.randint(0, GRID_SIZE)), 2)
    elif b_type in ["Iron", "Gold", "Diamond", "Uranium"]:
        # Draw little chunks
        for _ in range(4):
            pygame.draw.circle(surf, (min(255,color[0]+50), min(255,color[1]+50), min(255,color[2]+50)), 
                               (random.randint(5, GRID_SIZE-5), random.randint(5, GRID_SIZE-5)), random.randint(4, 8))
    elif b_type == "Coal":
        pygame.draw.circle(surf, (60, 60, 60), (10, 10), 5)
        pygame.draw.circle(surf, (60, 60, 60), (30, 25), 6)
    elif b_type == "Obsidian":
        pygame.draw.line(surf, (150, 0, 200), (0, 10), (40, 30), 1)
        pygame.draw.line(surf, (150, 0, 200), (10, 40), (30, 0), 1)
        
    return surf

# Pre-render all textures
BLOCK_TEXTURES = {b_type: generate_block_texture(data[1], b_type) for b_type, data in BLOCK_TYPES.items()}

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.life = 40

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3 
        self.life -= 1

    def draw(self, surface, cam_x, cam_y):
        pygame.draw.rect(surface, self.color, (self.x - cam_x, self.y - cam_y, 5, 5))

class Explosion:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.max_radius = radius * 2
        self.life = 25

    def update(self):
        self.radius += (self.max_radius - self.radius) * 0.3
        self.life -= 1

    def draw(self, surface, cam_x, cam_y):
        alpha = int(255 * (self.life / 25))
        surf = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 200, 0, alpha), (self.max_radius, self.max_radius), int(self.radius))
        surface.blit(surf, (self.x - self.max_radius - cam_x, self.y - self.max_radius - cam_y))

class Player:
    def __init__(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.max_health = 100
        self.health = 100
        self.max_fuel = 100
        self.fuel = 100
        self.money = 0
        self.depth = 0
        self.max_depth = 0
        
        self.hull_lvl = 1
        self.fuel_lvl = 1
        self.drill_lvl = 1
        self.scanner_lvl = 0
        self.cooling_lvl = 0 # New: Reduces heat damage
        
        self.bombs = 3
        self.move_timer = 0
        self.drill_anim_timer = 0

    def get_drill_power(self): return self.drill_lvl
    def get_max_health(self): return 100 + (self.hull_lvl - 1) * 50
    def get_max_fuel(self): return 100 + (self.fuel_lvl - 1) * 50
    def get_scan_radius(self): return self.scanner_lvl * 3

    def draw(self, surface, cam_x, cam_y):
        rect = pygame.Rect(self.grid_x * GRID_SIZE - cam_x, self.grid_y * GRID_SIZE - cam_y, GRID_SIZE, GRID_SIZE)
        
        if self.drill_anim_timer > 0:
            offset_x = random.randint(-2, 2)
            offset_y = random.randint(-2, 2)
            self.drill_anim_timer -= 1
        else:
            offset_x, offset_y = 0, 0
            
        pygame.draw.rect(surface, YELLOW, rect.move(offset_x, offset_y))
        bit_points = [
            (rect.left + offset_x, rect.bottom - 10 + offset_y),
            (rect.right + offset_x, rect.bottom - 10 + offset_y),
            (rect.centerx + offset_x, rect.bottom + offset_y)
        ]
        pygame.draw.polygon(surface, WHITE, bit_points)
        pygame.draw.circle(surface, BLUE, (rect.centerx + offset_x, rect.centery + offset_y), 8)
        pygame.draw.circle(surface, WHITE, (rect.centerx + offset_x, rect.centery + offset_y), 8, 2)

class Game:
    def __init__(self):
        self.grid_width = PLAY_AREA_WIDTH // GRID_SIZE
        self.grid_height = 1500 
        self.world = self.generate_world()
        
        self.player = Player(self.grid_width // 2, 0)
        self.world[self.player.grid_y][self.player.grid_x] = ["Air", 0]
        
        self.camera_y = 0
        self.camera_x = 0
        self.game_state = "PLAYING" 
        
        self.particles = []
        self.explosions = []
        self.move_cooldown = 120 
        self.liquid_timer = 0
        self.heat_timer = 0
        
        self.shake_intensity = 0
        self.shake_timer = 0

    def generate_world(self):
        world = []
        for y in range(self.grid_height):
            row = []
            for x in range(self.grid_width):
                if y == self.grid_height - 1:
                    b_type = "Bedrock"
                elif y < 2:
                    b_type = "Air"
                elif y < 4:
                    b_type = "Dirt"
                else:
                    depth_ratio = y / self.grid_height
                    if depth_ratio < 0.15: b_type = "Sandstone"
                    elif depth_ratio < 0.35: b_type = "Limestone"
                    elif depth_ratio < 0.65: b_type = "Granite"
                    else: b_type = "Basalt"

                    if depth_ratio > 0.4 and random.random() < 0.015: b_type = "Magma"

                max_hp = BLOCK_TYPES[b_type][2]
                row.append([b_type, max_hp])
            world.append(row)
            
        self.generate_veins(world, "Coal", 50, 30)
        self.generate_veins(world, "Iron", 150, 30)
        self.generate_veins(world, "Gold", 300, 20)
        self.generate_veins(world, "Diamond", 600, 15)
        self.generate_veins(world, "Uranium", 800, 10)
        
        self.generate_pocket(world, "Water", 20, 80, 5)
        self.generate_pocket(world, "Oil", 100, 250, 4)
        self.generate_pocket(world, "Gas", 50, 300, 6) # Gas pockets
        
        # Place the Core at the very bottom center
        core_y = self.grid_height - 2
        core_x = self.grid_width // 2
        world[core_y][core_x] = ["Core", BLOCK_TYPES["Core"][2]]
        # Surround core with magma for a dramatic finish
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dy == 0 and dx == 0: continue
                nx, ny = core_x + dx, core_y + dy
                if world[ny][nx][0] != "Bedrock":
                    world[ny][nx] = ["Magma", BLOCK_TYPES["Magma"][2]]
        
        return world

    def generate_veins(self, world, ore_type, max_depth, num_veins):
        for _ in range(num_veins):
            start_y = random.randint(10, min(max_depth, self.grid_height - 2))
            start_x = random.randint(0, self.grid_width - 1)
            vein_size = random.randint(3, 8)
            cx, cy = start_x, start_y
            for _ in range(vein_size):
                if 0 <= cx < self.grid_width and 0 <= cy < self.grid_height - 1:
                    if world[cy][cx][0] not in ["Air", "Bedrock", "Magma", "Core"]:
                        world[cy][cx] = [ore_type, BLOCK_TYPES[ore_type][2]]
                cx += random.choice([-1, 0, 1])
                cy += random.choice([-1, 0, 1])

    def generate_pocket(self, world, fluid_type, min_depth, max_depth, num_pockets):
        for _ in range(num_pockets):
            cy = random.randint(min_depth, min(max_depth, self.grid_height - 10))
            cx = random.randint(2, self.grid_width - 3)
            size = random.randint(2, 4)
            for dy in range(-size, size+1):
                for dx in range(-size, size+1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height - 1:
                        if math.sqrt(dx**2 + dy**2) <= size and world[ny][nx][0] != "Bedrock":
                            world[ny][nx] = [fluid_type, BLOCK_TYPES[fluid_type][2]]

    def trigger_shake(self, intensity, duration):
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_timer = max(self.shake_timer, duration)

    def trigger_gas_explosion(self, x, y):
        self.explosions.append(Explosion(x * GRID_SIZE + GRID_SIZE//2, y * GRID_SIZE + GRID_SIZE//2, 15))
        self.trigger_shake(20, 40)
        self.player.health -= 30
        if self.player.health <= 0: self.game_state = "GAME_OVER"
        
        # Clear 5x5 area
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    b = self.world[ny][nx]
                    if b[0] not in ["Bedrock", "Core"]:
                        self.spawn_particles(nx, ny, ORANGE, 5)
                        self.world[ny][nx] = ["Air", 0]

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()
        if self.game_state != "PLAYING": return
        
        self.player.move_timer -= dt
        if self.player.move_timer <= 0:
            dx, dy = 0, 0
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = 1
            elif keys[pygame.K_UP] or keys[pygame.K_w]: dy = -1
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = 1
                
            if dx != 0 or dy != 0:
                self.move_player(dx, dy)
                self.player.move_timer = self.move_cooldown

    def check_gravity_player(self):
        if self.game_state != "PLAYING": return
        below_y = self.player.grid_y + 1
        if below_y < self.grid_height:
            block_below = self.world[below_y][self.player.grid_x]
            if block_below[0] == "Air":
                self.player.grid_y += 1
                self.player.move_timer = 50 
                self.update_depth()
                self.check_gravity_player()

    def apply_gravity_to_blocks(self, x, y):
        if y > 0:
            above_block = self.world[y-1][x]
            b_type = above_block[0]
            if b_type != "Air" and BLOCK_TYPES[b_type][5]: # Gravity Affected
                self.world[y][x] = above_block
                self.world[y-1][x] = ["Air", 0]
                self.spawn_particles(x, y-1, BLOCK_TYPES[b_type][1], 2)
                self.trigger_shake(2, 10)
                self.apply_gravity_to_blocks(x, y-1)

    def move_player(self, dx, dy):
        new_x = self.player.grid_x + dx
        new_y = self.player.grid_y + dy

        if new_x < 0 or new_x >= self.grid_width or new_y < 0 or new_y >= self.grid_height: return

        target_block = self.world[new_y][new_x]
        b_type = target_block[0]
        name, color, max_hp, value, fuel, grav, fluid = BLOCK_TYPES[b_type]

        if b_type == "Bedrock": return 

        fuel_cost = 2
        if dy == -1: fuel_cost = 4
        
        if self.player.fuel <= 0:
            self.player.health -= 2
            if self.player.health <= 0: self.game_state = "GAME_OVER"
            return

        # Handle Magma
        if b_type == "Magma":
            self.player.fuel -= fuel_cost
            self.player.health -= 25
            self.world[new_y][new_x] = ["Air", 0]
            self.player.grid_x = new_x
            self.player.grid_y = new_y
            self.spawn_particles(new_x, new_y, RED, 10)
            self.trigger_shake(10, 20)
            if self.player.health <= 0: self.game_state = "GAME_OVER"
            return

        # Handle Digging
        if b_type != "Air":
            self.player.fuel -= fuel_cost
            target_block[1] -= self.player.get_drill_power()
            self.player.drill_anim_timer = 5
            self.spawn_particles(new_x, new_y, color, 3)
            
            if max_hp > 4: self.trigger_shake(2, 5)

            if target_block[1] <= 0:
                # Block Broken!
                self.world[new_y][new_x] = ["Air", 0]
                
                # Win Condition
                if b_type == "Core":
                    self.game_state = "WIN"
                    return
                
                self.player.money += value
                self.player.fuel = min(self.player.get_max_fuel(), self.player.fuel + fuel)
                self.spawn_particles(new_x, new_y, color, 8)
                
                if b_type == "Uranium": self.trigger_shake(5, 10)
                self.apply_gravity_to_blocks(new_x, new_y)
            else:
                return 
        else:
            self.player.fuel -= fuel_cost
                
        self.player.grid_x = new_x
        self.player.grid_y = new_y
        self.update_depth()

        target_cam_y = self.player.grid_y * GRID_SIZE - (SCREEN_HEIGHT // 2)
        self.camera_y += (target_cam_y - self.camera_y) * 0.2

    def use_bomb(self):
        if self.player.bombs > 0 and self.game_state == "PLAYING":
            self.player.bombs -= 1
            px, py = self.player.grid_x, self.player.grid_y
            self.explosions.append(Explosion(px * GRID_SIZE + GRID_SIZE//2, py * GRID_SIZE + GRID_SIZE//2, 10))
            self.trigger_shake(15, 30)
            
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        b = self.world[ny][nx]
                        if b[0] == "Gas":
                            self.trigger_gas_explosion(nx, ny)
                        elif b[0] not in ["Air", "Bedrock", "Core"]:
                            name, color, max_hp, val, fuel, grav, fluid = BLOCK_TYPES[b[0]]
                            self.player.money += val // 2 
                            self.world[ny][nx] = ["Air", 0]
                            self.spawn_particles(nx, ny, ORANGE, 5)
                            self.apply_gravity_to_blocks(nx, ny)

    def check_radiation(self, dt):
        if self.game_state != "PLAYING": return
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nx, ny = self.player.grid_x + dx, self.player.grid_y + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    if self.world[ny][nx][0] == "Uranium":
                        self.player.health -= 0.05 * (dt / 16.6)
                        if self.player.health <= 0: self.game_state = "GAME_OVER"
                        return

    def check_heat(self, dt):
        if self.game_state != "PLAYING": return
        self.heat_timer += dt
        if self.heat_timer < 500: return # Check every 0.5s
        self.heat_timer = 0
        
        # Below 10,000m (y=1000), ambient heat damage applies
        if self.player.grid_y > 1000:
            base_dmg = 1 if self.player.grid_y < 1300 else 3
            if self.player.cooling_lvl == 1: base_dmg *= 0.5
            elif self.player.cooling_lvl == 2: base_dmg *= 0.2
            elif self.player.cooling_lvl >= 3: base_dmg = 0
            
            self.player.health -= base_dmg
            if self.player.health <= 0: self.game_state = "GAME_OVER"

    def update_fluids(self, dt):
        self.liquid_timer += dt
        if self.liquid_timer < 100: return 
        self.liquid_timer = 0

        px, py = self.player.grid_x, self.player.grid_y
        radius = 15
        for y in range(max(0, py - radius), min(self.grid_height, py + radius)):
            for x in range(max(0, px - radius), min(self.grid_width, px + radius)):
                b = self.world[y][x]
                b_type = b[0]
                fluid_type = BLOCK_TYPES[b_type][6]
                
                if fluid_type == "Liquid":
                    if y + 1 < self.grid_height:
                        below = self.world[y+1][x]
                        if below[0] == "Air":
                            self.world[y+1][x] = b
                            self.world[y][x] = ["Air", 0]
                            continue
                        elif below[0] == "Magma" and b_type == "Water":
                            self.world[y+1][x] = ["Obsidian", BLOCK_TYPES["Obsidian"][2]]
                            self.world[y][x] = ["Air", 0]
                            self.spawn_particles(x, y, (200, 200, 255), 5)
                            self.trigger_shake(5, 15)
                            continue
                    
                    direction = random.choice([-1, 1])
                    if 0 <= x+direction < self.grid_width and self.world[y][x+direction][0] == "Air":
                        self.world[y][x+direction] = b
                        self.world[y][x] = ["Air", 0]
                    elif 0 <= x-direction < self.grid_width and self.world[y][x-direction][0] == "Air":
                        self.world[y][x-direction] = b
                        self.world[y][x] = ["Air", 0]
                        
                elif fluid_type == "Gas":
                    # Gas rises
                    if y > 0:
                        above = self.world[y-1][x]
                        if above[0] == "Air":
                            self.world[y-1][x] = b
                            self.world[y][x] = ["Air", 0]
                            continue
                        elif above[0] == "Magma":
                            self.trigger_gas_explosion(x, y)
                            continue

    def update_depth(self):
        self.player.depth = self.player.grid_y * 10 
        if self.player.depth > self.player.max_depth:
            self.player.max_depth = self.player.depth

    def spawn_particles(self, gx, gy, color, count=5):
        for _ in range(count):
            p = Particle(gx * GRID_SIZE + GRID_SIZE/2, gy * GRID_SIZE + GRID_SIZE/2, color)
            self.particles.append(p)

    def update(self, dt):
        if self.game_state == "PLAYING":
            self.handle_input(dt)
            self.check_gravity_player()
            self.check_radiation(dt)
            self.check_heat(dt)
            self.update_fluids(dt)
            
        for p in self.particles: p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        
        for e in self.explosions: e.update()
        self.explosions = [e for e in self.explosions if e.life > 0]
        
        if self.shake_timer > 0:
            self.shake_timer -= dt
        else:
            self.shake_intensity = 0

    def get_background_color(self):
        depth_ratio = max(0, min(1, self.camera_y / (self.grid_height * GRID_SIZE)))
        if depth_ratio < 0.3:
            t = depth_ratio / 0.3
            r = int(135 * (1-t) + 60 * t)
            g = int(206 * (1-t) + 40 * t)
            b = int(235 * (1-t) + 20 * t)
            return (r, g, b)
        elif depth_ratio < 0.7:
            t = (depth_ratio - 0.3) / 0.4
            r = int(60 * (1-t) + 20 * t)
            g = int(40 * (1-t) + 20 * t)
            b = int(20 * (1-t) + 30 * t)
            return (r, g, b)
        else:
            t = (depth_ratio - 0.7) / 0.3
            r = int(20 * (1-t) + 100 * t)
            g = int(20 * (1-t) + 10 * t)
            b = int(30 * (1-t) + 10 * t)
            return (r, g, b)

    def draw(self):
        bg_color = self.get_background_color()
        screen.fill(bg_color)
        
        cam_x = self.camera_x
        cam_y = self.camera_y
        if self.shake_intensity > 0:
            cam_x += random.randint(-self.shake_intensity, self.shake_intensity)
            cam_y += random.randint(-self.shake_intensity, self.shake_intensity)
        
        start_y = max(0, int(cam_y // GRID_SIZE) - 1)
        end_y = min(self.grid_height, int((cam_y + SCREEN_HEIGHT) // GRID_SIZE) + 1)

        scan_radius = self.player.get_scan_radius()
        valuable_ores = ["Gold", "Diamond", "Uranium", "Oil", "Obsidian", "Core"]

        for y in range(start_y, end_y):
            for x in range(self.grid_width):
                block = self.world[y][x]
                b_type = block[0]
                if b_type != "Air":
                    name, color, max_hp, val, fuel, grav, fluid = BLOCK_TYPES[b_type]
                    rect = pygame.Rect(x * GRID_SIZE - cam_x, y * GRID_SIZE - cam_y, GRID_SIZE, GRID_SIZE)
                    
                    if fluid in ["Liquid", "Gas"] and b_type != "Magma":
                        liquid_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                        alpha = 160 if b_type == "Water" else 200
                        pygame.draw.rect(liquid_surf, (*color, alpha), (0, 0, GRID_SIZE, GRID_SIZE))
                        screen.blit(liquid_surf, rect)
                    elif b_type == "Magma":
                        liquid_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                        alpha = int(180 + math.sin(pygame.time.get_ticks() * 0.01) * 50)
                        pygame.draw.rect(liquid_surf, (*color, alpha), (0, 0, GRID_SIZE, GRID_SIZE))
                        screen.blit(liquid_surf, rect)
                    elif b_type == "Core":
                        # Pulsing white core
                        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2
                        c_color = (int(255 - pulse*100), int(255 - pulse*50), 255)
                        pygame.draw.rect(screen, c_color, rect)
                    else:
                        screen.blit(BLOCK_TEXTURES[b_type], rect)
                        pygame.draw.rect(screen, DARK_GRAY, rect, 1)
                    
                    if block[1] < max_hp and max_hp < 9999 and block[1] > 0:
                        dmg_ratio = block[1] / max_hp
                        pygame.draw.line(screen, BLACK, rect.topleft, rect.bottomright, 2)
                        if dmg_ratio < 0.5: pygame.draw.line(screen, BLACK, rect.topright, rect.bottomleft, 2)
                        if dmg_ratio < 0.25: pygame.draw.line(screen, BLACK, rect.midleft, rect.midright, 2)
                            
                    if b_type == "Uranium":
                        glow_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                        pulse = (math.sin(pygame.time.get_ticks() * 0.01) + 1) / 2
                        pygame.draw.rect(glow_surf, (50, 255, 50, int(50 + pulse * 50)), (0, 0, GRID_SIZE, GRID_SIZE))
                        screen.blit(glow_surf, rect)

                    if scan_radius > 0 and b_type in valuable_ores:
                        dist = math.sqrt((x - self.player.grid_x)**2 + (y - self.player.grid_y)**2)
                        if dist <= scan_radius:
                            pulse = (math.sin(pygame.time.get_ticks() * 0.005 + x + y) + 1) / 2
                            glow_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                            pygame.draw.rect(glow_surf, (255, 255, 255, int(30 + pulse * 50)), (0, 0, GRID_SIZE, GRID_SIZE))
                            screen.blit(glow_surf, rect)
        
        for p in self.particles: p.draw(screen, cam_x, cam_y)
        for e in self.explosions: e.draw(screen, cam_x, cam_y)
        
        self.player.draw(screen, cam_x, cam_y)
        self.draw_hud()
        
        if self.game_state == "SHOP": self.draw_shop()
        if self.game_state == "GAME_OVER": self.draw_game_over()
        if self.game_state == "WIN": self.draw_win()

    def draw_hud(self):
        hud_x = PLAY_AREA_WIDTH
        pygame.draw.rect(screen, DARK_GRAY, (hud_x, 0, HUD_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(screen, WHITE, (hud_x, 0), (hud_x, SCREEN_HEIGHT), 2)

        depth_text = font.render(f"Depth: {self.player.depth} m", True, WHITE)
        screen.blit(depth_text, (hud_x + 20, 20))
        money_text = font.render(f"Minerals: ${self.player.money}", True, YELLOW)
        screen.blit(money_text, (hud_x + 20, 50))

        max_hp = self.player.get_max_health()
        hp_text = font.render(f"HULL ({int(self.player.health)}/{max_hp})", True, WHITE)
        screen.blit(hp_text, (hud_x + 20, 100))
        pygame.draw.rect(screen, BLACK, (hud_x + 20, 130, 360, 20))
        hp_color = GREEN if self.player.health > max_hp*0.5 else YELLOW if self.player.health > max_hp*0.25 else RED
        pygame.draw.rect(screen, hp_color, (hud_x + 20, 130, (self.player.health / max_hp) * 360, 20))

        max_fl = self.player.get_max_fuel()
        fuel_text = font.render(f"FUEL ({int(self.player.fuel)}/{max_fl})", True, WHITE)
        screen.blit(fuel_text, (hud_x + 20, 170))
        pygame.draw.rect(screen, BLACK, (hud_x + 20, 200, 360, 20))
        pygame.draw.rect(screen, ORANGE, (hud_x + 20, 200, (self.player.fuel / max_fl) * 360, 20))

        up_text = title_font.render("EQUIPMENT", True, BLUE)
        screen.blit(up_text, (hud_x + 20, 250))
        
        info_y = 300
        infos = [
            f"Hull Lvl: {self.player.hull_lvl}",
            f"Fuel Lvl: {self.player.fuel_lvl}",
            f"Drill Lvl: {self.player.drill_lvl}",
            f"Cooling Lvl: {self.player.cooling_lvl}",
            f"Scanner Lvl: {self.player.scanner_lvl} (R: {self.player.get_scan_radius()})",
            f"Dynamite: {self.player.bombs}"
        ]
        for info in infos:
            text = font.render(info, True, WHITE)
            screen.blit(text, (hud_x + 20, info_y))
            info_y += 25
            
        shop_hint = font.render("Press [E] for Shop", True, GREEN)
        screen.blit(shop_hint, (hud_x + 20, SCREEN_HEIGHT - 90))
        bomb_hint = font.render("Press [SPACE] for Dynamite", True, ORANGE)
        screen.blit(bomb_hint, (hud_x + 20, SCREEN_HEIGHT - 60))
        quit_hint = font.render("Press [Q] to Quit", True, GRAY)
        screen.blit(quit_hint, (hud_x + 20, SCREEN_HEIGHT - 30))

    def draw_shop(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.set_alpha(220)
        overlay.fill((0,0,0))
        screen.blit(overlay, (0,0))
        
        title = large_font.render("UPGRADE SHOP", True, YELLOW)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        money_text = font.render(f"Current Minerals: ${self.player.money}", True, GREEN)
        screen.blit(money_text, (SCREEN_WIDTH//2 - money_text.get_width()//2, 120))
        
        self.draw_shop_button(1, "Hull Plating", "+50 Max HP", self.player.hull_lvl, 100)
        self.draw_shop_button(2, "Fuel Tank", "+50 Max Fuel", self.player.fuel_lvl, 150)
        self.draw_shop_button(3, "Diamond Drill", "+1 Drill Power", self.player.drill_lvl, 300)
        self.draw_shop_button(4, "Cooling System", "Survive Deep Heat", self.player.cooling_lvl, 400)
        self.draw_shop_button(5, "Mineral Scanner", "Reveal Nearby Ores", self.player.scanner_lvl, 250)
        self.draw_shop_button(6, "Dynamite x3", "Explosive Mining", 1, 200)
        
        inst = font.render("Press [1]-[6] to buy. Press [E] to close.", True, WHITE)
        screen.blit(inst, (SCREEN_WIDTH//2 - inst.get_width()//2, 550))

    def draw_shop_button(self, num, name, desc, level, base_cost):
        cost = base_cost * level
        y_pos = 170 + (num-1) * 60
        
        color = BLUE if self.player.money >= cost else RED
        pygame.draw.rect(screen, color, (SCREEN_WIDTH//2 - 200, y_pos, 400, 45))
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH//2 - 200, y_pos, 400, 45), 2)
        
        text = title_font.render(f"[{num}] {name}", True, WHITE)
        screen.blit(text, (SCREEN_WIDTH//2 - 180, y_pos + 5))
        
        cost_text = font.render(f"${cost} - {desc}", True, WHITE)
        screen.blit(cost_text, (SCREEN_WIDTH//2 + 20, y_pos + 12))

    def buy_upgrade(self, upgrade_type):
        cost = 0
        if upgrade_type == 1:
            cost = 100 * self.player.hull_lvl
            if self.player.money >= cost:
                self.player.money -= cost
                self.player.hull_lvl += 1
                self.player.health += 50 
        elif upgrade_type == 2:
            cost = 150 * self.player.fuel_lvl
            if self.player.money >= cost:
                self.player.money -= cost
                self.player.fuel_lvl += 1
                self.player.fuel += 50 
        elif upgrade_type == 3:
            cost = 300 * self.player.drill_lvl
            if self.player.money >= cost:
                self.player.money -= cost
                self.player.drill_lvl += 1
        elif upgrade_type == 4:
            cost = 400 * max(1, self.player.cooling_lvl)
            if self.player.cooling_lvl == 0: cost = 400
            else: cost = 400 * self.player.cooling_lvl
            if self.player.money >= cost:
                self.player.money -= cost
                self.player.cooling_lvl += 1
        elif upgrade_type == 5:
            if self.player.scanner_lvl == 0: cost = 250
            else: cost = 250 * self.player.scanner_lvl
            if self.player.money >= cost:
                self.player.money -= cost
                self.player.scanner_lvl += 1
        elif upgrade_type == 6:
            cost = 200 
            if self.player.money >= cost:
                self.player.money -= cost
                self.player.bombs += 3

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.set_alpha(220)
        overlay.fill((0,0,0))
        screen.blit(overlay, (0,0))
        
        go_text = large_font.render("DRILL DESTROYED!", True, RED)
        screen.blit(go_text, (SCREEN_WIDTH//2 - go_text.get_width()//2, 200))
        
        stats = font.render(f"Max Depth: {self.player.max_depth}m | Total Minerals: ${self.player.money}", True, WHITE)
        screen.blit(stats, (SCREEN_WIDTH//2 - stats.get_width()//2, 300))
        
        restart_text = font.render("Press [R] to Restart", True, GREEN)
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 400))

    def draw_win(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.set_alpha(220)
        overlay.fill((0,0,0))
        screen.blit(overlay, (0,0))
        
        win_text = large_font.render("THE EARTH'S CORE!", True, YELLOW)
        screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, 200))
        
        stats = font.render(f"You reached the Mantle! Max Depth: {self.player.max_depth}m", True, WHITE)
        screen.blit(stats, (SCREEN_WIDTH//2 - stats.get_width()//2, 300))
        
        restart_text = font.render("Press [R] to Play Again", True, GREEN)
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 400))

def main():
    game = Game()
    running = True
    
    while running:
        dt = clock.tick(60) 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    if game.game_state == "PLAYING": game.game_state = "SHOP"
                    elif game.game_state == "SHOP": game.game_state = "PLAYING"
                
                if game.game_state == "SHOP":
                    if event.key == pygame.K_1: game.buy_upgrade(1)
                    if event.key == pygame.K_2: game.buy_upgrade(2)
                    if event.key == pygame.K_3: game.buy_upgrade(3)
                    if event.key == pygame.K_4: game.buy_upgrade(4)
                    if event.key == pygame.K_5: game.buy_upgrade(5)
                    if event.key == pygame.K_6: game.buy_upgrade(6)
                
                if game.game_state == "PLAYING":
                    if event.key == pygame.K_SPACE:
                        game.use_bomb()
                
                if game.game_state in ["GAME_OVER", "WIN"] and event.key == pygame.K_r:
                    game = Game() 
                    
                if event.key == pygame.K_q:
                    running = False

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()