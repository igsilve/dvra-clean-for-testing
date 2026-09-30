import secrets
import string

from apis.auth.utils import create_user_if_not_exists, system_authz
from apis.menu.schemas import MenuItemCreate
from apis.menu.utils import create_menu_item
from config import ENV, settings
from db.models import MenuItem, Order, OrderItem, OrderStatus, User, UserRole
from db.session import get_db
from password_policy import PasswordPolicyError, validate_password_policy
from sqlalchemy.orm import Session


def generate_random_secret():
    """Generate a 32-character password that satisfies the shared policy.

    Drawing 32 characters from a large alphabet almost always covers every
    required character class, but "almost always" is not a guarantee, so the
    result is checked and redrawn rather than assumed.
    """
    characters = string.ascii_letters + string.digits + string.punctuation

    while True:
        password = "".join(secrets.choice(characters) for _ in range(32))
        try:
            return validate_password_policy(password)
        except PasswordPolicyError:
            continue


def load_users(db: Session):
    """Create the one account operation requires: the initial Chef.

    Its password is generated and never printed or logged, so it is unknown
    even to whoever runs the seeding. Operations obtain a working credential
    through the password-reset flow rather than from a value in source or in
    the startup output.
    """
    create_user_if_not_exists(
        db,
        username=settings.CHEF_USERNAME,
        password=generate_random_secret(),
        first_name="Gustavo",
        last_name="",
        phone_number="(505) 146-0195",
        role=UserRole.CHEF,
        # The password was issued by the system, not chosen by the operator,
        # so the account is unusable until it is replaced.
        must_change_password=True,
    )


# Sample staff and customer accounts. These exist to make the application
# explorable in development and are not required for it to operate, so they
# are never created in production. Each password is generated per run, so no
# credential here is guessable from the source.
DEMO_USERS = (
    ("Mike", "Mike", "", "(505) 146-0190", UserRole.EMPLOYEE),
    ("Saul", "Saul", "", "(505) 842-5662", UserRole.EMPLOYEE),
    ("hhm", "Howard", "Hamlin", "(505) 56434-7345", UserRole.CUSTOMER),
    ("johndoe", "John", "Doe", "(505) 56434-7346", UserRole.CUSTOMER),
    ("alicesmith", "Alice", "Smith", "(505) 53436-7347", UserRole.CUSTOMER),
)


def load_demo_users(db: Session):
    for username, first_name, last_name, phone_number, role in DEMO_USERS:
        create_user_if_not_exists(
            db,
            username=username,
            password=generate_random_secret(),
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=role,
            must_change_password=True,
        )



def _seed_menu_item(db, menu_item: MenuItemCreate):
    """Create a menu item during seeding.

    The service function requires an authorization context. Seeding runs
    before any user exists, so it passes the system context — in one place
    here rather than at each of the call sites below, so there is a single
    line to audit.
    """
    return create_menu_item(db, menu_item, system_authz())


def load_menu(db: Session):
    # Breakfasts
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Pollos Classic Breakfast",
            price=2.99,
            category="Pollos Breakfasts",
        ),
    )
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Pollos Chicken Biscuit",
            price=3.99,
            category="Pollos Breakfasts",
            description="Fried chicken filet on a buttered biscuit",
        ),
    )
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Pollos Breakfast Sandwich",
            price=4.59,
            category="Pollos Breakfasts",
            description="Two eggs, boneless grilled chicken, green chile and salsa served on our classic bun",
        ),
    )
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Pollos Breakfast Tacos",
            price=4.99,
            category="Pollos Breakfasts",
        ),
    )

    # Burritos
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Basic Hand Held",
            price=2.49,
            category="Pollos Burritos",
            description="Egg & potato",
        ),
    )
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Basic Smothered Chile & Cheese on Top",
            price=3.39,
            category="Pollos Burritos",
            description="Egg & potato",
        ),
    )
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="New Mexico",
            price=3.99,
            category="Pollos Burritos",
            description="Egg, potato, green chile & cheese",
        ),
    )
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Albuquerque",
            price=4.59,
            category="Pollos Burritos",
            description="Sausage, egg, potato, red chile & cheese",
        ),
    )

    # Chicken Specialties
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Pollo Adovada",
            price=5.49,
            category="Chicken Specialties",
            description="Potato, red chile & cheese",
        ),
    )

    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Pollo Picante",
            price=5.49,
            category="Chicken Specialties",
            description="Bean, potato, green chile & cheese",
        ),
    )

    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Pollo Mexicana",
            price=5.49,
            category="Chicken Specialties",
            description="Potato, green chile & cheese",
        ),
    )

    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Giuso De Pollo",
            price=3.99,
            category="Chicken Specialties",
            description="Bean, potato, red chile & cheese",
        ),
    )

    # Desserts
    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Ice Cream",
            price=2.45,
            category="Desserts",
            description="Cone",
        ),
    )

    _seed_menu_item(
        db,
        MenuItemCreate(
            name="Chocoloate Shake",
            price=1.65,
            category="Desserts",
        ),
    )


def load_orders(db: Session):
    # Get users
    alice = db.query(User).filter(User.username == "alicesmith").first()
    john = db.query(User).filter(User.username == "johndoe").first()

    if not alice or not john:
        return

    # Use only menu items with IDs 6 to 10
    menu_items = (
        db.query(MenuItem)
        .filter(MenuItem.id.in_([6, 7, 8, 9, 10]))
        .order_by(MenuItem.id.asc())
        .all()
    )
    if len(menu_items) != 5:
        return

    # Create first order for alicesmith
    order1 = Order(
        user_id=alice.id,
        delivery_address="308 Negra Arroyo Lane, Albuquerque, NM 87104",
        phone_number=alice.phone_number,
        final_price=0.0,
        status=OrderStatus.DELIVERED,
    )
    db.add(order1)
    db.commit()
    db.refresh(order1)

    # Add items to first order for alice (2 items)
    total_price1 = 0.0
    order_item1 = OrderItem(
        order_id=order1.id,
        menu_item_id=menu_items[0].id,
        quantity=2,
    )
    db.add(order_item1)
    total_price1 += menu_items[0].price * 2

    order_item2 = OrderItem(
        order_id=order1.id,
        menu_item_id=menu_items[1].id,
        quantity=1,
    )
    db.add(order_item2)
    total_price1 += menu_items[1].price * 1

    order1.final_price = total_price1
    db.commit()

    # Create second order for alicesmith
    order2 = Order(
        user_id=alice.id,
        delivery_address="308 Negra Arroyo Lane, Albuquerque, NM 87104",
        phone_number=alice.phone_number,
        final_price=0.0,
        status=OrderStatus.DELIVERED,
    )
    db.add(order2)
    db.commit()
    db.refresh(order2)

    # Add items to second order for alice (3 items)
    total_price2 = 0.0
    order_item3 = OrderItem(
        order_id=order2.id,
        menu_item_id=menu_items[2].id,
        quantity=1,
    )
    db.add(order_item3)
    total_price2 += menu_items[2].price * 1

    order_item4 = OrderItem(
        order_id=order2.id,
        menu_item_id=menu_items[3].id,
        quantity=2,
    )
    db.add(order_item4)
    total_price2 += menu_items[3].price * 2

    order_item5 = OrderItem(
        order_id=order2.id,
        menu_item_id=menu_items[4].id,
        quantity=1,
    )
    db.add(order_item5)
    total_price2 += menu_items[4].price * 1

    order2.final_price = total_price2
    db.commit()

    # Create order for johndoe
    order3 = Order(
        user_id=john.id,
        delivery_address="1650 Central Ave SE, Albuquerque, NM 87106",
        phone_number=john.phone_number,
        final_price=0.0,
        status=OrderStatus.DELIVERED,
    )
    db.add(order3)
    db.commit()
    db.refresh(order3)

    # Add items to order for john (2 items)
    total_price3 = 0.0
    order_item6 = OrderItem(
        order_id=order3.id,
        menu_item_id=menu_items[0].id,
        quantity=3,
    )
    db.add(order_item6)
    total_price3 += menu_items[0].price * 3

    order_item7 = OrderItem(
        order_id=order3.id,
        menu_item_id=menu_items[2].id,
        quantity=1,
    )
    db.add(order_item7)
    total_price3 += menu_items[2].price * 1

    order3.final_price = total_price3
    db.commit()


def load_initial_data():
    db = next(get_db())

    chef_user = db.query(User).filter(User.username == settings.CHEF_USERNAME).first()
    if chef_user:
        # chef user is propagated to the database
        # it means that initial data is already loaded
        return

    load_users(db)
    load_menu(db)

    # Sample accounts and their order history are development conveniences.
    # In production the only seeded account is the Chef created above.
    if settings.ENVIRONMENT is not ENV.PRODUCTION:
        load_demo_users(db)
        load_orders(db)
