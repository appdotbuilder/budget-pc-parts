from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlmodel import select, or_, text
from app.database import get_session
from app.models import Product, Category, Brand, ProductImage, ProductFilter, ProductSummary, ProductStatus


class ProductService:
    """Service for managing products and product operations"""

    @staticmethod
    def get_products(filters: Optional[ProductFilter] = None, limit: int = 20, offset: int = 0) -> List[ProductSummary]:
        """Get filtered list of products with pagination"""
        with get_session() as session:
            query = select(Product).join(Category, isouter=True).join(Brand, isouter=True)

            if filters:
                # Apply filters
                if filters.category_id is not None:
                    query = query.where(Product.category_id == filters.category_id)

                if filters.brand_id is not None:
                    query = query.where(Product.brand_id == filters.brand_id)

                if filters.min_price is not None:
                    query = query.where(Product.price >= filters.min_price)

                if filters.max_price is not None:
                    query = query.where(Product.price <= filters.max_price)

                if filters.status is not None:
                    query = query.where(Product.status == filters.status)

                if filters.in_stock_only:
                    query = query.where(Product.stock_quantity > 0)

                if filters.search_query:
                    search_pattern = f"%{filters.search_query}%"
                    query = query.where(
                        or_(text("products.name ILIKE :search"), text("products.description ILIKE :search")).params(
                            search=search_pattern
                        )
                    )

            # Apply pagination and ordering
            query = query.order_by(text("products.created_at DESC")).offset(offset).limit(limit)

            products = session.exec(query).all()

            # Convert to ProductSummary with related data
            summaries = []
            for product in products:
                # Get primary image
                primary_image = session.exec(
                    select(ProductImage)
                    .where(ProductImage.product_id == product.id)
                    .where(ProductImage.is_primary)
                    .limit(1)
                ).first()

                summary = ProductSummary(
                    id=product.id or 0,
                    name=product.name,
                    price=product.price,
                    original_price=product.original_price,
                    status=product.status,
                    primary_image_url=primary_image.image_url if primary_image else None,
                    category_name=product.category.name if product.category else None,
                    brand_name=product.brand.name if product.brand else None,
                    stock_quantity=product.stock_quantity,
                    created_at=product.created_at.isoformat(),
                )
                summaries.append(summary)

            return summaries

    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """Get product by ID with all related data"""
        with get_session() as session:
            return session.get(Product, product_id)

    @staticmethod
    def get_product_by_slug(slug: str) -> Optional[Product]:
        """Get product by slug with all related data"""
        with get_session() as session:
            return session.exec(select(Product).where(Product.slug == slug)).first()

    @staticmethod
    def get_product_images(product_id: int) -> List[ProductImage]:
        """Get all images for a product ordered by display_order"""
        with get_session() as session:
            return list(
                session.exec(
                    select(ProductImage).where(ProductImage.product_id == product_id).order_by(text("display_order"))
                ).all()
            )

    @staticmethod
    def get_featured_products(limit: int = 8) -> List[ProductSummary]:
        """Get featured products (low price, in stock, recent)"""
        filters = ProductFilter(status=ProductStatus.ACTIVE, in_stock_only=True, max_price=Decimal("200.00"))
        return ProductService.get_products(filters=filters, limit=limit)

    @staticmethod
    def get_price_range() -> Dict[str, Decimal]:
        """Get min and max prices across all active products"""
        with get_session() as session:
            products = session.exec(select(Product).where(Product.status == ProductStatus.ACTIVE)).all()

            if not products:
                return {"min": Decimal("0"), "max": Decimal("1000")}

            prices = [product.price for product in products if product.price is not None]
            return {"min": min(prices) if prices else Decimal("0"), "max": max(prices) if prices else Decimal("1000")}

    @staticmethod
    def search_products(query: str, limit: int = 20) -> List[ProductSummary]:
        """Search products by name and description"""
        filters = ProductFilter(search_query=query, status=ProductStatus.ACTIVE)
        return ProductService.get_products(filters=filters, limit=limit)


class CategoryService:
    """Service for managing product categories"""

    @staticmethod
    def get_all_categories() -> List[Category]:
        """Get all active categories"""
        with get_session() as session:
            return list(session.exec(select(Category).where(Category.is_active).order_by(Category.name)).all())

    @staticmethod
    def get_root_categories() -> List[Category]:
        """Get top-level categories (no parent)"""
        with get_session() as session:
            return list(
                session.exec(
                    select(Category).where(text("parent_id IS NULL")).where(Category.is_active).order_by(Category.name)
                ).all()
            )

    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Category]:
        """Get category by ID"""
        with get_session() as session:
            return session.get(Category, category_id)

    @staticmethod
    def get_category_by_slug(slug: str) -> Optional[Category]:
        """Get category by slug"""
        with get_session() as session:
            return session.exec(select(Category).where(Category.slug == slug)).first()

    @staticmethod
    def get_categories_with_product_counts() -> List[Dict[str, Any]]:
        """Get categories with their product counts"""
        with get_session() as session:
            categories = session.exec(select(Category).where(Category.is_active).order_by(Category.name)).all()

            result = []
            for category in categories:
                product_count = session.exec(
                    select(Product)
                    .where(Product.category_id == category.id)
                    .where(Product.status == ProductStatus.ACTIVE)
                ).all()

                result.append({"category": category, "product_count": len(product_count)})

            return result


class BrandService:
    """Service for managing brands"""

    @staticmethod
    def get_all_brands() -> List[Brand]:
        """Get all active brands"""
        with get_session() as session:
            return list(session.exec(select(Brand).where(Brand.is_active).order_by(Brand.name)).all())

    @staticmethod
    def get_brand_by_id(brand_id: int) -> Optional[Brand]:
        """Get brand by ID"""
        with get_session() as session:
            return session.get(Brand, brand_id)

    @staticmethod
    def get_brands_with_product_counts() -> List[Dict[str, Any]]:
        """Get brands with their product counts"""
        with get_session() as session:
            brands = session.exec(select(Brand).where(Brand.is_active).order_by(Brand.name)).all()

            result = []
            for brand in brands:
                product_count = session.exec(
                    select(Product).where(Product.brand_id == brand.id).where(Product.status == ProductStatus.ACTIVE)
                ).all()

                result.append({"brand": brand, "product_count": len(product_count)})

            return result


class DataSeederService:
    """Service for seeding sample data"""

    @staticmethod
    def seed_sample_data():
        """Seed the database with sample gaming products"""
        with get_session() as session:
            # Check if data already exists
            existing_products = session.exec(select(Product)).first()
            if existing_products:
                return  # Data already seeded

            # Create categories
            categories = []
            cat_data_list = [
                ("Graphics Cards", "graphics-cards", "GPU cards for gaming performance"),
                ("Processors", "processors", "CPUs for gaming builds"),
                ("Memory", "memory", "RAM modules for gaming systems"),
                ("Storage", "storage", "SSDs and HDDs for games"),
                ("Motherboards", "motherboards", "Motherboards for gaming builds"),
                ("Power Supplies", "power-supplies", "PSUs for gaming systems"),
                ("Cases", "cases", "PC cases for gaming builds"),
                ("Peripherals", "peripherals", "Gaming keyboards, mice, and headsets"),
            ]

            for name, slug, description in cat_data_list:
                category = Category(name=name, slug=slug, description=description)
                session.add(category)
                categories.append(category)

            session.commit()

            # Create brands
            brands = []
            brand_data_list = [
                ("NVIDIA", "Leading GPU manufacturer"),
                ("AMD", "CPU and GPU manufacturer"),
                ("Intel", "Leading CPU manufacturer"),
                ("Corsair", "Gaming hardware manufacturer"),
                ("ASUS", "Computer hardware manufacturer"),
                ("MSI", "Gaming hardware specialist"),
                ("Kingston", "Memory and storage solutions"),
                ("Seagate", "Storage solutions"),
            ]

            for name, description in brand_data_list:
                brand = Brand(name=name, description=description)
                session.add(brand)
                brands.append(brand)

            session.commit()

            # Create sample products
            products_data = [
                {
                    "name": "RTX 4060 Gaming Graphics Card",
                    "description": "Affordable gaming GPU with excellent 1080p performance. Features 8GB GDDR6 memory and ray tracing support.",
                    "sku": "RTX4060-8G",
                    "price": Decimal("299.99"),
                    "original_price": Decimal("349.99"),
                    "category_id": categories[0].id,
                    "brand_id": brands[0].id,  # NVIDIA
                    "stock_quantity": 15,
                    "slug": "rtx-4060-gaming-graphics-card",
                    "specifications": {
                        "Memory": "8GB GDDR6",
                        "Memory Interface": "128-bit",
                        "Base Clock": "1830 MHz",
                        "Boost Clock": "2460 MHz",
                        "CUDA Cores": "3072",
                    },
                    "features": ["Ray Tracing", "DLSS 3", "AV1 Encoding"],
                },
                {
                    "name": "Ryzen 5 5600X Processor",
                    "description": "6-core, 12-thread processor perfect for gaming. Excellent price-to-performance ratio.",
                    "sku": "R5-5600X",
                    "price": Decimal("199.99"),
                    "original_price": Decimal("229.99"),
                    "category_id": categories[1].id,
                    "brand_id": brands[1].id,  # AMD
                    "stock_quantity": 25,
                    "slug": "ryzen-5-5600x-processor",
                    "specifications": {
                        "Cores": "6",
                        "Threads": "12",
                        "Base Clock": "3.7 GHz",
                        "Boost Clock": "4.6 GHz",
                        "Cache": "32MB L3",
                        "TDP": "65W",
                    },
                    "features": ["PCIe 4.0", "DDR4 Support", "Unlocked Multiplier"],
                },
                {
                    "name": "16GB DDR4-3200 Gaming Memory Kit",
                    "description": "High-performance 16GB (2x8GB) DDR4 memory kit optimized for gaming.",
                    "sku": "DDR4-3200-16G",
                    "price": Decimal("79.99"),
                    "original_price": Decimal("99.99"),
                    "category_id": categories[2].id,
                    "brand_id": brands[3].id,  # Corsair
                    "stock_quantity": 40,
                    "slug": "16gb-ddr4-3200-gaming-memory",
                    "specifications": {
                        "Capacity": "16GB (2x8GB)",
                        "Speed": "DDR4-3200",
                        "Timing": "16-18-18-36",
                        "Voltage": "1.35V",
                    },
                    "features": ["XMP 2.0", "Heat Spreaders", "Lifetime Warranty"],
                },
                {
                    "name": "1TB NVMe SSD Gaming Drive",
                    "description": "Fast 1TB NVMe SSD perfect for storing games and reducing load times.",
                    "sku": "NVME-1TB-GAME",
                    "price": Decimal("89.99"),
                    "original_price": Decimal("119.99"),
                    "category_id": categories[3].id,
                    "brand_id": brands[6].id,  # Kingston
                    "stock_quantity": 30,
                    "slug": "1tb-nvme-ssd-gaming-drive",
                    "specifications": {
                        "Capacity": "1TB",
                        "Interface": "PCIe 3.0 x4",
                        "Sequential Read": "2100 MB/s",
                        "Sequential Write": "1700 MB/s",
                        "Form Factor": "M.2 2280",
                    },
                    "features": ["NVMe 1.3", "3D NAND", "5-Year Warranty"],
                },
                {
                    "name": "B550 Gaming Motherboard",
                    "description": "AMD B550 chipset motherboard with PCIe 4.0 support and gaming features.",
                    "sku": "B550-GAMING",
                    "price": Decimal("129.99"),
                    "original_price": Decimal("159.99"),
                    "category_id": categories[4].id,
                    "brand_id": brands[4].id,  # ASUS
                    "stock_quantity": 20,
                    "slug": "b550-gaming-motherboard",
                    "specifications": {
                        "Socket": "AM4",
                        "Chipset": "AMD B550",
                        "Memory": "DDR4-4400 (O.C.)",
                        "Expansion Slots": "PCIe 4.0 x16, PCIe 3.0 x16",
                        "Form Factor": "ATX",
                    },
                    "features": ["PCIe 4.0", "USB 3.2 Gen2", "WiFi 6", "RGB Lighting"],
                },
                {
                    "name": "650W 80+ Gold Gaming PSU",
                    "description": "Fully modular 650W power supply with 80+ Gold efficiency rating.",
                    "sku": "PSU-650W-GOLD",
                    "price": Decimal("99.99"),
                    "original_price": Decimal("129.99"),
                    "category_id": categories[5].id,
                    "brand_id": brands[3].id,  # Corsair
                    "stock_quantity": 18,
                    "slug": "650w-80plus-gold-gaming-psu",
                    "specifications": {
                        "Wattage": "650W",
                        "Efficiency": "80+ Gold",
                        "Modular": "Fully Modular",
                        "Fan Size": "140mm",
                        "Dimensions": "150 x 86 x 160 mm",
                    },
                    "features": ["Zero RPM Mode", "Japanese Capacitors", "10-Year Warranty"],
                },
                {
                    "name": "Mid-Tower Gaming Case",
                    "description": "Stylish mid-tower case with tempered glass panel and RGB lighting.",
                    "sku": "CASE-MIDTOWER",
                    "price": Decimal("79.99"),
                    "category_id": categories[6].id,
                    "brand_id": brands[5].id,  # MSI
                    "stock_quantity": 12,
                    "slug": "mid-tower-gaming-case",
                    "specifications": {
                        "Form Factor": "Mid-Tower",
                        "Material": "Steel, Tempered Glass",
                        "Motherboard Support": "ATX, mATX, Mini-ITX",
                        "GPU Clearance": "370mm",
                        "CPU Cooler Height": "165mm",
                    },
                    "features": ["Tempered Glass", "RGB Lighting", "Tool-free Installation"],
                },
                {
                    "name": "Mechanical Gaming Keyboard",
                    "description": "RGB mechanical gaming keyboard with Cherry MX switches.",
                    "sku": "KB-MECH-RGB",
                    "price": Decimal("89.99"),
                    "original_price": Decimal("109.99"),
                    "category_id": categories[7].id,
                    "brand_id": brands[3].id,  # Corsair
                    "stock_quantity": 35,
                    "slug": "mechanical-gaming-keyboard",
                    "specifications": {
                        "Switch Type": "Cherry MX Red",
                        "Backlighting": "RGB per-key",
                        "Layout": "Full-size",
                        "Connection": "USB-C",
                        "Polling Rate": "1000Hz",
                    },
                    "features": ["N-Key Rollover", "Media Controls", "Software Customization"],
                },
            ]

            products = []
            for product_data in products_data:
                product = Product(**product_data)
                session.add(product)
                products.append(product)

            session.commit()

            # Add sample images
            sample_images = [
                # RTX 4060
                {
                    "product_id": products[0].id,
                    "image_url": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=400",
                    "alt_text": "RTX 4060 Graphics Card",
                    "is_primary": True,
                },
                # Ryzen 5600X
                {
                    "product_id": products[1].id,
                    "image_url": "https://images.unsplash.com/photo-1555617981-dac3880eac6e?w=400",
                    "alt_text": "AMD Ryzen Processor",
                    "is_primary": True,
                },
                # Memory
                {
                    "product_id": products[2].id,
                    "image_url": "https://images.unsplash.com/photo-1562976540-1502c2145186?w=400",
                    "alt_text": "DDR4 Memory Modules",
                    "is_primary": True,
                },
                # SSD
                {
                    "product_id": products[3].id,
                    "image_url": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=400",
                    "alt_text": "NVMe SSD Drive",
                    "is_primary": True,
                },
                # Motherboard
                {
                    "product_id": products[4].id,
                    "image_url": "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=400",
                    "alt_text": "Gaming Motherboard",
                    "is_primary": True,
                },
                # PSU
                {
                    "product_id": products[5].id,
                    "image_url": "https://images.unsplash.com/photo-1609694740799-82d2c0b2fcd8?w=400",
                    "alt_text": "Power Supply Unit",
                    "is_primary": True,
                },
                # Case
                {
                    "product_id": products[6].id,
                    "image_url": "https://images.unsplash.com/photo-1587202372634-32705e3bf49c?w=400",
                    "alt_text": "Gaming PC Case",
                    "is_primary": True,
                },
                # Keyboard
                {
                    "product_id": products[7].id,
                    "image_url": "https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=400",
                    "alt_text": "Mechanical Gaming Keyboard",
                    "is_primary": True,
                },
            ]

            for img_data in sample_images:
                image = ProductImage(**img_data)
                session.add(image)

            session.commit()
