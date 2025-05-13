"""init migr

Revision ID: 6b6b8442f981
Revises: 
Create Date: 2025-05-13 06:35:56.204740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '6b6b8442f981'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), unique=True),
        sa.Column('password', sa.String()),
    )

    # Создание таблицы chats
    op.create_table(
        'chats',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String()),
        sa.Column('chat_type', sa.Enum('private', 'group', name='chat_type'), server_default='private'),
    )

    # Создание таблицы groups
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('chat_id', sa.Integer(), sa.ForeignKey('chats.id'), nullable=False, index=True),
        sa.Column('name', sa.String()),
        sa.Column('creator_id', sa.Integer(), sa.ForeignKey('users.id')),
    )

    # Создание таблицы messages
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('chat_id', sa.Integer(), sa.ForeignKey('chats.id'), nullable=False),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True)),
        sa.Column('client_message_id', sa.String(), unique=True, nullable=True, index=True),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Создание таблицы group_members (many-to-many)
    op.create_table(
        'group_members',
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('groups.id'), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
    )

    # Создание таблицы chat_users (many-to-many)
    op.create_table(
        'chat_users',
        sa.Column('chat_id', sa.Integer(), sa.ForeignKey('chats.id'), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Удаление таблиц в обратном порядке (чтобы не нарушить зависимости)
    op.drop_table('chat_users')
    op.drop_table('group_members')
    op.drop_table('messages')
    op.drop_table('groups')
    op.drop_table('chats')
    op.drop_table('users')
