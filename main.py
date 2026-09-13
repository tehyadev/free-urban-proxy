from json import dump, load
from pathlib import Path
from time import time

from curl_cffi import requests

BASE = "https://api-pro.urban-vpn.com"
STATS = "https://stats.urban-vpn.com/api/rest/v2"
APP = {"name": "URBAN_VPN_BROWSER_EXTENSION"}
ACCESS_FILE = Path("access_token.json")


def register_anonymous_user():
    return requests.post(
        f"{BASE}/rest/v1/registrations/clientApps/URBAN_VPN_BROWSER_EXTENSION/users/anonymous",
        json={"clientApp": {**APP, "browser": "CHROME"}},
    ).json()


def get_access_token(value):
    body = {"type": "accs", "clientApp": APP}
    return requests.post(
        f"{BASE}/rest/v1/security/tokens/accs",
        json=body,
        headers={"Authorization": f"Bearer {value}"},
    ).json()


def get_proxy_token(access_token, signature):
    body = {"type": "accs-proxy", "clientApp": APP, "signature": signature}
    return requests.post(
        f"{BASE}/rest/v1/security/tokens/accs-proxy",
        json=body,
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()


def get_countries(access_token):
    data = requests.get(
        f"{STATS}/entrypoints/countries",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()
    return data["countries"]["elements"]


def save_to_file(data, filename):
    with open(filename, "w") as f:
        dump(data, f)


def load_from_file(filename):
    try:
        with open(filename) as f:
            return load(f)
    except FileNotFoundError:
        return None


def get_or_create_access_token():
    saved = load_from_file(ACCESS_FILE)
    if saved and time() * 1000 < saved["expiration"]:
        print("Using saved access token")
        return saved["token"]

    accs = get_access_token(register_anonymous_user()["value"])
    save_to_file({"token": accs["value"], "expiration": accs["expirationTime"]}, ACCESS_FILE)
    return accs["value"]


def countries_list(access_token):
    return [c["code"]["iso2"] for c in get_countries(access_token)]


def connect_to_country(access_token, iso2, index=0):
    for country in get_countries(access_token):
        if country["code"]["iso2"] == iso2.upper():
            proxy_server = country["servers"]["elements"][index]
            signature = proxy_server["signature"]
            proxy_data = get_proxy_token(access_token, signature)
            return {"ip": proxy_server["primary"]["ip"], "port": proxy_server["primary"]["port"], "username": proxy_data["value"], "password": "1"}
    return None


if __name__ == "__main__":
    token = get_or_create_access_token()

    print("Countries:", ", ".join(countries_list(token)))

    proxy = connect_to_country(token, "NL")
    print("\nNL proxy token:", proxy)
