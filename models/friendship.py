from datetime import datetime
from extensions import db

class Friendship(db.Model):
    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    addressee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / accepted / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        friend = self.addressee if self.status == "accepted" else self.addressee
        return {
            "id": self.id,
            "requester_id": self.requester_id,
            "requester_name": self.requester.full_name if self.requester else None,
            "requester_avatar": self.requester.avatar_url if self.requester else None,
            "addressee_id": self.addressee_id,
            "addressee_name": self.addressee.full_name if self.addressee else None,
            "addressee_avatar": self.addressee.avatar_url if self.addressee else None,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
