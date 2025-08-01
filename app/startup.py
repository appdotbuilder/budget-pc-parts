from app.database import create_tables
import app.pages


def startup() -> None:
    # this function is called before the first request
    create_tables()

    # Create all application pages
    app.pages.create()
