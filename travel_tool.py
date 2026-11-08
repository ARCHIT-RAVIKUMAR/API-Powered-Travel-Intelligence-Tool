import json
import os
import sys
from urllib.parse import quote

import requests


def load_config():
    """Read the API url and timeout from config.json. The API key is a secret,
    so it comes from the RESTCOUNTRIES_API_KEY environment variable and is
    never written in the code or the repo."""
    try:
        with open("config.json") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    except json.JSONDecodeError:
        print("config.json is not valid JSON, please fix it.")
        sys.exit(1)

    api_url = os.environ.get("COUNTRY_API_URL", config.get("api_url"))
    if not api_url:
        print("No API url found. Set api_url in config.json or COUNTRY_API_URL.")
        sys.exit(1)

    api_key = os.environ.get("RESTCOUNTRIES_API_KEY")
    if not api_key:
        print("No API key found. Set the RESTCOUNTRIES_API_KEY environment variable.")
        print("You can get a free key at https://restcountries.com/sign-up")
        sys.exit(1)

    return api_url.rstrip("/"), config.get("timeout", 10), api_key


def call_api(url, params, timeout, api_key):
    """Make one request and return the parsed JSON. Raises ValueError with a
    readable message if anything goes wrong, LookupError on a 404."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
    except requests.exceptions.Timeout:
        raise ValueError("The API took too long to respond. Try again.")
    except requests.exceptions.ConnectionError:
        raise ValueError("Could not connect. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Request failed: {e}")

    if response.status_code == 404:
        raise LookupError("not found")
    if response.status_code == 401:
        raise ValueError("The API key was rejected. Check RESTCOUNTRIES_API_KEY.")
    if response.status_code == 403:
        raise ValueError("Access denied. Your monthly request limit may be used up.")
    if response.status_code == 429:
        raise ValueError("Too many requests. Wait a few seconds and try again.")
    if response.status_code != 200:
        raise ValueError(f"The API returned an error (status {response.status_code}).")

    try:
        return response.json()
    except ValueError:
        raise ValueError("The API sent back something that is not valid JSON.")


def get_objects(result):
    """Pull the list of countries out of the response. The API can send an
    'errors' message even with a 200 status, so check for that first."""
    if not isinstance(result, dict):
        raise ValueError("The API gave an unexpected response.")
    if result.get("errors"):
        first = result["errors"][0]
        message = first.get("message", "unknown error") if isinstance(first, dict) else first
        raise ValueError(f"The API reported a problem: {message}")
    objects = (result.get("data") or {}).get("objects")
    if not isinstance(objects, list):
        raise ValueError("The API gave an unexpected response.")
    return objects


def name_of(item):
    """Get a readable name out of a string or a small dictionary."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("name", "english_name", "english", "common"):
            if isinstance(item.get(key), str):
                return item[key]
    return None


def get_neighbours(data, api_url, timeout, api_key):
    """Countries that share a border. The record only has border codes, so ask
    the API for the countries that border this one to get proper names."""
    codes = data.get("borders") or []
    if not codes:
        return []
    own_code = (data.get("codes") or {}).get("alpha_3")
    try:
        result = call_api(f"{api_url}/borders/{own_code}",
                          {"response_fields": "names.common", "limit": 100}, timeout, api_key)
        names = [c["names"]["common"] for c in get_objects(result)]
        return sorted(names) or codes
    except (ValueError, LookupError, KeyError, TypeError):
        return codes  # fall back to the plain codes


def get_country_info(country_name):
    """Fetch a country and return a dictionary with the fields we care about."""
    country_name = country_name.strip()
    if country_name == "":
        raise ValueError("Please enter a country name.")

    api_url, timeout, api_key = load_config()
    params = {"response_fields_omit": "names.translations"}

    # exact name first, then a partial search as a fallback
    try:
        objects = get_objects(call_api(f"{api_url}/names.common/{quote(country_name)}",
                                       params, timeout, api_key))
    except LookupError:
        objects = []
    if not objects:
        try:
            objects = get_objects(call_api(f"{api_url}/name",
                                           {**params, "q": country_name}, timeout, api_key))
        except LookupError:
            objects = []
    if not objects:
        raise ValueError(f"Couldn't find a country called '{country_name}'. Check the spelling.")

    # a partial search can return several (Niger / Nigeria), so prefer an exact match
    data = objects[0]
    for obj in objects:
        if (obj.get("names") or {}).get("common", "").lower() == country_name.lower():
            data = obj
            break

    # capitals
    capitals = [name_of(c) for c in (data.get("capitals") or [])]
    capitals = [c for c in capitals if c]

    # currencies (works whether the API sends a dictionary or a list)
    currencies = []
    raw_currencies = data.get("currencies") or {}
    if isinstance(raw_currencies, dict):
        for code, value in raw_currencies.items():
            currencies.append(f"{name_of(value) or code} ({code})")
    elif isinstance(raw_currencies, list):
        for item in raw_currencies:
            code = item.get("code", "") if isinstance(item, dict) else ""
            label = name_of(item)
            if label:
                currencies.append(f"{label} ({code})" if code else label)

    # languages (also works for a list or a dictionary)
    raw_languages = data.get("languages") or []
    if isinstance(raw_languages, dict):
        raw_languages = list(raw_languages.values())
    languages = [name_of(l) for l in raw_languages]
    languages = [l for l in languages if l]

    population = data.get("population")
    info = {
        "name": (data.get("names") or {}).get("common", "Unknown"),
        "capital": ", ".join(capitals) if capitals else "N/A",
        "currency": currencies,
        "population": population if isinstance(population, (int, float)) else None,
        "languages": languages,
        "region": data.get("region", "N/A"),
        "neighbours": get_neighbours(data, api_url, timeout, api_key),
    }
    return info


def print_info(info):
    population = f"{int(info['population']):,}" if info["population"] is not None else "N/A"
    print(f"Country    : {info['name']}")
    print(f"Capital    : {info['capital']}")
    print(f"Currency   : {', '.join(info['currency']) or 'N/A'}")
    print(f"Population : {population}")
    print(f"Languages  : {', '.join(info['languages']) or 'N/A'}")
    print(f"Region     : {info['region']}")
    print(f"Neighbours : {', '.join(info['neighbours']) or 'None (no land borders)'}")


def main():
    if len(sys.argv) > 1:
        names = sys.argv[1:]
    else:
        names = [input("Enter a country name: ")]

    for name in names:
        try:
            info = get_country_info(name)
            print_info(info)
        except ValueError as e:
            print(f"Error for '{name}': {e}")
        print()


if __name__ == "__main__":
    main()
