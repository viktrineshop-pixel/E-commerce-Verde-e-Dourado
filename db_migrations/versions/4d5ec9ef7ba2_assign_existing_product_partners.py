"""assign_existing_product_partners

Revision ID: 4d5ec9ef7ba2
Revises: c053e532354e
"""
from typing import Sequence, Union

from alembic import op

revision: str = '4d5ec9ef7ba2'
down_revision: Union[str, Sequence[str], None] = 'c053e532354e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("WITH shuffled AS (SELECT id, row_number() OVER (ORDER BY md5(sku || ':' || id::text)) AS n FROM products) UPDATE products AS p SET partner_name = CASE (shuffled.n - 1) % 3 WHEN 0 THEN 'Amazon' WHEN 1 THEN 'Mercado Livre' ELSE 'Shopee' END FROM shuffled WHERE p.id = shuffled.id;")


def downgrade() -> None:
    pass
