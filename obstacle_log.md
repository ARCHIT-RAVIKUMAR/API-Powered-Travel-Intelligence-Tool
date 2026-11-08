# Obstacle Log

1. **Every country came back as "The API gave an unexpected response."**
   Even a made-up country returned the same message, which meant the API was
   answering but not with country data. After searching it up, I found out that
   REST Countries retired its old v3.1 address (restcountries.com/v3.1). The old
   URLs now return an error message with a normal 200 status, so my status-code
   check passed and the data was missing. Fixed it by moving to the current v5
   API at api.restcountries.com.

2. **v5 needs an API key.**
   The new version requires a Bearer token. I signed up for a free key and
   read it from the RESTCOUNTRIES_API_KEY environment variable, so the key is
   not in the code or the GitHub repo. Added clear messages for a missing key
   (error before any request) and a rejected key (401).

3. **The response format changed.**
   Old version gave a plain list with fields like name.common. v5 wraps
   everything in data.objects and uses names.common, capitals (a list of
   objects), and so on. Rewrote the parsing, and added a check for an "errors"
   message in the response, since the API can send one with a 200 status.

4. **Neighbours are only given as country codes.**
   Used the API's /borders/{code} lookup to turn them into names, and fall back
   to the codes if that extra call fails.

5. **Islands and small territories have missing fields.**
   Used .get() with defaults everywhere so Japan (no land borders) prints
   "None (no land borders)" instead of crashing.
