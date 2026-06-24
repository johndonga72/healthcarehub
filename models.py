from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
# Initialize SQLAlchemy
db = SQLAlchemy()
class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    customer_name = db.Column(
        db.String(100),
        nullable=False
    )
    phone_number = db.Column(
        db.String(20),
        nullable=False
    )
    appointment_time = db.Column(
        db.DateTime,
        nullable=False
    )
    notification_status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    def __repr__(self):
        return (
            f"<Appointment "
            f"id={self.id}, "
            f"customer='{self.customer_name}', "
            f"time='{self.appointment_time}'>"
        )
    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "phone_number": self.phone_number,
            "appointment_time": self.appointment_time.isoformat(),
            "notification_status": self.notification_status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }