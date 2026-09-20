from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant


CATEGORIES = [
    {
        "name": "Pizzas Tradicionais",
        "slug": "pizzas-tradicionais",
    },
    {
        "name": "Especiais Bella Napoli",
        "slug": "especiais-bella-napoli",
    },
    {
        "name": "Bordas",
        "slug": "bordas",
    },
    {
        "name": "Bebidas",
        "slug": "bebidas",
    },
]


PRODUCTS = [
    {
        "category_slug": "pizzas-tradicionais",
        "name": "Margherita",
        "description": "Molho de tomate, muçarela, tomate e manjericão.",
    },
    {
        "category_slug": "pizzas-tradicionais",
        "name": "Calabresa",
        "description": "Molho de tomate, muçarela e calabresa.",
    },
    {
        "category_slug": "pizzas-tradicionais",
        "name": "Portuguesa",
        "description": "Molho de tomate, muçarela, presunto, ovo, cebola e ervilha.",
    },
    {
        "category_slug": "pizzas-tradicionais",
        "name": "Frango com Catupiry",
        "description": "Frango desfiado, muçarela e Catupiry.",
    },
    {
        "category_slug": "pizzas-tradicionais",
        "name": "Quatro Queijos",
        "description": "Muçarela, provolone, parmesão e Catupiry.",
    },
    {
        "category_slug": "pizzas-tradicionais",
        "name": "Pepperoni",
        "description": "Molho de tomate, muçarela e pepperoni.",
    },
    {
        "category_slug": "especiais-bella-napoli",
        "name": "Calabresa Diablo",
        "description": "Calabresa com toque picante especial Bella Napoli.",
    },
    {
        "category_slug": "especiais-bella-napoli",
        "name": "Pepperoni Jalapeño",
        "description": "Pepperoni, muçarela e jalapeño.",
    },
    {
        "category_slug": "especiais-bella-napoli",
        "name": "Frango Mexicano",
        "description": "Frango temperado com combinação especial inspirada na culinária mexicana.",
    },
    {
        "category_slug": "especiais-bella-napoli",
        "name": "Nacho Supreme",
        "description": "Pizza especial com inspiração mexicana e cobertura cremosa.",
    },
    {
        "category_slug": "bordas",
        "name": "Catupiry",
        "description": "Borda recheada com Catupiry.",
    },
    {
        "category_slug": "bordas",
        "name": "Cheddar",
        "description": "Borda recheada com cheddar.",
    },
    {
        "category_slug": "bordas",
        "name": "Cream Cheese",
        "description": "Borda recheada com cream cheese.",
    },
    {
        "category_slug": "bebidas",
        "name": "Coca-Cola",
        "description": "Refrigerante Coca-Cola.",
    },
    {
        "category_slug": "bebidas",
        "name": "Coca-Cola Zero",
        "description": "Refrigerante Coca-Cola Zero.",
    },
    {
        "category_slug": "bebidas",
        "name": "Guaraná",
        "description": "Refrigerante de guaraná.",
    },
    {
        "category_slug": "bebidas",
        "name": "Água sem gás",
        "description": "Água mineral sem gás.",
    },
    {
        "category_slug": "bebidas",
        "name": "Água com gás",
        "description": "Água mineral com gás.",
    },
]

VARIANTS = {
    "Margherita": [
        ("P", Decimal("32.90")),
        ("M", Decimal("42.90")),
        ("G", Decimal("52.90")),
    ],
    "Calabresa": [
        ("P", Decimal("34.90")),
        ("M", Decimal("44.90")),
        ("G", Decimal("54.90")),
    ],
    "Portuguesa": [
        ("P", Decimal("37.90")),
        ("M", Decimal("48.90")),
        ("G", Decimal("59.90")),
    ],
    "Frango com Catupiry": [
        ("P", Decimal("38.90")),
        ("M", Decimal("49.90")),
        ("G", Decimal("61.90")),
    ],
    "Quatro Queijos": [
        ("P", Decimal("39.90")),
        ("M", Decimal("51.90")),
        ("G", Decimal("63.90")),
    ],
    "Pepperoni": [
        ("P", Decimal("39.90")),
        ("M", Decimal("50.90")),
        ("G", Decimal("62.90")),
    ],
    "Calabresa Diablo": [
        ("P", Decimal("41.90")),
        ("M", Decimal("53.90")),
        ("G", Decimal("65.90")),
    ],
    "Pepperoni Jalapeño": [
        ("P", Decimal("42.90")),
        ("M", Decimal("54.90")),
        ("G", Decimal("66.90")),
    ],
    "Frango Mexicano": [
        ("P", Decimal("42.90")),
        ("M", Decimal("55.90")),
        ("G", Decimal("68.90")),
    ],
    "Nacho Supreme": [
        ("P", Decimal("44.90")),
        ("M", Decimal("57.90")),
        ("G", Decimal("70.90")),
    ],
    "Catupiry": [
        ("P", Decimal("5.90")),
        ("M", Decimal("7.90")),
        ("G", Decimal("9.90")),
    ],
    "Cheddar": [
        ("P", Decimal("5.90")),
        ("M", Decimal("7.90")),
        ("G", Decimal("9.90")),
    ],
    "Cream Cheese": [
        ("P", Decimal("6.90")),
        ("M", Decimal("8.90")),
        ("G", Decimal("10.90")),
    ],
    "Coca-Cola": [
        ("2L", Decimal("13.90")),
    ],
    "Coca-Cola Zero": [
        ("2L", Decimal("13.90")),
    ],
    "Guaraná": [
        ("2L", Decimal("12.90")),
    ],
    "Água sem gás": [
        ("350 ml", Decimal("4.50")),
    ],
    "Água com gás": [
        ("350 ml", Decimal("5.00")),
    ],
}


def seed_categories(session: Session) -> dict[str, Category]:
    categories_by_slug: dict[str, Category] = {}

    for data in CATEGORIES:
        category = session.scalar(
            select(Category).where(Category.slug == data["slug"])
        )

        if category is None:
            category = Category(
                name=data["name"],
                slug=data["slug"],
                active=True,
            )
            session.add(category)
            session.flush()

            print(f"Categoria criada: {data['name']}")
        else:
            print(f"Categoria já existe: {data['name']}")

        categories_by_slug[data["slug"]] = category

    return categories_by_slug


def seed_products(
    session: Session,
    categories_by_slug: dict[str, Category],
) -> None:
    for data in PRODUCTS:
        category = categories_by_slug[data["category_slug"]]

        product = session.scalar(
            select(Product).where(
                Product.category_id == category.id,
                Product.name == data["name"],
            )
        )

        if product is None:
            session.add(
                Product(
                    category_id=category.id,
                    name=data["name"],
                    description=data["description"],
                    active=True,
                )
            )
            print(f"Produto criado: {data['name']}")
        else:
            print(f"Produto já existe: {data['name']}")

def seed_variants(session: Session) -> None:
    for product_name, variants in VARIANTS.items():
        product = session.scalar(
            select(Product).where(Product.name == product_name)
        )

        if product is None:
            raise ValueError(
                f"Produto não encontrado para criar variantes: {product_name}"
            )

        for variant_name, price in variants:
            variant = session.scalar(
                select(ProductVariant).where(
                    ProductVariant.product_id == product.id,
                    ProductVariant.name == variant_name,
                )
            )

            if variant is None:
                session.add(
                    ProductVariant(
                        product_id=product.id,
                        name=variant_name,
                        price=price,
                        active=True,
                    )
                )
                print(
                    f"Variante criada: "
                    f"{product_name} / {variant_name} / R$ {price}"
                )
            else:
                print(
                    f"Variante já existe: "
                    f"{product_name} / {variant_name}"
                )


def seed_catalog() -> None:
    with Session(engine) as session: categories_by_slug = seed_categories(session)
    seed_products(session, categories_by_slug)
    seed_variants(session)

    session.commit()


if __name__ == "__main__":
    seed_catalog()