# Depending on project requirements, scheduled tasks can be used
from datetime import datetime, timedelta
import httpx
import asyncio
import pytz

async def schedule_email_example():
    """Example of scheduling an email"""
    async with httpx.AsyncClient() as client:
        # Schedule an email
        scheduled_time = datetime.now() + timedelta(minutes=5)
        response = await client.post(
            "http://localhost:8000/schedule-email",
            json={
                "to_emails": ["recipient@example.com"],
                "subject": "Scheduled Test Email",
                "body": "This email will be sent in 5 minutes",
                "html": False,
                "scheduled_time": scheduled_time.isoformat(),
                "timezone": "America/New_York"
            }
        )
        print("Scheduled email reservation result:", response.json())
        
        # Simulate user registration
        registration_time = datetime.now()
        response = await client.post(
            "http://localhost:8000/user-registration",
            json={
                "user_email": "newuser@example.com",
                "username": "Zhang San",
                "registration_time": registration_time.isoformat()
            }
        )
        print("User registration email processing result:", response.json())
        
        # View all scheduled tasks
        response = await client.get("http://localhost:8000/scheduled-jobs")
        print("Current scheduled tasks:", response.json())

if __name__ == "__main__":
    asyncio.run(schedule_email_example())
