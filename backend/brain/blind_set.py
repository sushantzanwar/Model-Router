"""
blind_set.py - Blind test prompts
----------------------------------
Written after the corpus was finalised and never used for tuning anything
(neither the training corpus nor the routing weights). This is the honest
estimate of how the brain performs on prompts it has never seen.
Each entry: (prompt, task, tier)
"""

BLIND_SET = [
    ("hey! how's it going", "conversation", "simple"),
    ("thanks, that fixed it", "conversation", "simple"),
    ("good evening, anyone home?", "conversation", "simple"),
    ("lmao you're hilarious", "conversation", "simple"),
    ("My manager keeps scheduling meetings during my lunch break and I'm starting to resent it. How do I raise this without sounding petty?", "conversation", "moderate"),
    ("I just got rejected from my dream university and I feel like a failure. Can you help me get through this?", "conversation", "moderate"),

    ("What's the capital of Kenya?", "factual", "simple"),
    ("who painted starry night", "factual", "simple"),
    ("How many players are on a basketball team?", "factual", "simple"),
    ("When did the Apollo 13 mission launch?", "factual", "simple"),
    ("What is the chemical formula for table salt?", "factual", "simple"),
    ("List all the countries that border Germany.", "factual", "moderate"),

    ("How does a refrigerator's compressor cool the air?", "explanation", "moderate"),
    ("why do we have leap years", "explanation", "simple"),
    ("Explain how vaccines create herd immunity.", "explanation", "moderate"),
    ("What's the difference between a crocodile and an alligator?", "explanation", "simple"),
    ("Explain how transformer self-attention scales with sequence length and why that matters for long-context models.", "explanation", "complex"),
    ("Explain how two-phase commit can block and how three-phase commit attempts to fix it.", "explanation", "complex"),

    ("Summarize: Sales of electric bikes doubled last year as cities expanded bike lanes and fuel prices rose. Manufacturers struggled to keep up with demand, and delivery times stretched to three months.", "summarization", "simple"),
    ("Can you summarize this chat log for me?\nAnna: Are we still on for Saturday?\nBen: Yes, but can we move it to 4pm?\nAnna: Sure. Should I bring anything?\nBen: Maybe snacks. Chris is bringing drinks.\nAnna: Great, see you then.", "summarization", "simple"),
    ("Key points please:\nThe new privacy regulation takes effect in January. Companies must obtain explicit consent before collecting personal data, provide a way for users to download their data, and report breaches within 72 hours. Fines can reach 4% of global revenue. Small businesses with fewer than 50 employees get a one-year grace period. Regulators say they will focus first on large platforms that process sensitive data such as health or location information. Industry groups have asked for clearer guidance on what counts as explicit consent, especially for mobile apps.", "summarization", "moderate"),

    ("How do you say 'I love you' in Korean?", "translation", "simple"),
    ("Translate to Spanish: The meeting starts at nine.", "translation", "simple"),
    ("Que veut dire 'je suis désolé' en anglais ?", "translation", "simple"),
    ("Translate this paragraph into German: Thank you for your order. Your items will ship within two business days. If you have any questions, reply to this email and our support team will help you.", "translation", "moderate"),

    ("Write a haiku about coffee.", "creative", "simple"),
    ("Tell me a joke about programmers.", "creative", "simple"),
    ("Write a short poem for my mom's birthday.", "creative", "moderate"),
    ("Write a short story about a robot who wants to become a chef.", "creative", "moderate"),
    ("Write a 4000-word thriller chapter with three POV characters, interleaved timelines and a reveal that recontextualizes the first scene.", "creative", "complex"),

    ("how do I reverse a list in python", "coding", "simple"),
    ("What's the git command to see the commit history?", "coding", "simple"),
    ("Write a function in TypeScript that groups an array of objects by a key.", "coding", "moderate"),
    ("I'm getting 'ReferenceError: process is not defined' in my Vite app. How do I fix it?", "coding", "moderate"),
    ("Implement an LFU cache in Java with O(1) operations.", "coding", "complex"),
    ("Build a fault-tolerant distributed lock service in Go using a consensus protocol, with lease expiry and fencing tokens.", "coding", "expert"),

    ("what is 45 times 12", "math", "simple"),
    ("Solve 3x + 9 = 0", "math", "simple"),
    ("Find the derivative of sin(x) * e^x", "math", "moderate"),
    ("If a loan of $20,000 has 6% annual interest compounded monthly, what is the monthly payment over 5 years?", "math", "moderate"),
    ("Find the general solution of y'' + 3y' + 2y = 0", "math", "complex"),
    ("Prove that the sum of the first n cubes equals the square of the sum of the first n integers.", "math", "expert"),

    ("If tomorrow is Wednesday, what day was yesterday?", "reasoning", "simple"),
    ("A doctor gives you three pills and tells you to take one every half hour. How long until they run out?", "reasoning", "moderate"),
    ("Some programmers are gamers. All gamers like pizza. Does it follow that some programmers like pizza?", "reasoning", "moderate"),
    ("You have 8 balls, one slightly heavier. Using a balance scale only twice, how do you find the heavy one? Explain.", "reasoning", "complex"),
    ("Explain the solution to the hundred prisoners and hats puzzle and prove why at most one prisoner can be wrong.", "reasoning", "expert"),

    ("Compare Netflix and Amazon Prime Video.", "analysis", "moderate"),
    ("What are the pros and cons of working from home?", "analysis", "moderate"),
    ("Here are our weekly orders: 210, 230, 225, 310, 305, 190. Analyze what happened and what we should check.", "analysis", "complex"),
    ("Critique the argument that banning cars from city centers always hurts local businesses.", "analysis", "complex"),
    ("Assess the risks of switching our entire company to a four-day work week next quarter.", "analysis", "complex"),
    ("Evaluate the long-term macroeconomic consequences of a universal basic income funded by a carbon tax, including labor supply elasticities and distributional effects.", "analysis", "expert"),
]
