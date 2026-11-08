# Travel Intelligence Tool

A Python script that takes a country name and prints a quick travel summary:
capital, currency, population, languages, region and neighbouring countries.
It uses the REST Countries API (v5).

## Setup

1. Install requests:
   ```
   pip install requests
   ```
2. Get a free API key at https://restcountries.com/sign-up
3. Set the key as an environment variable (Windows Command Prompt):
   ```
   set RESTCOUNTRIES_API_KEY=your_key_here
   ```

The API url and timeout are stored in `config.json`, and the key is read from
the environment so it never ends up in the code.

## Usage

```
python travel_tool.py India
python travel_tool.py India Japan Brazil
python test_countries.py
```

## Files

- `travel_tool.py` - the main script
- `config.json` - API url and timeout
- `test_countries.py` - runs the tool on several countries, including invalid input
- `sample_india.txt`, `sample_japan.txt`, `sample_brazil.txt` - sample outputs
- `obstacle_log.md` - problems I ran into and how I solved them
