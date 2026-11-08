# Step 4: run the tool against a few different countries,
# including one that doesn't exist.
from travel_tool import get_country_info, print_info

countries = [
    "India",          # common country, has several neighbours
    "Japan",          # island, no land borders
    "Brazil",         # lots of neighbours
    "Bhutan",         # smaller, less common
    "Niger",          # name is inside "Nigeria", checks the matching
    "Atlantis",       # invalid input
    "",               # empty input
]

for name in countries:
    print(f"--- Testing: '{name}' ---")
    try:
        print_info(get_country_info(name))
    except ValueError as e:
        print(f"Error: {e}")
    print()
