"""
final_test_set.py - Final untouched test prompts
-------------------------------------------------
Written after all tuning was finished. Nothing in the corpus, network, or routing
weights was changed after seeing results on this set. Report these numbers.
Each entry: (prompt, task, tier)
"""

FINAL_TEST_SET = [
    ("yo, what's new with you?", "conversation", "simple"),
    ("thank you!! you saved my day", "conversation", "simple"),
    ("are you awake?", "conversation", "simple"),
    ("can I ask you something personal?", "conversation", "simple"),
    ("I moved countries for work and I barely know anyone here. Evenings feel really empty. How can I start building a social life?", "conversation", "moderate"),
    ("My sister and I haven't spoken in two years after an argument about our father's care. I want to reach out but I'm scared. What should I say?", "conversation", "moderate"),

    ("Which planet is closest to the sun?", "factual", "simple"),
    ("who composed the moonlight sonata", "factual", "simple"),
    ("What's the population of Canada?", "factual", "simple"),
    ("When did the Titanic set sail?", "factual", "simple"),
    ("What is the largest bone in the human body?", "factual", "simple"),
    ("Name the five Great Lakes.", "factual", "moderate"),

    ("Why do we see lightning before we hear thunder?", "explanation", "simple"),
    ("How do credit cards make money?", "explanation", "moderate"),
    ("Explain how a bloom filter works and when it gives false positives.", "explanation", "moderate"),
    ("How does HTTPS prevent man-in-the-middle attacks?", "explanation", "moderate"),
    ("Explain how quantum tunnelling allows nuclear fusion in the sun despite the Coulomb barrier.", "explanation", "complex"),
    ("Explain how Spanner uses TrueTime to provide external consistency across datacenters.", "explanation", "complex"),

    ("Summarize this for me: The library will close for renovations from June to August. During that time, books can be borrowed from the temporary branch on Main Street. Late fees are waived for the summer.", "summarization", "simple"),
    ("Give me the gist:\nThe research team trained a small language model on children's stories and found it could produce coherent multi-paragraph text despite having only 30 million parameters. They argue that data quality matters more than scale for basic fluency. Critics note that the model still fails at reasoning tasks and that the findings may not transfer to broader domains.", "summarization", "simple"),
    ("Please summarize these customer complaints into themes:\n1. App logs me out every day.\n2. Checkout takes forever on Android.\n3. I was charged twice for one order.\n4. Delivery tracking never updates.\n5. Logged out again after the update.\n6. The checkout button freezes.\n7. Refund for the double charge took three weeks.\n8. Tracking shows 'pending' even after delivery.", "summarization", "moderate"),

    ("translate 'good night, sleep well' to italian", "translation", "simple"),
    ("What's 'happy new year' in Mandarin?", "translation", "simple"),
    ("Translate to English: Wo ist der Bahnhof?", "translation", "simple"),
    ("Can you translate this message to French for my landlord: The heating has stopped working since Monday. Could you send someone to repair it this week? I am home every afternoon.", "translation", "moderate"),

    ("Write a limerick about a cat who loves lasagna.", "creative", "simple"),
    ("Give me a slogan for an eco-friendly water bottle.", "creative", "simple"),
    ("Write a poem about the sound of rain on a tin roof.", "creative", "moderate"),
    ("Write a short bedtime story about a turtle who wants to fly.", "creative", "moderate"),
    ("Write a graduation speech for my little brother.", "creative", "moderate"),
    ("Create an original fantasy pantheon of seven gods, with their domains, rivalries, myths, and how mortals worship each of them.", "creative", "complex"),

    ("how do I make a string lowercase in javascript", "coding", "simple"),
    ("What's the command to create a new branch in git?", "coding", "simple"),
    ("Write a Python script that downloads all images from a list of URLs and saves them with unique names.", "coding", "moderate"),
    ("My Flask app returns 500 Internal Server Error when I submit the form. How do I debug it?", "coding", "moderate"),
    ("Write a SQL query that returns the second highest salary in each department.", "coding", "moderate"),
    ("Implement a skip list in C++ supporting insert, delete and search with expected O(log n) time.", "coding", "complex"),
    ("Write a thread-safe connection pool in Java with health checks, idle eviction and a maximum wait time.", "coding", "complex"),
    ("Design and implement a geo-replicated database in Rust with CRDT-based conflict resolution, anti-entropy and causal consistency.", "coding", "expert"),

    ("what's 15% of 340", "math", "simple"),
    ("Simplify 18/24", "math", "simple"),
    ("Find the area of a triangle with base 12 and height 7.", "math", "simple"),
    ("A shop sells pens at 3 for $2. How much do 45 pens cost?", "math", "moderate"),
    ("Find the integral of 1/(x^2 - 1) dx", "math", "complex"),
    ("Prove that for every integer n, n^2 + n is even.", "math", "expert"),

    ("If a red house is made of red bricks and a blue house of blue bricks, what is a greenhouse made of?", "reasoning", "simple"),
    ("Tom is taller than Jim. Jim is taller than Ann. Is Ann taller than Tom?", "reasoning", "simple"),
    ("A snail climbs 3 feet up a 10-foot well each day and slips back 2 feet each night. How many days to get out?", "reasoning", "moderate"),
    ("Five pirates must split 100 coins; the most senior proposes a split and needs at least half the votes or is thrown overboard. What does he propose? Explain the backward induction.", "reasoning", "complex"),
    ("Explain the Monty Fall variant of the Monty Hall problem and why the answer differs from the original.", "reasoning", "complex"),

    ("Kindle vs paper books: which is better for students?", "analysis", "moderate"),
    ("What are the advantages and drawbacks of nuclear power?", "analysis", "moderate"),
    ("Our support response time went from 2h to 9h after we cut two agents, while ticket volume stayed flat. Analyze the impact and recommend options.", "analysis", "complex"),
    ("Evaluate whether our 20-person startup should build its own authentication system or buy one, considering security, cost and time to market.", "analysis", "complex"),
    ("Assess the systemic risks that stablecoins pose to the traditional banking system, including run dynamics, collateral quality and regulatory arbitrage.", "analysis", "expert"),
]
