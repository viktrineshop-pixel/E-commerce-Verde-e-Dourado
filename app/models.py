import reflex as rx

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB
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


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_produtos_slug"),
        CheckConstraint("length(trim(nome)) > 0", name="nome_required"),
        CheckConstraint(
            "slug = lower(trim(slug)) AND slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'",
            name="slug_normalized",
        ),
        CheckConstraint(
            "link_afiliado_original = '' OR "
            "(link_afiliado_original ~ '^https://[^/@[:space:]]+(/|$)' "
            "AND link_afiliado_original !~ '[[:space:]]' "
            "AND strpos(link_afiliado_original, chr(92)) = 0)",
            name="affiliate_url_https",
        ),
        CheckConstraint(
            "NOT published OR length(trim(link_afiliado_original)) > 0",
            name="published_link_required",
        ),
        Index("ix_produtos_published_created", "published", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    nome: Mapped[str] = mapped_column(
        String(250), nullable=False, default="", server_default=""
    )
    descricao: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    link_afiliado_original: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    slug: Mapped[str] = mapped_column(
        String(250), nullable=False, default="", server_default=""
    )
    published: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        init=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )


class MediaProvaSocial(Base):
    __tablename__ = "media_prova_social"
    __table_args__ = (
        CheckConstraint("produto_id IS NOT NULL", name="produto_required"),
        CheckConstraint("tipo IN ('image', 'video')", name="tipo_valid"),
        CheckConstraint(
            "content_type = lower(trim(content_type)) AND "
            "((tipo = 'image' AND content_type ~ '^image/[a-z0-9.+-]+$') OR "
            "(tipo = 'video' AND content_type ~ '^video/[a-z0-9.+-]+$'))",
            name="content_type_matches_tipo",
        ),
        CheckConstraint(
            "(url_ficheiro ~ '^/media/prova-social/[1-9][0-9]*$' "
            "AND file_bytes IS NOT NULL) OR "
            "(url_ficheiro ~ '^https://[^/@[:space:]]+(/|$)' "
            "AND url_ficheiro !~ '[[:space:]]' "
            "AND strpos(url_ficheiro, chr(92)) = 0 "
            "AND file_bytes IS NULL)",
            name="persistent_media_source",
        ),
        CheckConstraint(
            "file_bytes IS NULL OR octet_length(file_bytes) > 0",
            name="file_bytes_nonempty",
        ),
        CheckConstraint(
            "filename IS NULL OR length(trim(filename)) > 0",
            name="filename_nonblank",
        ),
        CheckConstraint("position >= 0", name="position_nonnegative"),
        Index(
            "ix_media_prova_social_produto_position",
            "produto_id",
            "position",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    produto_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "produtos.id",
            name="fk_media_prova_social_produto_id_produtos",
            ondelete="CASCADE",
        ),
        nullable=True,
        default=None,
    )
    tipo: Mapped[str] = mapped_column(
        String(16), nullable=False, default="image", server_default="image"
    )
    url_ficheiro: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )
    content_type: Mapped[str] = mapped_column(
        String(127), nullable=False, default="", server_default=""
    )
    file_bytes: Mapped[bytes | None] = mapped_column(
        BYTEA, nullable=True, default=None, deferred=True, repr=False
    )
    filename: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        init=False,
    )
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
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
        CheckConstraint(
            "status IN ('draft', 'in_review', 'published', 'archived')",
            name="editorial_status_valid",
        ),
        Index("ix_products_status_category_id", "status", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    brand: Mapped[str | None] = mapped_column(
        String(160), nullable=True, default=None
    )
    model: Mapped[str | None] = mapped_column(
        String(160), nullable=True, default=None
    )
    gtin: Mapped[str | None] = mapped_column(
        String(14), nullable=True, default=None, index=True
    )
    short_description: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    attributes: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="draft", server_default="draft"
    )
    provenance: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    reviewed_by_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
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


class ProductLinkClick(Base):
    __tablename__ = "product_link_clicks"
    __table_args__ = (
        CheckConstraint(
            "length(trim(marketplace)) > 0",
            name="marketplace_valid",
        ),
        Index(
            "ix_product_link_clicks_product_created", "product_id", "created_at"
        ),
        Index(
            "ix_product_link_clicks_marketplace_created",
            "marketplace",
            "created_at",
        ),
        Index("ix_product_link_clicks_created", "created_at"),
        Index("ix_product_link_clicks_offer_created", "offer_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    # Preserve click history and snapshots when a catalog product is deleted.
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    title: Mapped[str] = mapped_column(
        String(250), nullable=False, default="", server_default=""
    )
    sku: Mapped[str] = mapped_column(
        String(100), nullable=False, default="", server_default=""
    )
    marketplace: Mapped[str] = mapped_column(
        String(120), nullable=False, default="Amazon", server_default="Amazon"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        init=False,
    )


class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = (
        UniqueConstraint("code", name="uq_coupons_code"),
        CheckConstraint("length(trim(code)) > 0", name="code_required"),
        CheckConstraint("code = upper(trim(code))", name="code_normalized"),
        CheckConstraint(
            "discount_kind IN ('percent', 'fixed')", name="discount_kind_valid"
        ),
        CheckConstraint("discount_value > 0", name="discount_value_positive"),
        CheckConstraint(
            "discount_kind <> 'percent' OR discount_value <= 100",
            name="percent_within_bounds",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    discount_kind: Mapped[str] = mapped_column(
        String(16), nullable=False, default="percent", server_default="percent"
    )
    # Whole percentage points for percent; BRL centavos for fixed.
    discount_value: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=1, server_default=text("1")
    )
    active: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=text("false")
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        init=False,
    )


class CustomerFavorite(Base):
    __tablename__ = "customer_favorites"
    __table_args__ = (
        UniqueConstraint(
            "subject",
            "product_id",
            name="uq_customer_favorites_subject_product",
        ),
        CheckConstraint("length(trim(subject)) > 0", name="subject_required"),
        Index("ix_customer_favorites_subject", "subject"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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
    coupon_code: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None
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


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_categories_slug"),
        CheckConstraint("length(trim(slug)) > 0", name="slug_required"),
        CheckConstraint("length(trim(name)) > 0", name="name_required"),
        CheckConstraint(
            "parent_id IS NULL OR parent_id <> id", name="not_own_parent"
        ),
        CheckConstraint("position >= 0", name="position_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(160), default="", server_default=""
    )
    slug: Mapped[str] = mapped_column(
        String(160), default="", server_default=""
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    position: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    active: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
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


class Merchant(Base):
    __tablename__ = "merchants"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_merchants_slug"),
        CheckConstraint("length(trim(name)) > 0", name="name_required"),
        CheckConstraint("length(trim(slug)) > 0", name="slug_required"),
        CheckConstraint(
            "status IN ('draft', 'active', 'inactive')", name="status_valid"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(
        String(160), default="", server_default=""
    )
    slug: Mapped[str] = mapped_column(
        String(160), default="", server_default=""
    )
    website_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    allowed_domains: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    logo_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(
        String(16), default="draft", server_default="draft", index=True
    )
    provenance: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
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


# Both names refer to the same partner-store table, not duplicate merchant records.
PartnerStore = Merchant


class AffiliateProgram(Base):
    __tablename__ = "affiliate_programs"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id", "code", name="uq_affiliate_programs_merchant_code"
        ),
        UniqueConstraint(
            "id", "merchant_id", name="uq_affiliate_programs_id_merchant"
        ),
        CheckConstraint("merchant_id IS NOT NULL", name="merchant_required"),
        CheckConstraint("length(trim(code)) > 0", name="code_required"),
        CheckConstraint(
            "status IN ('draft', 'active', 'inactive')", name="status_valid"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    merchant_id: Mapped[int | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    code: Mapped[str] = mapped_column(
        String(100), default="", server_default=""
    )
    name: Mapped[str | None] = mapped_column(
        String(160), nullable=True, default=None
    )
    network: Mapped[str | None] = mapped_column(
        String(160), nullable=True, default=None
    )
    terms_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    tracking_domains: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(
        String(16), default="draft", server_default="draft", index=True
    )
    provenance: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
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


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "variant_key", name="uq_product_variants_product_key"
        ),
        UniqueConstraint(
            "id", "product_id", name="uq_product_variants_id_product"
        ),
        CheckConstraint("product_id IS NOT NULL", name="product_required"),
        CheckConstraint(
            "length(trim(variant_key)) > 0", name="variant_key_required"
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')", name="status_valid"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    variant_key: Mapped[str] = mapped_column(
        String(160), default="", server_default=""
    )
    title: Mapped[str | None] = mapped_column(
        String(250), nullable=True, default=None
    )
    sku: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None, index=True
    )
    gtin: Mapped[str | None] = mapped_column(
        String(14), nullable=True, default=None, index=True
    )
    attributes: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    image_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    provenance: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(
        String(24), default="draft", server_default="draft"
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


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        ForeignKeyConstraint(
            ["variant_id", "product_id"],
            ["product_variants.id", "product_variants.product_id"],
            name="fk_offers_variant_product",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["program_id", "merchant_id"],
            ["affiliate_programs.id", "affiliate_programs.merchant_id"],
            name="fk_offers_program_merchant",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "merchant_id",
            "source",
            "external_id",
            name="uq_offers_merchant_source_external",
        ),
        CheckConstraint(
            "product_id IS NOT NULL AND merchant_id IS NOT NULL",
            name="product_merchant_required",
        ),
        CheckConstraint(
            "price_centavos IS NULL OR price_centavos >= 0",
            name="price_nonnegative",
        ),
        CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name="currency_valid",
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'unavailable', 'invalid', 'archived')",
            name="status_valid",
        ),
        CheckConstraint(
            "external_id IS NULL OR length(trim(external_id)) > 0",
            name="external_id_nonblank",
        ),
        CheckConstraint(
            "status <> 'published' OR (price_centavos IS NOT NULL AND observed_at IS NOT NULL "
            "AND source IS NOT NULL AND length(trim(source)) > 0 AND reviewed_at IS NOT NULL "
            "AND reviewed_by_sub IS NOT NULL AND length(trim(reviewed_by_sub)) > 0)",
            name="published_evidence_required",
        ),
        Index(
            "ix_offers_product_status_price",
            "product_id",
            "status",
            "price_centavos",
        ),
        Index("ix_offers_merchant_status", "merchant_id", "status"),
        Index("ix_offers_status_observed", "status", "observed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    merchant_id: Mapped[int | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    variant_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None, index=True
    )
    program_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None, index=True
    )
    price_centavos: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, default=None
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="BRL", server_default="BRL"
    )
    observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(
        String(24), default="draft", server_default="draft"
    )
    source: Mapped[str | None] = mapped_column(
        String(160), nullable=True, default=None
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    provenance: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    reviewed_by_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
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


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_campaigns_slug"),
        CheckConstraint("length(trim(slug)) > 0", name="slug_required"),
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')", name="status_valid"
        ),
        CheckConstraint(
            "starts_at IS NULL OR ends_at IS NULL OR ends_at > starts_at",
            name="dates_ordered",
        ),
        Index("ix_campaigns_status_dates", "status", "starts_at", "ends_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    slug: Mapped[str] = mapped_column(
        String(160), default="", server_default=""
    )
    title: Mapped[str] = mapped_column(
        String(250), default="", server_default=""
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(
        String(24), default="draft", server_default="draft"
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
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


class CampaignOffer(Base):
    __tablename__ = "campaign_offers"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "offer_id", name="uq_campaign_offers_campaign_offer"
        ),
        CheckConstraint(
            "campaign_id IS NOT NULL AND offer_id IS NOT NULL",
            name="association_required",
        ),
        CheckConstraint("position >= 0", name="position_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
    )
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    position: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"
    __table_args__ = (
        UniqueConstraint("offer_id", name="uq_affiliate_links_offer"),
        CheckConstraint("offer_id IS NOT NULL", name="offer_required"),
        CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid', 'expired')",
            name="validation_status_valid",
        ),
        CheckConstraint(
            "destination_url IS NULL OR destination_url LIKE 'https://%' OR destination_url LIKE 'http://%'",
            name="destination_http",
        ),
        CheckConstraint(
            "affiliate_url IS NULL OR affiliate_url LIKE 'https://%' OR affiliate_url LIKE 'http://%'",
            name="affiliate_http",
        ),
        CheckConstraint(
            "validation_status <> 'valid' OR (destination_url IS NOT NULL AND affiliate_url IS NOT NULL "
            "AND validated_at IS NOT NULL AND validated_by_sub IS NOT NULL "
            "AND length(trim(validated_by_sub)) > 0)",
            name="valid_evidence_required",
        ),
        CheckConstraint(
            "http_status IS NULL OR http_status BETWEEN 100 AND 599",
            name="http_status_valid",
        ),
        Index(
            "ix_affiliate_links_validation_expiry",
            "validation_status",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
    )
    campaign_id: Mapped[int | None] = mapped_column(
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    destination_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    affiliate_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    tracking_code: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    validation_status: Mapped[str] = mapped_column(
        String(16), default="pending", server_default="pending"
    )
    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    validated_by_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )
    http_status: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    resolved_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    validation_error: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    validation_metadata: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
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


class PriceObservation(Base):
    __tablename__ = "price_observations"
    __table_args__ = (
        UniqueConstraint(
            "offer_id",
            "source",
            "observed_at",
            name="uq_price_observations_offer_source_time",
        ),
        CheckConstraint("offer_id IS NOT NULL", name="offer_required"),
        CheckConstraint(
            "price_centavos IS NOT NULL AND price_centavos >= 0",
            name="price_required_nonnegative",
        ),
        CheckConstraint(
            "source IS NOT NULL AND length(trim(source)) > 0",
            name="source_required",
        ),
        CheckConstraint("observed_at IS NOT NULL", name="observed_at_required"),
        CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name="currency_valid",
        ),
        Index(
            "ix_price_observations_offer_observed", "offer_id", "observed_at"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
    )
    price_centavos: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, default=None
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="BRL", server_default="BRL"
    )
    source: Mapped[str | None] = mapped_column(
        String(160), nullable=True, default=None
    )
    observed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    evidence_url: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    provenance: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    recorded_by_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class ProductAudit(Base):
    __tablename__ = "product_audits"
    __table_args__ = (
        CheckConstraint(
            "actor_sub IS NOT NULL AND length(trim(actor_sub)) > 0",
            name="actor_required",
        ),
        CheckConstraint("length(trim(entity)) > 0", name="entity_required"),
        CheckConstraint(
            "entity_id IS NOT NULL AND entity_id > 0", name="entity_id_required"
        ),
        CheckConstraint("length(trim(action)) > 0", name="action_required"),
        Index(
            "ix_product_audits_entity_created",
            "entity",
            "entity_id",
            "created_at",
        ),
        Index("ix_product_audits_actor_created", "actor_sub", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    actor_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    entity: Mapped[str] = mapped_column(
        String(80), default="", server_default=""
    )
    entity_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    action: Mapped[str] = mapped_column(
        String(80), default="", server_default=""
    )
    diff: Mapped[dict[str, object]] = mapped_column(JSONB, default_factory=dict)
    reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class DuplicateReview(Base):
    __tablename__ = "duplicate_reviews"
    __table_args__ = (
        UniqueConstraint(
            "product_id",
            "candidate_product_id",
            name="uq_duplicate_reviews_product_pair",
        ),
        CheckConstraint(
            "product_id IS NOT NULL AND candidate_product_id IS NOT NULL",
            name="products_required",
        ),
        CheckConstraint(
            "product_id < candidate_product_id", name="pair_canonical"
        ),
        CheckConstraint(
            "status IN ('pending', 'duplicate', 'distinct', 'dismissed')",
            name="status_valid",
        ),
        CheckConstraint(
            "status = 'pending' OR (reviewed_at IS NOT NULL AND reviewed_by_sub IS NOT NULL "
            "AND length(trim(reviewed_by_sub)) > 0)",
            name="review_evidence_required",
        ),
        Index("ix_duplicate_reviews_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    candidate_product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(16), default="pending", server_default="pending"
    )
    detected_by_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    source: Mapped[str | None] = mapped_column(
        String(160), nullable=True, default=None
    )
    evidence: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    reviewed_by_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
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


class List(Base):
    __tablename__ = "saved_lists"
    __table_args__ = (
        UniqueConstraint("id", "owner_sub", name="uq_saved_lists_id_owner"),
        UniqueConstraint("owner_sub", "slug", name="uq_saved_lists_owner_slug"),
        CheckConstraint(
            "owner_sub IS NOT NULL AND length(trim(owner_sub)) > 0",
            name="owner_required",
        ),
        CheckConstraint("length(trim(slug)) > 0", name="slug_required"),
        CheckConstraint(
            "visibility IN ('private', 'public', 'unlisted')",
            name="visibility_valid",
        ),
        Index("ix_saved_lists_owner_updated", "owner_sub", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    owner_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    slug: Mapped[str] = mapped_column(
        String(160), default="", server_default=""
    )
    title: Mapped[str] = mapped_column(
        String(250), default="", server_default=""
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    visibility: Mapped[str] = mapped_column(
        String(16), default="private", server_default="private", index=True
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


class ListItem(Base):
    __tablename__ = "saved_list_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["list_id", "owner_sub"],
            ["saved_lists.id", "saved_lists.owner_sub"],
            name="fk_saved_list_items_list_owner",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "list_id", "product_id", name="uq_saved_list_items_list_product"
        ),
        CheckConstraint(
            "list_id IS NOT NULL AND product_id IS NOT NULL",
            name="list_product_required",
        ),
        CheckConstraint(
            "owner_sub IS NOT NULL AND length(trim(owner_sub)) > 0",
            name="owner_required",
        ),
        CheckConstraint("position >= 0", name="position_nonnegative"),
        Index("ix_saved_list_items_owner_list", "owner_sub", "list_id"),
        Index("ix_saved_list_items_list_position", "list_id", "position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    list_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    owner_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
        index=True,
    )
    position: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    note: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class ConversionReport(Base):
    __tablename__ = "conversion_reports"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "source",
            "external_id",
            name="uq_conversion_reports_merchant_source_external",
        ),
        ForeignKeyConstraint(
            ["program_id", "merchant_id"],
            ["affiliate_programs.id", "affiliate_programs.merchant_id"],
            name="fk_conversion_reports_program_merchant",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "record_kind = 'external_report'", name="external_only"
        ),
        CheckConstraint("merchant_id IS NOT NULL", name="merchant_required"),
        CheckConstraint(
            "source IS NOT NULL AND length(trim(source)) > 0",
            name="source_required",
        ),
        CheckConstraint(
            "external_id IS NOT NULL AND length(trim(external_id)) > 0",
            name="external_id_required",
        ),
        CheckConstraint("reported_at IS NOT NULL", name="reported_at_required"),
        CheckConstraint(
            "status IN ('reported', 'pending', 'approved', 'rejected', 'reversed')",
            name="status_valid",
        ),
        CheckConstraint(
            "amount_centavos IS NULL OR amount_centavos >= 0",
            name="amount_nonnegative",
        ),
        CheckConstraint(
            "commission_centavos IS NULL OR commission_centavos >= 0",
            name="commission_nonnegative",
        ),
        CheckConstraint(
            "currency IS NULL OR (length(currency) = 3 AND currency = upper(currency))",
            name="currency_valid",
        ),
        CheckConstraint(
            "(amount_centavos IS NULL AND commission_centavos IS NULL) OR currency IS NOT NULL",
            name="amount_currency_required",
        ),
        Index(
            "ix_conversion_reports_merchant_reported",
            "merchant_id",
            "reported_at",
        ),
        Index(
            "ix_conversion_reports_offer_reported", "offer_id", "reported_at"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    merchant_id: Mapped[int | None] = mapped_column(
        ForeignKey("merchants.id", ondelete="RESTRICT"),
        nullable=True,
        default=None,
    )
    program_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None, index=True
    )
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    affiliate_link_id: Mapped[int | None] = mapped_column(
        ForeignKey("affiliate_links.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    click_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_link_clicks.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    record_kind: Mapped[str] = mapped_column(
        String(24), default="external_report", server_default="external_report"
    )
    source: Mapped[str | None] = mapped_column(
        String(160), nullable=True, default=None
    )
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(
        String(16), default="reported", server_default="reported", index=True
    )
    amount_centavos: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, default=None
    )
    commission_centavos: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, default=None
    )
    currency: Mapped[str | None] = mapped_column(
        String(3), nullable=True, default=None
    )
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    reported_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    imported_by_sub: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )
    external_payload: Mapped[dict[str, object] | None] = mapped_column(
        JSON, nullable=True, default=None
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
