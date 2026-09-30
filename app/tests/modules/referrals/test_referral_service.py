from apis.auth.utils import get_password_hash
from db.models import DiscountCoupon, User, UserRole


def test_create_referral_code_should_return_201(test_db, customer_client):
    """Test that issuing a referral code returns 201 and a code."""
    response = customer_client.post("/referral-code")

    assert response.status_code == 201
    data = response.json()
    assert data.get("code") is not None
    assert len(data.get("code")) == 8


def test_get_referral_code_should_return_issued_code(test_db, customer_client):
    """Test that the read route returns the code issued by the write route."""
    created = customer_client.post("/referral-code")
    code = created.json().get("code")

    response = customer_client.get("/referral-code")

    assert response.status_code == 200
    assert response.json().get("code") == code


def test_create_referral_code_should_return_same_code_on_second_call(
    test_db, customer_client
):
    """Test that issuing a referral code twice returns the same code."""
    response1 = customer_client.post("/referral-code")
    code1 = response1.json().get("code")

    response2 = customer_client.post("/referral-code")
    code2 = response2.json().get("code")

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert code1 == code2


def test_get_referral_code_does_not_issue_one(test_db, customer_client):
    """A GET must not create state: with no code issued it returns 404."""
    response = customer_client.get("/referral-code")

    assert response.status_code == 404

    # Still absent, so the read really was side-effect free.
    assert customer_client.get("/referral-code").status_code == 404


def test_get_referral_code_unauthorised_should_return_401(test_db, anon_client):
    """Test that unauthenticated request returns 401."""
    response = anon_client.get("/referral-code")

    assert response.status_code == 401


def test_create_referral_code_unauthorised_should_return_401(test_db, anon_client):
    """Test that unauthenticated request to issue a code returns 401."""
    response = anon_client.post("/referral-code")

    assert response.status_code == 401


def test_apply_referral_code_should_return_200_for_valid_code(test_db, customer_client):
    """Test that applying a valid referral code returns 200."""
    # Create a second user with a referral code
    referrer = User(
        id=100,
        username="referrer",
        password=get_password_hash("password"),
        first_name="Referrer",
        last_name="",
        phone_number="9999",
        role=UserRole.CUSTOMER,
        referral_code="ABC12345",
    )
    test_db.add(referrer)
    test_db.commit()

    # Apply the referral code
    data = {"referral_code": "ABC12345"}
    response = customer_client.post("/apply-referral", json=data)

    assert response.status_code == 200
    result = response.json()
    assert result.get("discount") == 20
    assert "applied successfully" in result.get("message")


def test_apply_referral_code_should_return_200_with_zero_discount_for_invalid_code(
    test_db, customer_client
):
    """Test that applying an invalid referral code returns 200 with zero discount."""
    data = {"referral_code": "INVALID00"}
    response = customer_client.post("/apply-referral", json=data)

    assert response.status_code == 200
    result = response.json()
    assert result.get("discount") == 0.0
    assert "Invalid referral code" in result.get("message")


def test_apply_referral_code_should_create_discount_coupon_for_valid_coupon(
    test_db, customer_client
):
    """Test that applying a referral code creates a discount coupon record."""
    # Create a referrer user
    referrer = User(
        id=101,
        username="referrer2",
        password=get_password_hash("password"),
        first_name="Referrer",
        last_name="",
        phone_number="8888",
        role=UserRole.CUSTOMER,
        referral_code="XYZ98765",
    )
    test_db.add(referrer)
    test_db.commit()

    # Apply the referral code
    data = {"referral_code": "XYZ98765"}
    response = customer_client.post("/apply-referral", json=data)

    assert response.status_code == 200

    # Check that a discount coupon was created
    coupon = (
        test_db.query(DiscountCoupon)
        .filter(DiscountCoupon.referrer_user_id == referrer.id)
        .first()
    )
    assert coupon is not None
    assert coupon.discount_percentage == 20
    assert coupon.used is False


def test_get_discount_coupons_should_return_200_with_coupons(test_db, customer_client):
    """Test that getting discount coupons returns 200."""
    response = customer_client.get("/discount-coupons")

    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_get_discount_coupons_should_return_user_coupons(test_db, customer_client):
    """Test that getting discount coupons returns only user's coupons."""
    # Create a referrer user
    referrer = User(
        id=103,
        username="referrer4",
        password=get_password_hash("password"),
        first_name="Referrer",
        last_name="",
        phone_number="6666",
        role=UserRole.CUSTOMER,
        referral_code="GHI89012",
    )
    test_db.add(referrer)
    test_db.commit()

    # Apply the referral code
    data = {"referral_code": "GHI89012"}
    customer_client.post("/apply-referral", json=data)

    # Get the coupons
    response = customer_client.get("/discount-coupons")

    assert response.status_code == 200
    coupons = response.json()["items"]
    assert len(coupons) == 1
    assert coupons[0].get("discount_percentage") == 20
    assert coupons[0].get("used") is False


def test_get_discount_coupons_unauthorised_should_return_401(test_db, anon_client):
    """Test that unauthenticated request to get coupons returns 401."""
    response = anon_client.get("/discount-coupons")

    assert response.status_code == 401


def test_apply_referral_code_unauthorised_should_return_401(test_db, anon_client):
    """Test that unauthenticated request to apply referral returns 401."""
    data = {"referral_code": "ABC12345"}
    response = anon_client.post("/apply-referral", json=data)

    assert response.status_code == 401
