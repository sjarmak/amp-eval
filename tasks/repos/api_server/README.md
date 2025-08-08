# API Server Auth Refactoring

## Scenario
A Flask API server with authentication logic scattered across multiple files. Need to centralize auth into a proper middleware/service pattern.

## Issues to Fix
1. Extract JWT logic from route handlers into middleware
2. Centralize role-based access control (RBAC)
3. Move token validation out of individual endpoints
4. Create proper auth decorators for different permission levels

## Success Criteria
- All auth logic centralized in auth module
- Proper middleware pattern implemented
- RBAC system works correctly
- All tests pass
