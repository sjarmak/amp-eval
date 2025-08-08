"""Message handler with circular import issues."""
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# This creates circular import with user_manager.py
from user_manager import UserManager
# This creates circular import with notifications.py
from notifications import NotificationService


@dataclass
class Message:
    """Message data class."""
    message_id: str
    from_user: str
    to_user: str
    content: str
    timestamp: datetime
    is_read: bool = False


class MessageHandler:
    """Handles messages with circular dependencies."""
    
    def __init__(self, user_manager: UserManager):
        # Circular dependency - UserManager also imports MessageHandler
        self.user_manager = user_manager
        self.messages: Dict[str, List[Message]] = {}
        # Another circular dependency
        self.notification_service = NotificationService(user_manager)
    
    def send_message(self, from_user: str, to_user: str, content: str) -> str:
        """Send a message between users."""
        # Check if users exist - calls back to user_manager
        sender = self.user_manager.get_user(from_user)
        recipient = self.user_manager.get_user(to_user)
        
        if not sender or not recipient:
            raise ValueError("Invalid user(s)")
        
        message_id = f"msg_{datetime.now().timestamp()}"
        message = Message(
            message_id=message_id,
            from_user=from_user,
            to_user=to_user,
            content=content,
            timestamp=datetime.now()
        )
        
        # Store message
        if to_user not in self.messages:
            self.messages[to_user] = []
        self.messages[to_user].append(message)
        
        # Send notification - creates circular dependency
        self.notification_service.send_message_notification(to_user, from_user, content)
        
        return message_id
    
    def get_user_messages(self, user_id: str) -> List[Message]:
        """Get all messages for a user."""
        return self.messages.get(user_id, [])
    
    def mark_message_read(self, user_id: str, message_id: str):
        """Mark a message as read."""
        user_messages = self.get_user_messages(user_id)
        for message in user_messages:
            if message.message_id == message_id:
                message.is_read = True
                # Notify sender that message was read
                self.notification_service.send_read_receipt(message.from_user, message_id)
                break
    
    def get_conversation(self, user1: str, user2: str) -> List[Message]:
        """Get conversation between two users."""
        messages = []
        
        # Get messages from user1 to user2
        user1_messages = self.get_user_messages(user2)
        for msg in user1_messages:
            if msg.from_user == user1:
                messages.append(msg)
        
        # Get messages from user2 to user1  
        user2_messages = self.get_user_messages(user1)
        for msg in user2_messages:
            if msg.from_user == user2:
                messages.append(msg)
        
        # Sort by timestamp
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    def delete_message(self, user_id: str, message_id: str):
        """Delete a message."""
        user_messages = self.get_user_messages(user_id)
        for i, message in enumerate(user_messages):
            if message.message_id == message_id:
                del user_messages[i]
                # Notify about deletion
                self.notification_service.send_message_deleted_notification(
                    message.from_user, message_id
                )
                break
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread messages."""
        user_messages = self.get_user_messages(user_id)
        return sum(1 for msg in user_messages if not msg.is_read)
    
    def broadcast_message(self, from_user: str, content: str):
        """Broadcast message to all online friends."""
        # Get sender's online friends - calls back to user_manager
        online_friends = self.user_manager.get_online_friends(from_user)
        
        for friend in online_friends:
            self.send_message(from_user, friend.user_id, content)
