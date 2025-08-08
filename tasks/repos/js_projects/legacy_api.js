/**
 * Legacy API client with callback hell and no types
 * Needs conversion to TypeScript with async/await
 */

const https = require('https');
const fs = require('fs');

// Callback hell example - needs refactoring to async/await
function fetchUserData(userId, callback) {
    const options = {
        hostname: 'api.example.com',
        port: 443,
        path: `/users/${userId}`,
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token123'
        }
    };

    const req = https.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            try {
                const userData = JSON.parse(data);
                
                // Nested callback to fetch user posts
                fetchUserPosts(userId, (err, posts) => {
                    if (err) {
                        callback(err, null);
                        return;
                    }
                    
                    // Another nested callback to fetch user profile
                    fetchUserProfile(userId, (err, profile) => {
                        if (err) {
                            callback(err, null);
                            return;
                        }
                        
                        // Even more nesting to save data
                        saveUserToFile(userId, {
                            user: userData,
                            posts: posts,
                            profile: profile
                        }, (err) => {
                            if (err) {
                                callback(err, null);
                                return;
                            }
                            
                            callback(null, {
                                user: userData,
                                posts: posts,
                                profile: profile
                            });
                        });
                    });
                });
                
            } catch (error) {
                callback(error, null);
            }
        });
    });
    
    req.on('error', (error) => {
        callback(error, null);
    });
    
    req.end();
}

function fetchUserPosts(userId, callback) {
    const options = {
        hostname: 'api.example.com',
        port: 443,
        path: `/users/${userId}/posts`,
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token123'
        }
    };

    const req = https.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            try {
                const posts = JSON.parse(data);
                callback(null, posts);
            } catch (error) {
                callback(error, null);
            }
        });
    });
    
    req.on('error', (error) => {
        callback(error, null);
    });
    
    req.end();
}

function fetchUserProfile(userId, callback) {
    const options = {
        hostname: 'api.example.com',
        port: 443,
        path: `/users/${userId}/profile`,
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token123'
        }
    };

    const req = https.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
            data += chunk;
        });
        
        res.on('end', () => {
            try {
                const profile = JSON.parse(data);
                callback(null, profile);
            } catch (error) {
                callback(error, null);
            }
        });
    });
    
    req.on('error', (error) => {
        callback(error, null);
    });
    
    req.end();
}

function saveUserToFile(userId, userData, callback) {
    const filename = `user_${userId}.json`;
    const dataString = JSON.stringify(userData, null, 2);
    
    fs.writeFile(filename, dataString, 'utf8', (err) => {
        if (err) {
            callback(err);
            return;
        }
        callback(null);
    });
}

// Usage example with callback hell
function getUserCompleteData(userId) {
    fetchUserData(userId, (err, data) => {
        if (err) {
            console.error('Error fetching user data:', err);
            return;
        }
        
        console.log('User data fetched successfully:', data);
        
        // More callback nesting for additional operations
        processUserData(data, (err, processedData) => {
            if (err) {
                console.error('Error processing user data:', err);
                return;
            }
            
            sendNotification(userId, processedData, (err) => {
                if (err) {
                    console.error('Error sending notification:', err);
                    return;
                }
                
                console.log('All operations completed successfully');
            });
        });
    });
}

function processUserData(userData, callback) {
    // Simulate async processing
    setTimeout(() => {
        const processed = {
            ...userData,
            processedAt: new Date().toISOString(),
            postCount: userData.posts ? userData.posts.length : 0,
            hasProfile: !!userData.profile
        };
        callback(null, processed);
    }, 100);
}

function sendNotification(userId, data, callback) {
    // Simulate sending notification
    setTimeout(() => {
        console.log(`Notification sent to user ${userId}`);
        callback(null);
    }, 50);
}

// Export functions for use
module.exports = {
    fetchUserData,
    fetchUserPosts,
    fetchUserProfile,
    saveUserToFile,
    getUserCompleteData,
    processUserData,
    sendNotification
};

// Example usage with error-prone patterns
function exampleUsage() {
    // This creates deep callback nesting
    getUserCompleteData('123');
    
    // Multiple concurrent requests without proper coordination
    fetchUserData('456', (err, data) => {
        console.log('User 456:', data);
    });
    
    fetchUserData('789', (err, data) => {
        console.log('User 789:', data);
    });
    
    // No error handling in many places
    fetchUserPosts('999', (err, posts) => {
        posts.forEach(post => {
            console.log(post.title); // Could crash if posts is null
        });
    });
}

// Simulate some API calls
if (require.main === module) {
    exampleUsage();
}
