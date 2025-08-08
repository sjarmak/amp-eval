"""Notification service with circular import issues."""
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# This creates circular import with user_manager.py
from user_manager import UserManager
# This creates circular import with message_handler.py
from message_handler import MessageHandler


@dataclass
class Notification:
    """Notification data class."""
    notification_id: str
    user_id: str
    title: str
    content: str
    timestamp: datetime
    is_read: bool = False
    notification_type: str = "general"


class NotificationService:
    """Notification service with circular dependencies."""
    
    def __init__(self, user_manager: UserManager):
        # Circular dependency - UserManager also imports NotificationService
        self.user_manager = user_manager
        self.notifications: Dict[str, List[Notification]] = {}
        # This creates another potential circular import
        self.message_handler: Optional[MessageHandler] = None
    
    def set_message_handler(self, message_handler: MessageHandler):
        """Set message handler - creates circular dependency."""
        self.message_handler = message_handler
    
    def send_notification(self, user_id: str, content: str, title: str = "Notification"):
        """Send a notification to a user."""
        # Check if user exists - calls back to user_manager
        user = self.user_manager.get_user(user_id)
        if not user:
            return
        
        notification_id = f"notif_{datetime.now().timestamp()}"
        notification = Notification(
            notification_id=notification_id,
            user_id=user_id,
            title=title,
            content=content,
            timestamp=datetime.now()
        )
        
        if user_id not in self.notifications:
            self.notifications[user_id] = []
        self.notifications[user_id].append(notification)
    
    def send_welcome_notification(self, user_id: str):
        """Send welcome notification to new user."""
        self.send_notification(
            user_id,
            "Welcome to our messaging platform!",
            "Welcome"
        )
    
    def send_message_notification(self, user_id: str, sender: str, content: str):
        """Send notification about new message."""
        # Get sender info - calls back to user_manager  
        sender_user = self.user_manager.get_user(sender)
        sender_name = sender_user.username if sender_user else sender
        
        self.send_notification(
            user_id,
            f"New message from {sender_name}: {content[:50]}...",
            "New Message"
        )
    
    def send_friend_request_accepted(self, user_id: str, friend_id: str):
        """Send notification about friend request acceptance."""
        # Get friend info - calls back to user_manager
        friend = self.user_manager.get_user(friend_id)
        friend_name = friend.username if friend else friend_id
        
        self.send_notification(
            user_id,
            f"{friend_name} is now your friend!",
            "Friend Request Accepted"
        )
    
    def notify_friends_status_change(self, user_id: str, online: bool):
        """Notify friends about user status change."""
        # Get user and friends - calls back to user_manager
        user = self.user_manager.get_user(user_id)
        if not user:
            return
        
        status = "online" if online else "offline"
        
        for friend_id in user.friends:
            friend = self.user_manager.get_user(friend_id)
            if friend and friend.is_online:  # Only notify online friends
                self.send_notification(
                    friend_id,
                    f"{user.username} is now {status}",
                    "Friend Status"
                )
    
    def send_read_receipt(self, user_id: str, message_id: str):
        """Send read receipt notification."""
        self.send_notification(
            user_id,
            f"Your message {message_id} has been read",
            "Message Read"
        )
    
    def send_message_deleted_notification(self, user_id: str, message_id: str):
        """Send notification about message deletion."""
        self.send_notification(
            user_id,
            f"Message {message_id} has been deleted",
            "Message Deleted"
        )
    
    def get_user_notifications(self, user_id: str) -> List[Notification]:
        """Get all notifications for a user."""
        return self.notifications.get(user_id, [])
    
    def mark_notification_read(self, user_id: str, notification_id: str):
        """Mark notification as read."""
        user_notifications = self.get_user_notifications(user_id)
        for notification in user_notifications:
            if notification.notification_id == notification_id:
                notification.is_read = True
                break
    
    def get_unread_notification_count(self, user_id: str) -> int:
        """Get count of unread notifications."""
        user_notifications = self.get_user_notifications(user_id)
        return sum(1 for notif in user_notifications if not notif.is_read)
    
    def clear_user_notifications(self, user_id: str):
        """Clear all notifications for a user."""
        if user_id in self.notifications:
            del self.notifications[user_id]
