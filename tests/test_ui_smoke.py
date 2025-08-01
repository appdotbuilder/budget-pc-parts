import pytest
import logging
from app.database import reset_db
from app.services import DataSeederService

logger = logging.getLogger(__name__)


@pytest.fixture()
def clean_db():
    """Clean database for each test"""
    reset_db()
    DataSeederService.seed_sample_data()
    yield
    reset_db()


def test_pages_module_import():
    """Test that pages module can be imported without errors"""
    try:
        import app.pages

        app.pages.create()
    except Exception as e:
        logger.error(f"Error importing pages module: {e}")
        pytest.fail(f"Pages module import failed: {e}")


def test_components_module_import():
    """Test that components module can be imported without errors"""
    try:
        import app.components

        app.components.apply_theme()
    except Exception as e:
        logger.error(f"Error importing components module: {e}")
        pytest.fail(f"Components module import failed: {e}")


def test_services_integration_with_ui(clean_db):
    """Test that services work correctly for UI consumption"""
    from app.services import ProductService, CategoryService

    # Test data seeding worked
    products = ProductService.get_products(limit=5)
    assert len(products) > 0

    categories = CategoryService.get_all_categories()
    assert len(categories) > 0

    # Test product detail retrieval
    product = ProductService.get_product_by_id(1)
    assert product is not None

    # Test product images
    images = ProductService.get_product_images(1)
    assert len(images) > 0
