"""
Quick test script to verify DuckDuckGo search is working.
Run this from the venv to test if the search API works.
"""

from duckduckgo_search import DDGS

def test_search():
    print("Testing DuckDuckGo search...")
    
    try:
        ddgs = DDGS()
        query = "Python programming language"
        
        print(f"Searching for: {query}")
        
        results = []
        for i, result in enumerate(ddgs.text(query, max_results=3)):
            results.append(result)
            print(f"\nResult {i+1}:")
            print(f"  Title: {result.get('title', 'No title')}")
            print(f"  Body: {result.get('body', 'No body')[:100]}...")
            print(f"  Link: {result.get('href', 'No link')}")
        
        if results:
            print(f"\n✅ Success! Found {len(results)} results")
        else:
            print("\n❌ No results found")
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search()
