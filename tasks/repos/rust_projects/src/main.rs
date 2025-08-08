// File processing service with various Rust issues that need refactoring
// Issues: panics, no traits, poor error handling, blocking operations, lifetime issues

use std::collections::HashMap;
use std::fs;
use std::io::{self, Read, Write};
use std::path::Path;
use std::thread;
use std::time::Duration;

// User struct with lifetime issues
#[derive(Debug, Clone)]
pub struct User<'a> {
    pub id: u32,
    pub name: &'a str,     // Should probably own the string
    pub email: &'a str,    // Should probably own the string
    pub profile: &'a str,  // Should probably own the string
}

// File processor with panics and poor error handling
pub struct FileProcessor {
    base_path: String,
    cache: HashMap<String, String>,
    max_file_size: usize,
}

impl FileProcessor {
    pub fn new(base_path: String) -> Self {
        Self {
            base_path,
            cache: HashMap::new(),
            max_file_size: 1024 * 1024, // 1MB
        }
    }

    // ISSUE: Uses panic! instead of proper error handling
    pub fn read_file(&mut self, filename: &str) -> String {
        // Check cache first
        if let Some(content) = self.cache.get(filename) {
            return content.clone();
        }

        let full_path = format!("{}/{}", self.base_path, filename);
        
        // ISSUE: Panics on file not found
        let mut file = fs::File::open(&full_path)
            .expect("Failed to open file");

        let metadata = file.metadata()
            .expect("Failed to get file metadata");

        // ISSUE: Panics on large files
        if metadata.len() > self.max_file_size as u64 {
            panic!("File too large: {} bytes", metadata.len());
        }

        let mut content = String::new();
        // ISSUE: Panics on read error
        file.read_to_string(&mut content)
            .expect("Failed to read file");

        // Cache the content
        self.cache.insert(filename.to_string(), content.clone());
        content
    }

    // ISSUE: Uses panic! and blocking operations
    pub fn write_file(&mut self, filename: &str, content: &str) -> () {
        let full_path = format!("{}/{}", self.base_path, filename);
        
        // ISSUE: Panics on write error
        let mut file = fs::File::create(&full_path)
            .expect("Failed to create file");

        // ISSUE: Panics on write error
        file.write_all(content.as_bytes())
            .expect("Failed to write file");

        // Update cache
        self.cache.insert(filename.to_string(), content.to_string());

        // ISSUE: Blocking operation that could be async
        thread::sleep(Duration::from_millis(100));
    }

    // ISSUE: Panics and no proper error handling
    pub fn delete_file(&mut self, filename: &str) {
        let full_path = format!("{}/{}", self.base_path, filename);
        
        // ISSUE: Panics if file doesn't exist
        fs::remove_file(&full_path)
            .expect("Failed to delete file");

        // Remove from cache
        self.cache.remove(filename);
    }

    // ISSUE: Returns references with problematic lifetimes
    pub fn list_files(&self) -> Vec<&str> {
        let dir = fs::read_dir(&self.base_path)
            .expect("Failed to read directory");

        let mut files = Vec::new();
        for entry in dir {
            let entry = entry.expect("Failed to read directory entry");
            let path = entry.path();
            
            if path.is_file() {
                // ISSUE: This creates a dangling reference
                let filename = path.file_name()
                    .expect("No filename")
                    .to_str()
                    .expect("Invalid UTF-8");
                files.push(filename);
            }
        }
        files
    }

    // ISSUE: Blocking operation, should be async
    pub fn process_batch(&mut self, filenames: Vec<&str>) -> Vec<String> {
        let mut results = Vec::new();
        
        for filename in filenames {
            // ISSUE: Sequential processing, could be parallel
            let content = self.read_file(filename);
            let processed = self.transform_content(&content);
            
            // ISSUE: Blocking operation
            thread::sleep(Duration::from_millis(50));
            
            results.push(processed);
        }
        
        results
    }

    // ISSUE: Inefficient string operations
    fn transform_content(&self, content: &str) -> String {
        // ISSUE: Multiple string allocations
        let mut result = content.to_uppercase();
        result = result.replace(" ", "_");
        result = result.replace("\n", "\\n");
        
        // ISSUE: Unnecessary clone
        result.clone()
    }
}

// User manager with lifetime and borrowing issues
pub struct UserManager<'a> {
    users: HashMap<u32, User<'a>>,
    current_id: u32,
}

impl<'a> UserManager<'a> {
    pub fn new() -> Self {
        Self {
            users: HashMap::new(),
            current_id: 1,
        }
    }

    // ISSUE: Lifetime management problems
    pub fn add_user(&mut self, name: &'a str, email: &'a str, profile: &'a str) -> u32 {
        let user = User {
            id: self.current_id,
            name,
            email,
            profile,
        };
        
        self.users.insert(self.current_id, user);
        let id = self.current_id;
        self.current_id += 1;
        id
    }

    // ISSUE: Panic instead of returning Option/Result
    pub fn get_user(&self, id: u32) -> &User<'a> {
        self.users.get(&id)
            .expect("User not found")
    }

    // ISSUE: Borrowing issues
    pub fn update_user(&mut self, id: u32, name: &'a str, email: &'a str) {
        let user = self.users.get_mut(&id)
            .expect("User not found");
        
        user.name = name;
        user.email = email;
    }

    // ISSUE: Returns reference that might outlive the manager
    pub fn find_user_by_email(&self, email: &str) -> Option<&User<'a>> {
        for user in self.users.values() {
            if user.email == email {
                return Some(user);
            }
        }
        None
    }
}

// Data processor that should have a trait but doesn't
pub struct DataProcessor {
    rules: HashMap<String, String>,
}

impl DataProcessor {
    pub fn new() -> Self {
        Self {
            rules: HashMap::new(),
        }
    }

    // ISSUE: Should be part of a trait
    pub fn process(&self, data: &str) -> String {
        let mut result = data.to_string();
        
        for (pattern, replacement) in &self.rules {
            result = result.replace(pattern, replacement);
        }
        
        result
    }

    // ISSUE: Should be part of a trait
    pub fn add_rule(&mut self, pattern: String, replacement: String) {
        self.rules.insert(pattern, replacement);
    }

    // ISSUE: Blocking operation that could be async
    pub fn process_file(&self, filepath: &str) -> String {
        // ISSUE: Panics on error
        let content = fs::read_to_string(filepath)
            .expect("Failed to read file");
        
        // ISSUE: Blocking operation
        thread::sleep(Duration::from_millis(10));
        
        self.process(&content)
    }
}

// Network client with blocking operations
pub struct NetworkClient {
    base_url: String,
    timeout: Duration,
}

impl NetworkClient {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            timeout: Duration::from_secs(30),
        }
    }

    // ISSUE: Blocking HTTP request, should be async
    pub fn get(&self, path: &str) -> String {
        // Simulate HTTP request
        let url = format!("{}/{}", self.base_url, path);
        println!("Making request to: {}", url);
        
        // ISSUE: Blocking operation
        thread::sleep(self.timeout);
        
        // ISSUE: Always returns success, no error handling
        format!("Response from {}", url)
    }

    // ISSUE: Blocking POST request
    pub fn post(&self, path: &str, body: &str) -> String {
        let url = format!("{}/{}", self.base_url, path);
        println!("Posting to: {} with body: {}", url, body);
        
        // ISSUE: Blocking operation
        thread::sleep(Duration::from_millis(500));
        
        // ISSUE: No actual HTTP implementation
        "POST successful".to_string()
    }
}

// Configuration with poor error handling
#[derive(Debug)]
pub struct Config {
    pub database_url: String,
    pub server_port: u16,
    pub log_level: String,
}

impl Config {
    // ISSUE: Panics on missing environment variables
    pub fn from_env() -> Self {
        Self {
            database_url: std::env::var("DATABASE_URL")
                .expect("DATABASE_URL must be set"),
            server_port: std::env::var("SERVER_PORT")
                .expect("SERVER_PORT must be set")
                .parse()
                .expect("SERVER_PORT must be a valid number"),
            log_level: std::env::var("LOG_LEVEL")
                .unwrap_or_else(|_| "info".to_string()),
        }
    }

    // ISSUE: Panics on file not found or invalid format
    pub fn from_file(path: &str) -> Self {
        let content = fs::read_to_string(path)
            .expect("Failed to read config file");
        
        // ISSUE: Panics on invalid JSON
        serde_json::from_str(&content)
            .expect("Failed to parse config file")
    }
}

// Main function with various issues
fn main() {
    println!("Starting file processing service...");

    // ISSUE: Panics if environment variable not set
    let base_path = std::env::var("BASE_PATH")
        .expect("BASE_PATH environment variable must be set");

    let mut processor = FileProcessor::new(base_path);
    let mut user_manager = UserManager::new();
    let data_processor = DataProcessor::new();
    let client = NetworkClient::new("https://api.example.com".to_string());

    // ISSUE: Lifetime issues with string literals
    let user_id = user_manager.add_user("John Doe", "john@example.com", "Software Developer");
    println!("Created user with ID: {}", user_id);

    // ISSUE: Will panic if user not found
    let user = user_manager.get_user(user_id);
    println!("User: {:?}", user);

    // ISSUE: Will panic if file operations fail
    processor.write_file("test.txt", "Hello, World!");
    let content = processor.read_file("test.txt");
    println!("File content: {}", content);

    // ISSUE: Blocking operations
    let response = client.get("users");
    println!("API response: {}", response);

    // ISSUE: Will panic if config loading fails
    let config = Config::from_env();
    println!("Config: {:?}", config);

    println!("Service started successfully!");
}

// Example of how to add proper error handling (commented out)
/*
// Custom error types that should be implemented
#[derive(Debug)]
pub enum FileError {
    NotFound(String),
    PermissionDenied(String),
    TooLarge { size: u64, max_size: u64 },
    IoError(io::Error),
}

#[derive(Debug)]
pub enum UserError {
    NotFound(u32),
    InvalidEmail(String),
    DuplicateEmail(String),
}

// Trait that should be extracted
pub trait Processor {
    type Error;
    
    fn process(&self, data: &str) -> Result<String, Self::Error>;
    fn process_file(&self, filepath: &str) -> Result<String, Self::Error>;
}

// Async version of NetworkClient that should be implemented
pub struct AsyncNetworkClient {
    base_url: String,
    timeout: Duration,
}

impl AsyncNetworkClient {
    pub async fn get(&self, path: &str) -> Result<String, reqwest::Error> {
        // Proper async HTTP implementation
        todo!()
    }
    
    pub async fn post(&self, path: &str, body: &str) -> Result<String, reqwest::Error> {
        // Proper async HTTP implementation
        todo!()
    }
}
*/

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_user_manager() {
        let mut manager = UserManager::new();
        let id = manager.add_user("Test", "test@example.com", "Tester");
        assert_eq!(id, 1);
    }

    #[test]
    #[should_panic(expected = "User not found")]
    fn test_user_not_found_panics() {
        let manager = UserManager::new();
        manager.get_user(999); // Should panic
    }

    #[test]
    fn test_data_processor() {
        let processor = DataProcessor::new();
        let result = processor.process("hello world");
        assert_eq!(result, "hello world");
    }
}
