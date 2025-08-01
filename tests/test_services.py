import pytest
from decimal import Decimal
from app.database import reset_db
from app.services import ProductService, CategoryService, BrandService, DataSeederService
from app.models import ProductFilter, ProductStatus


@pytest.fixture()
def clean_db():
    """Clean database for each test"""
    reset_db()
    yield
    reset_db()


def test_data_seeder_creates_sample_data(clean_db):
    """Test that sample data is created correctly"""
    # Initially no products
    products = ProductService.get_products(limit=100)
    assert len(products) == 0

    # Seed data
    DataSeederService.seed_sample_data()

    # Check products were created
    products = ProductService.get_products(limit=100)
    assert len(products) > 0

    # Check categories were created
    categories = CategoryService.get_all_categories()
    assert len(categories) > 0

    # Check brands were created
    brands = BrandService.get_all_brands()
    assert len(brands) > 0


def test_data_seeder_idempotent(clean_db):
    """Test that running seeder multiple times doesn't duplicate data"""
    DataSeederService.seed_sample_data()
    initial_count = len(ProductService.get_products(limit=100))

    # Run seeder again
    DataSeederService.seed_sample_data()
    final_count = len(ProductService.get_products(limit=100))

    assert initial_count == final_count


def test_product_service_get_products_no_filters(clean_db):
    """Test getting products without filters"""
    DataSeederService.seed_sample_data()

    products = ProductService.get_products()
    assert len(products) > 0

    # Check product structure
    product = products[0]
    assert product.id > 0
    assert product.name
    assert product.price > Decimal("0")
    assert product.status == ProductStatus.ACTIVE


def test_product_service_filter_by_category(clean_db):
    """Test filtering products by category"""
    DataSeederService.seed_sample_data()

    # Get a category
    categories = CategoryService.get_all_categories()
    category = categories[0]

    # Filter by category
    filters = ProductFilter(category_id=category.id)
    products = ProductService.get_products(filters=filters)

    # All products should be from the specified category
    for product in products:
        assert product.category_name == category.name


def test_product_service_filter_by_price_range(clean_db):
    """Test filtering products by price range"""
    DataSeederService.seed_sample_data()

    min_price = Decimal("50.00")
    max_price = Decimal("150.00")

    filters = ProductFilter(min_price=min_price, max_price=max_price)
    products = ProductService.get_products(filters=filters)

    # All products should be within price range
    for product in products:
        assert min_price <= product.price <= max_price


def test_product_service_filter_in_stock_only(clean_db):
    """Test filtering for in-stock products only"""
    DataSeederService.seed_sample_data()

    filters = ProductFilter(in_stock_only=True)
    products = ProductService.get_products(filters=filters)

    # All products should have stock
    for product in products:
        assert product.stock_quantity > 0


def test_product_service_search_products(clean_db):
    """Test searching products by name"""
    DataSeederService.seed_sample_data()

    # Search for a known term that exists in our seeded data
    search_term = "RTX"
    filters = ProductFilter(search_query=search_term)
    products = ProductService.get_products(filters=filters)

    # Should find products containing the search term
    assert len(products) > 0
    for product in products:
        assert search_term.lower() in product.name.lower() or search_term.lower() in product.name


def test_product_service_get_product_by_id(clean_db):
    """Test getting a specific product by ID"""
    DataSeederService.seed_sample_data()

    # Get a product ID
    products = ProductService.get_products(limit=1)
    product_id = products[0].id

    # Get product by ID
    product = ProductService.get_product_by_id(product_id)

    assert product is not None
    assert product.id == product_id
    assert product.name
    assert product.price > Decimal("0")


def test_product_service_get_product_by_id_not_found(clean_db):
    """Test getting non-existent product returns None"""
    product = ProductService.get_product_by_id(999999)
    assert product is None


def test_product_service_get_featured_products(clean_db):
    """Test getting featured products"""
    DataSeederService.seed_sample_data()

    featured = ProductService.get_featured_products(limit=5)

    assert len(featured) <= 5
    # Featured products should be active and reasonably priced
    for product in featured:
        assert product.status == ProductStatus.ACTIVE
        assert product.stock_quantity > 0
        assert product.price <= Decimal("200.00")


def test_product_service_get_price_range(clean_db):
    """Test getting price range across all products"""
    DataSeederService.seed_sample_data()

    price_range = ProductService.get_price_range()

    assert "min" in price_range
    assert "max" in price_range
    assert price_range["min"] <= price_range["max"]
    assert price_range["min"] >= Decimal("0")


def test_product_service_get_price_range_empty_db(clean_db):
    """Test price range with no products"""
    price_range = ProductService.get_price_range()

    assert price_range["min"] == Decimal("0")
    assert price_range["max"] == Decimal("1000")


def test_category_service_get_all_categories(clean_db):
    """Test getting all categories"""
    DataSeederService.seed_sample_data()

    categories = CategoryService.get_all_categories()

    assert len(categories) > 0
    for category in categories:
        assert category.name
        assert category.slug
        assert category.is_active


def test_category_service_get_root_categories(clean_db):
    """Test getting root categories (no parent)"""
    DataSeederService.seed_sample_data()

    root_categories = CategoryService.get_root_categories()

    assert len(root_categories) > 0
    for category in root_categories:
        assert category.parent_id is None


def test_category_service_get_category_by_slug(clean_db):
    """Test getting category by slug"""
    DataSeederService.seed_sample_data()

    # Get a known category slug
    categories = CategoryService.get_all_categories()
    test_slug = categories[0].slug

    category = CategoryService.get_category_by_slug(test_slug)

    assert category is not None
    assert category.slug == test_slug


def test_category_service_get_category_by_slug_not_found(clean_db):
    """Test getting non-existent category by slug returns None"""
    category = CategoryService.get_category_by_slug("non-existent-slug")
    assert category is None


def test_category_service_get_categories_with_product_counts(clean_db):
    """Test getting categories with product counts"""
    DataSeederService.seed_sample_data()

    categories_with_counts = CategoryService.get_categories_with_product_counts()

    assert len(categories_with_counts) > 0
    for item in categories_with_counts:
        assert "category" in item
        assert "product_count" in item
        assert item["category"].name
        assert item["product_count"] >= 0


def test_brand_service_get_all_brands(clean_db):
    """Test getting all brands"""
    DataSeederService.seed_sample_data()

    brands = BrandService.get_all_brands()

    assert len(brands) > 0
    for brand in brands:
        assert brand.name
        assert brand.is_active


def test_brand_service_get_brand_by_id(clean_db):
    """Test getting brand by ID"""
    DataSeederService.seed_sample_data()

    brands = BrandService.get_all_brands()
    assert len(brands) > 0

    brand_id = brands[0].id
    if brand_id is not None:
        brand = BrandService.get_brand_by_id(brand_id)
        assert brand is not None
        assert brand.id == brand_id


def test_brand_service_get_brand_by_id_not_found(clean_db):
    """Test getting non-existent brand returns None"""
    brand = BrandService.get_brand_by_id(999999)
    assert brand is None


def test_brand_service_get_brands_with_product_counts(clean_db):
    """Test getting brands with product counts"""
    DataSeederService.seed_sample_data()

    brands_with_counts = BrandService.get_brands_with_product_counts()

    assert len(brands_with_counts) > 0
    for item in brands_with_counts:
        assert "brand" in item
        assert "product_count" in item
        assert item["brand"].name
        assert item["product_count"] >= 0


def test_product_service_get_product_images(clean_db):
    """Test getting product images"""
    DataSeederService.seed_sample_data()

    # Get a product
    products = ProductService.get_products(limit=1)
    product_id = products[0].id

    images = ProductService.get_product_images(product_id)

    # Should have at least one image from seeded data
    assert len(images) >= 1

    primary_image = next((img for img in images if img.is_primary), None)
    assert primary_image is not None
    assert primary_image.image_url
    assert primary_image.product_id == product_id


def test_product_filter_combinations(clean_db):
    """Test complex filter combinations"""
    DataSeederService.seed_sample_data()

    # Get category and brand for testing
    categories = CategoryService.get_all_categories()
    brands = BrandService.get_all_brands()

    # Ensure we have categories and brands
    assert len(categories) > 0
    assert len(brands) > 0

    # Simple filter test without Optional issues
    filters = ProductFilter(
        min_price=Decimal("50.00"), max_price=Decimal("500.00"), in_stock_only=True, status=ProductStatus.ACTIVE
    )

    products = ProductService.get_products(filters=filters)

    # Verify filters are applied
    for product in products:
        assert Decimal("50.00") <= product.price <= Decimal("500.00")
        assert product.stock_quantity > 0
        assert product.status == ProductStatus.ACTIVE


def test_pagination(clean_db):
    """Test product pagination"""
    DataSeederService.seed_sample_data()

    # Get first page
    page1 = ProductService.get_products(limit=3, offset=0)

    # Get second page
    page2 = ProductService.get_products(limit=3, offset=3)

    # Pages should be different
    page1_ids = {p.id for p in page1}
    page2_ids = {p.id for p in page2}

    assert len(page1_ids.intersection(page2_ids)) == 0  # No overlap
