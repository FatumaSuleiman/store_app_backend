"""add changes

Revision ID: 2c149a758cb2
Revises: 
Create Date: 2025-01-07 14:11:59.184141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2c149a758cb2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('image', sa.String(), nullable=True),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('customer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('firstName', sa.String(), nullable=True),
    sa.Column('lastName',  sa.String(), nullable=True),
    sa.Column('email',  sa.String(), nullable=True),
    sa.Column('address',  sa.String(), nullable=True),
    sa.Column('phone',  sa.String(), nullable=True),
    sa.Column('accountNumber',  sa.String(), nullable=True),
    sa.Column('cardNumber',  sa.String(), nullable=True),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('institution',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('active_status',  sa.String(), nullable=True),
    sa.Column('name',  sa.String(), nullable=True),
    sa.Column('phone',  sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('address',  sa.String(), nullable=True),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.Column('invoicing_period_type',  sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('firstName',  sa.String(), nullable=False),
    sa.Column('lastName',  sa.String(), nullable=False),
    sa.Column('userName',  sa.String(), nullable=False),
    sa.Column('email',  sa.String(), nullable=False),
    sa.Column('password',  sa.String(), nullable=False),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_staff', sa.Boolean(), nullable=False),
    sa.Column('is_default_password', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('referenceId',  sa.String(), nullable=True),
    sa.Column('referenceName',  sa.String(), nullable=True),
    sa.Column('role',  sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=False)
    op.create_index(op.f('ix_user_firstName'), 'user', ['firstName'], unique=False)
    op.create_index(op.f('ix_user_lastName'), 'user', ['lastName'], unique=False)
    op.create_index(op.f('ix_user_password'), 'user', ['password'], unique=False)
    op.create_index(op.f('ix_user_userName'), 'user', ['userName'], unique=False)
    op.create_table('account',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('account_number',  sa.String(), nullable=True),
    sa.Column('institution_id', sa.Integer(), nullable=True),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['institution_id'], ['institution.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('product',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('name',  sa.String(), nullable=True),
    sa.Column('buyingPrice', sa.Float(), nullable=True),
    sa.Column('sellingPrice', sa.Float(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('description',  sa.String(), nullable=True),
    sa.Column('image',  sa.String(), nullable=True),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('shoppingcart',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('items', sa.JSON(), nullable=True),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('store',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('name',  sa.String(), nullable=True),
    sa.Column('location',  sa.String(), nullable=True),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.Column('products', sa.JSON(), nullable=True),
    sa.Column('institution_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['institution_id'], ['institution.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('expense',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('name',  sa.String(), nullable=True),
    sa.Column('description',  sa.String(), nullable=True),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('deleteStatus', sa.Boolean(), nullable=False),
    sa.Column('store_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['store_id'], ['store.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('order',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('totalAmount', sa.Float(), nullable=True),
    sa.Column('items', sa.JSON(), nullable=True),
    sa.Column('orderDate', sa.DateTime(), nullable=False),
    sa.Column('status',  sa.String(), nullable=False),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.Column('customer_id', sa.Integer(), nullable=True),
    sa.Column('store_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
    sa.ForeignKeyConstraint(['store_id'], ['store.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('storeproductlink',
    sa.Column('store_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
    sa.ForeignKeyConstraint(['store_id'], ['store.id'], ),
    sa.PrimaryKeyConstraint('store_id', 'product_id')
    )
    op.create_table('supplier',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('name',  sa.String(), nullable=True),
    sa.Column('contactPhone',  sa.String(), nullable=True),
    sa.Column('email',  sa.String(), nullable=True),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.Column('suppliedProducts', sa.JSON(), nullable=True),
    sa.Column('store_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['store_id'], ['store.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('paymentDate', sa.DateTime(), nullable=False),
    sa.Column('paymentMethod',  sa.String(), nullable=False),
    sa.Column('deletedStatus', sa.Boolean(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['order_id'], ['order.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('payment')
    op.drop_table('supplier')
    op.drop_table('storeproductlink')
    op.drop_table('order')
    op.drop_table('expense')
    op.drop_table('store')
    op.drop_table('shoppingcart')
    op.drop_table('product')
    op.drop_table('account')
    op.drop_index(op.f('ix_user_userName'), table_name='user')
    op.drop_index(op.f('ix_user_password'), table_name='user')
    op.drop_index(op.f('ix_user_lastName'), table_name='user')
    op.drop_index(op.f('ix_user_firstName'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_table('institution')
    op.drop_table('customer')
    op.drop_table('category')
    # ### end Alembic commands ###