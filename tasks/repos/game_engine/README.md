# Game Engine File Splitting Challenge

## Scenario
A monolithic game engine file that contains multiple concerns (rendering, physics, input, audio) that need to be split into separate modules.

## Issues to Fix
1. Split `game_engine.py` into separate modules:
   - `renderer.py` for rendering logic
   - `physics.py` for physics calculations
   - `input_handler.py` for input management
   - `audio_manager.py` for audio systems
2. Create proper interfaces between modules
3. Update imports and dependencies
4. Maintain game loop functionality

## Success Criteria
- Monolithic file split into logical modules
- Proper separation of concerns
- All tests pass
- Game loop still functional
