import pygame
import math
import text
import random

pygame.init()

# debug option, skips levels by pressing enter
skiplevels = False

# colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
yellow = (255, 255, 0)
green = (0, 255, 0)
cyan = (0, 255, 255)
blue = (0, 0, 255)
magenta = (255, 0, 255)

# display constants
res_x = 800
res_y = 576
fps = 60

# create the list of levels
from os import listdir
from os.path import isfile, join
leveldir = "./levels"
levels = [leveldir + "/" + f for f in listdir(leveldir) if isfile(join(leveldir, f))]

gameDisplay = pygame.display.set_mode((res_x, res_y))
pygame.display.set_caption('don\'t touch the sides')
clock = pygame.time.Clock()

class Entity(pygame.sprite.Sprite):
	def __init__(self):
		pygame.sprite.Sprite.__init__(self)
		
class Ship(Entity):
	def __init__(self, pos_x, pos_y):
		Entity.__init__(self)
		self.ship_size = 16
		self.pos_x = pos_x
		self.pos_y = pos_y
		self.vel_x = 0.0
		self.vel_y = 0.0
		self.accel_x = 0.0
		self.accel_y = 0.0
		self.mass = 3
		self.max_accel = 1
		self.trail = [[pos_x, pos_y]]
		self.trail_len = 20
		self.hitbox = pygame.Rect(self.pos_x-self.ship_size/2, self.pos_y-self.ship_size/2, self.ship_size, self.ship_size)

	def update(self, lkey, rkey, ukey, dkey, spacebar):
		if not spacebar:
			self.accel_x = self.max_accel*(int(rkey) - int(lkey))
			self.accel_y = self.max_accel*(int(dkey) - int(ukey))
		else:
			self.accel_x = -self.vel_x
			self.accel_y = -self.vel_y
			scale = self.max_accel/2
			if abs(self.accel_x) > self.max_accel:
				scale = abs(self.accel_x)
			elif abs(self.accel_y) > self.max_accel:
				scale = abs(self.accel_y)
			self.accel_x *= self.max_accel/scale
			self.accel_y *= self.max_accel/scale
			# print ('acceleration: ({0},{1}); velocity: ({2},{3})'.format(self.accel_x, self.accel_y, self.vel_x, self.vel_y))
		self.vel_x += self.accel_x/self.mass
		self.vel_y += self.accel_y/self.mass
		if abs(self.vel_x) < 0.05:
			self.vel_x = 0
		if abs(self.vel_y) < 0.05:
			self.vel_y = 0
		
		self.pos_x += self.vel_x
		self.pos_y += self.vel_y
		self.hitbox.center = (self.pos_x, self.pos_y)
		self.trail.append([self.pos_x, self.pos_y])
		if len(self.trail) > self.trail_len:
			del self.trail[0]
	
	def collide(self, walls):
		for w in walls:
			if w.hitbox.colliderect(self.hitbox):
				if w.color == white:
					return True
				elif w.color == red or w.color == blue:
					if w.opened == False:
						return True
	
	def switchCheck(self, switches):
		for s in switches:
			if s.hitbox.colliderect(self.hitbox):
				if s.color == red or s.color == blue:
					s.flipped = True
	
	def draw(self):
		if len(self.trail) > 1:
			pygame.draw.lines(gameDisplay, white, False, self.trail)
		drawShip(self.pos_x, self.pos_y, self.accel_x, self.accel_y, self.ship_size)

class Wall(Entity):
	def __init__(self, x, y, wid, hi):
		Entity.__init__(self)
		self.x = x
		self.y = y
		self.wid = wid
		self.hi = hi
		self.color = white
		self.hitbox = pygame.Rect(x, y, wid, hi)
		self.leftline = False
		self.rightline = False
		self.upline = False
		self.downline = False
		self.upleft = False
		self.upright = False
		self.downleft = False
		self.downright = False
	
	def draw(self, ship_xy):
		#pygame.draw.rect(gameDisplay, self.color, [self.x, self.y, self.wid, self.hi])
		diff_x = ship_xy[0] - self.x
		diff_y = ship_xy[1] - self.y
		diff_x *= diff_x
		diff_y *= diff_y
		#thickness = int(40000/(diff_x+diff_y))
		thickness = 2
		if thickness > 8:
			thickness = 8
		if self.leftline:
			gameDisplay.fill(white, pygame.Rect([self.x, self.y, thickness, self.hi]))
		if self.rightline:
			gameDisplay.fill(white, pygame.Rect([self.x+self.wid-thickness, self.y, thickness, self.hi]))
		if self.upline:
			gameDisplay.fill(white, pygame.Rect([self.x, self.y, self.wid, thickness]))
		if self.downline:
			gameDisplay.fill(white, pygame.Rect([self.x, self.y+self.hi-thickness, self.wid, thickness]))
		if self.upleft:
			gameDisplay.fill(white, pygame.Rect([self.x, self.y, thickness, thickness]))
		if self.upright:
			gameDisplay.fill(white, pygame.Rect([self.x+self.wid-thickness, self.y, thickness, thickness]))
		if self.downleft:
			gameDisplay.fill(white, pygame.Rect([self.x, self.y+self.hi-thickness, thickness, thickness]))
		if self.downright:
			gameDisplay.fill(white, pygame.Rect([self.x+self.wid-thickness, self.y+self.hi-thickness, thickness, thickness]))

		
# doors work as follows:
# - blue doors are tied to blue switches. flip all the blue switches to open all the blue doors
# - red doors work the same as blue doors, except with red switches
# - yellow doors alternate between open and closed on a timer. They can start open or closed, and alternate in turn
# - green doors and magenta doors are paired. Hit a green switch to open all green doors and close all magenta doors. 
#    hit a magenta switch to do the opposite. if you hit a green switch, it disables all green switches and enables 
#    all magenta switches, and vice versa. magenta doors start open, and green doors start closed

class Door(Entity):
	def __init__(self, x, y, wid, hi, color):
		Entity.__init__(self)
		self.x = x
		self.y = y
		self.wid = wid
		self.hi = hi
		self.hitbox = pygame.Rect(x, y, wid, hi)
		self.color = color
		self.opened = False
		
	def draw(self):
		if not self.opened:
			pygame.draw.rect(gameDisplay, self.color, [self.x, self.y, self.wid, self.hi])
		else:
			pygame.draw.rect(gameDisplay, self.color, [self.x, self.y, self.wid, self.hi], 1)
	
class Switch(Entity):
	def __init__(self, x, y, wid, hi, color):
		Entity.__init__(self)
		self.x = x
		self.y = y
		self.wid = wid
		self.hi = hi
		self.hitbox = pygame.Rect(x, y, wid, hi)
		self.color = color
		self.flipped = False
		self.font = pygame.font.SysFont('Arial Black', 14)

	def draw(self):
		if not self.flipped:
			pygame.draw.rect(gameDisplay, self.color, [self.x, self.y, self.wid, self.hi])
		else:
			pygame.draw.rect(gameDisplay, self.color, [self.x, self.y, self.wid, self.hi], 1)
		switchtext = self.font.render('!', True, white)
		gameDisplay.blit(switchtext, (self.x+5+int(self.color == blue), self.y-3))
		
class Scene(object):
	def __init__(self):
		pass
		
	def render(self):
		raise NotImplementedError
		
	def update(self):
		raise NotImplementedError
		
	def handle_events(self, events):
		raise NotImplementedError
		
class TitleScene(Scene):
	def __init__(self):
		super(TitleScene, self).__init__()
		self.framecount = 0
		self.entities = pygame.sprite.Group()
		self.ship = Ship(res_x/2, res_y/2)
		self.entities.add(self.ship)
	
	def render(self):
		gameDisplay.fill(black)
		self.ship.draw()
		flashtimer = 40
		if (self.framecount % flashtimer < flashtimer/2):
			entercolor = yellow
		else:
			entercolor = blue
		wasdcolor = magenta
		arrowcolor = magenta
		spacebarcolor = magenta
		
		y_line = 67
		wid_str = text.sizeString("don't touch the sides",6)[0]
		x_start = (res_x - wid_str)/2
		x_next = text.placeString(gameDisplay, "don't touch the sides", white, x_start, y_line, 6)

		
		linespace = 48
		
		y_line = 320
		wid_str = text.sizeString("wasd or <_^> to move")[0]
		x_start = (res_x - wid_str)/2
		x_next = text.placeString(gameDisplay, "wasd", wasdcolor, x_start, y_line)
		x_next = text.placeString(gameDisplay, "or", white, x_next, y_line)
		x_next = text.placeString(gameDisplay, "<_^>", arrowcolor, x_next, y_line)
		x_next = text.placeString(gameDisplay, "to", white, x_next, y_line)
		x_next = text.placeString(gameDisplay, "move", green, x_next, y_line)
		
		y_line += linespace
		wid_str = text.sizeString("spacebar to stop")[0]
		x_start = (res_x - wid_str)/2
		x_next = text.placeString(gameDisplay, "spacebar", spacebarcolor, x_start, y_line)
		x_next = text.placeString(gameDisplay, "to", white, x_next, y_line)
		x_next = text.placeString(gameDisplay, "stop", red, x_next, y_line)

		y_line += linespace
		wid_str = text.sizeString("find the exit in each level")[0]
		x_start = (res_x - wid_str)/2
		x_next = text.placeString(gameDisplay, "find the exit", cyan, x_start, y_line)
		x_next = text.placeString(gameDisplay, "in each level", white, x_next, y_line)

		y_line += linespace
		wid_str = text.sizeString("press enter/return to begin")[0]
		x_start = (res_x - wid_str)/2
		x_next = text.placeString(gameDisplay, "press", white, x_start, y_line)
		x_next = text.placeString(gameDisplay, "enter/return", entercolor, x_next, y_line)
		x_next = text.placeString(gameDisplay, "to begin", white, x_next, y_line)

	def update(self):
		self.framecount += 1
		pressed = pygame.key.get_pressed()
		left, right, up, down, wkey, akey, skey, dkey, spacebar, escape, enter = [pressed[key] for key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN)]
		if enter:
			self.manager.go_to(GameScene(0))
		if escape:
			self.ship = Ship(res_x/2, res_y/2)
		self.ship.update(left or akey, right or dkey, up or wkey, down or skey, spacebar)
		
	def handle_events(self, events):
		for e in events:
			pass

class GameScene(Scene):
	def __init__(self, levelno):
		super(GameScene, self).__init__()
		self.ispaused = False
		self.pausedelay = 0
		self.framecount = 0
		self.levelno = levelno
		self.entities = pygame.sprite.Group()
		self.walls = []
		self.doors = []
		self.switches = []
		self.pausecolors = [red, yellow, green, cyan, blue, magenta]
		level_tiles = loadLevel(levels[levelno])
		for y in range (0, len(level_tiles)):
			for x in range (0, len(level_tiles[0])):
				tile = level_tiles[y][x]
				if tile == "S" and level_tiles[y+1][x] == "S" and level_tiles[y][x+1] == "S":
					self.spawn_x = (x+1)*8
					self.spawn_y = (y+1)*8
				elif tile == "W":
					w = Wall(x*8, y*8, 8, 8)
					if x == 0 or level_tiles[y][x-1] != "W":
						w.leftline = True
					if x == len(level_tiles[0])-1 or level_tiles[y][x+1] != "W":
						w.rightline = True
					if y == 0 or level_tiles[y-1][x] != "W":
						w.upline = True
					if y == len(level_tiles)-1 or level_tiles[y+1][x] != "W":
						w.downline = True
					if x != 0 and y != 0 and level_tiles[y][x-1] == "W" and level_tiles[y-1][x] == "W" and level_tiles[y-1][x-1] != "W":
						w.upleft = True
					if x != len(level_tiles[0])-1 and y != 0 and level_tiles[y][x+1] == "W" and level_tiles[y-1][x] == "W" and level_tiles[y-1][x+1] != "W":
						w.upright = True
					if x != 0 and y != len(level_tiles)-1 and level_tiles[y][x-1] == "W" and level_tiles[y+1][x] == "W" and level_tiles[y+1][x-1] != "W":
						w.downleft = True
					if x != len(level_tiles[0])-1 and y != len(level_tiles)-1 and level_tiles[y][x+1] == "W" and level_tiles[y+1][x] == "W" and level_tiles[y+1][x+1] != "W":
						w.downright = True
					self.walls.append(w)
					self.entities.add(w)
				elif tile == "R":
					d = Door(x*8, y*8, 8, 8, red)
					self.doors.append(d)
					self.entities.add(d)
				elif tile == "r" and level_tiles[y+1][x] == "r" and level_tiles[y][x+1] == "r":
					s = Switch(x*8, y*8, 16, 16, red)
					self.switches.append(s)
					self.entities.add(s)
				elif tile == "B":
					d = Door(x*8, y*8, 8, 8, blue)
					self.doors.append(d)
					self.entities.add(d)
				elif tile == "b" and level_tiles[y+1][x] == "b" and level_tiles[y][x+1] == "b":
					s = Switch(x*8, y*8, 16, 16, blue)
					self.switches.append(s)
					self.entities.add(s)
		self.ship = Ship(self.spawn_x, self.spawn_y)
		self.entities.add(self.ship)
		self.reddoorsopen = False
		self.bluedoorsopen = False
		self.yellowdoorsparity = False
		self.greendoorsopen = False
	
	def render(self):
		gameDisplay.fill(black)
		for w in self.walls:
			w.draw((self.ship.pos_x, self.ship.pos_y))
		for d in self.doors:
			d.draw()
		for s in self.switches:
			s.draw()
		if not self.ispaused:
			self.ship.draw()
		else:
			wid_str, hi_str = text.sizeString("pause",8)
			x_next = (res_x - wid_str)/2
			y_line = (res_y - hi_str)/2
			x_next = text.placeString(gameDisplay, "pause", yellow, x_next, y_line, 8)
			
		
	def update(self):
		pressed = pygame.key.get_pressed()
		left, right, up, down, wkey, akey, skey, dkey, spacebar, escape, enter = [pressed[key] for key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN)]
		if self.ispaused:
			if escape and self.pauseframes > 15:
				self.ispaused = False
				self.pausedelay = 15
			self.pauseframes += 1
		else:
			self.reddoorsopen = True
			self.bluedoorsopen = True
			for s in self.switches:
				if s.color == red and s.flipped == False:
					self.reddoorsopen = False
				elif s.color == blue and s.flipped == False:
					self.bluedoorsopen = False
			if self.reddoorsopen:
				for d in self.doors:
					if d.color == red:
						d.opened = True
			if self.bluedoorsopen:
				for d in self.doors:
					if d.color == blue:
						d.opened = True
			if self.framecount > 15:
				self.ship.update(left or akey, right or dkey, up or wkey, down or skey, spacebar)
			self.ship.switchCheck(self.switches)
			dead = self.ship.collide(self.walls + self.doors)
			if dead:
				self.manager.go_to(GameScene(self.levelno))
			if escape and self.pausedelay <= 0:
				#self.manager.go_to(TitleScene())
				self.ispaused = True
				self.pauseframes = 0
				
			# level is considered beaten when the ship leaves the window range. If this happens, go to the next level
			if self.ship.pos_x > (res_x + self.ship.ship_size) or self.ship.pos_x < (0 - self.ship.ship_size) or self.ship.pos_y > (res_y + self.ship.ship_size) or self.ship.pos_y < (0 - self.ship.ship_size) or (enter and self.framecount > 15 and skiplevels == True):
				self.manager.go_to(GameScene(self.levelno + 1))
			self.framecount += 1
			if self.pausedelay > 0:
				self.pausedelay -= 1
		
	def handle_events(self, events):
		for e in events:
			pass
				
class SceneManager(object):
	def __init__(self):
		self.go_to(TitleScene())
		
	def go_to(self, scene):
		self.scene = scene
		self.scene.manager = self
	
def loadLevel(levelimg):
	file = open(levelimg, 'rb')
	fileoffset = 0x436
	width = 100
	height = 72
	pixellist = []
	file.seek(fileoffset)
	for x in range (0,height):
		temp = file.read(width)
		pixellist = [temp] + pixellist
	
	# tile constants for loading a level from bmp
	spawntile = b'\xff'
	bgtile = b'\x00'
	walltile = b'\xa4'
	bluedoortile = b'\xe8'
	blueswitchtile = b'\x09'
	reddoortile = b'\x4f'
	redswitchtile = b'\xef'
	yellowdoorclosedtile = b'\xfb'
	yellowdooropentile = b'\x08'
	greendoortile = b'\x71'
	greenswitchtile = b'\x3E'
	magentadoortile = b'\xd5'
	magentaswitchtile = b'\x07'

	level = []
	for row in pixellist:
		str = []
		splitrow = [row[i:i+1] for i in range(0, len(row))]
		for col in splitrow:
			if col == spawntile:
				str += ["S"]
			elif col == walltile:
				str += ["W"]
			elif col == reddoortile:
				str += ["R"]
			elif col == redswitchtile:
				str += ["r"]
			elif col == bluedoortile:
				str += ["B"]
			elif col == blueswitchtile:
				str += ["b"]
			elif col == yellowdoorclosedtile:
				str += ["Y"]
			elif col == yellowdooropentile:
				str += ["y"]
			elif col == greendoortile:
				str += ["G"]
			elif col == greenswitchtile:
				str += ["g"]
			elif col == magentadoortile:
				str += ["M"]
			elif col == magentaswitchtile:
				str += ["m"]
			else:
				str += [" "]
		
		level.append(str)
		
	return level

def drawShip(pos_x, pos_y, accel_x, accel_y, ship_size):
	if accel_x > 0:
		pos_plume_x_x = pos_x-ship_size/2
	elif accel_x < 0:
		pos_plume_x_x = pos_x+ship_size/2
	else:
		pos_plume_x_x = pos_x
	pos_plume_x_y = pos_y-ship_size/4
	
	if accel_y > 0:
		pos_plume_y_y = pos_y-ship_size/2
	elif accel_y < 0:
		pos_plume_y_y = pos_y+ship_size/2
	else:
		pos_plume_y_y = pos_y
	pos_plume_y_x = pos_x-ship_size/4
	
	l_plume_x = -accel_x*ship_size/2
	w_plume_x = ship_size/2
	l_plume_y = -accel_y*ship_size/2
	w_plume_y = ship_size/2
	
	pygame.draw.rect(gameDisplay, cyan, [pos_plume_x_x, pos_plume_x_y, l_plume_x, w_plume_x])
	pygame.draw.rect(gameDisplay, cyan, [pos_plume_y_x, pos_plume_y_y, w_plume_y, l_plume_y])
	pygame.draw.rect(gameDisplay, white, [pos_x-ship_size/4, pos_y-ship_size/2, ship_size/2, ship_size])
	pygame.draw.rect(gameDisplay, white, [pos_x-ship_size/2, pos_y-ship_size/4, ship_size, ship_size/2])
	
def gameLoop():
	gameExit = False
	
	manager = SceneManager()
	
	while not gameExit:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				gameExit = True
		
		manager.scene.handle_events(pygame.event.get())
		manager.scene.update()
		manager.scene.render()
		pygame.display.update()
		clock.tick(fps)
		
	pygame.quit()
	quit()
	
gameLoop()
