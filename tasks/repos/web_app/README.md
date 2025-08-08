# Web App Refactoring Challenge

## Scenario
A Django web application with tightly coupled components that needs to be refactored into separate modules with proper separation of concerns.

## Issues to Fix
1. Move authentication logic from views to separate auth module
2. Extract email utilities into separate service
3. Refactor user management into proper models/services pattern
4. Fix circular import between models and utils

## Success Criteria
- All tests pass after refactoring
- No circular imports
- Proper separation of concerns
- Email service is reusable
