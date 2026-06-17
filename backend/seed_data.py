"""Seed the DEV database with sample retail data.

Run after starting the API once (so tables exist), or standalone:
    python seed_data.py
"""
import random
from datetime import date, timedelta

from app.database import Base, SessionLocal, engine
from app import models

CITIES = ["Chennai", "Mumbai", "Bangalore", "Delhi", "Hyderabad", "Pune"]
PRODUCTS = ["Laptop", "Phone", "Headphones", "Monitor", "Keyboard", "Mouse", "Tablet"]
CUSTOMERS = [
    ("Alice Johnson", "alice@example.com", "9000000001"),
    ("Bob Smith", "bob@example.com", "9000000002"),
    ("Carol White", "carol@example.com", "9000000003"),
    ("David Lee", "david@example.com", "9000000004"),
    ("Eva Brown", "eva@example.com", "9000000005"),
    ("Frank Green", "frank@example.com", "9000000006"),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Customer).count() > 0:
            print("Data already present, skipping seed.")
            return

        customers = []
        for i, (name, email, phone) in enumerate(CUSTOMERS):
            c = models.Customer(name=name, email=email, phone=phone, city=random.choice(CITIES))
            db.add(c)
            customers.append(c)
        db.commit()

        for c in customers:
            for _ in range(random.randint(2, 6)):
                db.add(models.Order(
                    customer_id=c.customer_id,
                    product_name=random.choice(PRODUCTS),
                    quantity=random.randint(1, 5),
                    amount=round(random.uniform(20, 2000), 2),
                    order_date=date.today() - timedelta(days=random.randint(0, 60)),
                ))
        db.commit()
        print(f"Seeded {len(customers)} customers and {db.query(models.Order).count()} orders.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
