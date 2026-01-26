"""
Debug script to see what Wikipedia returns for World Cup 2022.
"""

import wikipedia

wikipedia.set_lang("es")

query = "Copa Mundial de Fútbol de 2022"
print(f"Searching Wikipedia for: {query}\n")

# Search
results = wikipedia.search(query, results=3)
print(f"Search results: {results}\n")

# Get first result
if results:
    title = results[0]
    print(f"Getting article: {title}\n")
    
    # Different sentence counts
    for sentences in [2, 3, 5]:
        try:
            summary = wikipedia.summary(title, sentences=sentences, auto_suggest=False)
            print(f"--- Summary ({sentences} sentences) ---")
            print(summary)
            print("\n")
        except Exception as e:
            print(f"Error with {sentences} sentences: {e}\n")
    
    # Get full page
    try:
        page = wikipedia.page(title, auto_suggest=False)
        print(f"Full URL: {page.url}")
        print(f"\nFirst 500 chars of content:\n{page.content[:500]}")
    except Exception as e:
        print(f"Error getting page: {e}")
