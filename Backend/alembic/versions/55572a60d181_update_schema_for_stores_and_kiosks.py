"""update_schema_for_stores_and_kiosks

Revision ID: 55572a60d181
Revises: bb1203ab14b1
Create Date: 2026-06-08 22:33:50.744918

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '55572a60d181'
down_revision: Union[str, Sequence[str], None] = 'bb1203ab14b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. RENAME TABLE
    op.rename_table('store_info', 'stores')
    
    # 2. RENAME INDEX
    op.drop_index('ix_store_info_id', table_name='stores')
    op.create_index(op.f('ix_stores_id'), 'stores', ['id'], unique=False)
    
    # 3. ADD COLUMNS (as nullable=True initially)
    op.add_column('stores', sa.Column('code', sa.String(length=6), nullable=True))
    op.add_column('stores', sa.Column('owner_name', sa.String(length=50), nullable=True))
    op.add_column('stores', sa.Column('status', sa.String(length=20), nullable=True))
    
    # 4. Fill values for existing rows to prevent Null errors
    connection = op.get_bind()
    
    # Set unique code (ST0001, ST0002...) for existing stores
    connection.execute(sa.text("""
        WITH numbered_stores AS (
            SELECT id, 'ST' || lpad(row_number() OVER (ORDER BY created_date)::text, 4, '0') as new_code
            FROM stores
        )
        UPDATE stores s
        SET code = ns.new_code
        FROM numbered_stores ns
        WHERE s.id = ns.id
    """))
    
    # Set owner_name from user_info table
    connection.execute(sa.text("""
        UPDATE stores s
        SET owner_name = u.name
        FROM user_info u
        WHERE s.user_id = u.id
    """))
    
    # Set default status ACTIVE
    connection.execute(sa.text("UPDATE stores SET status = 'ACTIVE'"))
    
    # 5. Make columns nullable=False and set default status
    op.alter_column('stores', 'code', nullable=False)
    op.alter_column('stores', 'status', nullable=False, server_default='ACTIVE')
    
    # 6. Create index & constraints for stores
    op.create_index(op.f('ix_stores_code'), 'stores', ['code'], unique=True)
    
    # 7. Create kiosks table
    op.create_table('kiosks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('code', sa.String(length=8), nullable=False),
        sa.Column('store_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=50), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('payment_status', sa.String(length=20), nullable=False),
        sa.Column('next_payment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['store_id'], ['stores.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kiosks_code'), 'kiosks', ['code'], unique=True)
    op.create_index(op.f('ix_kiosks_id'), 'kiosks', ['id'], unique=False)
    
    # 8. Update foreign keys and add new fields in related tables
    op.add_column('order_info', sa.Column('order_no', sa.String(length=32), nullable=True))
    op.create_index(op.f('ix_order_info_order_no'), 'order_info', ['order_no'], unique=False)
    op.drop_constraint('store_info_user_id_fkey', 'stores', type_='foreignkey')
    op.create_foreign_key(None, 'stores', 'user_info', ['user_id'], ['id'])
    
    op.drop_constraint('order_info_store_id_fkey', 'order_info', type_='foreignkey')
    op.create_foreign_key(None, 'order_info', 'stores', ['store_id'], ['id'])
    
    op.add_column('product_category', sa.Column('kiosk_id', sa.Uuid(), nullable=True))
    op.add_column('product_category', sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'))
    op.drop_constraint('product_category_store_id_fkey', 'product_category', type_='foreignkey')
    op.create_foreign_key(None, 'product_category', 'stores', ['store_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'product_category', 'kiosks', ['kiosk_id'], ['id'], ondelete='CASCADE')
    
    op.add_column('product_list', sa.Column('kiosk_id', sa.Uuid(), nullable=True))
    op.add_column('product_list', sa.Column('sequence', sa.Integer(), nullable=False, server_default='0'))
    op.drop_constraint('product_list_store_id_fkey', 'product_list', type_='foreignkey')
    op.create_foreign_key(None, 'product_list', 'kiosks', ['kiosk_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'product_list', 'stores', ['store_id'], ['id'], ondelete='CASCADE')
    
    op.drop_constraint('shelve_info_store_id_fkey', 'shelve_info', type_='foreignkey')
    op.create_foreign_key(None, 'shelve_info', 'stores', ['store_id'], ['id'])
    
    op.drop_constraint('user_info_store_id_fkey', 'user_info', type_='foreignkey')
    op.create_foreign_key(None, 'user_info', 'stores', ['store_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(None, 'user_info', type_='foreignkey')
    op.create_foreign_key('user_info_store_id_fkey', 'user_info', 'store_info', ['store_id'], ['id'], ondelete='SET NULL')
    
    op.drop_constraint(None, 'shelve_info', type_='foreignkey')
    op.create_foreign_key('shelve_info_store_id_fkey', 'shelve_info', 'store_info', ['store_id'], ['id'])
    
    op.drop_constraint(None, 'product_list', type_='foreignkey')
    op.drop_constraint(None, 'product_list', type_='foreignkey')
    op.create_foreign_key('product_list_store_id_fkey', 'product_list', 'store_info', ['store_id'], ['id'])
    op.drop_column('product_list', 'sequence')
    op.drop_column('product_list', 'kiosk_id')
    
    op.drop_constraint(None, 'product_category', type_='foreignkey')
    op.drop_constraint(None, 'product_category', type_='foreignkey')
    op.create_foreign_key('product_category_store_id_fkey', 'product_category', 'store_info', ['store_id'], ['id'])
    op.drop_column('product_category', 'sequence')
    op.drop_column('product_category', 'kiosk_id')
    
    op.drop_constraint(None, 'order_info', type_='foreignkey')
    op.create_foreign_key('order_info_store_id_fkey', 'order_info', 'store_info', ['store_id'], ['id'])
    op.drop_index(op.f('ix_order_info_order_no'), table_name='order_info')
    op.drop_column('order_info', 'order_no')
    
    op.drop_index(op.f('ix_kiosks_id'), table_name='kiosks')
    op.drop_index(op.f('ix_kiosks_code'), table_name='kiosks')
    op.drop_table('kiosks')
    
    op.drop_index(op.f('ix_stores_code'), table_name='stores')
    op.drop_index(op.f('ix_stores_id'), table_name='stores')
    op.drop_column('stores', 'status')
    op.drop_column('stores', 'owner_name')
    op.drop_column('stores', 'code')
    
    op.drop_constraint(None, 'stores', type_='foreignkey')
    op.create_foreign_key('store_info_user_id_fkey', 'stores', 'user_info', ['user_id'], ['id'])
    op.rename_table('stores', 'store_info')
    op.create_index('ix_store_info_id', 'store_info', ['id'], unique=False)
