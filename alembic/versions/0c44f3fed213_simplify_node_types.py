"""simplify node types

Revision ID: 0c44f3fed213
Revises: 70319cbe8799
Create Date: 2025-06-15 23:06:45.887961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0c44f3fed213'
down_revision: Union[str, None] = '70319cbe8799'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 创建一个临时表来更新节点类型
    op.execute("UPDATE document_nodes SET node_type = 'TEXT' WHERE node_type IN ('SECTION', 'LIST')")
    
    # 2. 删除原有枚举类型并重新创建
    # PostgreSQL特有操作，SQLite不需要这步
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # 创建新的枚举类型
        op.execute("ALTER TYPE nodetype RENAME TO nodetype_old")
        op.execute("CREATE TYPE nodetype AS ENUM('HEADER', 'TABLE', 'IMAGE', 'TEXT')")
        
        # 使用USING将列转换为新的枚举类型
        op.execute("ALTER TABLE document_nodes ALTER COLUMN node_type TYPE nodetype USING node_type::text::nodetype")
        
        # 删除旧的枚举类型
        op.execute("DROP TYPE nodetype_old")


def downgrade() -> None:
    """Downgrade schema."""
    # 还原枚举类型
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # 创建原来的枚举类型
        op.execute("ALTER TYPE nodetype RENAME TO nodetype_new")
        op.execute("CREATE TYPE nodetype AS ENUM('SECTION', 'HEADER', 'TABLE', 'IMAGE', 'TEXT', 'LIST')")
        
        # 使用USING将列转换为原来的枚举类型
        op.execute("ALTER TABLE document_nodes ALTER COLUMN node_type TYPE nodetype USING node_type::text::nodetype")
        
        # 删除临时枚举类型
        op.execute("DROP TYPE nodetype_new")
