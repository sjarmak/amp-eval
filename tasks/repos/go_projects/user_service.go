// Package main contains a user service that needs refactoring
// Issues: no interfaces, poor error handling, large functions, no context handling
package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

// User struct needs proper JSON tags and validation
type User struct {
	ID       int
	Name     string
	Email    string
	Age      int
	Created  time.Time
	Updated  time.Time
	IsActive bool
}

// UserService is a concrete implementation that should have an interface
type UserService struct {
	db *sql.DB
}

// NewUserService creates a new user service
func NewUserService(db *sql.DB) *UserService {
	return &UserService{db: db}
}

// CreateUser creates a new user - NEEDS REFACTORING
// Issues: no error wrapping, no validation, no context, too large
func (s *UserService) CreateUser(name, email string, age int) (*User, error) {
	// No input validation
	if name == "" {
		return nil, fmt.Errorf("name is required")
	}
	if email == "" {
		return nil, fmt.Errorf("email is required")
	}
	if age < 0 {
		return nil, fmt.Errorf("age must be positive")
	}

	// Check if email already exists - should be separate function
	var count int
	err := s.db.QueryRow("SELECT COUNT(*) FROM users WHERE email = $1", email).Scan(&count)
	if err != nil {
		log.Printf("Error checking email existence: %v", err)
		return nil, fmt.Errorf("database error")
	}
	if count > 0 {
		return nil, fmt.Errorf("email already exists")
	}

	// Validate email format - should be separate function
	if !strings.Contains(email, "@") || !strings.Contains(email, ".") {
		return nil, fmt.Errorf("invalid email format")
	}

	// Create user - should use context
	query := `
		INSERT INTO users (name, email, age, created, updated, is_active)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING id
	`
	var userID int
	err = s.db.QueryRow(query, name, email, age, time.Now(), time.Now(), true).Scan(&userID)
	if err != nil {
		log.Printf("Error creating user: %v", err)
		return nil, fmt.Errorf("failed to create user")
	}

	// Return created user - should use GetUser method
	user := &User{
		ID:       userID,
		Name:     name,
		Email:    email,
		Age:      age,
		Created:  time.Now(),
		Updated:  time.Now(),
		IsActive: true,
	}

	log.Printf("Created user: %d", userID)
	return user, nil
}

// GetUser retrieves a user by ID - NEEDS REFACTORING
// Issues: no context, poor error handling
func (s *UserService) GetUser(id int) (*User, error) {
	if id <= 0 {
		return nil, fmt.Errorf("invalid user ID")
	}

	query := `
		SELECT id, name, email, age, created, updated, is_active
		FROM users
		WHERE id = $1 AND is_active = true
	`

	user := &User{}
	err := s.db.QueryRow(query, id).Scan(
		&user.ID,
		&user.Name,
		&user.Email,
		&user.Age,
		&user.Created,
		&user.Updated,
		&user.IsActive,
	)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("user not found")
		}
		log.Printf("Error getting user %d: %v", id, err)
		return nil, fmt.Errorf("database error")
	}

	return user, nil
}

// UpdateUser updates an existing user - NEEDS REFACTORING
// Issues: no context, no proper error wrapping, too large
func (s *UserService) UpdateUser(id int, name, email string, age int) (*User, error) {
	// Check if user exists first
	existingUser, err := s.GetUser(id)
	if err != nil {
		return nil, err
	}
	if existingUser == nil {
		return nil, fmt.Errorf("user not found")
	}

	// Validate input - should be separate function
	if name == "" {
		return nil, fmt.Errorf("name is required")
	}
	if email == "" {
		return nil, fmt.Errorf("email is required")
	}
	if age < 0 {
		return nil, fmt.Errorf("age must be positive")
	}

	// Validate email format - duplicate code
	if !strings.Contains(email, "@") || !strings.Contains(email, ".") {
		return nil, fmt.Errorf("invalid email format")
	}

	// Check if email is taken by another user
	var count int
	err = s.db.QueryRow("SELECT COUNT(*) FROM users WHERE email = $1 AND id != $2", email, id).Scan(&count)
	if err != nil {
		log.Printf("Error checking email uniqueness: %v", err)
		return nil, fmt.Errorf("database error")
	}
	if count > 0 {
		return nil, fmt.Errorf("email already taken")
	}

	// Update user
	query := `
		UPDATE users
		SET name = $1, email = $2, age = $3, updated = $4
		WHERE id = $5 AND is_active = true
	`
	_, err = s.db.Exec(query, name, email, age, time.Now(), id)
	if err != nil {
		log.Printf("Error updating user %d: %v", id, err)
		return nil, fmt.Errorf("failed to update user")
	}

	// Return updated user
	updatedUser := &User{
		ID:       id,
		Name:     name,
		Email:    email,
		Age:      age,
		Created:  existingUser.Created,
		Updated:  time.Now(),
		IsActive: true,
	}

	log.Printf("Updated user: %d", id)
	return updatedUser, nil
}

// DeleteUser soft deletes a user - NEEDS REFACTORING
func (s *UserService) DeleteUser(id int) error {
	if id <= 0 {
		return fmt.Errorf("invalid user ID")
	}

	// Check if user exists
	_, err := s.GetUser(id)
	if err != nil {
		return err
	}

	// Soft delete
	query := "UPDATE users SET is_active = false, updated = $1 WHERE id = $2"
	_, err = s.db.Exec(query, time.Now(), id)
	if err != nil {
		log.Printf("Error deleting user %d: %v", id, err)
		return fmt.Errorf("failed to delete user")
	}

	log.Printf("Deleted user: %d", id)
	return nil
}

// ListUsers returns all active users - NEEDS REFACTORING
// Issues: no pagination, no context, no filtering
func (s *UserService) ListUsers() ([]*User, error) {
	query := `
		SELECT id, name, email, age, created, updated, is_active
		FROM users
		WHERE is_active = true
		ORDER BY created DESC
	`

	rows, err := s.db.Query(query)
	if err != nil {
		log.Printf("Error listing users: %v", err)
		return nil, fmt.Errorf("database error")
	}
	defer rows.Close()

	var users []*User
	for rows.Next() {
		user := &User{}
		err := rows.Scan(
			&user.ID,
			&user.Name,
			&user.Email,
			&user.Age,
			&user.Created,
			&user.Updated,
			&user.IsActive,
		)
		if err != nil {
			log.Printf("Error scanning user: %v", err)
			continue // Should handle this better
		}
		users = append(users, user)
	}

	if err = rows.Err(); err != nil {
		log.Printf("Error iterating users: %v", err)
		return nil, fmt.Errorf("database error")
	}

	return users, nil
}

// SearchUsers searches users by name or email - NEEDS REFACTORING
func (s *UserService) SearchUsers(query string) ([]*User, error) {
	if query == "" {
		return s.ListUsers()
	}

	sqlQuery := `
		SELECT id, name, email, age, created, updated, is_active
		FROM users
		WHERE is_active = true
		AND (LOWER(name) LIKE LOWER($1) OR LOWER(email) LIKE LOWER($1))
		ORDER BY created DESC
	`

	searchPattern := "%" + query + "%"
	rows, err := s.db.Query(sqlQuery, searchPattern)
	if err != nil {
		log.Printf("Error searching users: %v", err)
		return nil, fmt.Errorf("database error")
	}
	defer rows.Close()

	var users []*User
	for rows.Next() {
		user := &User{}
		err := rows.Scan(
			&user.ID,
			&user.Name,
			&user.Email,
			&user.Age,
			&user.Created,
			&user.Updated,
			&user.IsActive,
		)
		if err != nil {
			log.Printf("Error scanning user: %v", err)
			continue
		}
		users = append(users, user)
	}

	return users, rows.Err()
}

// HTTP Handlers - NEED REFACTORING
// Issues: no proper error handling, no context, large functions

// CreateUserHandler handles user creation - NEEDS REFACTORING
func (s *UserService) CreateUserHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Parse request body
	var req struct {
		Name  string `json:"name"`
		Email string `json:"email"`
		Age   int    `json:"age"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Create user
	user, err := s.CreateUser(req.Name, req.Email, req.Age)
	if err != nil {
		// Poor error handling - should differentiate error types
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(user)
}

// GetUserHandler handles getting a user - NEEDS REFACTORING
func (s *UserService) GetUserHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Extract user ID from URL - poor URL parsing
	pathParts := strings.Split(r.URL.Path, "/")
	if len(pathParts) < 3 {
		http.Error(w, "Invalid URL", http.StatusBadRequest)
		return
	}

	idStr := pathParts[2]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid user ID", http.StatusBadRequest)
		return
	}

	// Get user
	user, err := s.GetUser(id)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			http.Error(w, "User not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
}

// ListUsersHandler handles listing users - NEEDS REFACTORING
func (s *UserService) ListUsersHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// Check for search query
	searchQuery := r.URL.Query().Get("q")
	
	var users []*User
	var err error
	
	if searchQuery != "" {
		users, err = s.SearchUsers(searchQuery)
	} else {
		users, err = s.ListUsers()
	}

	if err != nil {
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	// Return response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"users": users,
		"count": len(users),
	})
}

// main function - NEEDS REFACTORING
func main() {
	// Database connection - should be configurable
	db, err := sql.Open("postgres", "postgres://user:password@localhost/testdb?sslmode=disable")
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	// Create service
	userService := NewUserService(db)

	// Setup routes - should use a router
	http.HandleFunc("/users", userService.ListUsersHandler)
	http.HandleFunc("/users/", userService.GetUserHandler)
	http.HandleFunc("/users/create", userService.CreateUserHandler)

	// Start server
	log.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
