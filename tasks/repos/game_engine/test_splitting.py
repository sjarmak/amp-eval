"""Tests to validate proper file splitting."""
import pytest
import os


def test_renderer_module_created():
    """Test that renderer module is properly created."""
    assert os.path.exists('renderer.py'), "renderer.py should be created"
    
    try:
        from renderer import Renderer
        renderer = Renderer(800, 600)
        assert hasattr(renderer, 'render')
        assert hasattr(renderer, 'clear_screen')
        assert hasattr(renderer, 'render_object')
    except ImportError:
        pytest.fail("Renderer class not properly implemented")


def test_physics_module_created():
    """Test that physics module is properly created."""
    assert os.path.exists('physics.py'), "physics.py should be created"
    
    try:
        from physics import PhysicsEngine
        physics = PhysicsEngine()
        assert hasattr(physics, 'update_physics')
        assert hasattr(physics, 'check_collisions')
        assert hasattr(physics, 'apply_gravity')
    except ImportError:
        pytest.fail("PhysicsEngine class not properly implemented")


def test_input_handler_module_created():
    """Test that input handler module is properly created."""
    assert os.path.exists('input_handler.py'), "input_handler.py should be created"
    
    try:
        from input_handler import InputHandler
        input_handler = InputHandler()
        assert hasattr(input_handler, 'handle_input')
        assert hasattr(input_handler, 'on_key_press')
        assert hasattr(input_handler, 'on_mouse_click')
    except ImportError:
        pytest.fail("InputHandler class not properly implemented")


def test_audio_manager_module_created():
    """Test that audio manager module is properly created."""
    assert os.path.exists('audio_manager.py'), "audio_manager.py should be created"
    
    try:
        from audio_manager import AudioManager
        audio = AudioManager()
        assert hasattr(audio, 'play_sound')
        assert hasattr(audio, 'load_sound')
        assert hasattr(audio, 'set_master_volume')
    except ImportError:
        pytest.fail("AudioManager class not properly implemented")


def test_game_engine_refactored():
    """Test that GameEngine class is properly refactored."""
    try:
        from game_engine import GameEngine
        engine = GameEngine()
        
        # Should have references to separate modules
        assert hasattr(engine, 'renderer')
        assert hasattr(engine, 'physics')
        assert hasattr(engine, 'input_handler')
        assert hasattr(engine, 'audio_manager')
        
        # Should not have the old monolithic methods
        assert not hasattr(engine, 'render_object')  # Should be in renderer
        assert not hasattr(engine, 'update_physics')  # Should be in physics
        assert not hasattr(engine, 'handle_input')   # Should be in input_handler
        assert not hasattr(engine, 'play_sound')     # Should be in audio_manager
        
    except ImportError:
        pytest.fail("GameEngine not properly refactored")


def test_vector2_preserved():
    """Test that Vector2 class is preserved and accessible."""
    try:
        from game_engine import Vector2
        v = Vector2(1, 2)
        assert v.x == 1
        assert v.y == 2
    except ImportError:
        pytest.fail("Vector2 class should be preserved")


def test_game_object_preserved():
    """Test that GameObject class is preserved and accessible."""
    try:
        from game_engine import GameObject, Vector2
        obj = GameObject(
            position=Vector2(0, 0),
            velocity=Vector2(0, 0)
        )
        assert obj.position.x == 0
        assert obj.mass == 1.0
    except ImportError:
        pytest.fail("GameObject class should be preserved")


def test_main_game_loop_functional():
    """Test that main game loop still works after refactoring."""
    try:
        from game_engine import GameEngine, GameObject, Vector2
        
        engine = GameEngine(400, 300)
        
        # Add a test object
        obj = GameObject(
            position=Vector2(100, 100),
            velocity=Vector2(0, 0)
        )
        engine.add_object(obj)
        
        # Should be able to run one frame without errors
        engine.delta_time = 1/60
        
        # These should work through the separated modules
        engine.physics.update_physics(engine.objects, engine.delta_time)
        engine.renderer.render(engine.objects)
        
        assert len(engine.objects) == 1
        
    except (ImportError, AttributeError) as e:
        pytest.fail(f"Game loop not functional after refactoring: {e}")


def test_modules_properly_separated():
    """Test that concerns are properly separated."""
    # Read the refactored game_engine.py
    with open('game_engine.py', 'r') as f:
        content = f.read()
    
    # Should not contain rendering methods
    assert 'def render_object(' not in content
    assert 'def clear_screen(' not in content
    
    # Should not contain physics methods
    assert 'def update_physics(' not in content
    assert 'def check_boundary_collision(' not in content
    
    # Should not contain input methods
    assert 'def handle_input(' not in content
    assert 'def on_key_press(' not in content
    
    # Should not contain audio methods
    assert 'def play_sound(' not in content
    assert 'def load_sound(' not in content


def test_interfaces_between_modules():
    """Test that modules can communicate properly."""
    try:
        from game_engine import GameEngine, Vector2, GameObject
        
        engine = GameEngine()
        
        # Test that modules can interact
        # Physics should be able to update objects
        obj = GameObject(Vector2(0, 0), Vector2(1, 1))
        engine.add_object(obj)
        
        # Renderer should be able to render objects
        engine.renderer.render(engine.objects)
        
        # Input should be able to affect game state
        engine.input_handler.on_key_press('W')
        
        # Audio should be able to play sounds
        engine.audio_manager.play_sound('test')
        
    except Exception as e:
        pytest.fail(f"Module interfaces not working: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
