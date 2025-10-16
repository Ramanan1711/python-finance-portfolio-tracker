import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Health check passed")

def test_user_creation():
    # Test creating a new user
    response = requests.post(
        f"{BASE_URL}/users/",
        json={"email": "newuser@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    print("✅ User creation test passed")

    # Test duplicate email
    response = requests.post(
        f"{BASE_URL}/users/",
        json={"email": "newuser@example.com", "password": "testpassword"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Email already registered"
    print("✅ Duplicate email test passed")

def test_authentication():
    # Test login
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": "newuser@example.com", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]
    print("✅ Login test passed")

    # Test protected endpoint
    response = requests.get(
        f"{BASE_URL}/users/me/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    print("✅ Protected endpoint test passed")

    # Test invalid token
    response = requests.get(
        f"{BASE_URL}/users/me/",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    print("✅ Invalid token test passed")

def main():
    try:
        test_health_check()
        test_user_creation()
        test_authentication()
        print("\n🎉 All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
