# Database Schema Updates for Communication Service

This document describes the database schema changes required to implement the communication service's email batching and phone call scheduling functionality.

## Overview of Changes

The following updates to the database schema are needed:

1. **Therapist Model Updates**:
   - Add potentially available flag
   - Add field for notes about potential availability
   - Define JSON structure for telephone availability times

2. **New Tables**:
   - Email Batch table
   - Phone Call table
   - Phone Call Batch table

3. **Updates to Existing Tables**:
   - Add additional fields to Email table
   - Add relationship fields to Placement Request table

## Detailed Schema Changes

### 1. Therapist Table Updates

The `therapists` table requires the following new fields:

```sql
-- Add to the existing therapists table
ALTER TABLE therapist_service.therapists
ADD COLUMN potentially_available BOOLEAN DEFAULT FALSE,
ADD COLUMN potentially_available_notes TEXT;
```

The `telefonische_erreichbarkeit` field already exists as a JSONB column, but we need to establish a standard format for it:

```json
{
  "monday": [
    {"start": "09:00", "end": "12:00"},
    {"start": "14:00", "end": "16:30"}
  ],
  "wednesday": [
    {"start": "10:00", "end": "14:00"}
  ],
  "friday": [
    {"start": "08:30", "end": "11:30"}
  ]
}
```

This structure will be enforced at the application level, not the database level.

### 2. Phone Call Table

A new table for tracking scheduled and completed phone calls:

```sql
CREATE TABLE communication_service.phone_calls (
    id SERIAL PRIMARY KEY,
    therapist_id INTEGER NOT NULL,
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 5,
    actual_date DATE,
    actual_time TIME,
    status VARCHAR(20) CHECK (status IN ('scheduled', 'completed', 'failed', 'canceled')),
    outcome TEXT,
    notes TEXT,
    retry_after DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_phone_calls_therapist_id ON communication_service.phone_calls(therapist_id);
CREATE INDEX idx_phone_calls_scheduled_date ON communication_service.phone_calls(scheduled_date);
CREATE INDEX idx_phone_calls_status ON communication_service.phone_calls(status);
```

### 3. Phone Call Batch Table

A table to connect phone calls to placement requests:

```sql
CREATE TABLE communication_service.phone_call_batches (
    id SERIAL PRIMARY KEY,
    phone_call_id INTEGER NOT NULL,
    placement_request_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 1,
    discussed BOOLEAN DEFAULT FALSE,
    outcome VARCHAR(50),
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (phone_call_id, placement_request_id),
    FOREIGN KEY (phone_call_id) REFERENCES communication_service.phone_calls(id) ON DELETE CASCADE,
    FOREIGN KEY (placement_request_id) REFERENCES matching_service.placement_requests(id) ON DELETE CASCADE
);

CREATE INDEX idx_phone_call_batches_phone_call_id ON communication_service.phone_call_batches(phone_call_id);
CREATE INDEX idx_phone_call_batches_placement_request_id ON communication_service.phone_call_batches(placement_request_id);
```

### 4. Email Batch Table

A table to connect emails to placement requests:

```sql
CREATE TABLE communication_service.email_batches (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL,
    placement_request_id INTEGER NOT NULL,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (email_id, placement_request_id),
    FOREIGN KEY (email_id) REFERENCES communication_service.emails(id) ON DELETE CASCADE,
    FOREIGN KEY (placement_request_id) REFERENCES matching_service.placement_requests(id) ON DELETE CASCADE
);

CREATE INDEX idx_email_batches_email_id ON communication_service.email_batches(email_id);
CREATE INDEX idx_email_batches_placement_request_id ON communication_service.email_batches(placement_request_id);
```

### 5. Updates to Email Table

The existing `emails` table already has most of the needed fields but should be updated:

```sql
-- Add to existing emails table if these fields don't exist
ALTER TABLE communication_service.emails
ADD COLUMN batch_id VARCHAR(50),
ADD COLUMN response_received BOOLEAN DEFAULT FALSE,
ADD COLUMN response_date TIMESTAMP,
ADD COLUMN response_content TEXT,
ADD COLUMN follow_up_required BOOLEAN DEFAULT FALSE,
ADD COLUMN follow_up_notes TEXT;
```

## Python SQLAlchemy Models

### 1. Updated Therapist Model

```python
class Therapist(Base):
    """Therapist database model."""

    __tablename__ = "therapists"
    __table_args__ = {"schema": "therapist_service"}

    # Existing fields...
    
    # New fields
    potentially_available = Column(Boolean, default=False)
    potentially_available_notes = Column(Text)
    
    # Helper methods for availability
    def get_available_slots(self, date=None):
        """Get available time slots for a given date.
        
        Args:
            date: Optional date to filter slots (default: all slots)
            
        Returns:
            Dictionary of day -> list of time slots
        """
        availability = self.telefonische_erreichbarkeit or {}
        
        if date is None:
            return availability
            
        day_name = date.strftime("%A").lower()
        return {day_name: availability.get(day_name, [])}
    
    def is_available_at(self, date, time):
        """Check if therapist is available at a specific date and time.
        
        Args:
            date: Date to check
            time: Time string in format "HH:MM"
            
        Returns:
            Boolean indicating if therapist is available
        """
        day_name = date.strftime("%A").lower()
        day_slots = self.telefonische_erreichbarkeit.get(day_name, [])
        
        for slot in day_slots:
            if slot["start"] <= time <= slot["end"]:
                return True
                
        return False
```

### 2. Phone Call Model

```python
class PhoneCallStatus(str, Enum):
    """Enumeration for phone call status values."""

    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class PhoneCall(Base):
    """Phone call database model."""

    __tablename__ = "phone_calls"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    therapist_id = Column(Integer, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=5)
    actual_date = Column(Date)
    actual_time = Column(Time)
    status = Column(
        SQLAlchemyEnum(PhoneCallStatus),
        default=PhoneCallStatus.SCHEDULED
    )
    outcome = Column(Text)
    notes = Column(Text)
    retry_after = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationship
    placement_requests = relationship(
        "PlacementRequest",
        secondary="communication_service.phone_call_batches",
        back_populates="phone_calls"
    )
    
    def __repr__(self):
        """Provide a string representation of the PhoneCall instance."""
        return (
            f"<PhoneCall id={self.id} therapist_id={self.therapist_id} "
            f"scheduled={self.scheduled_date} {self.scheduled_time} "
            f"status={self.status}>"
        )
```

### 3. Phone Call Batch Model

```python
class PhoneCallBatch(Base):
    """Phone call batch database model."""

    __tablename__ = "phone_call_batches"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    phone_call_id = Column(
        Integer,
        ForeignKey("communication_service.phone_calls.id", ondelete="CASCADE"),
        nullable=False
    )
    placement_request_id = Column(
        Integer,
        ForeignKey("matching_service.placement_requests.id", ondelete="CASCADE"),
        nullable=False
    )
    priority = Column(Integer, default=1)
    discussed = Column(Boolean, default=False)
    outcome = Column(String(50))
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    phone_call = relationship("PhoneCall", back_populates="batches")
    placement_request = relationship("PlacementRequest", back_populates="phone_call_batches")
    
    def __repr__(self):
        """Provide a string representation of the PhoneCallBatch instance."""
        return (
            f"<PhoneCallBatch id={self.id} "
            f"phone_call_id={self.phone_call_id} "
            f"placement_request_id={self.placement_request_id}>"
        )
```

### 4. Email Batch Model

```python
class EmailBatch(Base):
    """Email batch database model."""

    __tablename__ = "email_batches"
    __table_args__ = {"schema": "communication_service"}

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(
        Integer,
        ForeignKey("communication_service.emails.id", ondelete="CASCADE"),
        nullable=False
    )
    placement_request_id = Column(
        Integer,
        ForeignKey("matching_service.placement_requests.id", ondelete="CASCADE"),
        nullable=False
    )
    priority = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    email = relationship("Email", back_populates="batches")
    placement_request = relationship("PlacementRequest", back_populates="email_batches")
    
    def __repr__(self):
        """Provide a string representation of the EmailBatch instance."""
        return (
            f"<EmailBatch id={self.id} "
            f"email_id={self.email_id} "
            f"placement_request_id={self.placement_request_id}>"
        )
```

### 5. Updated Email Model

```python
class Email(Base):
    """Email database model."""

    __tablename__ = "emails"
    __table_args__ = {"schema": "communication_service"}

    # Existing fields...
    
    # New fields
    batch_id = Column(String(50))
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    response_content = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_notes = Column(Text)
    
    # Relationships
    batches = relationship(
        "EmailBatch",
        back_populates="email",
        cascade="all, delete-orphan"
    )
    placement_requests = relationship(
        "PlacementRequest",
        secondary="communication_service.email_batches",
        back_populates="emails"
    )
```

### 6. Updated PlacementRequest Model

```python
class PlacementRequest(Base):
    """Placement request database model."""

    __tablename__ = "placement_requests"
    __table_args__ = {"schema": "matching_service"}

    # Existing fields...
    
    # Relationships
    emails = relationship(
        "Email",
        secondary="communication_service.email_batches",
        back_populates="placement_requests"
    )
    email_batches = relationship(
        "EmailBatch",
        back_populates="placement_request",
        cascade="all, delete-orphan"
    )
    phone_calls = relationship(
        "PhoneCall",
        secondary="communication_service.phone_call_batches",
        back_populates="placement_requests"
    )
    phone_call_batches = relationship(
        "PhoneCallBatch",
        back_populates="placement_request",
        cascade="all, delete-orphan"
    )
```

## Migration Script

Here's the Alembic migration script that would implement these changes:

```python
"""add communication batching tables

Revision ID: 6efc92f7c7g9
Revises: 5dfc91e6b6f9
Create Date: 2025-05-06 15:30:08.196334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6efc92f7c7g9'
down_revision: Union[str, None] = '5dfc91e6b6f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add potentially available fields to therapist table
    op.add_column('therapists', 
                  sa.Column('potentially_available', sa.Boolean(), server_default='false'),
                  schema='therapist_service')
    op.add_column('therapists',
                  sa.Column('potentially_available_notes', sa.Text()),
                  schema='therapist_service')
                  
    # Create phone_call_status enum
    phone_call_status = sa.Enum('scheduled', 'completed', 'failed', 'canceled',
                               name='phonecallstatus')
    
    # Create phone_calls table
    op.create_table('phone_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('therapist_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('scheduled_time', sa.Time(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True, server_default='5'),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('actual_time', sa.Time(), nullable=True),
        sa.Column('status', phone_call_status, nullable=True),
        sa.Column('outcome', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('retry_after', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='communication_service'
    )
    
    # Create indexes for phone_calls
    op.create_index('idx_phone_calls_therapist_id', 'phone_calls', ['therapist_id'], 
                   schema='communication_service')
    op.create_index('idx_phone_calls_scheduled_date', 'phone_calls', ['scheduled_date'], 
                   schema='communication_service')
    op.create_index('idx_phone_calls_status', 'phone_calls', ['status'], 
                   schema='communication_service')
    
    # Create phone_call_batches table
    op.create_table('phone_call_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('phone_call_id', sa.Integer(), nullable=False),
        sa.Column('placement_request_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('discussed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('outcome', sa.String(length=50), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('follow_up_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['phone_call_id'], ['communication_service.phone_calls.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['placement_request_id'], ['matching_service.placement_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_call_id', 'placement_request_id'),
        schema='communication_service'
    )
    
    # Create indexes for phone_call_batches
    op.create_index('idx_phone_call_batches_phone_call_id', 'phone_call_batches', ['phone_call_id'], 
                   schema='communication_service')
    op.create_index('idx_phone_call_batches_placement_request_id', 'phone_call_batches', ['placement_request_id'], 
                   schema='communication_service')
    
    # Create email_batches table
    op.create_table('email_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('placement_request_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['email_id'], ['communication_service.emails.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['placement_request_id'], ['matching_service.placement_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email_id', 'placement_request_id'),
        schema='communication_service'
    )
    
    # Create indexes for email_batches
    op.create_index('idx_email_batches_email_id', 'email_batches', ['email_id'], 
                   schema='communication_service')
    op.create_index('idx_email_batches_placement_request_id', 'email_batches', ['placement_request_id'], 
                   schema='communication_service')
    
    # Add fields to existing emails table
    op.add_column('emails', 
                  sa.Column('batch_id', sa.String(length=50), nullable=True),
                  schema='communication_service')
    op.add_column('emails',
                  sa.Column('response_received', sa.Boolean(), nullable=True, server_default='false'),
                  schema='communication_service')
    op.add_column('emails',
                  sa.Column('response_date', sa.DateTime(), nullable=True),
                  schema='communication_service')
    op.add_column('emails',
                  sa.Column('response_content', sa.Text(), nullable=True),
                  schema='communication_service')
    op.add_column('emails',
                  sa.Column('follow_up_required', sa.Boolean(), nullable=True, server_default='false'),
                  schema='communication_service')
    op.add_column('emails',
                  sa.Column('follow_up_notes', sa.Text(), nullable=True),
                  schema='communication_service')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop added columns from emails table
    op.drop_column('emails', 'follow_up_notes', schema='communication_service')
    op.drop_column('emails', 'follow_up_required', schema='communication_service')
    op.drop_column('emails', 'response_content', schema='communication_service')
    op.drop_column('emails', 'response_date', schema='communication_service')
    op.drop_column('emails', 'response_received', schema='communication_service')
    op.drop_column('emails', 'batch_id', schema='communication_service')
    
    # Drop email_batches table and indexes
    op.drop_index('idx_email_batches_placement_request_id', table_name='email_batches', 
                 schema='communication_service')
    op.drop_index('idx_email_batches_email_id', table_name='email_batches', 
                 schema='communication_service')
    op.drop_table('email_batches', schema='communication_service')
    
    # Drop phone_call_batches table and indexes
    op.drop_index('idx_phone_call_batches_placement_request_id', table_name='phone_call_batches', 
                 schema='communication_service')
    op.drop_index('idx_phone_call_batches_phone_call_id', table_name='phone_call_batches', 
                 schema='communication_service')
    op.drop_table('phone_call_batches', schema='communication_service')
    
    # Drop phone_calls table and indexes
    op.drop_index('idx_phone_calls_status', table_name='phone_calls', 
                 schema='communication_service')
    op.drop_index('idx_phone_calls_scheduled_date', table_name='phone_calls', 
                 schema='communication_service')
    op.drop_index('idx_phone_calls_therapist_id', table_name='phone_calls', 
                 schema='communication_service')
    op.drop_table('phone_calls', schema='communication_service')
    
    # Drop the enum type
    sa.Enum(name='phonecallstatus').drop(op.get_bind())
    
    # Drop added columns from therapists table
    op.drop_column('therapists', 'potentially_available_notes', schema='therapist_service')
    op.drop_column('therapists', 'potentially_available', schema='therapist_service')
```

## Implementation Guidelines

When implementing these database changes:

1. **Run migrations in order**:
   - Ensure that all previous migrations have been applied first
   - Test the migration in a development environment before production

2. **Data consistency checks**:
   - Validate the JSON structure of `telefonische_erreichbarkeit` at the application level
   - Implement validators for time slot formats

3. **Relationships**:
   - Ensure proper cascading deletes to avoid orphaned records
   - Add appropriate foreign key constraints

4. **Indexing strategy**:
   - The indexes created focus on common query patterns
   - Additional indexes may be needed based on actual query patterns

5. **Performance considerations**:
   - The JSONB field for availability allows for flexible storage but may impact query performance
   - Consider adding GIN indexes for JSONB fields if querying them directly