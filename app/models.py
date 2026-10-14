import reflex as rx

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class StoreMember(Base):
    __tablename__ = "store_members"
    __table_args__ = (
        UniqueConstraint("subject", name="uq_store_members_subject"),
        UniqueConstraint("admin_slot", name="uq_store_members_admin_slot"),
        CheckConstraint("length(trim(subject)) > 0", name="subject_required"),
        CheckConstraint("role IN ('admin', 'member')", name="role_valid"),
        CheckConstraint(
            "(role = 'admin' AND admin_slot IS NOT NULL AND admin_slot = 1) "
            "OR (role = 'member' AND admin_slot IS NULL)",
            name="admin_slot_matches_role",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subject: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", server_default=""
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="member", server_default="member"
    )
    admin_slot: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    email: Mapped[str | None] = mapped_column(
        String(320), nullable=True, default=None
    )
    name: Mapped[str | None] = mapped_column(
        String(250), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_centavos >= 0", name="price_nonnegative"),
        CheckConstraint(
            "compare_at_price_centavos IS NULL OR compare_at_price_centavos >= price_centavos",
            name="compare_at_not_below_price",
        ),
        CheckConstraint("stock >= 0", name="stock_nonnegative"),
        CheckConstraint(
            "partner_name IN ('Amazon', 'Mercado Livre', 'Shopee')",
            name="partner_name_valid",
        ),
        Index("ix_products_category_featured", "category", "featured"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    # SKU is a stable catalog identifier, never derived from the editable title.
    sku: Mapped[str] = mapped_column(String(100), unique=True, default="")
    partner_name: Mapped[str] = mapped_column(
        String(120), nullable=False, default="Amazon", server_default="Amazon"
    )
    affiliate_url: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    title: Mapped[str] = mapped_column(
        String(250), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    category: Mapped[str] = mapped_column(
        String(120), default="", server_default=""
    )
    image_url: Mapped[str] = mapped_column(Text, default="", server_default="")
    price_centavos: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0")
    )
    compare_at_price_centavos: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, default=None
    )
    badge: Mapped[str] = mapped_column(
        String(80), default="", server_default=""
    )
    featured: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )
    stock: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "cart_key", "product_id", name="uq_cart_items_cart_product"
        ),
        CheckConstraint("length(trim(cart_key)) > 0", name="cart_key_required"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_cart_items_owner_cart", "owner_sub", "cart_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    cart_key: Mapped[str] = mapped_column(String(128), default="")
    owner_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[int] = mapped_column(default=1, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("subtotal_centavos >= 0", name="subtotal_nonnegative"),
        CheckConstraint("shipping_centavos >= 0", name="shipping_nonnegative"),
        CheckConstraint("discount_centavos >= 0", name="discount_nonnegative"),
        CheckConstraint("total_centavos >= 0", name="total_nonnegative"),
        CheckConstraint(
            "discount_centavos <= subtotal_centavos + shipping_centavos",
            name="discount_within_total",
        ),
        CheckConstraint(
            "total_centavos = subtotal_centavos + shipping_centavos - discount_centavos",
            name="total_matches_components",
        ),
        CheckConstraint(
            "status IN ('pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')",
            name="status_valid",
        ),
        Index("ix_orders_purchaser_created", "purchaser_sub", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    purchaser_sub: Mapped[str] = mapped_column(
        String(255), default="", server_default=""
    )
    contact_name: Mapped[str] = mapped_column(
        String(250), default="", server_default=""
    )
    contact_email: Mapped[str] = mapped_column(
        String(320), default="", server_default=""
    )
    contact_phone: Mapped[str] = mapped_column(
        String(40), default="", server_default=""
    )
    shipping_recipient: Mapped[str] = mapped_column(
        String(250), default="", server_default=""
    )
    shipping_street: Mapped[str] = mapped_column(
        String(250), default="", server_default=""
    )
    shipping_number: Mapped[str] = mapped_column(
        String(40), default="", server_default=""
    )
    shipping_complement: Mapped[str] = mapped_column(
        String(250), default="", server_default=""
    )
    shipping_neighborhood: Mapped[str] = mapped_column(
        String(120), default="", server_default=""
    )
    shipping_city: Mapped[str] = mapped_column(
        String(120), default="", server_default=""
    )
    shipping_state: Mapped[str] = mapped_column(
        String(100), default="", server_default=""
    )
    shipping_postal_code: Mapped[str] = mapped_column(
        String(24), default="", server_default=""
    )
    shipping_country_code: Mapped[str] = mapped_column(
        String(2), default="BR", server_default="BR"
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="BRL", server_default="BRL"
    )
    subtotal_centavos: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0")
    )
    shipping_centavos: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0")
    )
    discount_centavos: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0")
    )
    total_centavos: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0")
    )
    status: Mapped[str] = mapped_column(
        String(24), default="pending", server_default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint(
            "order_id", "line_number", name="uq_order_items_order_line"
        ),
        CheckConstraint("line_number > 0", name="line_number_positive"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "unit_price_centavos >= 0", name="unit_price_nonnegative"
        ),
        CheckConstraint("discount_centavos >= 0", name="discount_nonnegative"),
        CheckConstraint("total_centavos >= 0", name="total_nonnegative"),
        CheckConstraint(
            "total_centavos = quantity * unit_price_centavos - discount_centavos",
            name="total_matches_line",
        ),
        CheckConstraint(
            "compare_at_price_centavos IS NULL OR compare_at_price_centavos >= unit_price_centavos",
            name="compare_at_not_below_price",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    # Catalog deletion must not erase historical purchase snapshots.
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        default=1, server_default=text("1")
    )
    sku: Mapped[str] = mapped_column(String(100), default="", server_default="")
    title: Mapped[str] = mapped_column(
        String(250), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    category: Mapped[str] = mapped_column(
        String(120), default="", server_default=""
    )
    image_url: Mapped[str] = mapped_column(Text, default="", server_default="")
    quantity: Mapped[int] = mapped_column(default=1, server_default=text("1"))
    unit_price_centavos: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0")
    )
    compare_at_price_centavos: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, default=None
    )
    discount_centavos: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0")
    )
    total_centavos: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
