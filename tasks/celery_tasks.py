from app import celery, mail
from flask_mail import Message
from datetime import datetime
from utils.reporting import generate_member_statement

@celery.task
def send_contribution_reminder(member_id):
    from models.members import Member
    member = Member.query.get(member_id)
    msg = Message("Contribution Reminder",
                 recipients=[member.email],
                 body=f"Dear {member.name}, please remember to submit your contribution.")
    mail.send(msg)

@celery.task
def generate_monthly_reports():
    members = Member.query.all()
    for member in members:
        report = generate_member_statement(member.id)
        # Save or email report