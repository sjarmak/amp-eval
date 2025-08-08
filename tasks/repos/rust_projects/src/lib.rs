// Library file for testing the refactored modules

pub mod file_processor;
pub mod user_manager;
pub mod data_processor;
pub mod network_client;
pub mod config;
pub mod errors;

// Re-export main types for easier testing
pub use file_processor::FileProcessor;
pub use user_manager::{UserManager, User};
pub use data_processor::DataProcessor;
pub use network_client::NetworkClient;
pub use config::Config;
pub use errors::*;
