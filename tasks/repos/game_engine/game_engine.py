"""Monolithic game engine that needs to be split into modules."""
import math
import time
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class Vector2:
    """2D Vector class."""
    x: float
    y: float
    
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return Vector2(self.x * scalar, self.y * scalar)


@dataclass
class GameObject:
    """Game object with position, velocity, and properties."""
    position: Vector2
    velocity: Vector2
    mass: float = 1.0
    radius: float = 10.0
    color: str = "white"
    health: int = 100


class GameEngine:
    """Monolithic game engine with multiple concerns."""
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.objects: List[GameObject] = []
        self.running = False
        self.delta_time = 0.0
        self.last_frame_time = time.time()
        
        # Input state (should be in separate input module)
        self.keys_pressed = set()
        self.mouse_pos = Vector2(0, 0)
        self.mouse_buttons = set()
        
        # Audio state (should be in separate audio module)
        self.audio_channels = {}
        self.master_volume = 1.0
        self.sound_effects = {}
        
        # Rendering state (should be in separate renderer module)
        self.screen_buffer = [[' ' for _ in range(width)] for _ in range(height)]
        self.camera_pos = Vector2(0, 0)
        self.zoom = 1.0
        
        # Physics constants (should be in separate physics module)
        self.gravity = Vector2(0, -9.81)
        self.air_resistance = 0.01
        self.ground_level = 50
    
    def run(self):
        """Main game loop."""
        self.running = True
        while self.running:
            current_time = time.time()
            self.delta_time = current_time - self.last_frame_time
            self.last_frame_time = current_time
            
            self.handle_input()
            self.update_physics()
            self.update_audio()
            self.render()
            
            time.sleep(1/60)  # 60 FPS
    
    # INPUT HANDLING (should be in input_handler.py)
    def handle_input(self):
        """Handle input events."""
        # Simulate input polling
        if 'W' in self.keys_pressed:
            self.move_player(Vector2(0, 1))
        if 'S' in self.keys_pressed:
            self.move_player(Vector2(0, -1))
        if 'A' in self.keys_pressed:
            self.move_player(Vector2(-1, 0))
        if 'D' in self.keys_pressed:
            self.move_player(Vector2(1, 0))
        
        if 'ESC' in self.keys_pressed:
            self.running = False
    
    def move_player(self, direction: Vector2):
        """Move player object."""
        if self.objects:
            player = self.objects[0]  # Assume first object is player
            player.velocity = player.velocity + direction * 50.0
    
    def on_key_press(self, key: str):
        """Handle key press."""
        self.keys_pressed.add(key)
        if key == 'SPACE':
            self.play_sound('jump')
    
    def on_key_release(self, key: str):
        """Handle key release."""
        self.keys_pressed.discard(key)
    
    def on_mouse_move(self, x: int, y: int):
        """Handle mouse movement."""
        self.mouse_pos = Vector2(x, y)
    
    def on_mouse_click(self, button: str, x: int, y: int):
        """Handle mouse click."""
        self.mouse_buttons.add(button)
        if button == 'LEFT':
            self.spawn_object_at(Vector2(x, y))
            self.play_sound('click')
    
    # PHYSICS (should be in physics.py)
    def update_physics(self):
        """Update physics for all objects."""
        for obj in self.objects:
            # Apply gravity
            obj.velocity = obj.velocity + self.gravity * self.delta_time
            
            # Apply air resistance
            resistance = obj.velocity * -self.air_resistance
            obj.velocity = obj.velocity + resistance
            
            # Update position
            obj.position = obj.position + obj.velocity * self.delta_time
            
            # Ground collision
            if obj.position.y <= self.ground_level:
                obj.position.y = self.ground_level
                obj.velocity.y = max(0, obj.velocity.y)  # Stop downward velocity
            
            # Boundary collision
            self.check_boundary_collision(obj)
        
        # Check object-object collisions
        self.check_object_collisions()
    
    def check_boundary_collision(self, obj: GameObject):
        """Check collision with screen boundaries."""
        if obj.position.x < obj.radius:
            obj.position.x = obj.radius
            obj.velocity.x = -obj.velocity.x * 0.8  # Bounce with energy loss
        elif obj.position.x > self.width - obj.radius:
            obj.position.x = self.width - obj.radius
            obj.velocity.x = -obj.velocity.x * 0.8
    
    def check_object_collisions(self):
        """Check collisions between objects."""
        for i, obj1 in enumerate(self.objects):
            for obj2 in self.objects[i+1:]:
                distance = math.sqrt(
                    (obj1.position.x - obj2.position.x) ** 2 +
                    (obj1.position.y - obj2.position.y) ** 2
                )
                
                if distance < obj1.radius + obj2.radius:
                    self.resolve_collision(obj1, obj2)
                    self.play_sound('collision')
    
    def resolve_collision(self, obj1: GameObject, obj2: GameObject):
        """Resolve collision between two objects."""
        # Simple elastic collision
        temp_vel = obj1.velocity
        obj1.velocity = obj2.velocity
        obj2.velocity = temp_vel
    
    # AUDIO (should be in audio_manager.py)
    def update_audio(self):
        """Update audio system."""
        # Update audio channels, fade effects, etc.
        for channel_id, channel_data in self.audio_channels.items():
            if channel_data['fade_out']:
                channel_data['volume'] *= 0.95
                if channel_data['volume'] < 0.01:
                    self.stop_sound(channel_id)
    
    def play_sound(self, sound_name: str, volume: float = 1.0):
        """Play a sound effect."""
        if sound_name in self.sound_effects:
            channel_id = f"{sound_name}_{time.time()}"
            self.audio_channels[channel_id] = {
                'sound': sound_name,
                'volume': volume * self.master_volume,
                'fade_out': False,
                'loop': False
            }
    
    def stop_sound(self, channel_id: str):
        """Stop a sound channel."""
        if channel_id in self.audio_channels:
            del self.audio_channels[channel_id]
    
    def set_master_volume(self, volume: float):
        """Set master volume."""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def load_sound(self, sound_name: str, file_path: str):
        """Load a sound file."""
        self.sound_effects[sound_name] = file_path
    
    # RENDERING (should be in renderer.py)
    def render(self):
        """Render the current frame."""
        # Clear screen buffer
        self.clear_screen()
        
        # Render all objects
        for obj in self.objects:
            self.render_object(obj)
        
        # Render UI
        self.render_ui()
        
        # Display frame
        self.display_frame()
    
    def clear_screen(self):
        """Clear the screen buffer."""
        for row in self.screen_buffer:
            for i in range(len(row)):
                row[i] = ' '
    
    def render_object(self, obj: GameObject):
        """Render a game object."""
        # Convert world coordinates to screen coordinates
        screen_x = int(obj.position.x - self.camera_pos.x)
        screen_y = int(obj.position.y - self.camera_pos.y)
        
        # Simple circle rendering
        char = self.get_color_char(obj.color)
        radius = int(obj.radius)
        
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx*dx + dy*dy <= radius*radius:
                    px = screen_x + dx
                    py = screen_y + dy
                    if 0 <= px < self.width and 0 <= py < self.height:
                        self.screen_buffer[py][px] = char
    
    def get_color_char(self, color: str) -> str:
        """Get character representation for color."""
        color_map = {
            'white': '*',
            'red': '#',
            'blue': '@',
            'green': '+',
            'yellow': '%'
        }
        return color_map.get(color, '*')
    
    def render_ui(self):
        """Render UI elements."""
        # Render object count
        count_text = f"Objects: {len(self.objects)}"
        for i, char in enumerate(count_text):
            if i < self.width:
                self.screen_buffer[0][i] = char
        
        # Render FPS
        fps = int(1.0 / self.delta_time) if self.delta_time > 0 else 0
        fps_text = f"FPS: {fps}"
        for i, char in enumerate(fps_text):
            if i < self.width:
                self.screen_buffer[1][i] = char
    
    def display_frame(self):
        """Display the current frame."""
        # In a real game, this would send to graphics API
        # For now, just simulate frame completion
        pass
    
    def set_camera_position(self, pos: Vector2):
        """Set camera position."""
        self.camera_pos = pos
    
    def set_zoom(self, zoom: float):
        """Set zoom level."""
        self.zoom = max(0.1, min(10.0, zoom))
    
    # GAME LOGIC
    def spawn_object_at(self, position: Vector2):
        """Spawn a new object at the given position."""
        obj = GameObject(
            position=position,
            velocity=Vector2(0, 0),
            mass=1.0,
            radius=10.0,
            color='blue'
        )
        self.objects.append(obj)
    
    def add_object(self, obj: GameObject):
        """Add an object to the game."""
        self.objects.append(obj)
    
    def remove_object(self, obj: GameObject):
        """Remove an object from the game."""
        if obj in self.objects:
            self.objects.remove(obj)


def main():
    """Main function to run the game."""
    engine = GameEngine(800, 600)
    
    # Load some sounds
    engine.load_sound('jump', 'sounds/jump.wav')
    engine.load_sound('click', 'sounds/click.wav')
    engine.load_sound('collision', 'sounds/collision.wav')
    
    # Create initial objects
    player = GameObject(
        position=Vector2(400, 300),
        velocity=Vector2(0, 0),
        color='red',
        radius=15
    )
    engine.add_object(player)
    
    # Add some obstacles
    for i in range(3):
        obstacle = GameObject(
            position=Vector2(100 + i * 200, 200),
            velocity=Vector2(0, 0),
            color='green',
            radius=20
        )
        engine.add_object(obstacle)
    
    print("Game starting... Press ESC to quit")
    engine.run()


if __name__ == "__main__":
    main()
