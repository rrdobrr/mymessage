from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Table
from src.core.db import Base

message_read_status = Table(
    'message_read_status',
    Base.metadata,
    Column('message_id', Integer, ForeignKey('messages.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('read_at', DateTime, nullable=False, default=datetime.utcnow),
) 