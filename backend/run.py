import os
from app import create_app
from app.utils.seeder import seed_database

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.cli.command("seed-db")
def seed_command():
    """Seed the database with sample data."""
    seed_database()


if __name__ == "__main__":
    # Auto-seed database if empty
    with app.app_context():
        try:
            seed_database()
        except Exception as e:
            print(f"Notice: database seeding note: {e}")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
