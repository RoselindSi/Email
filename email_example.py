# email_example.py  // Example usage of email_tool.py
from fastapi import FastAPI, HTTPException
from pathlib import Path
from typing import List
from pydantic import BaseModel, EmailStr
import os
from email_tool import AsyncGmailTool
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from typing import Optional
import pytz

# Create a FastAPI application
app = FastAPI()

# Store sensitive information using environment variables // You can also place them in env/settings/config and import as needed
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# Initialize the email tool
gmail_tool = AsyncGmailTool(
    smtp_username=GMAIL_USERNAME,
    smtp_password=GMAIL_APP_PASSWORD
)

# Initialize the scheduler for scheduled tasks / Can be added directly to the main file
scheduler = AsyncIOScheduler()
scheduler.start()

# Define request models
class EmailRequest(BaseModel):
    """Email request pydantic model"""
    to_emails: List[EmailStr]
    subject: str
    body: str
    html: bool = False

class EmailWithAttachmentRequest(EmailRequest):
    """Email request model with attachment"""
    attachment_paths: List[str] = []

class ScheduledEmailRequest(EmailRequest):
    """Scheduled email request model"""
    scheduled_time: datetime
    timezone: str = "America/New_York"

class UserRegistrationEvent(BaseModel):
    """User registration event model / Import the correct pydantic model as needed"""
    user_email: EmailStr
    username: str
    registration_time: datetime

# Basic email sending endpoint
@app.post("/send-email")
async def send_email(email_req: EmailRequest):
    """
    Send a basic email

    Example request:
    {
        "to_emails": ["recipient@example.com"],
        "subject": "Test email",
        "body": "This is a test email",
        "html": false
    }
    """
    result = await gmail_tool.send_email(
        to_emails=email_req.to_emails,
        subject=email_req.subject,
        body=email_req.body,
        html=email_req.html
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Email sending failed")
    
    return {"message": "Email sent successfully"}

# Endpoint example for sending HTML emails
@app.post("/send-html-email")
async def send_html_email(email_req: EmailRequest):
    """
    Send an HTML formatted email

    Example request:
    {
        "to_emails": ["recipient@example.com"],
        "subject": "HTML Test Email",
        "body": "<h1>Title</h1><p>This is a <strong>HTML</strong> test email</p>",
        "html": true
    }
    """
    # Ensure html is set to True
    email_req.html = True
    
    result = await gmail_tool.send_email(
        to_emails=email_req.to_emails,
        subject=email_req.subject,
        body=email_req.body,
        html=True
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Email sending failed")
    
    return {"message": "HTML email sent successfully"}

# Endpoint for sending emails with attachments
@app.post("/send-email-with-attachment")
async def send_email_with_attachment(email_req: EmailWithAttachmentRequest):
    """
    Send an email with attachments

    Example request:
    {
        "to_emails": ["recipient@example.com"],
        "subject": "Test email with attachment",
        "body": "This is a test email with attachments",
        "html": false,
        "attachment_paths": ["/path/to/file1.pdf", "/path/to/file2.jpg"]
    }
    """
    # Convert attachment paths to Path objects
    attachments = [Path(path) for path in email_req.attachment_paths]
    
    # Verify files exist
    for attachment in attachments:
        if not attachment.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Attachment not found: {attachment}"
            )
    
    result = await gmail_tool.send_email(
        to_emails=email_req.to_emails,
        subject=email_req.subject,
        body=email_req.body,
        html=email_req.html,
        attachments=attachments
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Email sending failed")
    
    return {"message": "Email with attachments sent successfully"}

# Example endpoint for sending template emails
@app.post("/send-template-email/{template_name}")
async def send_template_email(
    template_name: str,
    email_req: EmailRequest
):
    """
    Send a template email

    Args:
        template_name: Template name (welcome/notification/report)
        email_req: Email request data
    """
    # Template examples
    templates = {
        "welcome": """
            <h1>Welcome aboard!</h1>
            <p>Dear user:</p>
            <p>{body}</p>
            <p>Enjoy your experience!</p>
        """,
        "notification": """
            <div style="background-color: #f5f5f5; padding: 20px;">
                <h2>System Notification</h2>
                <p>{body}</p>
            </div>
        """,
        "report": """
            <div style="border: 1px solid #ddd; padding: 15px;">
                <h2>Report Summary</h2>
                <div>{body}</div>
            </div>
        """
    }
    
    if template_name not in templates:
        raise HTTPException(
            status_code=400,
            detail="Invalid template name"
        )
    
    # Format email content using template
    html_content = templates[template_name].format(body=email_req.body)
    
    result = await gmail_tool.send_email(
        to_emails=email_req.to_emails,
        subject=email_req.subject,
        body=html_content,
        html=True
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Email sending failed")
    
    return {"message": f"{template_name} template email sent successfully"}

@app.post("/schedule-email")
async def schedule_email(email_req: ScheduledEmailRequest):
    """
    Schedule an email to be sent at a specified time

    Example request:
    {
        "to_emails": ["recipient@example.com"],
        "subject": "Scheduled Test Email",
        "body": "This is a scheduled test email",
        "html": false,
        "scheduled_time": "2024-03-20T10:00:00",
        "timezone": "America/New_York"
    }
    """
    try:
        # Convert timezone
        tz = pytz.timezone(email_req.timezone)
        scheduled_time = tz.localize(email_req.scheduled_time)
        
        # Add a scheduled job
        job = scheduler.add_job(
            gmail_tool.send_email,
            'date',
            run_date=scheduled_time,
            kwargs={
                'to_emails': email_req.to_emails,
                'subject': email_req.subject,
                'body': email_req.body,
                'html': email_req.html
            }
        )
        
        return {
            "message": "Email successfully scheduled",
            "job_id": job.id,
            "scheduled_time": scheduled_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scheduling email failed: {str(e)}")

@app.post("/user-registration")
async def handle_user_registration(event: UserRegistrationEvent):
    """
    Handle a user registration event and send a welcome email

    Example request/Modify slightly as needed:
    {
        "user_email": "newuser@example.com",
        "username": "New User",
        "registration_time": "2024-03-19T15:30:00"
    }
    """
    # Send a welcome email immediately
    welcome_result = await gmail_tool.send_email(
        to_emails=[event.user_email],
        subject="Welcome aboard!",
        body=f"""
        <h1>Welcome {event.username}!</h1>
        <p>Thank you for registering.</p>
        <p>If you have any questions, feel free to contact our support team.</p>
        """,
        html=True
    )
    
    # Schedule a follow-up email 3 days later / Remove if not needed
    follow_up_time = event.registration_time + timedelta(days=3)
    scheduler.add_job(
        gmail_tool.send_email,
        'date',
        run_date=follow_up_time,
        kwargs={
            'to_emails': [event.user_email],
            'subject': "How are you enjoying it?",
            'body': f"""
            <h2>Dear {event.username}:</h2>
            <p>We hope you've enjoyed your experience over the past few days.</p>
            <p>We would love to hear your feedback, please reply directly to this email with any suggestions.</p>
            """,
            'html': True
        }
    )
    
    return {
        "message": "User registration event handled successfully",
        "welcome_email_sent": welcome_result,
        "follow_up_scheduled": follow_up_time.isoformat()
    }

@app.get("/scheduled-jobs")
async def get_scheduled_jobs():
    """Retrieve all scheduled email jobs"""
    jobs = scheduler.get_jobs()
    return {
        "jobs": [
            {
                "id": job.id,
                "run_time": job.next_run_time.isoformat(),
                "kwargs": job.kwargs
            }
            for job in jobs
        ]
    }

@app.delete("/cancel-scheduled-job/{job_id}")
async def cancel_scheduled_job(job_id: str):
    """Cancel a scheduled email job"""
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    scheduler.remove_job(job_id)
    return {"message": "Job cancelled"}

# Start the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
