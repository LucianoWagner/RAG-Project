"""
Test Wikipedia search functionality.
"""

import wikipedia

def test_wikipedia():
    print("Testing Wikipedia API...")
    
    # Set to Spanish
    wikipedia.set_lang("es")
    
    # Test search
    query = "Lionel Messi"
    print(f"\nSearching for: {query}")
    
    try:
        # Search
        results = wikipedia.search(query, results=3)
        print(f"Found {len(results)} results: {results}")
        
        # Get summary
        if results:
            title = results[0]
            summary = wikipedia.summary(title, sentences=3)
            page = wikipedia.page(title)
            
            print(f"\nTitle: {title}")
            print(f"Summary: {summary[:200]}...")
            print(f"URL: {page.url}")
            print("\n✅ Wikipedia test successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wikipedia()
