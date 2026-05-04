"""Meeting service - business logic for meeting operations."""

import logging
import uuid
from typing import Dict
from config import settings

logger = logging.getLogger(__name__)


class MeetingService:
    
    # In-memory storage for demo purposes. Replace with database in production.
    _meetings: Dict[str, dict] = {}
    
    def generate_meeting_url(self) -> str:
        meeting_id = str(uuid.uuid4())[:8]
        logger.info(f"Generated meeting ID: {meeting_id}")
        
        # Store meeting for later reference
        self._meetings[meeting_id] = {
            "id": meeting_id,
            "status": "pending"
        }
        
        meeting_url = f"{settings.TERMEET_DOMAIN}/meet?id={meeting_id}"
        return meeting_url
    
    def get_meeting(self, meeting_id: str) -> dict:
        """
        Get meeting details.
        
        Args:
            meeting_id: ID of the meeting
            
        Returns:
            Dictionary with meeting data or empty dict if not found
        """
        return self._meetings.get(meeting_id, {})
    
    def update_meeting(self, meeting_id: str, data: dict) -> bool:
        if meeting_id in self._meetings:
            self._meetings[meeting_id].update(data)
            logger.info(f"Meeting {meeting_id} updated: {data}")
            return True
        return False
