from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

camera_pos = (0, -800, 400)
fovY = 60
ROAD_LENGTH = 1200
LANE_WIDTH = 150

# Camera system variables
camera_mode = "third_person"  # "third_person" or "first_person"
THIRD_PERSON_POS = (0, -800, 400)
first_person_offset = (0, -20, 50)  # Offset from car position for first person view

# Game variables
player_lane = 0
player_x = 0
target_x = 0
player_z = -200
game_speed = 1.0
score = 0
gameover = False
game_paused = False
quit_game = False

# Track total distance traveled for rain positioning
total_distance_traveled = 0

# Smooth movement variables
TRANSITION_SPEED = 8
is_transitioning = False

# Coin and Turbo system with time-based system
coins_collected = 0
coins = []
turbo_active = False
turbo_start_time = 0  # When turbo was activated
TURBO_DURATION = 5.0  # Boost lasts 5 seconds
COINS_FOR_TURBO = 5
turbo_available = False

# Dynamic lists for moving objects
enemy_vehicles = []
dynamic_trees = []

# Game timing and spacing
marker_offset = 0
spawn_timer = 0
coin_spawn_timer = 0
MIN_SPAWN_DISTANCE = 200
MIN_LANE_GAP = 300
TREE_DISTANCE_FROM_ROAD = 200
NUM_TREES = 40
TREE_LOOP_LENGTH = NUM_TREES * 100

# Weather system variables
weather_mode = "day"  # "day", "night", "rain", "sunny"
weather_transition_timer = 0
WEATHER_CYCLE_TIME = 300  # Change weather every 300 frames

# Rain system variables
rain_particles = []
NUM_RAIN_PARTICLES = 500
RAIN_SPEED = 8
RAIN_RANGE = 1000  # Horizontal and depth range around camera


class EnemyVehicle:

    def __init__(self, lane, z_pos):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.z = z_pos
        self.color = (random.uniform(0.2, 1.0), random.uniform(0.2, 1.0), random.uniform(0.2, 1.0))
        # Give each enemy its own speed relative to the road
        self.relative_speed = random.uniform(-0.4, 0.4)
        self.original_relative_speed = self.relative_speed  # Store original speed
        self.lane_change_timer = 0  # Timer for lane changing

    def update(self):
        # The enemy's speed is the game_speed plus its own relative speed
        effective_speed = game_speed + self.relative_speed

        if turbo_active:
            # During turbo, its speed is also multiplied
            self.z -= effective_speed * 2
        else:
            self.z -= effective_speed

        # Update lane change timer
        if self.lane_change_timer > 0:
            self.lane_change_timer -= 1

    def is_off_screen(self):
        return self.z < -400

    def can_change_lane(self, new_lane, enemy_list):
        #Checking if this enemy can safely change to a new lane
        if new_lane < -1 or new_lane > 1:
            return False

        # Checking if there's space in the new lane
        for other in enemy_list:
            if other != self and other.lane == new_lane:
                distance = abs(other.z - self.z)
                if distance < 120:  # Need more space for lane changes
                    return False
        return True


class Coin:

    def __init__(self, lane, z_pos):
        self.lane = lane
        self.x = lane * LANE_WIDTH
        self.z = z_pos
        self.rotation = 0

    def update(self):
        if turbo_active:
            self.z -= game_speed * 2
        else:
            self.z -= game_speed
        self.rotation += 3  # Coin spinning speed

    def is_off_screen(self):
        return self.z < -400


class RainParticle:

    def __init__(self):
        self.offset_x = random.uniform(-RAIN_RANGE, RAIN_RANGE)
        self.offset_y = random.uniform(-RAIN_RANGE, RAIN_RANGE)
        self.z = random.uniform(0, 400)
        self.speed = random.uniform(RAIN_SPEED * 0.8, RAIN_SPEED * 1.2)

    def update(self):
        self.z -= self.speed
        current_speed = game_speed * 2 if turbo_active else game_speed
        self.offset_y -= current_speed * 0.5
        if self.z < -50 or self.offset_y < -RAIN_RANGE:
            self.reset()

    def reset(self):
        self.offset_x = random.uniform(-RAIN_RANGE, RAIN_RANGE)
        self.offset_y = random.uniform(RAIN_RANGE * 0.5, RAIN_RANGE)
        self.z = random.uniform(300, 400)

    def get_world_position(self):
        cam_x, cam_y, cam_z = camera_pos
        return cam_x + self.offset_x, cam_y + self.offset_y, self.z


def toggle_camera():
    global camera_mode, camera_pos
    if camera_mode == "third_person":
        camera_mode = "first_person"
    else:
        camera_mode = "third_person"
        camera_pos = THIRD_PERSON_POS
    print(f"TERMINAL: Camera changed to {camera_mode.replace('_', ' ').title()}")


def update_first_person_camera():
    global camera_pos
    if camera_mode == "first_person":
        cam_x = player_x + first_person_offset[0]
        cam_y = player_z + first_person_offset[1]
        cam_z = first_person_offset[2]
        camera_pos = (cam_x, cam_y, cam_z)


def update_player_position():
    global player_x, is_transitioning
    distance = target_x - player_x
    if abs(distance) < 2.0:
        player_x = target_x
        is_transitioning = False
    else:
        player_x += distance * TRANSITION_SPEED * 0.02
        is_transitioning = True


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_coin(coin):
    glPushMatrix()
    glTranslatef(coin.x, coin.z, 25)
    glRotatef(coin.rotation, 0, 0, 1)
    glColor3f(1.0, 0.8, 0.0)
    glScalef(1.0, 1.0, 0.3)
    glutSolidCube(30)
    glPopMatrix()


def get_turbo_fill_ratio():
    if turbo_active:
        elapsed_time = time.time() - turbo_start_time
        remaining_time = TURBO_DURATION - elapsed_time
        return max(0, remaining_time / TURBO_DURATION)
    elif turbo_available:
        return 1.0
    else:
        return min(1.0, coins_collected / COINS_FOR_TURBO)


def draw_turbo_bar():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(750, 720)
    glVertex2f(950, 720)
    glVertex2f(950, 740)
    glVertex2f(750, 740)
    glEnd()
    fill_ratio = get_turbo_fill_ratio()
    fill_width = 200 * fill_ratio

    if turbo_available:
        glColor3f(0.0, 1.0, 0.0)
    elif turbo_active:
        glColor3f(1.0, 0.3, 0.0)
    else:
        glColor3f(0.0, 0.5, 1.0)

    glBegin(GL_QUADS)
    glVertex2f(750, 720)
    glVertex2f(750 + fill_width, 720)
    glVertex2f(750 + fill_width, 740)
    glVertex2f(750, 740)
    glEnd()
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def spawn_coin():
    global coin_spawn_timer
    if coin_spawn_timer > 0:
        coin_spawn_timer -= 1
        return
    occupied_lanes = [enemy.lane for enemy in enemy_vehicles if enemy.z > 400]
    available_lanes = [lane for lane in [-1, 0, 1] if lane not in occupied_lanes]

    if available_lanes and random.uniform(0, 1) < 0.3:
        num_coins = 2 if random.uniform(0, 1) > 0.8 and len(available_lanes) > 1 else 1
        for _ in range(num_coins):
            if not available_lanes:
                break
            lane = random.choice(available_lanes)
            coins.append(Coin(lane, 800))
            available_lanes.remove(lane)
    coin_spawn_timer = random.randint(100, 140)


def update_coins():
    global score, coins_collected, turbo_available
    for coin in coins[:]:
        coin.update()
        if coin.is_off_screen():
            coins.remove(coin)
            continue

        player_lane_approx = round(player_x / LANE_WIDTH)

        if coin.lane == player_lane_approx and abs(coin.z - player_z) < 50:
            coins.remove(coin)
            score += 2
            if not turbo_active:
                coins_collected += 1
                if coins_collected >= COINS_FOR_TURBO:
                    turbo_available = True
                    print("Turbo is now available!")


def activate_turbo():
    global turbo_active, turbo_start_time, turbo_available
    if turbo_available and not turbo_active:
        turbo_active = True
        turbo_start_time = time.time()
        turbo_available = False
        print("Turbo activated!")


def update_turbo():
    global turbo_active, coins_collected
    if turbo_active and (time.time() - turbo_start_time >= TURBO_DURATION):
        turbo_active = False
        coins_collected = 0
        print("Turbo finished!")


def initialize_dynamic_trees():
    global dynamic_trees
    dynamic_trees = []
    tree_spacing = TREE_LOOP_LENGTH / NUM_TREES
    for i in range(NUM_TREES):
        x = (-300 - TREE_DISTANCE_FROM_ROAD if i % 2 == 0 else 300 + TREE_DISTANCE_FROM_ROAD) + random.randint(-50, 50)
        z = -ROAD_LENGTH + i * tree_spacing
        dynamic_trees.append([x, z])


def update_dynamic_trees():
    speed_multiplier = 2 if turbo_active else 1
    for tree in dynamic_trees:
        tree[1] -= game_speed * speed_multiplier
        if tree[1] < -ROAD_LENGTH - 100:
            tree[1] += TREE_LOOP_LENGTH
            tree[0] = (-300 - TREE_DISTANCE_FROM_ROAD if tree[0] < 0
                       else 300 + TREE_DISTANCE_FROM_ROAD) + random.randint(-50, 50)


def draw_tree(x, z):
    glPushMatrix()
    glTranslatef(x, z, 0)
    glColor3f(0.6, 0.3, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glScalef(0.3, 0.3, 1.5)
    glutSolidCube(60)
    glPopMatrix()
    glColor3f(0.1, 0.6, 0.1)
    glTranslatef(0, 0, 100)
    gluSphere(gluNewQuadric(), 50, 8, 8)
    glPopMatrix()


def draw_trees():
    for x, z in dynamic_trees:
        draw_tree(x, z)


def draw_road():
    road_color = get_weather_road_color()
    glColor3f(*road_color)
    glBegin(GL_QUADS)
    glVertex3f(-300, -ROAD_LENGTH, 0)
    glVertex3f(300, -ROAD_LENGTH, 0)
    glVertex3f(300, ROAD_LENGTH, 0)
    glVertex3f(-300, ROAD_LENGTH, 0)
    glEnd()
    grass_color = get_weather_grass_color()
    glColor3f(*grass_color)
    glBegin(GL_QUADS)
    glVertex3f(-800, -ROAD_LENGTH, 0)
    glVertex3f(-300, -ROAD_LENGTH, 0)
    glVertex3f(-300, ROAD_LENGTH, 0)
    glVertex3f(-800, ROAD_LENGTH, 0)
    glVertex3f(300, -ROAD_LENGTH, 0)
    glVertex3f(800, -ROAD_LENGTH, 0)
    glVertex3f(800, ROAD_LENGTH, 0)
    glVertex3f(300, ROAD_LENGTH, 0)
    glEnd()
    speed_multiplier = 2 if turbo_active else 1
    glColor3f(1, 1, 0)

    for z_pos in range(-ROAD_LENGTH, ROAD_LENGTH, 100):
        marker_z = z_pos + marker_offset
        if -ROAD_LENGTH <= marker_z <= ROAD_LENGTH:
            glBegin(GL_QUADS)
            glVertex3f(-75, marker_z, 1)
            glVertex3f(-75, marker_z + 50, 1)
            glVertex3f(-65, marker_z + 50, 1)
            glVertex3f(-65, marker_z, 1)
            glVertex3f(65, marker_z, 1)
            glVertex3f(65, marker_z + 50, 1)
            glVertex3f(75, marker_z + 50, 1)
            glVertex3f(75, marker_z, 1)
            glEnd()


def draw_player_car():
    if camera_mode == "third_person":
        glPushMatrix()
        glTranslatef(player_x, player_z, 12)
        glPushMatrix()
        if turbo_active:
            glColor3f(1.0, 0.5, 0.0)  # Bright orange for turbo
        else:
            glColor3f(0.0, 0.4, 0.8)  # Standard blue

        glTranslatef(0, 0, 8)
        glScalef(1.2, 2.0, 0.8)
        glutSolidCube(30)
        glPopMatrix()
        glPushMatrix()
        if turbo_active:
            glColor3f(1.0, 0.8, 0.0)
        else:
            glColor3f(0.6, 0.8, 1.0)

        glTranslatef(0, 0, 25)
        glScalef(0.8, 1.0, 0.7)
        glutSolidCube(30)
        glPopMatrix()
        glColor3f(0.1, 0.1, 0.1)

        wheel_positions = [
            [12, 25],  # Front-right
            [-20, 25],  # Front-left
            [12, -25],  # Rear-right
            [-20, -25]  # Rear-left
        ]

        quad = gluNewQuadric()

        for x_pos, y_pos in wheel_positions:
            glPushMatrix()
            glTranslatef(x_pos, y_pos, 0)
            glRotatef(90, 0, 1, 0)
            gluCylinder(quad, 10, 10, 8, 12, 1)
            gluDisk(quad, 0, 10, 12, 1)
            glTranslatef(0, 0, 8)
            gluDisk(quad, 0, 10, 12, 1)

            glPopMatrix()

        glPopMatrix()


def draw_enemy_vehicle(enemy):
    glPushMatrix()
    glTranslatef(enemy.x, enemy.z, 0)
    glColor3f(*enemy.color)
    glPushMatrix()
    glTranslatef(0, 0, 20)
    glScalef(1.6, 3.0, 0.6)
    glutSolidCube(30)
    glPopMatrix()
    glColor3f(enemy.color[0] * 0.7, enemy.color[1] * 0.7, enemy.color[2] * 0.7)
    glPushMatrix()
    glTranslatef(0, 5, 35)
    glScalef(1.2, 1.8, 0.8)
    glutSolidCube(25)
    glPopMatrix()
    glColor3f(0.6, 0.6, 0.6)
    glPushMatrix()
    glTranslatef(0, 47, 15)
    glScalef(1.4, 0.5, 0.4)
    glutSolidCube(20)
    glPopMatrix()
    glColor3f(1, 1, 0.9)
    glPushMatrix()
    glTranslatef(-18, 49, 15)
    gluSphere(gluNewQuadric(), 5, 6, 6)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(18, 49, 15)
    gluSphere(gluNewQuadric(), 5, 6, 6)
    glPopMatrix()
    glColor3f(0.8, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(-15, -47, 18)
    gluSphere(gluNewQuadric(), 4, 6, 6)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(15, -47, 18)
    gluSphere(gluNewQuadric(), 4, 6, 6)
    glPopMatrix()
    glColor3f(0.1, 0.1, 0.1)
    glPushMatrix()
    glTranslatef(-20, 22, 5)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 10, 10, 5, 8, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(20, 22, 5)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 10, 10, 5, 8, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-20, -22, 5)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 10, 10, 5, 8, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(20, -22, 5)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 10, 10, 5, 8, 1)
    glPopMatrix()
    glPopMatrix()


def find_safe_spawn_lane():
    available_lanes = [lane for lane in [-1, 0, 1] if all(
        not (enemy.lane == lane and abs(enemy.z - 800) < MIN_SPAWN_DISTANCE) and not (
                abs(enemy.lane - lane) == 1 and abs(enemy.z - 800) < MIN_LANE_GAP) for enemy in enemy_vehicles)]
    return random.choice(available_lanes) if available_lanes else None


def spawn_enemy():
    global spawn_timer
    if spawn_timer > 0:
        spawn_timer -= 1
        return
    if len(enemy_vehicles) < 2:
        safe_lane = find_safe_spawn_lane()
        if safe_lane is not None:
            enemy_vehicles.append(EnemyVehicle(safe_lane, 800))
            spawn_timer = random.randint(80, 150)
        else:
            spawn_timer = 20


def update_enemies():
    global score

    # Handle collision avoidance between enemies
    for i, enemy in enumerate(enemy_vehicles):
        # Reset speed to original
        enemy.relative_speed = enemy.original_relative_speed

        # Check for cars in front in the same lane
        cars_in_front = []
        for j, other in enumerate(enemy_vehicles):
            if (i != j and other.lane == enemy.lane and
                    other.z > enemy.z):  # other car is in front
                cars_in_front.append(other)

        # Find the closest car in front
        if cars_in_front:
            closest = min(cars_in_front, key=lambda car: car.z - enemy.z)
            distance = closest.z - enemy.z

            # If too close, take action
            if distance < 90:  # Safe following distance
                # Try to change lanes
                lane_changed = False
                if enemy.lane_change_timer == 0:  # Can attempt lane change
                    # Try left lane first, then right
                    for new_lane in [enemy.lane - 1, enemy.lane + 1]:
                        if enemy.can_change_lane(new_lane, enemy_vehicles):
                            enemy.lane = new_lane
                            enemy.x = new_lane * LANE_WIDTH
                            enemy.lane_change_timer = 60  # Wait before next lane change
                            lane_changed = True
                            break

                # If can't change lanes, slow down
                if not lane_changed:
                    # Match the speed of the car in front, but slightly slower
                    enemy.relative_speed = min(enemy.relative_speed,
                                               closest.relative_speed - 0.2)
                    # Don't go too slow
                    enemy.relative_speed = max(enemy.relative_speed, -0.8)

    # Update all enemy positions
    for enemy in enemy_vehicles[:]:
        enemy.update()
        if enemy.is_off_screen():
            enemy_vehicles.remove(enemy)
            score += 1


def check_collision():
    global gameover
    if turbo_active:
        return
    player_lane_approx = round(player_x / LANE_WIDTH)
    for enemy in enemy_vehicles:
        if enemy.lane == player_lane_approx and abs(enemy.z - player_z) < 80:
            gameover = True
            print(f"GAME OVER! Score: {score}")
            print("Press 'R' to restart or 'Q' to quit the game")
            break


def update_game():
    global marker_offset, total_distance_traveled
    if not gameover and not game_paused:
        speed_multiplier = 2 if turbo_active else 1
        distance_this_frame = game_speed * speed_multiplier
        total_distance_traveled += distance_this_frame
        marker_offset -= distance_this_frame
        if marker_offset <= -100:
            marker_offset = 0
        spawn_enemy()
        update_enemies()
        spawn_coin()
        update_coins()
        update_dynamic_trees()
        update_player_position()
        update_first_person_camera()
        update_turbo()
        update_weather()
        check_collision()


def reset_game():
    globals().update(
        player_lane=0, player_x=0, target_x=0, score=0, gameover=False,
        game_speed=1.0, is_transitioning=False, spawn_timer=0, marker_offset=0,
        coins_collected=0, coins=[], turbo_active=False, turbo_available=False,
        coin_spawn_timer=0, turbo_start_time=0, total_distance_traveled=0,
        camera_mode="third_person", camera_pos=THIRD_PERSON_POS, enemy_vehicles=[]
    )
    initialize_dynamic_trees()


def initialize_rain():
    global rain_particles
    rain_particles = [RainParticle() for i in range(NUM_RAIN_PARTICLES)]


def update_weather():
    if weather_mode == "rain":
        if not rain_particles:
            initialize_rain()
        for particle in rain_particles:
            particle.update()
    elif rain_particles:
        rain_particles.clear()


def set_weather_lighting():
    colors = {"day": (0.5, 0.8, 1.0, 1.0), "night": (0.1, 0.1, 0.3, 1.0), "sunny": (0.9, 0.9, 0.6, 1.0),
              "rain": (0.4, 0.4, 0.5, 1.0)}
    glClearColor(*colors.get(weather_mode, colors["day"]))


def draw_rain():
    if weather_mode == "rain" and rain_particles:
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.7, 0.7, 0.9, 0.7)
        glLineWidth(1.5)
        glBegin(GL_LINES)

        for particle in rain_particles:
            world_x, world_y, world_z = particle.get_world_position()
            glVertex3f(world_x, world_y, world_z)
            glVertex3f(world_x - 3, world_y - 25, world_z - 30)

        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)


def get_weather_road_color():
    return {"day": (0.3, 0.3, 0.3), "night": (0.2, 0.2, 0.2), "sunny": (0.4, 0.4, 0.35), "rain": (0.25, 0.25, 0.3)}.get(
        weather_mode, (0.3, 0.3, 0.3))


def get_weather_grass_color():
    return {"day": (0.2, 0.8, 0.2), "night": (0.1, 0.4, 0.1), "sunny": (0.3, 1.0, 0.3), "rain": (0.15, 0.6, 0.15)}.get(
        weather_mode, (0.2, 0.8, 0.2))


def keyboard(key, x, y):
    global player_lane, target_x, game_paused, game_speed, weather_mode
    if not gameover:
        if key == b'a' and player_lane > -1:
            player_lane -= 1
            print("Player moved to the Left!")
        elif key == b'd' and player_lane < 1:
            player_lane += 1
            print("Player moved to the Right!")
        elif key == b'p':
            game_paused = not game_paused
            print(f"TERMINAL: Game {'Paused' if game_paused else 'Resumed'}.")
        elif key == b't':
            activate_turbo()
        elif key == b'v':
            toggle_camera()
        elif key == b'w':
            game_speed += 0.5
            print(f"Speed increased to {game_speed}")
        elif key == b's':
            game_speed = max(0.5, game_speed - 0.5)
            print(f"Speed decreased to {game_speed}")
        elif key in b'1234':
            weather_modes = {b'1': "day", b'2': "night", b'3': "sunny", b'4': "rain"}
            weather_mode = weather_modes[key]
            print(f"Weather changed to {weather_mode.title()}")
        target_x = player_lane * LANE_WIDTH

    if key == b'r' and gameover:
        print("Player restarted the game!")
        reset_game()
    if key == b'q':
        import os
        print("Player quit the game!")
        os._exit(0)


def special_key(key, x, y):
    global camera_pos
    if camera_mode == "third_person":
        x_cam, y_cam, z_cam = camera_pos
        if key == GLUT_KEY_UP:
            z_cam += 10
            print("Camera moved up.")
        elif key == GLUT_KEY_DOWN:
            z_cam -= 10
            print("Camera moved down.")
        elif key == GLUT_KEY_LEFT:
            x_cam -= 10
            print("Camera moved left.")
        elif key == GLUT_KEY_RIGHT:
            x_cam += 10
            print("Camera moved right.")
        camera_pos = (x_cam, y_cam, z_cam)


def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    current_fov = 90 if camera_mode == "first_person" else fovY
    gluPerspective(current_fov, 1.25, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x_cam, y_cam, z_cam = camera_pos

    if camera_mode == "first_person":
        gluLookAt(x_cam, y_cam, z_cam, x_cam, y_cam + 500, z_cam, 0, 0, 1)
    else:
        gluLookAt(x_cam, y_cam, z_cam, 0, 0, 0, 0, 0, 1)


def idle():
    if quit_game:
        import sys
        sys.exit(0)
    update_game()
    glutPostRedisplay()


def show_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    set_weather_lighting()
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setup_camera()
    glEnable(GL_DEPTH_TEST)
    draw_road()
    draw_trees()
    draw_player_car()

    for enemy in enemy_vehicles:
        draw_enemy_vehicle(enemy)
    for coin in coins:
        draw_coin(coin)

    draw_rain()
    draw_text(10, 770, f"Score: {score}")
    remaining_time_str = f" [TURBO! {TURBO_DURATION - (time.time() - turbo_start_time):.1f}s]" if turbo_active else ""
    draw_text(10, 745, f"Speed: {game_speed}{remaining_time_str}")
    lane_text = ["Left", "Middle", "Right"][player_lane + 1]
    draw_text(10, 720, f"Lane: {lane_text}")
    draw_text(10, 695, f"Camera: {camera_mode.replace('_', ' ').title()}")
    weather_display = "Rainy" if weather_mode == "rain" else weather_mode.title()
    draw_text(10, 670, f"Weather: {weather_display}")
    draw_text(300, 770, "Controls:")
    draw_text(320, 745, "A/D - Move | W/S - Speed | P - Pause")
    draw_text(320, 720, "T - Turbo | V - Camera | 1/2/3/4 - Weather")
    draw_text(320, 695, "Arrow Keys: Adjust camera view")
    draw_text(320, 670, "R - Restart | Q - Quit")
    draw_turbo_bar()
    draw_text(815, 750, "TURBO")

    if game_paused and not gameover:
        draw_text(400, 400, "GAME PAUSED - Press P to continue")
    if gameover:
        draw_text(450, 450, "GAME OVER!")
        draw_text(450, 420, f"Final Score: {score}")
        draw_text(390, 390, "Press R to restart or Q to quit")
    glutSwapBuffers()


def print_instructions():
    print("\n---------------------------------------")
    print("\n--- Welcome to EndlessDriver! ---")
    print("Objective: Drive as far as you can, collect coins, and avoid crashing!")
    print("\nControls:")
    print("  A/D: Change lanes")
    print("  W/S: Increase/Decrease speed")
    print("  T: Activate Turbo (when available)")
    print("  V: Toggle camera view")
    print("  P: Pause/Resume game")
    print("  Arrow Keys: Adjust camera view (in third-person mode)")
    print("  1/2/3/4: Change weather (Day, Night, Sunny, Rain)")
    print("  R: Restart game (when game over)")
    print("  Q: Quit game")
    print("\nGood luck and drive safely!")
    print("\n---------------------------------------\n")
    print("Game started!")


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(250, 10)
    glutCreateWindow(b"EndlessDriver")
    print_instructions()
    initialize_dynamic_trees()
    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_key)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()
