"""
corpus.py - Labelled training examples for the routing brain
-------------------------------------------------------------
These are *training examples*, not routing rules: the router never looks words up in
this file. The neural network reads these examples once at training time and learns
its own internal representation of what different requests need.

Labels per example:
  task   : conversation | factual | explanation | summarization | translation |
           creative | coding | math | reasoning | analysis
  tier   : simple | moderate | complex | expert   (how much model capability is needed)
  length : short | medium | long                   (expected answer size)

Tier guideline used for labelling:
  simple   - one-step, common knowledge, small talk, tiny snippets
  moderate - standard multi-step work any competent general model handles
  complex  - multi-constraint, non-trivial algorithms, multi-step derivations, deep critique
  expert   - formal proofs, research-grade systems design, notoriously hard puzzles
"""

import random
from typing import List, Tuple

Example = Tuple[str, str, str, str]  # (text, task, tier, length)

# ---------------------------------------------------------------------------
# Shared vocabulary pools
# ---------------------------------------------------------------------------
LANGS = ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "C#", "Kotlin",
         "Swift", "Ruby", "PHP", "C", "Scala", "Dart"]

HUMAN_LANGS = ["French", "Spanish", "German", "Italian", "Portuguese", "Hindi", "Japanese",
               "Chinese", "Korean", "Russian", "Arabic", "Turkish", "Dutch", "Polish", "Bengali",
               "Marathi", "Tamil", "Swahili", "Greek", "Vietnamese"]

NAMES = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy",
         "Priya", "Rahul", "Mei", "Omar", "Sofia", "Lucas", "Aisha", "Kenji", "Nina", "Tom"]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

EXPLAIN_BASIC = [
    "why the sky is blue", "how rainbows form", "why we have seasons", "how magnets work",
    "how a refrigerator keeps food cold", "why leaves change color in autumn", "how plants grow",
    "what a computer virus is", "how a bicycle stays upright", "why ice floats on water",
    "what clouds are made of", "how a microwave heats food", "what gravity is",
    "why the moon has phases", "how a battery stores energy", "what a password manager does",
    "why we need sleep", "what the internet is", "how soap removes dirt", "what a calorie is",
]
EXPLAIN_MID = [
    "photosynthesis", "how vaccines train the immune system", "plate tectonics", "the greenhouse effect",
    "how DNA replication works", "how the stock market works", "inflation and why prices rise",
    "how the heart pumps blood", "how DNS resolves a domain name", "how HTTPS keeps data secure",
    "how TCP guarantees delivery", "how a compiler turns code into machine instructions",
    "how database indexes speed up queries", "how caching improves performance", "how load balancers work",
    "how GPS determines location", "how neural networks learn", "what a REST API is",
    "how virtual memory works", "how containers differ from virtual machines", "how compound interest works",
    "supply and demand", "the water cycle", "how antibiotics work and why resistance develops",
    "how electric motors work", "the causes of World War I", "why the Roman Empire fell",
    "how volcanoes erupt", "how blockchain works", "the difference between weather and climate",
    "the difference between a process and a thread", "the difference between TCP and UDP",
    "how recursion works", "what big O notation means", "how garbage collection works",
    "how solar panels generate electricity", "how the immune system fights infection",
    "how memory is formed in the brain", "how airplanes generate lift", "how interest rates affect the economy",
]
EXPLAIN_DEEP = [
    "quantum entanglement and why it does not allow faster-than-light communication",
    "how the attention mechanism in transformer models works mathematically",
    "the practical implications of the CAP theorem for distributed databases",
    "Byzantine fault tolerance and why it needs 3f+1 nodes",
    "Godel's incompleteness theorems and what they imply for mathematics",
    "renormalization in quantum field theory", "how zero-knowledge proofs work",
    "why RSA is secure and how Shor's algorithm threatens it",
    "how general relativity describes gravity as spacetime curvature",
    "the monetary transmission mechanism and its lags", "how CRISPR off-target effects arise",
    "how linearizability differs from serializability", "the bias-variance tradeoff in depth",
    "how backpropagation through time works and why gradients vanish",
    "how the Krebs cycle couples to oxidative phosphorylation", "how protein folding is predicted",
    "Paxos consensus and its failure modes", "how speculative execution attacks like Spectre work",
    "the measurement problem in quantum mechanics", "how copy-on-write B-trees enable MVCC",
]

FACT_QUESTIONS = [
    "What is the capital of {country}?", "Who painted the Mona Lisa?", "What is the boiling point of water?",
    "How far is the moon from Earth?", "What is the largest ocean on Earth?", "What is the tallest mountain in the world?",
    "What is the chemical symbol for gold?", "What language is spoken in Brazil?", "What is the population of {country}?",
    "When did World War II end?", "Who discovered penicillin?", "What does CPU stand for?",
    "How many bones are in the human body?", "What is the speed of light?", "What is the currency of {country}?",
    "Who wrote Romeo and Juliet?", "When was the Eiffel Tower built?", "Who was the first person on the moon?",
    "How many continents are there?", "What is the longest river in Africa?", "Who invented the telephone?",
    "What year did the Berlin Wall fall?", "What is the smallest planet in our solar system?",
    "How many players are on a football team?", "What is the freezing point of water in Fahrenheit?",
    "Who is the author of Harry Potter?", "What is the hardest natural substance?", "Where is the Great Barrier Reef?",
    "What is the national animal of {country}?", "Which planet is known as the Red Planet?",
    "Who developed the theory of relativity?", "What does HTML stand for?", "How many hours are in a week?",
    "What is the main ingredient in guacamole?", "Who founded Microsoft?", "What is the largest desert in the world?",
    "Which element has atomic number 1?", "In which country are the pyramids of Giza?", "What is the square footage of a football field?",
    "When did India gain independence?", "Who is known as the father of computers?", "What is the official language of {country}?",
    "How many days are in a leap year?", "What gas do plants absorb?", "What is the largest mammal?",
    "Who composed the Fifth Symphony?", "What time zone is {country} in?", "What does NASA stand for?",
]
FACT_LISTS = [
    "List the {n} largest countries by area.", "Name all the planets in order from the sun.",
    "List the {n} most spoken languages in the world.", "Give me the names of the {n} longest rivers.",
    "Which countries border {country}?", "List the noble gases.", "Name {n} famous paintings by Van Gogh.",
    "What are the {n} largest cities in {country}?", "List the members of the G7.",
    "Name the {n} tallest buildings in the world.", "List all the US presidents since 1980.",
    "What are the official languages of the United Nations?", "Name the first {n} elements of the periodic table.",
]
COUNTRIES = ["France", "Japan", "Brazil", "India", "Canada", "Australia", "Kenya", "Germany", "Mexico",
             "Egypt", "Norway", "Argentina", "Thailand", "Italy", "Nigeria", "Spain", "Peru", "Vietnam"]

CHAT_SIMPLE = [
    "hi", "hello", "hey", "hii", "hey there!", "good morning", "good evening", "how are you?",
    "how are you doing today?", "what's up", "sup", "yo", "thanks!", "thank you so much",
    "that was really helpful, thanks", "ok", "okay cool", "nice", "lol", "haha that's funny",
    "good night", "bye", "see you later", "who are you?", "what can you do?", "tell me about yourself",
    "are you a robot?", "what's your name?", "i'm bored", "can we just chat?", "you're awesome",
    "do you like music?", "what's your favorite color?", "happy friday!", "test", "testing 123",
    "hello, is anyone there?", "nice to meet you", "how's your day going?", "I'm back",
    "great job", "cool, thanks", "hmm interesting", "wow", "really?", "morning!", "hiya",
    "what are you up to?", "do you have feelings?", "I love this app",
]
CHAT_EMOTIONS = ["stressed", "anxious", "lonely", "overwhelmed", "sad", "nervous", "burnt out", "unmotivated", "frustrated"]
CHAT_SITUATIONS = [
    "my exams are next week", "I just moved to a new city", "my friend stopped replying to my messages",
    "I have a job interview tomorrow", "work has been piling up", "I can't sleep at night",
    "I failed my driving test", "my team project is falling apart", "I keep procrastinating",
]
CHAT_ASKS = ["Any advice?", "What should I do?", "Can you help me feel better?", "How do I deal with this?",
             "Do you have any tips?", "Can we talk about it?"]

SUMMARY_PARAS = [
    "The city council met on Tuesday to discuss the proposed budget for next year. Members debated funding for public transport, with several arguing that bus routes in the northern districts are underserved. The council ultimately approved a 4% increase in transit spending while cutting the parks maintenance budget by 2%.",
    "Researchers at the university have developed a new battery chemistry based on sodium rather than lithium. The cells retain 90% of their capacity after 3,000 charge cycles and use materials that are far more abundant. The team expects pilot production to begin within two years, though energy density remains about 20% lower than current lithium-ion cells.",
    "Hi team, a quick update on the release. QA found two blocking bugs in the payment flow, both related to currency rounding. The fixes are in review and should merge by Thursday. That pushes the launch from Monday to Wednesday next week. Please update your customers accordingly.",
    "I bought these headphones a month ago. The noise cancellation is excellent on flights and the battery easily lasts a week. However, the ear cushions get warm after an hour and the companion app crashes often. For the price, I would still recommend them to frequent travellers.",
    "The tenant shall pay rent on the first day of each month. Late payments incur a fee of 5% of the monthly rent. The landlord is responsible for structural repairs, while the tenant must maintain the interior in good condition. Either party may terminate this agreement with sixty days written notice.",
    "Once upon a time, a small fox lived at the edge of a great forest. Every winter the fox struggled to find food, until one day it befriended an old crow who knew where the farmers stored their grain. Together they survived the harshest winter in memory, and the fox learned that cleverness is nothing without friendship.",
    "Global shipping rates rose sharply in the third quarter as congestion at major ports worsened. Analysts attribute the spike to a combination of labor shortages, extreme weather, and a surge in consumer demand ahead of the holiday season. Several retailers have warned of delayed deliveries and higher prices.",
    "In this paper we propose a sparse attention mechanism that reduces the quadratic cost of transformers to near-linear. Our method routes each token to a small set of learned clusters. On long-document benchmarks it matches dense attention accuracy while using 70% less memory and running three times faster.",
    "Patients enrolled in the trial received either the new drug or a placebo for twelve weeks. Those on the drug showed a 30% reduction in symptoms compared with placebo, and side effects were mostly mild headaches. The authors caution that the sample was small and call for a larger multi-site study.",
    "The meeting covered three topics: the hiring plan, the office move, and the new expense policy. Two engineering roles will open next month. The move to the new building is scheduled for March. Expenses above $500 now require manager approval before purchase.",
    "Climate scientists report that the past decade was the warmest on record. Arctic sea ice continues to shrink, and extreme heat events have become more frequent across Europe and Asia. The report urges governments to accelerate emission cuts to keep warming below 1.5 degrees.",
    "Our app's daily active users grew 18% month over month, driven mainly by the new referral program. Churn decreased slightly, but average session length fell from 11 to 9 minutes. The product team suspects the redesigned home screen and will run an A/B test next sprint.",
    "The Industrial Revolution began in Britain in the late eighteenth century. Mechanized textile production, steam power, and new iron-making techniques transformed the economy. Cities grew rapidly as workers left farms for factories, bringing both prosperity and harsh working conditions.",
    "To reset your router, unplug it for thirty seconds and plug it back in. If the internet light stays red, press and hold the reset button for ten seconds using a paperclip. After the reset, reconnect using the default network name and password printed on the label.",
    "The novel follows a young engineer who returns to her hometown after her father's death. As she restores his abandoned workshop, she uncovers letters revealing a secret invention and a family feud spanning decades. The story blends mystery with a meditation on grief and inheritance.",
    "Quarterly revenue reached $4.2 billion, up 12% year over year, beating analyst expectations. Cloud services grew 31%, while hardware sales declined 5%. The company raised its full-year guidance and announced a $10 billion share buyback program.",
]
SUMMARY_INSTR = [
    "Summarize the following:", "Summarize this text:", "TL;DR:", "Give me the key points of this:",
    "Can you condense this into a few sentences?", "Summarise this for me:", "What's the gist of this?",
    "Write a short summary of the following passage:", "Boil this down to 3 bullet points:",
    "Give me a one-paragraph summary:", "Please summarize this email:", "Sum up this article:",
    "Extract the main takeaways from this:", "Shorten this text while keeping the important parts:",
    "Summarize the meeting notes below:", "Can you give me an executive summary of this?",
    "Recap this in plain language:", "What are the main points here?",
]

TRANSLATE_SENTENCES = [
    "Where is the nearest train station?", "I would like a cup of coffee, please.", "How much does this cost?",
    "Good morning, how did you sleep?", "The meeting has been moved to Friday.", "I love learning new languages.",
    "Can you help me find my hotel?", "Happy birthday, my friend!", "The weather is beautiful today.",
    "Please turn off your phone during the movie.", "I am allergic to peanuts.", "Thank you for your hospitality.",
    "We are running late, start without us.", "This book changed my life.", "What time does the store close?",
    "My name is Anna and I am a teacher.", "The project deadline is next Monday.", "Could you speak more slowly?",
    "I lost my wallet on the bus.", "Let's meet at the park at five.",
]
FOREIGN_SENTENCES = [
    "Je voudrais réserver une table pour deux personnes ce soir.", "¿Dónde está la biblioteca más cercana?",
    "Ich habe meinen Schlüssel zu Hause vergessen.", "今日はとても暑いですね。", "我明天要去北京出差。",
    "Мне нужно купить билет на поезд.", "मुझे यह किताब बहुत पसंद है।", "Sono molto felice di conoscerti.",
    "Eu gostaria de aprender a tocar violão.", "오늘 저녁에 뭐 먹을까요?", "أين يمكنني شراء تذكرة؟",
    "Bugün hava çok güzel.", "Ik ben op zoek naar een appartement.", "Η θάλασσα είναι πολύ ήρεμη σήμερα.",
    "मला मराठी शिकायची आहे.", "Tôi muốn đặt một phòng khách sạn.",
]
TRANSLATE_FRAMES = [
    ("Translate to {lang}: {s}", "simple"), ("How do you say '{s}' in {lang}?", "simple"),
    ("Translate this into {lang}:\n{s}", "simple"), ("What is '{s}' in {lang}?", "simple"),
    ("{lang} translation please: {s}", "simple"), ("Can you translate '{s}' to {lang}?", "simple"),
]
TRANSLATE_FOREIGN_FRAMES = [
    "Translate to English: {f}", "What does this mean? {f}", "Translate this sentence: {f}",
    "Can you translate this for me?\n{f}", "{f}\nTranslate the above to English.", "What does '{f}' mean in English?",
]
TRANSLATE_PARA_FRAMES = [
    "Translate the following paragraph into {lang}:\n{p}", "Please translate this email to {lang}:\n{p}",
    "Translate this text from English to {lang}, keeping the meaning accurate:\n{p}",
]
TRANSLATE_HARD_FRAMES = [
    "Translate this legal clause into {lang}, preserving the formal register and exact legal meaning:\n{p}",
    "Localize this marketing copy for a {lang}-speaking audience, adapting idioms and cultural references:\n{p}",
    "Translate this technical abstract into {lang} using correct domain terminology and keep the citations intact:\n{p}",
    "Translate the poem below into {lang} while keeping its rhyme scheme and rhythm:\n{p}",
]

CREATIVE_SUBJECTS = [
    "the ocean", "a robot who learns to love", "autumn leaves", "friendship", "a cat detective",
    "space travel", "a lost city", "coffee", "Monday mornings", "programmers", "the moon", "a rainy day",
    "an old lighthouse keeper", "first love", "a dragon who is afraid of fire", "time travel",
    "a small village in the mountains", "artificial intelligence", "the last tree on Earth", "my grandmother's kitchen",
    "a haunted library", "a talking dog", "city lights at night", "a pirate ship", "winter", "dreams",
]
CREATIVE_SIMPLE = [
    "Tell me a joke about {s}.", "Write a haiku about {s}.", "Give me a slogan for a company that sells {s}.",
    "Write a one-line pun about {s}.", "Write a limerick about {s}.", "Write a short birthday message for my sister.",
    "Suggest a catchy name for a podcast about {s}.", "Write a tagline for a bakery.", "Write a two-line rhyme about {s}.",
    "Give me a funny Instagram caption about {s}.", "Write a fortune cookie message.", "Make up a riddle about {s}.",
]
CREATIVE_MID = [
    "Write a poem about {s}.", "Write a short story about {s}.", "Write song lyrics about {s}.",
    "Write a product description for a smartwatch.", "Write a wedding toast for my best friend.",
    "Write a bedtime story for a 5 year old about {s}.", "Write a dialogue between two strangers on a train about {s}.",
    "Write a motivational speech for a high school graduation.", "Compose a sonnet about {s}.",
    "Write a fairy tale about {s}.", "Write a blog post intro about {s}.", "Write a love letter inspired by {s}.",
    "Write a free verse poem that captures the feeling of {s}.", "Write a funny story about {s}.",
]
CREATIVE_HARD = [
    "Write a 2000-word short story about {s} told from three different characters' perspectives, with a twist ending that recontextualizes the opening scene.",
    "Write a screenplay scene about {s} with stage directions, subtext-heavy dialogue, and a slow reveal of a hidden betrayal.",
    "Write an epic poem in iambic pentameter about {s}, structured in five cantos with a recurring motif.",
    "Create a detailed fantasy world centered on {s}, including a magic system with costs and limits, three political factions, and their history of conflict.",
    "Write the first chapter of a mystery novel about {s}, planting three subtle clues and one red herring, in the style of Agatha Christie.",
    "Write a nonlinear short story about {s} where each section moves backward in time and the final section explains the first.",
]

CODE_SIMPLE = [
    "reverse a string", "check if a number is even", "find the maximum value in a list", "print hello world",
    "convert celsius to fahrenheit", "count the vowels in a string", "sum a list of numbers",
    "check if a string is a palindrome", "read a file line by line", "sort a list of numbers",
    "remove duplicates from a list", "get the current date and time", "swap two variables",
    "find the length of a string", "check if a list is empty", "generate a random number between 1 and 10",
    "convert a string to uppercase", "loop over a dictionary", "calculate the factorial of a number",
    "find the average of an array",
]
CODE_MID = [
    "parse a CSV file and compute the average of each column", "implement binary search on a sorted array",
    "build a REST API endpoint that creates a new user", "validate an email address with a regular expression",
    "implement a stack using a linked list", "fetch JSON from an API and handle network errors",
    "write unit tests for a simple calculator class", "implement merge sort", "create a login form component with validation",
    "write a SQL query that finds the top 5 customers by total revenue", "debounce a function call",
    "connect to PostgreSQL and run a parameterized query", "paginate results from a database query",
    "upload a file to cloud storage", "implement a queue with two stacks", "write a script that renames files in bulk",
    "build a simple command line todo app", "implement a basic HTTP server", "flatten a nested list",
    "find all anagrams of a word in a list", "implement depth-first search on a graph", "scrape titles from a web page",
]
CODE_HARD = [
    "implement an LRU cache with O(1) get and put", "build a thread-safe producer-consumer queue",
    "write a rate limiter using the token bucket algorithm", "implement Dijkstra's shortest path with a priority queue",
    "refactor a 500-line god class into smaller cohesive services", "design a database schema with migrations for an e-commerce platform",
    "implement JWT authentication with refresh token rotation", "write a parser for arithmetic expressions with operator precedence",
    "build a websocket chat server that supports rooms", "implement a trie with autocomplete ranking",
    "optimize a slow SQL query with multiple joins and explain which indexes to add", "implement an interval tree",
    "write a concurrent web crawler with a worker pool and politeness delays", "implement A* pathfinding on a grid with obstacles",
    "build a plugin system with dynamic loading and dependency resolution", "implement a segment tree with lazy propagation",
    "write a retry decorator with exponential backoff and jitter", "implement an event-sourced shopping cart",
]
CODE_EXPERT = [
    "design and implement a distributed key-value store using the Raft consensus algorithm",
    "write a lock-free concurrent hash map", "implement a garbage collector for a toy language",
    "build a cost-based query optimizer for a relational database", "implement a CRDT-based collaborative text editor",
    "write a JIT compiler for a stack-based bytecode", "design a globally distributed rate limiter with consistent hashing",
    "implement MVCC transactions in a storage engine", "write a custom memory allocator with size classes and thread caches",
    "implement a B+ tree storage engine with write-ahead logging and crash recovery",
    "build a type checker with Hindley-Milner type inference", "implement a distributed transaction coordinator with two-phase commit and failure recovery",
]
CODE_FRAMES = [
    "Write a {lang} function to {t}.", "How do I {t} in {lang}?", "Implement code to {t} in {lang}.",
    "Can you show me {lang} code that will {t}?", "Give me a {lang} program to {t}.", "{lang}: {t}",
    "I need a {lang} snippet to {t}.", "What's the best way to {t} using {lang}?", "Write code that can {t}.",
    "Help me write a {lang} script to {t}.",
]
CODE_SNIPPETS = [
    "def add(a, b):\n    return a - b\n\nprint(add(2, 3))",
    "for (let i = 0; i <= arr.length; i++) {\n  console.log(arr[i].name);\n}",
    "public int divide(int a, int b) {\n    return a / b;\n}",
    "def get_user(users, id):\n    for u in users:\n        if u['id'] == id:\n            return u\n    return users[0]",
    "const data = fetch('/api/items').json();\nconsole.log(data.length);",
    "x = input('number: ')\nprint(x + 10)",
    "SELECT name, COUNT(*) FROM orders GROUP BY customer_id;",
    "int* p;\n*p = 5;\nprintf(\"%d\", *p);",
    "items = [1, 2, 3]\nfor i in range(len(items)):\n    items.remove(items[i])",
    "func main() {\n    var m map[string]int\n    m[\"a\"] = 1\n}",
    "async function load() {\n  const res = await fetch(url)\n  return res.data\n}",
    "while True:\n    data = sock.recv(1024)\n    process(data)",
    "let v = vec![1, 2, 3];\nlet first = &v[0];\nv.push(4);\nprintln!(\"{}\", first);",
    "class Counter:\n    count = []\n    def add(self, x):\n        self.count.append(x)",
]
CODE_SNIPPETS_HARD = [
    "import threading\nbalance = 0\ndef deposit(n):\n    global balance\n    for _ in range(n):\n        balance += 1\nthreads = [threading.Thread(target=deposit, args=(100000,)) for _ in range(8)]\nfor t in threads: t.start()\nfor t in threads: t.join()\nprint(balance)",
    "def fib(n):\n    if n < 2:\n        return n\n    return fib(n - 1) + fib(n - 2)\n\nresults = [fib(i) for i in range(40)]",
    "useEffect(() => {\n  const id = setInterval(() => setCount(count + 1), 1000);\n}, []);\n\nuseEffect(() => {\n  fetchData(query).then(setResults);\n}, [results]);",
    "SELECT o.id, c.name, SUM(i.price * i.qty)\nFROM orders o\nJOIN customers c ON c.id = o.customer_id\nJOIN items i ON i.order_id = o.id\nWHERE o.created_at > NOW() - INTERVAL '30 days'\nGROUP BY o.id, c.name\nORDER BY 3 DESC;",
    "public class Singleton {\n    private static Singleton instance;\n    public static Singleton get() {\n        if (instance == null) {\n            instance = new Singleton();\n        }\n        return instance;\n    }\n}",
]
CODE_SNIPPET_FRAMES = [
    ("Why does this code not work?\n```\n{c}\n```", "moderate"), ("Fix the bug in this code:\n{c}", "moderate"),
    ("What's wrong with this?\n{c}", "moderate"), ("Can you explain what this code does?\n```\n{c}\n```", "simple"),
    ("This throws an error, help:\n{c}", "moderate"), ("Refactor this to be cleaner:\n```\n{c}\n```", "moderate"),
    ("Add comments and type hints to this code:\n{c}", "simple"), ("Write unit tests for this:\n```\n{c}\n```", "moderate"),
]
CODE_SNIPPET_HARD_FRAMES = [
    "This has a race condition / performance problem. Find the root cause and give a production-ready fix:\n```\n{c}\n```",
    "Review this code for correctness, concurrency issues and performance, then rewrite it:\n{c}",
    "Optimize this and explain the complexity before and after:\n```\n{c}\n```",
]

MATH_FUNCS = ["x^2 sin(x)", "e^(3x) cos(x)", "ln(x^2 + 1)", "x^3 - 4x + 7", "sqrt(1 + x^2)", "tan(2x)", "x e^(-x)", "(x^2 + 1)/(x - 3)"]
MATH_INTEGRALS = ["x e^x", "sin^2(x)", "1/(x^2 + 4)", "x^2 ln(x)", "e^(2x) sin(x)", "1/(x(x+1))", "sqrt(4 - x^2)", "x cos(3x)"]
MATH_PROOFS = [
    "Prove that the square root of 2 is irrational.", "Prove that there are infinitely many prime numbers.",
    "Prove that every continuous function on a closed interval is bounded.", "Prove the Cauchy-Schwarz inequality.",
    "Show that the harmonic series diverges.", "Prove that every group of prime order is cyclic.",
    "Derive a closed form for the Fibonacci numbers using generating functions.", "Prove that e is irrational.",
    "Prove the fundamental theorem of arithmetic.", "Show that the real numbers are uncountable using Cantor's diagonal argument.",
    "Prove that a bounded monotone sequence converges.", "Prove that the sum of the reciprocals of the primes diverges.",
    "Prove that every finite integral domain is a field.", "Show that the eigenvalues of a real symmetric matrix are real.",
    "Prove Lagrange's theorem for finite groups.", "Prove that the set of rational numbers is countable.",
    "Prove the Bolzano-Weierstrass theorem.", "Show that a compact subset of a metric space is closed and bounded.",
]


def _rand_num(r: random.Random, lo: int, hi: int) -> int:
    return r.randint(lo, hi)


def _math_simple(r: random.Random) -> str:
    a, b, c = r.randint(2, 99), r.randint(2, 99), r.randint(10, 200)
    return r.choice([
        f"What is {a} + {b}?", f"What is {r.choice([5, 10, 15, 20, 25, 30, 40])}% of {c}?", f"Calculate {a} times {b}",
        f"Solve for x: {r.randint(2, 9)}x + {b} = {c}", f"What is the square root of {r.choice([16, 25, 49, 64, 81, 144, 169, 225])}?",
        f"Is {r.randint(10, 200)} a prime number?", f"What is {a}/{b} as a decimal?", f"{a} * {b} = ?",
        f"what's {a} minus {b}", f"Convert {c} km to miles", f"Round {a}.{b} to the nearest whole number",
        f"What is {a} squared?", f"How much is {a} plus {b} plus {c}?", f"What is the area of a rectangle {a} by {b}?",
    ])


def _math_moderate(r: random.Random) -> str:
    b, c = r.randint(1, 12), r.randint(1, 30)
    P, rate, n = r.choice([1000, 5000, 2500, 10000]), r.choice([3, 4, 5, 7, 8]), r.randint(3, 15)
    return r.choice([
        f"Solve the quadratic equation x^2 + {b}x - {c} = 0", f"Find the derivative of {r.choice(MATH_FUNCS)}",
        f"A train travels {r.randint(100, 900)} km in {r.randint(2, 9)} hours. What is its average speed in m/s?",
        f"If I invest ${P} at {rate}% interest compounded annually, how much will I have after {n} years?",
        f"What is the probability of getting at least one six in {r.randint(2, 8)} rolls of a fair die?",
        f"Find the area of a circle with radius {r.randint(2, 20)} cm", f"Find the slope of the line through ({b}, {c}) and ({b + 3}, {c - 5})",
        f"Simplify (x^2 - {b * b}) / (x - {b})", f"Find the mean, median and mode of {', '.join(str(r.randint(1, 50)) for _ in range(7))}",
        f"A shirt costs ${c + 20} after a {r.choice([10, 20, 25])}% discount. What was the original price?",
        f"Solve the system: x + y = {c}, x - y = {b}", f"How many ways can {r.randint(4, 9)} people sit in a row?",
        f"Find the {r.randint(5, 20)}th term of the arithmetic sequence {b}, {b + 3}, {b + 6}, ...",
    ])


def _math_complex(r: random.Random) -> str:
    a, b, c, d = (r.randint(-5, 9) for _ in range(4))
    red, blue = r.randint(3, 9), r.randint(3, 9)
    return r.choice([
        f"Evaluate the integral of {r.choice(MATH_INTEGRALS)} dx", f"Find the eigenvalues and eigenvectors of the matrix [[{a}, {b}], [{c}, {d}]]",
        f"Find the Taylor series of {r.choice(['e^x sin(x)', 'ln(1+x)', 'cos(x^2)', '1/(1-2x)'])} around 0 up to the x^4 term",
        f"Solve the differential equation dy/dx = {r.choice(['y(1 - y)', 'x y^2', 'y + e^x', '-2y + sin(x)'])}",
        f"A bag has {red} red and {blue} blue balls. Drawing 3 without replacement, what is the probability exactly 2 are red?",
        "Compute the limit as x approaches 0 of (sin x - x) / x^3", "Use Lagrange multipliers to maximize f(x, y) = xy subject to x^2 + y^2 = 8",
        f"Solve the system of equations: {a}x + {b}y - z = 3, 2x - y + {c}z = 1, x + y + z = {d}",
        "Find the volume of the solid formed by rotating y = sqrt(x) from x = 0 to 4 about the x-axis",
        "Find the general solution of y'' - 4y' + 4y = e^(2x)", "Compute the determinant and inverse of the 3x3 matrix [[2, 1, 0], [1, 3, 1], [0, 1, 4]]",
        "Expected number of coin flips to get two heads in a row? Show the derivation with states.",
        "Find the Fourier series of f(x) = x on the interval (-pi, pi)",
    ])


MATH_FRAMES = ["{q}", "Solve: {q}", "Can you help with this math problem? {q}", "{q} Show your work.", "Math question: {q}"]

PUZZLE_SIMPLE = [
    lambda r: f"If today is {r.choice(DAYS)}, what day will it be in {r.randint(2, 20)} days?",
    lambda r: "Which is heavier, a kilogram of feathers or a kilogram of steel?",
    lambda r: f"If all cats are animals and {r.choice(NAMES)} is a cat, is {r.choice(NAMES)} an animal?",
    lambda r: f"What comes next in the sequence: {', '.join(str(2 * i + r.randint(0, 1) * 0) for i in range(1, 6))}, ?",
    lambda r: f"{r.choice(NAMES)} is taller than {r.choice(NAMES)}. Who is shorter?",
    lambda r: "If you have 3 apples and take away 2, how many do you have?",
    lambda r: "What is the odd one out: apple, banana, carrot, mango?",
]
PUZZLE_MID = [
    lambda r: "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?",
    lambda r: f"{r.choice(NAMES)} is older than {r.choice(NAMES)}, and {r.choice(NAMES)} is younger than {r.choice(NAMES)} but older than {r.choice(NAMES)}. Who is the youngest? Explain your reasoning.",
    lambda r: "If some doctors are artists and all artists are musicians, can we conclude that some doctors are musicians?",
    lambda r: "How many times do the hour and minute hands of a clock overlap in 12 hours?",
    lambda r: f"What is the next number: {', '.join(str(x) for x in [1, 1, 2, 3, 5, 8, 13][:r.randint(5, 7)])}, ?",
    lambda r: "If it takes 5 machines 5 minutes to make 5 widgets, how long would 100 machines take to make 100 widgets?",
    lambda r: "A farmer has 17 sheep and all but 9 run away. How many are left? Explain the trick.",
    lambda r: "If the day before yesterday was Thursday, what day will the day after tomorrow be?",
    lambda r: f"Four friends {', '.join(r.sample(NAMES, 4))} finished a race. The first didn't win, the second beat the third, and the fourth was not last. Work out a valid finishing order.",
    lambda r: "A lily pad doubles in size every day and covers the lake on day 48. On which day does it cover half the lake?",
    lambda r: "Is this argument valid? All birds can fly. Penguins are birds. Therefore penguins can fly. Explain.",
]
PUZZLE_HARD = [
    lambda r: "Five houses in a row are painted different colors, owned by people of different nationalities, who drink different drinks and keep different pets. Given the 15 clues of the classic Einstein riddle, who owns the fish? Show the full deduction.",
    lambda r: "A farmer must cross a river with a wolf, a goat and a cabbage. The boat holds only the farmer and one item. Find the sequence of crossings and prove it is minimal.",
    lambda r: "Three boxes are labeled Apples, Oranges and Mixed, and every label is wrong. You may draw one fruit from one box. How do you relabel all boxes correctly?",
    lambda r: "In the Monty Hall problem, should the contestant switch doors? Justify with conditional probability and generalize to n doors.",
    lambda r: f"On an island of knights and knaves, {r.choice(NAMES)} says 'Exactly one of us is a knave' and {r.choice(NAMES)} says 'We are both knights'. Determine who is what.",
    lambda r: f"Schedule {r.randint(5, 7)} meetings across 3 rooms given that the CEO cannot attend two consecutive slots, the design review must precede the launch meeting, and two teams share members. Find a feasible schedule and explain the reasoning.",
    lambda r: "You have 12 coins, one of which is counterfeit and either heavier or lighter. With a balance scale and only three weighings, how do you find it and determine whether it's heavier or lighter?",
    lambda r: "In an infinitely repeated prisoner's dilemma with discount factor d, under what conditions is tit-for-tat a Nash equilibrium? Reason carefully.",
    lambda r: "Two trains 300 km apart head toward each other at 60 and 90 km/h while a bird flies back and forth between them at 120 km/h. How far does the bird fly? Then explain the shortcut and the infinite-series approach.",
    lambda r: "Four people must cross a bridge at night with one torch; they take 1, 2, 5 and 10 minutes, and at most two cross at a time. What is the minimum total time? Prove optimality.",
]
PUZZLE_EXPERT = [
    "100 prisoners and a light bulb: devise a protocol that guarantees someone eventually declares all prisoners have visited the room, and analyze its expected running time.",
    "Solve the blue-eyed islanders puzzle and explain precisely what new information the visitor's announcement provides, using common knowledge.",
    "For the 100 prisoners and 100 boxes problem, describe the cycle-following strategy and prove its success probability tends to 1 - ln 2.",
    "Analyze the unexpected hanging paradox: identify exactly where the prisoner's backward induction fails, with reference to self-referential knowledge.",
    "Newcomb's problem: rigorously compare the evidential and causal decision theory answers and argue which is rational under a near-perfect predictor.",
    "Resolve the two envelopes paradox, showing exactly which step of the naive expected-value argument is invalid for proper and improper priors.",
    "Sleeping Beauty problem: present the halfer and thirder arguments formally, then evaluate which is correct under different betting setups.",
    "Design a winning strategy for the hat puzzle with 100 prisoners in a line wearing black or white hats, prove that at most one dies, and generalize to k colors.",
]
REASON_FRAMES = ["{q}", "Logic puzzle: {q}", "Think step by step. {q}", "Here's a brain teaser: {q}", "Riddle for you: {q}", "{q} Walk me through your reasoning."]

COMPARE_PAIRS = [
    ("Python", "JavaScript"), ("SQL databases", "NoSQL databases"), ("renting", "buying a house"),
    ("iPhone", "Android"), ("React", "Vue"), ("electric cars", "gasoline cars"), ("AWS", "Azure"),
    ("remote work", "office work"), ("stocks", "bonds"), ("Kubernetes", "serverless"), ("PostgreSQL", "MongoDB"),
    ("public universities", "private universities"), ("freelancing", "a full-time job"), ("Mac", "Windows laptops"),
    ("index funds", "picking individual stocks"), ("solar power", "wind power"), ("GraphQL", "REST"),
    ("Agile", "Waterfall"), ("Netflix", "Disney+"), ("leasing a car", "buying a car"),
]
ANALYZE_THINGS = [
    "a four-day work week", "nuclear energy", "social media for teenagers", "universal basic income", "self-driving cars",
    "moving our monolith to microservices", "learning to code in 2026", "open-plan offices", "cryptocurrency as an investment",
    "standardized testing", "a startup offering subscription meal kits", "raising the minimum wage", "electric scooters in cities",
]
DATA_SERIES = [
    "Q1: 120k, Q2: 135k, Q3: 128k, Q4: 171k", "Jan 4.2%, Feb 4.0%, Mar 4.5%, Apr 5.1%, May 5.0%, Jun 5.8%",
    "2019: 1.2M users, 2020: 2.9M, 2021: 3.4M, 2022: 3.1M, 2023: 3.0M", "North 32%, South 18%, East 27%, West 23%",
    "conversion 2.1% -> 2.4% -> 1.9% -> 1.7% while traffic rose 10% each month",
]
ANALYSIS_MID = [
    "Compare {a} and {b}.", "What are the pros and cons of {t}?", "Which is better for a beginner: {a} or {b}?",
    "Evaluate the strengths and weaknesses of {t}.", "{a} vs {b} - which should I choose and why?",
    "Give me a comparison table of {a} and {b}.", "Is {t} a good idea? Weigh both sides.",
]
ANALYSIS_HARD = [
    "Analyze this sales data and identify trends, anomalies and likely causes: {d}", "Do a SWOT analysis of {t}.",
    "Critique the argument that {t} will inevitably improve productivity. Identify hidden assumptions and counterexamples.",
    "Assess the risks of {t} for a mid-sized company, ranking them by likelihood and impact, with mitigations.",
    "Analyze the impact of {t} on low-income households, considering short- and long-term effects.",
    "Here are our metrics: {d}. What story do they tell and what should we investigate next?",
    "Compare {a} and {b} for a team of 50 engineers handling 10 million requests a day, considering cost, reliability, hiring and migration risk.",
]
ANALYSIS_EXPERT = [
    "Evaluate the second-order macroeconomic effects of {t} under stagflation, including game-theoretic responses from firms, unions and the central bank.",
    "Perform a rigorous comparative analysis of Paxos, Raft and PBFT with respect to fault model, message complexity, latency under partitions and throughput.",
    "Analyze the long-run equilibrium effects of {t} using a general-equilibrium framing, discussing elasticities, incidence and welfare trade-offs.",
    "Critically assess the methodology of a randomized controlled trial with differential attrition and non-compliance, and explain how to estimate the causal effect correctly.",
    "Assess the geopolitical, supply-chain and technological implications of a semiconductor export ban for the next decade, with scenario analysis.",
]

PREFIX_I = ["", "", "", "please ", "Please ", "can you ", "Could you ", "I need you to ", "help me ", "pls ", "Hey, ", "Quick one: "]
PREFIX_Q = ["", "", "", "hey, ", "Quick question: ", "I was wondering, ", "Hi! ", "So, "]
SUFFIX = ["", "", "", "", " Thanks!", " thanks", " Please.", " :)"]
SHORT_MODS = [" Keep it brief.", " Answer in one sentence.", " Short answer please.", " In a few words."]
LONG_MODS = [" Explain in detail.", " Be thorough and give examples.", " Give a comprehensive answer.", " Go deep on this."]


def _typo(r: random.Random, text: str) -> str:
    words = text.split(" ")
    idx = [i for i, w in enumerate(words) if len(w) > 4 and w.isalpha()]
    if not idx:
        return text
    i = r.choice(idx)
    w = words[i]
    j = r.randint(1, len(w) - 2)
    words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


def _noise(r: random.Random, text: str) -> str:
    if r.random() < 0.25:
        text = text.lower()
    if r.random() < 0.2:
        text = text.rstrip("?.!")
    if r.random() < 0.15:
        text = _typo(r, text)
    return text


def _wrap(r: random.Random, text: str, imperative: bool) -> str:
    if imperative:
        p = r.choice(PREFIX_I)
        if p and text[:1].isupper() and not text[:2].isupper():
            text = text[0].lower() + text[1:]
    else:
        p = r.choice(PREFIX_Q)
    return p + text + r.choice(SUFFIX)


def build_corpus(seed: int = 42, per_task: int = 650) -> List[Example]:
    r = random.Random(seed)
    out: List[Example] = []

    def add(text: str, task: str, tier: str, length: str, imperative: bool = True, noise: bool = True,
            allow_len_mod: bool = True):
        if allow_len_mod and r.random() < 0.12:
            if r.random() < 0.5:
                text, length = text + r.choice(SHORT_MODS), "short"
            else:
                text, length = text + r.choice(LONG_MODS), "long"
        text = _wrap(r, text, imperative)
        if noise:
            text = _noise(r, text)
        out.append((text, task, tier, length))

    # conversation
    for _ in range(per_task):
        if r.random() < 0.7:
            add(r.choice(CHAT_SIMPLE), "conversation", "simple", "short", imperative=False, allow_len_mod=False)
        else:
            add(f"I'm feeling {r.choice(CHAT_EMOTIONS)} because {r.choice(CHAT_SITUATIONS)}. {r.choice(CHAT_ASKS)}",
                "conversation", "moderate", "medium", imperative=False, allow_len_mod=False)

    # factual
    for _ in range(per_task):
        if r.random() < 0.75:
            q = r.choice(FACT_QUESTIONS).format(country=r.choice(COUNTRIES))
            add(q, "factual", "simple", "short", imperative=False)
        else:
            q = r.choice(FACT_LISTS).format(n=r.randint(3, 10), country=r.choice(COUNTRIES))
            add(q, "factual", "moderate", "medium")

    # explanation
    exp_frames_q = ["How does {t} work?", "Why {t}?", "What is {t}?", "Can you explain {t}?", "I don't understand {t}, can you help?"]
    exp_frames_i = ["Explain {t}.", "Explain {t} in simple terms.", "Describe {t}.", "Teach me {t}.", "Walk me through {t}.",
                    "Help me understand {t}.", "Explain {t} like I'm five.", "Give me an overview of {t}."]
    for _ in range(per_task):
        roll = r.random()
        if roll < 0.25:
            t, tier, length = r.choice(EXPLAIN_BASIC), "simple", "medium"
        elif roll < 0.75:
            t, tier, length = r.choice(EXPLAIN_MID), "moderate", "medium"
        else:
            t, tier, length = r.choice(EXPLAIN_DEEP), "complex", "long"
        if r.random() < 0.5:
            add(r.choice(exp_frames_i).format(t=t), "explanation", tier, length)
        else:
            add(r.choice(["Explain {t}.", "Can you explain {t}?", "Help me understand {t}."]).format(t=t),
                "explanation", tier, length, imperative=False)

    # summarization
    for _ in range(per_task):
        k = r.choices([1, 2, 3, 4], weights=[3, 3, 2, 1])[0]
        payload = " ".join(r.sample(SUMMARY_PARAS, k)) if r.random() < 0.6 else "\n\n".join(r.sample(SUMMARY_PARAS, k))
        tier = {1: "simple", 2: "moderate", 3: "moderate", 4: "complex"}[k]
        instr = r.choice(SUMMARY_INSTR)
        text = f"{instr}\n{payload}" if r.random() < 0.8 else f"{payload}\n\n{instr}"
        add(text, "summarization", tier, "short" if k == 1 else "medium", allow_len_mod=False)

    # translation
    for _ in range(per_task):
        roll = r.random()
        lang = r.choice(HUMAN_LANGS)
        if roll < 0.45:
            frame, tier = r.choice(TRANSLATE_FRAMES)
            add(frame.format(lang=lang, s=r.choice(TRANSLATE_SENTENCES)), "translation", tier, "short", allow_len_mod=False)
        elif roll < 0.7:
            add(r.choice(TRANSLATE_FOREIGN_FRAMES).format(f=r.choice(FOREIGN_SENTENCES)), "translation", "simple", "short",
                allow_len_mod=False)
        elif roll < 0.88:
            p = " ".join(r.sample(TRANSLATE_SENTENCES, r.randint(3, 6)))
            add(r.choice(TRANSLATE_PARA_FRAMES).format(lang=lang, p=p), "translation", "moderate", "medium", allow_len_mod=False)
        else:
            p = r.choice(SUMMARY_PARAS)
            add(r.choice(TRANSLATE_HARD_FRAMES).format(lang=lang, p=p), "translation", "complex", "medium", allow_len_mod=False)

    # creative
    for _ in range(per_task):
        roll = r.random()
        s = r.choice(CREATIVE_SUBJECTS)
        if roll < 0.35:
            add(r.choice(CREATIVE_SIMPLE).format(s=s), "creative", "simple", "short", allow_len_mod=False)
        elif roll < 0.8:
            add(r.choice(CREATIVE_MID).format(s=s), "creative", "moderate", "medium")
        else:
            add(r.choice(CREATIVE_HARD).format(s=s), "creative", "complex", "long", allow_len_mod=False)

    # coding
    for _ in range(per_task):
        roll = r.random()
        lang = r.choice(LANGS)
        frame = r.choice(CODE_FRAMES)
        if roll < 0.2:
            add(frame.format(lang=lang, t=r.choice(CODE_SIMPLE)), "coding", "simple", "short")
        elif roll < 0.45:
            add(frame.format(lang=lang, t=r.choice(CODE_MID)), "coding", "moderate", "medium")
        elif roll < 0.62:
            add(frame.format(lang=lang, t=r.choice(CODE_HARD)), "coding", "complex", "long")
        elif roll < 0.72:
            add(frame.format(lang=lang, t=r.choice(CODE_EXPERT)), "coding", "expert", "long", allow_len_mod=False)
        elif roll < 0.92:
            f, tier = r.choice(CODE_SNIPPET_FRAMES)
            add(f.format(c=r.choice(CODE_SNIPPETS)), "coding", tier, "medium", allow_len_mod=False)
        else:
            add(r.choice(CODE_SNIPPET_HARD_FRAMES).format(c=r.choice(CODE_SNIPPETS_HARD)), "coding", "complex", "long",
                allow_len_mod=False)

    # math
    for _ in range(per_task):
        roll = r.random()
        frame = r.choice(MATH_FRAMES)
        if roll < 0.3:
            add(frame.format(q=_math_simple(r)), "math", "simple", "short", imperative=False)
        elif roll < 0.62:
            add(frame.format(q=_math_moderate(r)), "math", "moderate", "medium", imperative=False)
        elif roll < 0.85:
            add(frame.format(q=_math_complex(r)), "math", "complex", "long", imperative=False, allow_len_mod=False)
        else:
            add(r.choice(["{q}", "{q} Give a rigorous proof.", "Can you prove this? {q}"]).format(q=r.choice(MATH_PROOFS)),
                "math", "expert", "long", imperative=False, allow_len_mod=False)

    # reasoning
    for _ in range(per_task):
        roll = r.random()
        frame = r.choice(REASON_FRAMES)
        if roll < 0.2:
            add(frame.format(q=r.choice(PUZZLE_SIMPLE)(r)), "reasoning", "simple", "short", imperative=False)
        elif roll < 0.5:
            add(frame.format(q=r.choice(PUZZLE_MID)(r)), "reasoning", "moderate", "medium", imperative=False)
        elif roll < 0.82:
            add(frame.format(q=r.choice(PUZZLE_HARD)(r)), "reasoning", "complex", "long", imperative=False, allow_len_mod=False)
        else:
            add(frame.format(q=r.choice(PUZZLE_EXPERT)), "reasoning", "expert", "long", imperative=False, allow_len_mod=False)

    # analysis
    for _ in range(per_task):
        roll = r.random()
        a, b = r.choice(COMPARE_PAIRS)
        t, d = r.choice(ANALYZE_THINGS), r.choice(DATA_SERIES)
        if roll < 0.45:
            add(r.choice(ANALYSIS_MID).format(a=a, b=b, t=t), "analysis", "moderate", "medium")
        elif roll < 0.85:
            add(r.choice(ANALYSIS_HARD).format(a=a, b=b, t=t, d=d), "analysis", "complex", "long", allow_len_mod=False)
        else:
            add(r.choice(ANALYSIS_EXPERT).format(t=t), "analysis", "expert", "long", allow_len_mod=False)

    from .corpus_extra import extra_examples
    for _ in range(2):
        for text, task, tier, length, imperative in extra_examples(r, LANGS, HUMAN_LANGS, CREATIVE_SUBJECTS,
                                                                    TRANSLATE_SENTENCES, COUNTRIES):
            add(text, task, tier, length, imperative=imperative, allow_len_mod=False)

    seen, unique = set(), []
    for ex in out:
        if ex[0] not in seen:
            seen.add(ex[0])
            unique.append(ex)
    r.shuffle(unique)
    return unique
