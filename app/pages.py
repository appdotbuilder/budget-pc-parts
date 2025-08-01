import logging
from nicegui import ui, app
from app.components import NavigationBar, ProductGrid, SimpleFilterPanel, ProductDetail, ProductCard, apply_theme
from app.services import ProductService, CategoryService, DataSeederService
from app.models import ProductFilter, ProductStatus

logger = logging.getLogger(__name__)


def create():
    """Create all pages for the PC gaming products website"""

    # Apply theme
    apply_theme()

    # Seed sample data
    DataSeederService.seed_sample_data()

    @ui.page("/")
    def home_page():
        """Home page with featured products"""
        NavigationBar().render()

        with ui.column().classes("w-full max-w-7xl mx-auto px-4 py-8"):
            # Hero section
            with ui.card().classes("w-full p-8 bg-gradient-to-r from-blue-600 to-purple-600 text-white mb-8"):
                ui.label("Find Your Perfect Gaming Setup").classes("text-4xl font-bold mb-4")
                ui.label("Discover budget-friendly PC gaming products with unbeatable prices").classes("text-xl mb-6")
                ui.button("Shop Now", on_click=lambda: ui.navigate.to("/products")).classes(
                    "bg-white text-blue-600 font-bold px-6 py-3 rounded-lg hover:bg-gray-100"
                )

            # Featured products section
            ui.label("Featured Products").classes("text-2xl font-bold mb-6")

            try:
                featured_products = ProductService.get_featured_products(limit=8)
                if featured_products:
                    ProductGrid(featured_products).render()
                else:
                    with ui.card().classes("p-8 text-center"):
                        ui.label("No featured products available").classes("text-xl text-gray-600")
                        ui.button("Browse All Products", on_click=lambda: ui.navigate.to("/products")).classes("mt-4")
            except Exception as e:
                logger.error(f"Error loading featured products: {e}")
                with ui.card().classes("p-8 text-center"):
                    ui.label("Unable to load featured products").classes("text-xl text-gray-600")
                    ui.button("Browse All Products", on_click=lambda: ui.navigate.to("/products")).classes("mt-4")

            # Quick category links
            ui.label("Shop by Category").classes("text-2xl font-bold mt-12 mb-6")

            try:
                categories = CategoryService.get_root_categories()[:6]  # Show first 6 categories
                if categories:
                    with ui.element("div").classes("grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"):
                        for category in categories:
                            with (
                                ui.card()
                                .classes("p-4 text-center cursor-pointer hover:shadow-lg transition-shadow")
                                .on("click", lambda cat_id=category.id: ui.navigate.to(f"/products?category={cat_id}"))
                            ):
                                # Category icon (simplified mapping)
                                icon_map = {
                                    "graphics-cards": "memory",
                                    "processors": "developer_board",
                                    "memory": "storage",
                                    "storage": "hard_drive",
                                    "motherboards": "developer_board",
                                    "power-supplies": "power",
                                    "cases": "computer",
                                    "peripherals": "keyboard",
                                }
                                icon = icon_map.get(category.slug, "category")
                                ui.icon(icon, size="32px").classes("text-primary mb-2")
                                ui.label(category.name).classes("font-semibold text-gray-800")
            except Exception as e:
                logger.error(f"Error loading categories: {e}")
                ui.label("Categories will be available soon").classes("text-gray-600")

    @ui.page("/products")
    async def products_page():
        """Products listing page with filters"""
        NavigationBar().render()

        # Get URL parameters for initial filters
        await ui.context.client.connected()
        query_params = app.storage.client.get("query_params", {})

        # Parse filters from URL
        initial_filters = {}
        if "category" in query_params:
            try:
                initial_filters["category_id"] = int(query_params["category"])
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid category parameter in URL: {query_params.get('category')}: {e}")
                pass

        if "search" in query_params:
            initial_filters["search_query"] = query_params["search"]

        # State for products
        products_container = ui.column().classes("w-full")

        def load_products(filters: dict):
            """Load and display products based on filters"""
            try:
                # Convert filters to ProductFilter object
                filter_obj = ProductFilter(
                    category_id=filters.get("category_id"),
                    brand_id=filters.get("brand_id"),
                    min_price=filters.get("min_price"),
                    max_price=filters.get("max_price"),
                    search_query=filters.get("search_query"),
                    in_stock_only=filters.get("in_stock_only", False),
                    status=ProductStatus.ACTIVE,
                )

                products = ProductService.get_products(filters=filter_obj, limit=50)

                # Clear and update products container
                products_container.clear()
                with products_container:
                    # Results header
                    results_text = f"Found {len(products)} product{'s' if len(products) != 1 else ''}"
                    if filters.get("search_query"):
                        results_text += f' for "{filters["search_query"]}"'
                    ui.label(results_text).classes("text-lg font-semibold mb-4")

                    # Products grid
                    ProductGrid(products).render()

            except Exception as e:
                logger.error(f"Error loading products with filters {filters}: {e}")
                products_container.clear()
                with products_container:
                    ui.label("Error loading products. Please try again.").classes("text-red-600")

        with ui.column().classes("w-full max-w-7xl mx-auto px-4 py-8"):
            ui.label("Gaming Products").classes("text-3xl font-bold mb-6")

            with ui.row().classes("w-full gap-8"):
                # Filters sidebar
                with ui.column().classes("w-64 flex-shrink-0"):
                    filter_panel = SimpleFilterPanel(on_filter_change=load_products)
                    filter_panel.render()

                # Products area
                with ui.column().classes("flex-1"):
                    with products_container:
                        pass  # Container will be populated by load_products

        # Load initial products
        load_products(initial_filters)

    @ui.page("/product/{product_id}")
    def product_detail_page(product_id: int):
        """Individual product detail page"""
        NavigationBar().render()

        try:
            product = ProductService.get_product_by_id(product_id)

            if not product:
                with ui.column().classes("w-full max-w-7xl mx-auto px-4 py-8 text-center"):
                    ui.label("Product Not Found").classes("text-3xl font-bold text-gray-800 mb-4")
                    ui.label("The product you are looking for does not exist.").classes("text-gray-600 mb-6")
                    ui.button("Back to Products", on_click=lambda: ui.navigate.to("/products")).classes(
                        "bg-primary text-white px-6 py-3"
                    )
                return

            with ui.column().classes("w-full max-w-7xl mx-auto px-4 py-8"):
                # Product detail component
                ProductDetail(product).render()

                # Related products section
                ui.label("You might also like").classes("text-2xl font-bold mt-12 mb-6")

                try:
                    # Get related products (same category, different product)
                    related_filters = ProductFilter(category_id=product.category_id, status=ProductStatus.ACTIVE)
                    related_products = ProductService.get_products(filters=related_filters, limit=4)
                    # Remove current product from related
                    related_products = [p for p in related_products if p.id != product.id][:4]

                    if related_products:
                        with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"):
                            for related_product in related_products:
                                ProductCard(related_product).render()
                    else:
                        ui.label("No related products found").classes("text-gray-600")

                except Exception as e:
                    logger.error(f"Error loading related products for product {product_id}: {e}")
                    ui.label("Unable to load related products").classes("text-gray-600")

        except Exception as e:
            logger.error(f"Error loading product {product_id}: {e}")
            with ui.column().classes("w-full max-w-7xl mx-auto px-4 py-8 text-center"):
                ui.label("Error Loading Product").classes("text-3xl font-bold text-red-600 mb-4")
                ui.label("There was an error loading the product details.").classes("text-gray-600 mb-6")
                ui.button("Back to Products", on_click=lambda: ui.navigate.to("/products")).classes(
                    "bg-primary text-white px-6 py-3"
                )

    @ui.page("/category/{category_slug}")
    def category_page(category_slug: str):
        """Category-specific product listing"""
        NavigationBar().render()

        try:
            category = CategoryService.get_category_by_slug(category_slug)

            if not category:
                with ui.column().classes("w-full max-w-7xl mx-auto px-4 py-8 text-center"):
                    ui.label("Category Not Found").classes("text-3xl font-bold text-gray-800 mb-4")
                    ui.button("Back to Products", on_click=lambda: ui.navigate.to("/products")).classes(
                        "bg-primary text-white px-6 py-3"
                    )
                return

            with ui.column().classes("w-full max-w-7xl mx-auto px-4 py-8"):
                # Category header
                ui.label(category.name).classes("text-3xl font-bold mb-2")
                if category.description:
                    ui.label(category.description).classes("text-gray-600 mb-6")

                # Load category products
                try:
                    filters = ProductFilter(category_id=category.id, status=ProductStatus.ACTIVE)
                    products = ProductService.get_products(filters=filters, limit=50)

                    if products:
                        ui.label(f"{len(products)} product{'s' if len(products) != 1 else ''} found").classes(
                            "text-lg font-semibold mb-4"
                        )
                        ProductGrid(products).render()
                    else:
                        with ui.card().classes("p-8 text-center"):
                            ui.label("No products in this category yet").classes("text-xl text-gray-600 mb-4")
                            ui.button("Browse All Products", on_click=lambda: ui.navigate.to("/products")).classes(
                                "bg-primary text-white px-4 py-2"
                            )

                except Exception as e:
                    logger.error(f"Error loading products for category {category_slug}: {e}")
                    ui.label("Error loading category products").classes("text-red-600")

        except Exception as e:
            logger.error(f"Error loading category {category_slug}: {e}")
            with ui.column().classes("w-full max-w-7xl mx-auto px-4 py-8 text-center"):
                ui.label("Error Loading Category").classes("text-3xl font-bold text-red-600 mb-4")
                ui.button("Back to Products", on_click=lambda: ui.navigate.to("/products")).classes(
                    "bg-primary text-white px-6 py-3"
                )
