"""
Test Summarization (HuggingFace Task #6)

What this does:
- Takes long disruption reports
- Condenses them into one-line alerts
- Shows before/after comparison

Why this matters:
- Risk explanations need to be concise
- Users don't want to read full articles
- Summarized events are easier to compare
"""

import sys
sys.path.append(".")

from models.news_analyzer import NewsAnalyzer

def main():
    print("=" * 70)
    print("SUMMARIZATION TEST - Task #6")
    print("=" * 70)
    
    # Initialize analyzer
    print("\n🔧 Initializing NewsAnalyzer with summarization...")
    analyzer = NewsAnalyzer()
    
    # Test cases: Long disruption reports
    test_cases = [
        {
            "title": "Suez Canal Blockage 2021",
            "text": """The Ever Given, a 400-meter-long container ship operated by 
            Evergreen Marine, ran aground in the Suez Canal on March 23, 2021. The 
            incident blocked the canal for six days, one of the world's busiest 
            shipping routes connecting Asia and Europe. More than 400 vessels were 
            delayed, causing an estimated 9 to 10 billion dollars per day in held-up 
            trade. The blockage highlighted vulnerabilities in global supply chains 
            and prompted discussions about alternative shipping routes and contingency 
            planning for major maritime disruptions."""
        },
        {
            "title": "COVID-19 Port Closures",
            "text": """During the COVID-19 pandemic, major Asian and European ports 
            experienced significant capacity reductions and operational disruptions. 
            Shanghai port, the world's busiest container port, operated at reduced 
            capacity due to strict lockdown measures. Los Angeles and Long Beach ports 
            faced unprecedented congestion with container ships waiting up to three 
            weeks for berth availability. The disruptions led to global supply chain 
            bottlenecks, with average shipping delays reaching 12-15 days above normal. 
            Container freight rates surged to record highs, and many companies struggled 
            with inventory shortages throughout 2020 and 2021."""
        },
        {
            "title": "Ukraine Conflict Impact",
            "text": """The conflict in Ukraine that began in February 2022 significantly 
            disrupted Black Sea shipping routes. Major Ukrainian ports including Odessa 
            and Mariupol were blocked or severely restricted, affecting grain exports 
            that normally feed millions globally. Insurance costs for vessels in the 
            region increased by over 500 percent, and many shipping companies rerouted 
            their vessels entirely. The disruption contributed to global food price 
            inflation and highlighted the critical role of regional conflicts in 
            international supply chain stability."""
        }
    ]
    
    print("\n" + "=" * 70)
    print("📝 SUMMARIZATION RESULTS")
    print("=" * 70)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['title']}")
        print("-" * 70)
        
        original_length = len(case['text'].split())
        print(f"Original: {original_length} words")
        print(f"Text: {case['text'][:100]}...")
        
        # Summarize
        summary = analyzer.summarize(case['text'], max_length=40)
        summary_length = len(summary.split())
        
        print(f"\n✨ Summary: {summary_length} words")
        print(f"➜  {summary}")
        
        reduction = ((original_length - summary_length) / original_length) * 100
        print(f"📊 Compression: {reduction:.1f}% reduction")
    
    print("\n" + "=" * 70)
    print("✅ Summarization test complete!")
    print("💡 These summaries will appear in risk explanations\n")

if __name__ == "__main__":
    main()