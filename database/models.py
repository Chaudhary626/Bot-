from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class DiscoveryType(enum.Enum):
    search = 'search'
    link = 'link'
    channel = 'channel'

class TargetAction(enum.Enum):
    like = 'like'
    comment = 'comment'
    watch = 'watch'
    subscribe = 'subscribe'

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_user_id = Column(Integer, unique=True, index=True)
    username = Column(String)
    strikes = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    videos = relationship("Video", back_populates="owner")
    tasks_given = relationship("Task", back_populates="giver", foreign_keys="Task.giver_id")
    tasks_received = relationship("Task", back_populates="receiver", foreign_keys="Task.receiver_id")

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    thumbnail_file_id = Column(String)
    video_link = Column(String)
    duration = Column(Integer)
    discovery_type = Column(Enum(DiscoveryType))
    target_actions = Column(String)  # CSV of TargetAction
    is_open = Column(Boolean, default=True)
    is_processing = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("User", back_populates="videos")
    tasks = relationship("Task", back_populates="video")

class TaskStatus(enum.Enum):
    pending = 'pending'
    proof_submitted = 'proof_submitted'
    accepted = 'accepted'
    rejected = 'rejected'
    disputed = 'disputed'

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    giver_id = Column(Integer, ForeignKey('users.id'))   # The user who gives the view
    receiver_id = Column(Integer, ForeignKey('users.id')) # The video owner
    status = Column(Enum(TaskStatus), default=TaskStatus.pending)
    assigned_at = Column(DateTime, server_default=func.now())
    proof_id = Column(Integer, ForeignKey('proofs.id'), nullable=True)
    skipped_step = Column(String, nullable=True)
    skip_reason = Column(Text, nullable=True)

    video = relationship("Video", back_populates="tasks")
    giver = relationship("User", back_populates="tasks_given", foreign_keys=[giver_id])
    receiver = relationship("User", back_populates="tasks_received", foreign_keys=[receiver_id])
    proof = relationship("Proof", uselist=False, back_populates="task")

class Proof(Base):
    __tablename__ = 'proofs'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    file_id = Column(String)
    submitted_by = Column(Integer, ForeignKey('users.id'))
    reviewed = Column(Boolean, default=False)
    accepted = Column(Boolean, default=None)
    created_at = Column(DateTime, server_default=func.now())

    task = relationship("Task", back_populates="proof")

class Dispute(Base):
    __tablename__ = 'disputes'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    reporter_id = Column(Integer, ForeignKey('users.id'))
    reason = Column(Text)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
