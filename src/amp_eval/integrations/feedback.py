"""
Feedback collection and integration system for the Amp Evaluation Suite.
Handles user feedback, bug reports, and feature requests.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import requests
from pydantic import BaseModel, ValidationError


class FeedbackType(Enum):
    """Types of feedback that can be collected."""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    GENERAL_FEEDBACK = "general_feedback"
    PERFORMANCE_ISSUE = "performance_issue"
    DOCUMENTATION_ISSUE = "documentation_issue"


class Priority(Enum):
    """Priority levels for feedback items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FeedbackItem:
    """Represents a single piece of user feedback."""
    id: str
    user_id: str
    feedback_type: FeedbackType
    title: str
    description: str
    priority: Priority
    created_at: datetime
    updated_at: datetime
    status: str = "open"
    assignee: Optional[str] = None
    tags: List[str] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


class FeedbackRequest(BaseModel):
    """Pydantic model for validating feedback requests."""
    user_id: str
    feedback_type: str
    title: str
    description: str
    priority: str = "medium"
    tags: Optional[List[str]] = []
    metadata: Optional[Dict] = {}


class FeedbackManager:
    """Manages collection, storage, and processing of user feedback."""
    
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = db_path
        self.slack_webhook_url = os.getenv("SLACK_FEEDBACK_WEBHOOK")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo = os.getenv("GITHUB_REPO", "org/amp-eval")
        self._init_database()
    
    def _init_database(self):
        """Initialize the feedback database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    assignee TEXT,
                    tags TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_priority ON feedback(priority)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON feedback(status)
            """)
    
    def submit_feedback(self, feedback_data: Dict) -> str:
        """Submit new feedback item."""
        try:
            # Validate input
            request = FeedbackRequest(**feedback_data)
            
            # Create feedback item
            feedback_id = self._generate_feedback_id()
            feedback = FeedbackItem(
                id=feedback_id,
                user_id=request.user_id,
                feedback_type=FeedbackType(request.feedback_type),
                title=request.title,
                description=request.description,
                priority=Priority(request.priority),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=request.tags or [],
                metadata=request.metadata or {}
            )
            
            # Store in database
            self._save_feedback(feedback)
            
            # Send notifications
            self._notify_slack(feedback)
            
            # Create GitHub issue for bugs and feature requests
            if feedback.feedback_type in [FeedbackType.BUG_REPORT, FeedbackType.FEATURE_REQUEST]:
                self._create_github_issue(feedback)
            
            return feedback_id
            
        except ValidationError as e:
            raise ValueError(f"Invalid feedback data: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to submit feedback: {e}")
    
    def get_feedback(self, feedback_id: str) -> Optional[FeedbackItem]:
        """Retrieve a specific feedback item."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM feedback WHERE id = ?", (feedback_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return self._row_to_feedback(row)
            return None
    
    def list_feedback(
        self,
        feedback_type: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[FeedbackItem]:
        """List feedback items with optional filtering."""
        query = "SELECT * FROM feedback WHERE 1=1"
        params = []
        
        if feedback_type:
            query += " AND feedback_type = ?"
            params.append(feedback_type)
        
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_feedback(row) for row in rows]
    
    def update_feedback(self, feedback_id: str, updates: Dict) -> bool:
        """Update an existing feedback item."""
        allowed_fields = ['status', 'assignee', 'priority', 'tags', 'metadata']
        update_fields = []
        params = []
        
        for field, value in updates.items():
            if field not in allowed_fields:
                continue
            
            if field in ['tags', 'metadata']:
                value = json.dumps(value)
            
            update_fields.append(f"{field} = ?")
            params.append(value)
        
        if not update_fields:
            return False
        
        update_fields.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(feedback_id)
        
        query = f"UPDATE feedback SET {', '.join(update_fields)} WHERE id = ?"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.rowcount > 0
    
    def get_feedback_stats(self, days: int = 30) -> Dict:
        """Get feedback statistics for the specified time period."""
        since_date = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Total feedback by type
            cursor = conn.execute("""
                SELECT feedback_type, COUNT(*) as count
                FROM feedback
                WHERE created_at >= ?
                GROUP BY feedback_type
            """, (since_date.isoformat(),))
            
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Total feedback by priority
            cursor = conn.execute("""
                SELECT priority, COUNT(*) as count
                FROM feedback
                WHERE created_at >= ?
                GROUP BY priority
            """, (since_date.isoformat(),))
            
            by_priority = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Total feedback by status
            cursor = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM feedback
                WHERE created_at >= ?
                GROUP BY status
            """, (since_date.isoformat(),))
            
            by_status = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Average response time for closed items
            cursor = conn.execute("""
                SELECT AVG(
                    julianday(updated_at) - julianday(created_at)
                ) as avg_days
                FROM feedback
                WHERE status = 'closed' AND created_at >= ?
            """, (since_date.isoformat(),))
            
            avg_response_time = cursor.fetchone()[0] or 0
            
            return {
                "period_days": days,
                "total_feedback": sum(by_type.values()),
                "by_type": by_type,
                "by_priority": by_priority,
                "by_status": by_status,
                "avg_response_time_days": round(avg_response_time, 2)
            }
    
    def _generate_feedback_id(self) -> str:
        """Generate a unique feedback ID."""
        import uuid
        return f"FB-{uuid.uuid4().hex[:8].upper()}"
    
    def _save_feedback(self, feedback: FeedbackItem):
        """Save feedback item to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO feedback (
                    id, user_id, feedback_type, title, description,
                    priority, status, assignee, tags, metadata,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.id,
                feedback.user_id,
                feedback.feedback_type.value,
                feedback.title,
                feedback.description,
                feedback.priority.value,
                feedback.status,
                feedback.assignee,
                json.dumps(feedback.tags),
                json.dumps(feedback.metadata),
                feedback.created_at.isoformat(),
                feedback.updated_at.isoformat()
            ))
    
    def _row_to_feedback(self, row) -> FeedbackItem:
        """Convert database row to FeedbackItem."""
        return FeedbackItem(
            id=row['id'],
            user_id=row['user_id'],
            feedback_type=FeedbackType(row['feedback_type']),
            title=row['title'],
            description=row['description'],
            priority=Priority(row['priority']),
            status=row['status'],
            assignee=row['assignee'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    
    def _notify_slack(self, feedback: FeedbackItem):
        """Send Slack notification for new feedback."""
        if not self.slack_webhook_url:
            return
        
        priority_emoji = {
            Priority.LOW: "🟢",
            Priority.MEDIUM: "🟡", 
            Priority.HIGH: "🟠",
            Priority.CRITICAL: "🔴"
        }
        
        type_emoji = {
            FeedbackType.BUG_REPORT: "🐛",
            FeedbackType.FEATURE_REQUEST: "✨",
            FeedbackType.GENERAL_FEEDBACK: "💬",
            FeedbackType.PERFORMANCE_ISSUE: "⚡",
            FeedbackType.DOCUMENTATION_ISSUE: "📚"
        }
        
        message = {
            "text": f"New Feedback: {feedback.title}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{type_emoji.get(feedback.feedback_type, '💬')} New Feedback Submitted"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Type:* {feedback.feedback_type.value.replace('_', ' ').title()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Priority:* {priority_emoji.get(feedback.priority, '')} {feedback.priority.value.title()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*User:* {feedback.user_id}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*ID:* {feedback.id}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{feedback.title}*\n{feedback.description[:200]}{'...' if len(feedback.description) > 200 else ''}"
                    }
                }
            ]
        }
        
        try:
            requests.post(self.slack_webhook_url, json=message, timeout=10)
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
    
    def _create_github_issue(self, feedback: FeedbackItem):
        """Create GitHub issue for bugs and feature requests."""
        if not self.github_token:
            return
        
        labels = ["feedback"]
        if feedback.feedback_type == FeedbackType.BUG_REPORT:
            labels.append("bug")
        elif feedback.feedback_type == FeedbackType.FEATURE_REQUEST:
            labels.append("enhancement")
        
        labels.append(f"priority-{feedback.priority.value}")
        
        issue_body = f"""
**Submitted by:** {feedback.user_id}
**Feedback ID:** {feedback.id}
**Priority:** {feedback.priority.value.title()}

{feedback.description}

---
*This issue was automatically created from user feedback.*
        """.strip()
        
        issue_data = {
            "title": feedback.title,
            "body": issue_body,
            "labels": labels
        }
        
        try:
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.post(
                f"https://api.github.com/repos/{self.github_repo}/issues",
                json=issue_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                issue_url = response.json()["html_url"]
                # Update feedback with GitHub issue URL
                self.update_feedback(feedback.id, {
                    "metadata": {**feedback.metadata, "github_issue": issue_url}
                })
            
        except Exception as e:
            print(f"Failed to create GitHub issue: {e}")


# CLI interface for feedback management
def main():
    """Command-line interface for feedback operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Amp Evaluation Feedback Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Submit feedback
    submit_parser = subparsers.add_parser("submit", help="Submit new feedback")
    submit_parser.add_argument("--user", required=True, help="User ID")
    submit_parser.add_argument("--type", required=True, choices=[t.value for t in FeedbackType])
    submit_parser.add_argument("--title", required=True, help="Feedback title")
    submit_parser.add_argument("--description", required=True, help="Feedback description")
    submit_parser.add_argument("--priority", choices=[p.value for p in Priority], default="medium")
    
    # List feedback
    list_parser = subparsers.add_parser("list", help="List feedback items")
    list_parser.add_argument("--type", choices=[t.value for t in FeedbackType])
    list_parser.add_argument("--priority", choices=[p.value for p in Priority])
    list_parser.add_argument("--status")
    list_parser.add_argument("--limit", type=int, default=10)
    
    # Show stats
    subparsers.add_parser("stats", help="Show feedback statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = FeedbackManager()
    
    if args.command == "submit":
        feedback_id = manager.submit_feedback({
            "user_id": args.user,
            "feedback_type": args.type,
            "title": args.title,
            "description": args.description,
            "priority": args.priority
        })
        print(f"Feedback submitted with ID: {feedback_id}")
    
    elif args.command == "list":
        items = manager.list_feedback(
            feedback_type=args.type,
            priority=args.priority,
            status=args.status,
            limit=args.limit
        )
        
        for item in items:
            print(f"[{item.id}] {item.title}")
            print(f"  Type: {item.feedback_type.value}, Priority: {item.priority.value}")
            print(f"  Status: {item.status}, Created: {item.created_at.strftime('%Y-%m-%d %H:%M')}")
            print()
    
    elif args.command == "stats":
        stats = manager.get_feedback_stats()
        print(f"Feedback Statistics (Last {stats['period_days']} days)")
        print(f"Total feedback: {stats['total_feedback']}")
        print(f"By type: {stats['by_type']}")
        print(f"By priority: {stats['by_priority']}")
        print(f"By status: {stats['by_status']}")
        print(f"Average response time: {stats['avg_response_time_days']} days")


if __name__ == "__main__":
    main()
