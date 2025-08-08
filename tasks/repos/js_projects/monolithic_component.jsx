/**
 * Monolithic React component that needs to be split into smaller components
 * Contains multiple concerns that should be separated
 */

import React, { useState, useEffect } from 'react';

// Large monolithic component that needs refactoring
const UserDashboard = () => {
    const [user, setUser] = useState(null);
    const [posts, setPosts] = useState([]);
    const [friends, setFriends] = useState([]);
    const [notifications, setNotifications] = useState([]);
    const [settings, setSettings] = useState({});
    const [loading, setLoading] = useState(true);
    const [editingPost, setEditingPost] = useState(null);
    const [showSettings, setShowSettings] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);
    const [newPost, setNewPost] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [filteredFriends, setFilteredFriends] = useState([]);
    const [theme, setTheme] = useState('light');
    const [errors, setErrors] = useState({});

    useEffect(() => {
        // Simulate API calls
        fetchUserData();
        fetchPosts();
        fetchFriends();
        fetchNotifications();
        fetchSettings();
    }, []);

    useEffect(() => {
        // Filter friends based on search
        const filtered = friends.filter(friend => 
            friend.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            friend.email.toLowerCase().includes(searchQuery.toLowerCase())
        );
        setFilteredFriends(filtered);
    }, [friends, searchQuery]);

    const fetchUserData = async () => {
        try {
            // Simulate API call
            const response = await fetch('/api/user');
            const userData = await response.json();
            setUser(userData);
        } catch (error) {
            setErrors(prev => ({...prev, user: 'Failed to load user data'}));
        }
    };

    const fetchPosts = async () => {
        try {
            const response = await fetch('/api/posts');
            const postsData = await response.json();
            setPosts(postsData);
        } catch (error) {
            setErrors(prev => ({...prev, posts: 'Failed to load posts'}));
        }
    };

    const fetchFriends = async () => {
        try {
            const response = await fetch('/api/friends');
            const friendsData = await response.json();
            setFriends(friendsData);
        } catch (error) {
            setErrors(prev => ({...prev, friends: 'Failed to load friends'}));
        } finally {
            setLoading(false);
        }
    };

    const fetchNotifications = async () => {
        try {
            const response = await fetch('/api/notifications');
            const notificationsData = await response.json();
            setNotifications(notificationsData);
        } catch (error) {
            setErrors(prev => ({...prev, notifications: 'Failed to load notifications'}));
        }
    };

    const fetchSettings = async () => {
        try {
            const response = await fetch('/api/settings');
            const settingsData = await response.json();
            setSettings(settingsData);
            setTheme(settingsData.theme || 'light');
        } catch (error) {
            setErrors(prev => ({...prev, settings: 'Failed to load settings'}));
        }
    };

    const createPost = async () => {
        if (!newPost.trim()) {
            setErrors(prev => ({...prev, newPost: 'Post content is required'}));
            return;
        }

        try {
            const response = await fetch('/api/posts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: newPost }),
            });
            
            const newPostData = await response.json();
            setPosts(prev => [newPostData, ...prev]);
            setNewPost('');
            setErrors(prev => ({...prev, newPost: null}));
        } catch (error) {
            setErrors(prev => ({...prev, newPost: 'Failed to create post'}));
        }
    };

    const updatePost = async (postId, content) => {
        try {
            const response = await fetch(`/api/posts/${postId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content }),
            });
            
            const updatedPost = await response.json();
            setPosts(prev => prev.map(post => 
                post.id === postId ? updatedPost : post
            ));
            setEditingPost(null);
        } catch (error) {
            setErrors(prev => ({...prev, editPost: 'Failed to update post'}));
        }
    };

    const deletePost = async (postId) => {
        try {
            await fetch(`/api/posts/${postId}`, {
                method: 'DELETE',
            });
            
            setPosts(prev => prev.filter(post => post.id !== postId));
        } catch (error) {
            setErrors(prev => ({...prev, deletePost: 'Failed to delete post'}));
        }
    };

    const addFriend = async (friendId) => {
        try {
            const response = await fetch('/api/friends', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ friendId }),
            });
            
            const newFriend = await response.json();
            setFriends(prev => [...prev, newFriend]);
        } catch (error) {
            setErrors(prev => ({...prev, addFriend: 'Failed to add friend'}));
        }
    };

    const removeFriend = async (friendId) => {
        try {
            await fetch(`/api/friends/${friendId}`, {
                method: 'DELETE',
            });
            
            setFriends(prev => prev.filter(friend => friend.id !== friendId));
        } catch (error) {
            setErrors(prev => ({...prev, removeFriend: 'Failed to remove friend'}));
        }
    };

    const markNotificationRead = async (notificationId) => {
        try {
            await fetch(`/api/notifications/${notificationId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ read: true }),
            });
            
            setNotifications(prev => prev.map(notif => 
                notif.id === notificationId ? {...notif, read: true} : notif
            ));
        } catch (error) {
            setErrors(prev => ({...prev, notification: 'Failed to mark notification as read'}));
        }
    };

    const updateSettings = async (newSettings) => {
        try {
            const response = await fetch('/api/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newSettings),
            });
            
            const updatedSettings = await response.json();
            setSettings(updatedSettings);
            setTheme(updatedSettings.theme || 'light');
        } catch (error) {
            setErrors(prev => ({...prev, settings: 'Failed to update settings'}));
        }
    };

    if (loading) {
        return (
            <div className="loading-spinner">
                <div className="spinner"></div>
                <p>Loading your dashboard...</p>
            </div>
        );
    }

    return (
        <div className={`dashboard ${theme}`}>
            {/* Header Section - should be separate component */}
            <header className="dashboard-header">
                <div className="user-info">
                    <img src={user?.avatar} alt="Profile" className="avatar" />
                    <h1>Welcome back, {user?.name}!</h1>
                </div>
                <div className="header-actions">
                    <button 
                        onClick={() => setShowNotifications(!showNotifications)}
                        className="notification-btn"
                    >
                        Notifications ({notifications.filter(n => !n.read).length})
                    </button>
                    <button 
                        onClick={() => setShowSettings(!showSettings)}
                        className="settings-btn"
                    >
                        Settings
                    </button>
                </div>
            </header>

            {/* Notifications Panel - should be separate component */}
            {showNotifications && (
                <div className="notifications-panel">
                    <h3>Notifications</h3>
                    {notifications.length === 0 ? (
                        <p>No notifications</p>
                    ) : (
                        <ul>
                            {notifications.map(notification => (
                                <li 
                                    key={notification.id} 
                                    className={notification.read ? 'read' : 'unread'}
                                >
                                    <div className="notification-content">
                                        <p>{notification.message}</p>
                                        <small>{new Date(notification.createdAt).toLocaleString()}</small>
                                    </div>
                                    {!notification.read && (
                                        <button 
                                            onClick={() => markNotificationRead(notification.id)}
                                            className="mark-read-btn"
                                        >
                                            Mark as Read
                                        </button>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            )}

            {/* Settings Panel - should be separate component */}
            {showSettings && (
                <div className="settings-panel">
                    <h3>Settings</h3>
                    <div className="setting-group">
                        <label>Theme:</label>
                        <select 
                            value={theme} 
                            onChange={(e) => updateSettings({...settings, theme: e.target.value})}
                        >
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                        </select>
                    </div>
                    <div className="setting-group">
                        <label>Email Notifications:</label>
                        <input 
                            type="checkbox" 
                            checked={settings.emailNotifications || false}
                            onChange={(e) => updateSettings({...settings, emailNotifications: e.target.checked})}
                        />
                    </div>
                    <div className="setting-group">
                        <label>Privacy:</label>
                        <select 
                            value={settings.privacy || 'public'} 
                            onChange={(e) => updateSettings({...settings, privacy: e.target.value})}
                        >
                            <option value="public">Public</option>
                            <option value="friends">Friends Only</option>
                            <option value="private">Private</option>
                        </select>
                    </div>
                </div>
            )}

            <div className="dashboard-content">
                {/* Posts Section - should be separate component */}
                <div className="posts-section">
                    <h2>Posts</h2>
                    
                    {/* Create Post - should be separate component */}
                    <div className="create-post">
                        <textarea
                            value={newPost}
                            onChange={(e) => setNewPost(e.target.value)}
                            placeholder="What's on your mind?"
                            rows="3"
                        />
                        {errors.newPost && <p className="error">{errors.newPost}</p>}
                        <button onClick={createPost} className="post-btn">
                            Post
                        </button>
                    </div>

                    {/* Posts List - should be separate component */}
                    <div className="posts-list">
                        {posts.length === 0 ? (
                            <p>No posts yet. Create your first post!</p>
                        ) : (
                            posts.map(post => (
                                <div key={post.id} className="post">
                                    {editingPost === post.id ? (
                                        <div className="edit-post">
                                            <textarea
                                                defaultValue={post.content}
                                                onBlur={(e) => updatePost(post.id, e.target.value)}
                                                onKeyPress={(e) => {
                                                    if (e.key === 'Enter' && e.ctrlKey) {
                                                        updatePost(post.id, e.target.value);
                                                    }
                                                }}
                                            />
                                            <button onClick={() => setEditingPost(null)}>
                                                Cancel
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="post-content">
                                            <p>{post.content}</p>
                                            <div className="post-meta">
                                                <small>{new Date(post.createdAt).toLocaleString()}</small>
                                                <div className="post-actions">
                                                    <button onClick={() => setEditingPost(post.id)}>
                                                        Edit
                                                    </button>
                                                    <button onClick={() => deletePost(post.id)}>
                                                        Delete
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Friends Section - should be separate component */}
                <div className="friends-section">
                    <h2>Friends</h2>
                    
                    {/* Friend Search - should be separate component */}
                    <div className="friend-search">
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search friends..."
                        />
                    </div>

                    {/* Friends List - should be separate component */}
                    <div className="friends-list">
                        {filteredFriends.length === 0 ? (
                            <p>No friends found</p>
                        ) : (
                            <ul>
                                {filteredFriends.map(friend => (
                                    <li key={friend.id} className="friend-item">
                                        <img src={friend.avatar} alt={friend.name} className="friend-avatar" />
                                        <div className="friend-info">
                                            <h4>{friend.name}</h4>
                                            <p>{friend.email}</p>
                                            <span className={`status ${friend.online ? 'online' : 'offline'}`}>
                                                {friend.online ? 'Online' : 'Offline'}
                                            </span>
                                        </div>
                                        <button 
                                            onClick={() => removeFriend(friend.id)}
                                            className="remove-friend-btn"
                                        >
                                            Remove
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                </div>
            </div>

            {/* Error Display - should be separate component */}
            {Object.keys(errors).length > 0 && (
                <div className="error-panel">
                    <h4>Errors:</h4>
                    <ul>
                        {Object.entries(errors).map(([key, error]) => 
                            error && <li key={key}>{error}</li>
                        )}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default UserDashboard;
