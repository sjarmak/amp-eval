"""User manager with circular import issues."""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# This creates circular import with message_handler.py
from message_handler import MessageHandler
# This creates circular import with notifications.py  
from notifications import NotificationService


@dataclass
class User:
    """User data class."""
    user_id: str
    username: str
    email: str
    is_online: bool = False
    last_seen: Optional[datetime] = None
    friends: List[str] = None
    
    def __post_init__(self):
        if self.friends is None:
            self.friends = []


class UserManager:
    """Manages users with circular dependencies."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        # Circular dependency - MessageHandler imports UserManager
        self.message_handler = MessageHandler(self)  
        # Circular dependency - NotificationService imports UserManager
        self.notification_service = NotificationService(self)
    
    def create_user(self, user_id: str, username: str, email: str) -> User:
        """Create a new user."""
        user = User(user_id, username, email)
        self.users[user_id] = user
        
        # This creates circular call through notification service
        self.notification_service.send_welcome_notification(user_id)
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)
    
    def set_user_online(self, user_id: str, online: bool):
        """Set user online status."""
        if user_id in self.users:
            self.users[user_id].is_online = online
            self.users[user_id].last_seen = datetime.now()
            
            # Notify friends about status change - creates circular dependency
            self.notification_service.notify_friends_status_change(user_id, online)
    
    def add_friend(self, user_id: str, friend_id: str):
        """Add friend relationship."""
        if user_id in self.users and friend_id in self.users:
            self.users[user_id].friends.append(friend_id)
            self.users[friend_id].friends.append(user_id)
            
            # Send notification through circular dependency
            self.notification_service.send_friend_request_accepted(user_id, friend_id)
    
    def send_message(self, from_user: str, to_user: str, content: str):
        """Send message between users."""
        # This calls back to message_handler which imported this module
        return self.message_handler.send_message(from_user, to_user, content)
    
    def get_user_messages(self, user_id: str):
        """Get messages for user."""
        # Another circular call
        return self.message_handler.get_user_messages(user_id)
    
    def get_online_friends(self, user_id: str) -> List[User]:
        """Get online friends of a user."""
        user = self.get_user(user_id)
        if not user:
            return []
        
        online_friends = []
        for friend_id in user.friends:
            friend = self.get_user(friend_id)
            if friend and friend.is_online:
                online_friends.append(friend)
        
        return online_friends
    
    def notify_user(self, user_id: str, message: str):
        """Notify a user - creates circular dependency."""
        self.notification_service.send_notification(user_id, message)
