# Phase 6 Evaluation Repository Summary

## Created Repository Structures

This document summarizes the test repository structures created for Phase 6 evaluations. Each repository contains realistic code scenarios that require specific refactoring skills.

### 1. Web App (`tasks/repos/web_app/`)
**Scenario**: Django web application with tightly coupled components
**Files Created**:
- `README.md` - Scenario description and success criteria
- `views.py` - Mixed concerns (auth, email, user logic)
- `models.py` - Business logic embedded in models
- `utils.py` - Circular import issues
- `test_refactoring.py` - Tests for proper separation

**Key Issues to Fix**:
- Extract authentication logic to separate auth module
- Extract email utilities into service
- Fix circular imports between models/utils
- Implement proper separation of concerns

### 2. API Server (`tasks/repos/api_server/`)
**Scenario**: Flask API with scattered authentication logic
**Files Created**:
- `README.md` - Auth refactoring requirements
- `app.py` - JWT logic scattered across endpoints
- `test_auth_refactoring.py` - Tests for centralized auth

**Key Issues to Fix**:
- Centralize JWT logic into middleware
- Implement role-based access control (RBAC)
- Create proper auth decorators
- Remove duplicate token validation

### 3. Data Pipeline (`tasks/repos/data_pipeline/`)
**Scenario**: ETL pipeline with poorly named classes
**Files Created**:
- `README.md` - Class renaming requirements
- `processor.py` - `DataProcessor` → `ETLPipeline`
- `handlers.py` - `DataHandler` → `DataTransformer`
- `pipeline_runner.py` - Cross-references to update
- `test_renaming.py` - Tests for consistent renaming
- `__init__.py` - Package structure

**Key Issues to Fix**:
- Rename `DataProcessor` to `ETLPipeline`
- Rename `process()` method to `run_pipeline()`
- Update all imports and references
- Maintain functionality through renaming

### 4. Game Engine (`tasks/repos/game_engine/`)
**Scenario**: Monolithic game engine file
**Files Created**:
- `README.md` - File splitting requirements
- `game_engine.py` - Large monolithic file with multiple concerns
- `test_splitting.py` - Tests for proper module separation

**Key Issues to Fix**:
- Split into `renderer.py`, `physics.py`, `input_handler.py`, `audio_manager.py`
- Create proper interfaces between modules
- Maintain game loop functionality
- Implement proper separation of concerns

### 5. Messaging (`tasks/repos/messaging/`)
**Scenario**: Messaging system with circular imports
**Files Created**:
- `README.md` - Circular import resolution
- `user_manager.py` - Imports message_handler and notifications
- `message_handler.py` - Imports user_manager and notifications
- `notifications.py` - Imports user_manager and message_handler
- `test_circular_imports.py` - Tests for dependency resolution

**Key Issues to Fix**:
- Break circular dependencies between modules
- Implement dependency injection or event system
- Maintain functionality with proper architecture
- Use interfaces or abstract base classes

### 6. Performance (`tasks/repos/performance/`)
**Scenario**: Data processing with performance bottlenecks
**Files Created**:
- `README.md` - Performance optimization requirements
- `slow_processor.py` - O(n²) algorithms, memory leaks, N+1 queries
- `test_performance.py` - Performance benchmarks and tests

**Key Issues to Fix**:
- Optimize O(n²) duplicate detection algorithm
- Fix memory leaks in file processing
- Resolve N+1 database query problems
- Implement proper caching strategies
- Add parallelization for CPU-intensive operations

### 7. Security (`tasks/repos/security/`)
**Scenario**: Web application with security vulnerabilities
**Files Created**:
- `README.md` - Security vulnerability descriptions
- `vulnerable_app.py` - SQL injection, XSS, path traversal, command injection
- `test_security_fixes.py` - Security vulnerability tests

**Key Issues to Fix**:
- Fix SQL injection with parameterized queries
- Prevent XSS with proper output encoding
- Stop path traversal with path validation
- Implement secure password hashing
- Prevent command injection with input validation

### 8. JavaScript Projects (`tasks/repos/js_projects/`)
**Scenario**: JavaScript/TypeScript refactoring challenges
**Files Created**:
- `README.md` - JS/TS refactoring requirements
- `legacy_api.js` - Callback hell, no type safety
- `monolithic_component.jsx` - Large React component
- `test_js_refactoring.test.js` - Modern JS/TS pattern tests

**Key Issues to Fix**:
- Convert callback hell to async/await
- Add TypeScript type definitions
- Split monolithic React component
- Implement proper error boundaries
- Add performance optimizations

### 9. Go Projects (`tasks/repos/go_projects/`)
**Scenario**: Go application refactoring
**Files Created**:
- `README.md` - Go refactoring requirements
- `user_service.go` - No interfaces, poor error handling, large functions
- `user_service_test.go` - Tests for Go best practices

**Key Issues to Fix**:
- Extract interfaces from concrete implementations
- Improve error handling with proper wrapping
- Add context handling for goroutines
- Break down large functions
- Implement proper validation

### 10. Rust Projects (`tasks/repos/rust_projects/`)
**Scenario**: Rust application with safety and performance issues
**Files Created**:
- `README.md` - Rust refactoring requirements
- `src/main.rs` - Panics, lifetime issues, blocking operations
- `src/lib.rs` - Library structure
- `Cargo.toml` - Dependencies
- `tests/refactoring_tests.rs` - Rust best practices tests

**Key Issues to Fix**:
- Replace panics with Result error handling
- Extract traits from implementations
- Fix lifetime and borrowing issues
- Convert to async/await patterns
- Implement proper error types

### 11. Real World (`tasks/repos/real_world/`)
**Scenario**: Production code issues and legacy migration
**Files Created**:
- `README.md` - Real-world scenario descriptions
- `legacy_migration.py` - Python 2 to 3 migration issues
- `test_real_world.py` - Legacy code modernization tests

**Key Issues to Fix**:
- Migrate Python 2 syntax to Python 3
- Update deprecated library imports
- Modernize string formatting and exception handling
- Add type hints and modern patterns
- Improve error handling and logging

## Usage Instructions

Each repository contains:
1. **README.md** - Describes the scenario and success criteria
2. **Source files** - Code with realistic issues to fix
3. **Test files** - Validate that refactoring was successful
4. **Supporting files** - Configuration, package definitions, etc.

To use these for evaluation:
1. Present the scenario and requirements from README.md
2. Allow the AI to examine the source files
3. Request specific refactoring improvements
4. Run tests to validate the changes
5. Verify that functionality is preserved

## Evaluation Criteria

Each repository tests different aspects of refactoring skills:
- **Code architecture** - Separation of concerns, modularity
- **Performance** - Algorithm optimization, caching, concurrency
- **Security** - Vulnerability detection and remediation
- **Modernization** - Language best practices, modern patterns
- **Error handling** - Proper exception handling and propagation
- **Testing** - Maintaining test coverage through refactoring

These repositories provide realistic, hands-on scenarios for evaluating advanced refactoring capabilities across multiple programming languages and domains.
