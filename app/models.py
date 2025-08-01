from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum


class ProductStatus(str, Enum):
    """Product availability status"""

    ACTIVE = "active"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


# Persistent models (stored in database)
class Category(SQLModel, table=True):
    """Product categories for PC gaming products"""

    __tablename__ = "categories"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    description: str = Field(default="", max_length=500)
    slug: str = Field(max_length=100, unique=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Self-referential relationship for category hierarchy
    parent: Optional["Category"] = Relationship(
        back_populates="children", sa_relationship_kwargs={"remote_side": "Category.id"}
    )
    children: List["Category"] = Relationship(back_populates="parent")
    products: List["Product"] = Relationship(back_populates="category")


class Brand(SQLModel, table=True):
    """Product brands/manufacturers"""

    __tablename__ = "brands"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
    description: str = Field(default="", max_length=500)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    website_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    products: List["Product"] = Relationship(back_populates="brand")


class Product(SQLModel, table=True):
    """Main product model for PC gaming products"""

    __tablename__ = "products"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    sku: str = Field(max_length=50, unique=True)
    price: Decimal = Field(decimal_places=2, gt=0)
    original_price: Optional[Decimal] = Field(default=None, decimal_places=2)
    status: ProductStatus = Field(default=ProductStatus.ACTIVE)

    # Foreign keys
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    brand_id: Optional[int] = Field(default=None, foreign_key="brands.id")

    # Product specifications and features
    specifications: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    features: List[str] = Field(default=[], sa_column=Column(JSON))

    # Inventory and availability
    stock_quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=5, ge=0)

    # SEO and display
    slug: str = Field(max_length=200, unique=True)
    meta_title: Optional[str] = Field(default=None, max_length=200)
    meta_description: Optional[str] = Field(default=None, max_length=500)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    category: Optional[Category] = Relationship(back_populates="products")
    brand: Optional[Brand] = Relationship(back_populates="products")
    images: List["ProductImage"] = Relationship(back_populates="product", cascade_delete=True)


class ProductImage(SQLModel, table=True):
    """Product images for gallery and thumbnails"""

    __tablename__ = "product_images"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    image_url: str = Field(max_length=500)
    alt_text: str = Field(default="", max_length=200)
    is_primary: bool = Field(default=False)
    display_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    product: Product = Relationship(back_populates="images")


# Non-persistent schemas (for validation, forms, API requests/responses)
class CategoryCreate(SQLModel, table=False):
    """Schema for creating new categories"""

    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)
    slug: str = Field(max_length=100)
    parent_id: Optional[int] = Field(default=None)


class CategoryUpdate(SQLModel, table=False):
    """Schema for updating categories"""

    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    slug: Optional[str] = Field(default=None, max_length=100)
    parent_id: Optional[int] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


class BrandCreate(SQLModel, table=False):
    """Schema for creating new brands"""

    name: str = Field(max_length=100)
    description: str = Field(default="", max_length=500)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    website_url: Optional[str] = Field(default=None, max_length=500)


class BrandUpdate(SQLModel, table=False):
    """Schema for updating brands"""

    name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    website_url: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = Field(default=None)


class ProductCreate(SQLModel, table=False):
    """Schema for creating new products"""

    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    sku: str = Field(max_length=50)
    price: Decimal = Field(decimal_places=2, gt=0)
    original_price: Optional[Decimal] = Field(default=None, decimal_places=2)
    category_id: Optional[int] = Field(default=None)
    brand_id: Optional[int] = Field(default=None)
    specifications: Dict[str, Any] = Field(default={})
    features: List[str] = Field(default=[])
    stock_quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=5, ge=0)
    slug: str = Field(max_length=200)


class ProductUpdate(SQLModel, table=False):
    """Schema for updating products"""

    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Optional[Decimal] = Field(default=None, decimal_places=2, gt=0)
    original_price: Optional[Decimal] = Field(default=None, decimal_places=2)
    status: Optional[ProductStatus] = Field(default=None)
    category_id: Optional[int] = Field(default=None)
    brand_id: Optional[int] = Field(default=None)
    specifications: Optional[Dict[str, Any]] = Field(default=None)
    features: Optional[List[str]] = Field(default=None)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    min_stock_level: Optional[int] = Field(default=None, ge=0)
    slug: Optional[str] = Field(default=None, max_length=200)


class ProductImageCreate(SQLModel, table=False):
    """Schema for creating product images"""

    product_id: int
    image_url: str = Field(max_length=500)
    alt_text: str = Field(default="", max_length=200)
    is_primary: bool = Field(default=False)
    display_order: int = Field(default=0)


class ProductImageUpdate(SQLModel, table=False):
    """Schema for updating product images"""

    image_url: Optional[str] = Field(default=None, max_length=500)
    alt_text: Optional[str] = Field(default=None, max_length=200)
    is_primary: Optional[bool] = Field(default=None)
    display_order: Optional[int] = Field(default=None)


class ProductFilter(SQLModel, table=False):
    """Schema for filtering products"""

    category_id: Optional[int] = Field(default=None)
    brand_id: Optional[int] = Field(default=None)
    min_price: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0)
    max_price: Optional[Decimal] = Field(default=None, decimal_places=2, ge=0)
    status: Optional[ProductStatus] = Field(default=None)
    in_stock_only: bool = Field(default=False)
    search_query: Optional[str] = Field(default=None, max_length=200)


class ProductSummary(SQLModel, table=False):
    """Lightweight product summary for listings"""

    id: int
    name: str
    price: Decimal
    original_price: Optional[Decimal]
    status: ProductStatus
    primary_image_url: Optional[str]
    category_name: Optional[str]
    brand_name: Optional[str]
    stock_quantity: int
    created_at: str  # ISO format string
