from decimal import Decimal
from typing import List, Optional, Callable
from nicegui import ui
from app.models import ProductSummary, Category, Brand, Product
from app.services import ProductService, CategoryService, BrandService


class ProductCard:
    """Reusable product card component"""

    def __init__(self, product: ProductSummary, on_click: Optional[Callable] = None):
        self.product = product
        self.on_click = on_click

    def render(self):
        """Render the product card"""
        with (
            ui.card()
            .classes("w-full max-w-sm cursor-pointer hover:shadow-lg transition-shadow")
            .on("click", self.on_click if self.on_click else lambda: ui.navigate.to(f"/product/{self.product.id}"))
        ):
            # Product image
            if self.product.primary_image_url:
                ui.image(self.product.primary_image_url).classes("w-full h-48 object-cover rounded-t")
            else:
                with ui.element("div").classes("w-full h-48 bg-gray-200 flex items-center justify-center rounded-t"):
                    ui.icon("image", size="48px").classes("text-gray-400")

            # Product details
            with ui.column().classes("p-4 gap-2"):
                # Product name
                ui.label(self.product.name).classes("text-lg font-semibold text-gray-800 line-clamp-2")

                # Category and brand
                if self.product.category_name or self.product.brand_name:
                    category_brand = []
                    if self.product.brand_name:
                        category_brand.append(self.product.brand_name)
                    if self.product.category_name:
                        category_brand.append(self.product.category_name)
                    ui.label(" • ".join(category_brand)).classes("text-sm text-gray-500")

                # Price section
                with ui.row().classes("items-center gap-2 mt-2"):
                    # Current price
                    ui.label(f"${self.product.price:.2f}").classes("text-xl font-bold text-primary")

                    # Original price (if discounted)
                    if self.product.original_price and self.product.original_price > self.product.price:
                        ui.label(f"${self.product.original_price:.2f}").classes("text-sm text-gray-500 line-through")
                        discount_percent = int(
                            ((self.product.original_price - self.product.price) / self.product.original_price) * 100
                        )
                        ui.label(f"-{discount_percent}%").classes("text-sm text-green-600 font-medium")

                # Stock status
                if self.product.stock_quantity > 0:
                    ui.label(f"{self.product.stock_quantity} in stock").classes("text-sm text-green-600")
                else:
                    ui.label("Out of stock").classes("text-sm text-red-600")


class SimpleFilterPanel:
    """Simplified product filtering panel component"""

    def __init__(self, on_filter_change: Callable[[dict], None]):
        self.on_filter_change = on_filter_change
        self.categories: List[Category] = []
        self.brands: List[Brand] = []

        # Load filter options
        self._load_filter_options()

    def _load_filter_options(self):
        """Load categories and brands for filters"""
        self.categories = CategoryService.get_all_categories()
        self.brands = BrandService.get_all_brands()

    def render(self):
        """Render the filter panel"""
        with ui.card().classes("p-4 bg-white shadow-sm"):
            ui.label("Filters").classes("text-lg font-semibold mb-4")

            # Search
            search_input = ui.input(label="Search products", placeholder="Enter product name...").classes("w-full mb-4")

            # Category filter
            category_select = None
            if self.categories:
                category_options = {0: "All Categories"}
                category_options.update({cat.id: cat.name for cat in self.categories if cat.id is not None})

                category_select = ui.select(options=category_options, label="Category", value=0).classes("w-full mb-4")

            # Brand filter
            brand_select = None
            if self.brands:
                brand_options = {0: "All Brands"}
                brand_options.update({brand.id: brand.name for brand in self.brands if brand.id is not None})

                brand_select = ui.select(options=brand_options, label="Brand", value=0).classes("w-full mb-4")

            # Price range
            ui.label("Price Range").classes("text-sm font-medium text-gray-700 mb-2")

            with ui.row().classes("gap-2 mb-4"):
                min_price_input = ui.number(label="Min $", min=0, format="%.2f").classes("flex-1")

                max_price_input = ui.number(label="Max $", min=0, format="%.2f").classes("flex-1")

            # In stock only
            stock_checkbox = ui.checkbox("In stock only").classes("mb-4")

            # Apply filters button
            def apply_filters():
                filters = {
                    "search_query": search_input.value if search_input.value else None,
                    "category_id": category_select.value if category_select and category_select.value != 0 else None,
                    "brand_id": brand_select.value if brand_select and brand_select.value != 0 else None,
                    "min_price": Decimal(str(min_price_input.value)) if min_price_input.value else None,
                    "max_price": Decimal(str(max_price_input.value)) if max_price_input.value else None,
                    "in_stock_only": stock_checkbox.value,
                }
                self.on_filter_change(filters)

            ui.button("Apply Filters", on_click=apply_filters).classes("w-full bg-primary text-white")

            # Clear filters button
            def clear_filters():
                search_input.set_value("")
                if category_select:
                    category_select.set_value(0)
                if brand_select:
                    brand_select.set_value(0)
                min_price_input.set_value(None)
                max_price_input.set_value(None)
                stock_checkbox.set_value(False)
                apply_filters()

            ui.button("Clear Filters", on_click=clear_filters).classes("w-full mt-2").props("outline")


class ProductGrid:
    """Product grid display component"""

    def __init__(self, products: List[ProductSummary]):
        self.products = products

    def render(self):
        """Render products in a responsive grid"""
        if not self.products:
            with ui.column().classes("w-full text-center py-12"):
                ui.icon("search_off", size="64px").classes("text-gray-400 mb-4")
                ui.label("No products found").classes("text-xl text-gray-600 mb-2")
                ui.label("Try adjusting your filters or search terms").classes("text-gray-500")
            return

        with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"):
            for product in self.products:
                ProductCard(product).render()


class ProductDetail:
    """Product detail view component"""

    def __init__(self, product: Product):
        self.product = product
        self.images = ProductService.get_product_images(product.id or 0)

    def render(self):
        """Render detailed product view"""
        with ui.row().classes("w-full gap-8"):
            # Left side - Images
            with ui.column().classes("flex-1"):
                self._render_image_gallery()

            # Right side - Product info
            with ui.column().classes("flex-1 gap-4"):
                self._render_product_info()

    def _render_image_gallery(self):
        """Render product image gallery"""
        if not self.images:
            with ui.element("div").classes("w-full h-96 bg-gray-200 flex items-center justify-center rounded"):
                ui.icon("image", size="64px").classes("text-gray-400")
            return

        # Main image
        primary_image = next((img for img in self.images if img.is_primary), self.images[0])
        ui.image(primary_image.image_url).classes("w-full h-96 object-cover rounded")

    def _render_product_info(self):
        """Render product information section"""
        # Breadcrumb
        with ui.row().classes("text-sm text-gray-500 mb-2"):
            if self.product.category:
                ui.label(self.product.category.name)
                ui.label(">")
            ui.label(self.product.name).classes("text-gray-800")

        # Product name
        ui.label(self.product.name).classes("text-3xl font-bold text-gray-800 mb-2")

        # Brand
        if self.product.brand:
            ui.label(f"By {self.product.brand.name}").classes("text-lg text-gray-600 mb-4")

        # Price section
        with ui.row().classes("items-center gap-4 mb-4"):
            ui.label(f"${self.product.price:.2f}").classes("text-3xl font-bold text-primary")

            if self.product.original_price and self.product.original_price > self.product.price:
                ui.label(f"${self.product.original_price:.2f}").classes("text-xl text-gray-500 line-through")
                discount_percent = int(
                    ((self.product.original_price - self.product.price) / self.product.original_price) * 100
                )
                ui.badge(f"{discount_percent}% OFF", color="positive").classes("text-sm")

        # Stock status
        if self.product.stock_quantity > 0:
            ui.label(f"✓ {self.product.stock_quantity} in stock").classes("text-green-600 font-medium mb-4")
        else:
            ui.label("⚠ Out of stock").classes("text-red-600 font-medium mb-4")

        # SKU
        ui.label(f"SKU: {self.product.sku}").classes("text-sm text-gray-500 mb-4")

        # Description
        if self.product.description:
            ui.label("Description").classes("text-lg font-semibold mb-2")
            ui.label(self.product.description).classes("text-gray-700 leading-relaxed mb-6")

        # Specifications
        if self.product.specifications:
            ui.label("Specifications").classes("text-lg font-semibold mb-2")
            with ui.card().classes("p-4 bg-gray-50"):
                for key, value in self.product.specifications.items():
                    with ui.row().classes("justify-between py-1 border-b border-gray-200 last:border-b-0"):
                        ui.label(key).classes("font-medium text-gray-700")
                        ui.label(str(value)).classes("text-gray-600")

        # Features
        if self.product.features:
            ui.label("Features").classes("text-lg font-semibold mt-6 mb-2")
            with ui.column().classes("gap-1"):
                for feature in self.product.features:
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("check_circle", size="16px").classes("text-green-500")
                        ui.label(feature).classes("text-gray-700")


class NavigationBar:
    """Main navigation bar component"""

    def __init__(self):
        self.categories = CategoryService.get_root_categories()

    def render(self):
        """Render the navigation bar"""
        with ui.header().classes("bg-white shadow-sm border-b border-gray-200"):
            with ui.row().classes("w-full max-w-7xl mx-auto px-4 items-center justify-between h-16"):
                # Logo/Brand
                with ui.row().classes("items-center gap-2"):
                    ui.icon("sports_esports", size="32px").classes("text-primary")
                    ui.label("GameDeals").classes("text-xl font-bold text-gray-800").on(
                        "click", lambda: ui.navigate.to("/")
                    )

                # Main navigation
                with ui.row().classes("items-center gap-6 hidden md:flex"):
                    ui.link("Home", "/").classes("text-gray-700 hover:text-primary font-medium")
                    ui.link("Products", "/products").classes("text-gray-700 hover:text-primary font-medium")

                # Simple search
                with ui.row().classes("items-center flex-1 max-w-md mx-4"):
                    search_input = ui.input(placeholder="Search products...").classes("w-full")
                    ui.button(
                        icon="search",
                        on_click=lambda: ui.navigate.to(f"/products?search={search_input.value}")
                        if search_input.value
                        else None,
                    ).props("flat round").classes("ml-2")


def apply_theme():
    """Apply consistent theme across the application"""
    ui.colors(
        primary="#2563eb",  # Professional blue
        secondary="#64748b",  # Subtle gray
        accent="#10b981",  # Success green
        positive="#10b981",
        negative="#ef4444",  # Error red
        warning="#f59e0b",  # Warning amber
        info="#3b82f6",  # Info blue
    )

    # Add custom CSS for better styling
    ui.add_head_html("""
    <style>
        .line-clamp-2 {
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .transition-shadow {
            transition: box-shadow 0.2s ease-in-out;
        }
        
        .hover\\:shadow-lg:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        
        .grid {
            display: grid;
        }
        
        .grid-cols-1 {
            grid-template-columns: repeat(1, minmax(0, 1fr));
        }
        
        @media (min-width: 768px) {
            .md\\:grid-cols-2 {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        
        @media (min-width: 1024px) {
            .lg\\:grid-cols-3 {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
        }
        
        @media (min-width: 1280px) {
            .xl\\:grid-cols-4 {
                grid-template-columns: repeat(4, minmax(0, 1fr));
            }
        }
    </style>
    """)
