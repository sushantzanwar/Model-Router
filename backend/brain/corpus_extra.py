"""
corpus_extra.py - Additional labelled training examples (natural phrasings)
----------------------------------------------------------------------------
Broadens the training distribution with naturally phrased requests so the network
learns intent from many surface forms rather than a few templates.
Yields (text, task, tier, length, imperative) tuples.
"""

import random
from typing import Iterator, Tuple

Raw = Tuple[str, str, str, str, bool]

MECHANISMS_BASIC = [
    "a toaster", "a light bulb", "a thermometer", "a doorbell", "a zipper", "a compass", "a flashlight",
    "a vending machine", "an elevator", "a smoke detector", "a ceiling fan", "a washing machine", "a calculator",
    "a credit card", "a QR code", "a remote control", "a parachute", "a thermos flask", "a piano", "a lock and key",
]
MECHANISMS_MID = [
    "a jet engine", "a nuclear power plant", "noise cancelling earbuds", "a stock exchange", "an electric car battery",
    "a search engine", "a hash table", "a CPU cache", "a transistor", "a 3D printer", "wifi", "bluetooth",
    "a credit score", "a central bank", "a touchscreen", "an MRI scanner", "a heat pump", "the kidneys",
    "an operating system scheduler", "a car's anti-lock braking system", "a digital camera sensor", "a VPN",
    "two-factor authentication", "a mortgage", "an insurance policy", "a hybrid car", "a wind turbine",
    "the lymphatic system", "a recommendation algorithm", "a content delivery network", "an index fund",
    "a password hash", "a database transaction", "a garbage collector", "a load balancer", "an electric guitar pickup",
    "the human eye", "the digestive system", "a hearing aid", "a lithium-ion battery", "a radar", "a satellite in orbit",
    "the electoral college", "a tariff", "an MP3 encoder", "a version control system like git",
]
MECHANISMS_DEEP = [
    "the Higgs field", "a Bose-Einstein condensate", "the Raft consensus protocol", "a Bloom filter's false positive rate",
    "homomorphic encryption", "the Diffie-Hellman key exchange's security", "CRISPR-Cas9 gene editing at the molecular level",
    "a quantum computer's error correction", "the Black-Scholes model's assumptions", "garbage-first (G1) collection in the JVM",
    "a Merkle tree in distributed systems", "Hawking radiation", "the Lamb shift", "variational autoencoders",
    "the Kalman filter", "a skip list's expected complexity", "lattice-based cryptography", "TCP congestion control (CUBIC vs BBR)",
    "epigenetic inheritance", "the photoelectric effect and its quantum interpretation", "mitochondrial ATP synthase",
    "the yield curve inversion as a recession signal", "spontaneous symmetry breaking", "the P vs NP problem",
    "reinforcement learning from human feedback", "the Fourier transform's role in signal processing",
    "neutrino oscillation", "the Byzantine generals problem", "log-structured merge trees", "vector clocks",
    "the central limit theorem", "dark matter evidence from galaxy rotation curves", "the Coriolis effect on weather systems",
    "the endosymbiotic theory", "two-phase locking", "Shannon entropy", "the Navier-Stokes equations", "group theory in particle physics",
]
EXPLAIN_HOW_FRAMES = [
    "How does {m} work?", "how does {m} work", "Can you explain how {m} works?", "What happens inside {m}?",
    "What's the mechanism behind {m}?", "Describe how {m} works.", "Walk me through how {m} functions.",
    "I've always wondered how {m} works.", "Explain the working of {m}.", "How exactly does {m} do its job?",
    "Break down how {m} works step by step.", "What is going on inside {m} when it runs?",
]
EXPLAIN_PLAIN_FRAMES = [
    "Explain {m} to a non-technical person.", "Can you explain {m} to a beginner?", "Explain {m} in plain English.",
    "Describe {m} for someone with no background.", "Give me a simple explanation of {m}.", "ELI5: {m}",
    "Explain {m} like I'm 10 years old.", "What is {m}, in simple words?",
]
EXPLAIN_DEEP_FRAMES = [
    "Explain {m} in depth.", "Explain the theory behind {m}.", "How does {m} work, at a rigorous level?",
    "Give a technical explanation of {m}.", "Explain {m}, including the math behind it.", "What is {m} and why does it matter?",
    "Explain {m} to a graduate student.", "Describe {m} and its underlying principles.",
]
WHY_CLAUSES = [
    "do we yawn", "do onions make us cry", "does bread rise", "do stars twinkle", "does metal feel colder than wood",
    "do we dream", "does the moon look bigger near the horizon", "do our ears pop on airplanes", "is the sea blue",
    "do cats purr", "does popcorn pop", "do we get goosebumps", "does hot air rise", "do birds migrate",
    "do we have different blood types", "does coffee keep us awake", "do mirrors flip left and right but not up and down",
    "does the economy have recessions", "do prices go up over time", "do bubbles form in soda", "do leaves fall in autumn",
    "does iron rust", "do we need vitamins", "is the night sky dark", "do some people need glasses", "does salt melt ice",
    "do planes leave white trails", "do we hiccup", "do zebras have stripes", "do volcanoes form near plate boundaries",
]
WHY_FRAMES = ["Why {c}?", "why {c}", "Can you explain why {c}?", "Why exactly {c}?", "I'm curious, why {c}?", "Explain why {c}."]
DIFF_PAIRS = [
    ("a virus", "bacteria"), ("weather", "climate"), ("an LLC", "a corporation"), ("HTTP", "HTTPS"), ("a CPU", "a GPU"),
    ("speed", "velocity"), ("a stock", "a bond"), ("mitosis", "meiosis"), ("affect", "effect"), ("a compiler", "an interpreter"),
    ("RAM", "a hard drive"), ("a crocodile", "an alligator"), ("socialism", "communism"), ("machine learning", "AI"),
    ("a hurricane", "a tornado"), ("debit", "credit"), ("a list", "a tuple in Python"), ("latency", "bandwidth"),
]
DIFF_FRAMES = ["What's the difference between {a} and {b}?", "How is {a} different from {b}?", "{a} vs {b}, what's the difference?",
               "Explain the difference between {a} and {b}."]

FACT_EXTRA = [
    "Who directed Jurassic Park?", "When was the Magna Carta signed?", "Where is Mount Kilimanjaro?", "What is the deepest lake in the world?",
    "How many strings does a violin have?", "Who was the first female prime minister of the UK?", "What year did the internet go public?",
    "Which ocean is the Bermuda Triangle in?", "What's the population of Tokyo?", "Who wrote The Odyssey?", "How old is the universe?",
    "When did the first humans land on the moon?", "What's the tallest animal?", "Which country produces the most coffee?",
    "Who invented the light bulb?", "What is the melting point of iron?", "What's the biggest stadium in the world?",
    "Which is the largest country in Africa?", "How many teeth does an adult human have?", "Who discovered gravity?",
    "What is the national sport of Canada?", "When does summer start in Australia?", "What is the most spoken language in Africa?",
    "How long is a marathon?", "Which bird can fly backwards?", "Who was Nelson Mandela?", "What does GDP stand for?",
    "What's the boiling point of ethanol?", "How many squares are on a chessboard?", "Where was pizza invented?",
    "who won the 2018 world cup", "who is the founder of tesla", "capital of canada?", "how many states in the US",
    "What is the largest organ in the human body?", "Which metal is liquid at room temperature?", "What does RAM stand for?",
]
FACT_LIST_EXTRA = [
    "Name all the countries in {region}.", "List the oceans of the world.", "Which countries use the euro?",
    "What are the primary colors?", "Name the members of the Beatles.", "List the planets that have moons.",
    "Which countries have won the World Cup?", "Name the largest moons of Saturn.", "List the Shakespeare tragedies.",
    "What are the official languages of {country}?", "Which US states border Canada?", "Name every Harry Potter book in order.",
    "List the bones in the human arm.", "Which elements are halogens?", "Name the Olympic host cities since 2000.",
]
REGIONS = ["Europe", "Asia", "Africa", "Central America", "the Middle East", "Scandinavia", "Oceania", "the Caribbean"]

CHAT_PEOPLE = ["roommate", "coworker", "boss", "best friend", "sister", "brother", "partner", "neighbor", "classmate", "mom", "dad"]
CHAT_BEHAVIORS = ["keeps borrowing my stuff without asking", "ignores my texts", "takes credit for my work", "is always late",
                  "keeps criticizing my choices", "plays loud music at night", "forgot my birthday", "is moving away soon",
                  "wants me to lend them money", "keeps interrupting me in meetings"]
CHAT_FEELINGS = ["don't know how to bring it up", "feel hurt", "am getting really annoyed", "feel awkward about it",
                 "don't want to ruin the relationship", "am losing patience"]
CHAT_EXTRA_SIMPLE = [
    "howdy", "hola", "namaste", "good to see you", "hey how's it going", "sup buddy", "u there?", "back again lol",
    "that's awesome", "perfect, thank you", "thanks a ton", "appreciate it!", "no worries", "sounds good", "got it",
    "cool cool", "ok thanks", "you're the best", "what's new?", "how was your weekend?", "tell me something interesting",
    "are you human?", "who made you?", "can you hear me?", "what are you?", "hello friend", "I'm so tired today",
    "today was a good day", "I passed my exam!!", "guess what", "ugh mondays", "what do you think about me?",
    "you're so clever", "ur funny lol", "you're really helpful", "nice work buddy", "you're kinda cool", "love u bot",
    "you're smarter than my friends haha", "thank u so much!!", "big thanks for earlier", "that's brilliant, cheers",
    "well done!", "you nailed it", "lol ok", "hmm ok", "alright then", "talk later", "catch you later", "brb",
    "gtg bye", "night night", "morning sunshine", "yo what's good", "how are things", "long time no see",
    "do you sleep?", "do you get bored?", "what do you like to do?", "are you happy?", "can you be my friend?",
    "what should we talk about?", "first time here, hi", "just saying hi", "hey it's me again",
]

SUMMARY_PARAS_EXTRA = [
    "The startup raised $12 million in Series A funding led by a major venture firm. The money will be used to expand its engineering team and enter the European market. The founders said profitability is expected within three years.",
    "Local residents protested the planned highway expansion, arguing it would destroy wetlands and increase noise. Officials maintain the project will cut commute times by twenty minutes. A public hearing is scheduled for next month.",
    "The museum's new exhibition features over 200 works by impressionist painters, many never shown publicly before. Curators spent four years negotiating loans from private collectors. Tickets are already sold out for the opening weekend.",
    "Dear customer, your subscription will renew automatically on the 15th. If you wish to cancel, please do so at least 48 hours before renewal. Your current plan includes unlimited streaming and two simultaneous devices.",
    "The study followed 5,000 adults for ten years and found that those who walked at least 7,000 steps a day had a 40% lower risk of early death. The benefits plateaued above 10,000 steps. Researchers note the results are observational.",
    "Team lunch is moved to Friday at 1pm at the Italian place downtown. Please RSVP by Wednesday so we can book a table. Vegetarian options are available.",
    "The central bank held interest rates steady at 5.25%, citing cooling inflation but a still-tight labor market. Policymakers signaled that cuts could begin later in the year if price growth continues to slow.",
    "The software update introduces dark mode, faster sync, and a redesigned settings page. It also fixes a bug that caused crashes on older devices. The update will roll out gradually over the next two weeks.",
    "During the expedition, the climbers faced sudden storms near the summit and had to wait three days at high camp. Two members turned back due to altitude sickness. The remaining four reached the top on the morning of the fifth day.",
    "Our customer survey received 2,300 responses. Most users praised the app's speed, but many complained about confusing navigation and too many notifications. The most requested feature was offline mode.",
    "The court ruled that the company violated consumer protection laws by hiding fees in its terms of service. It must refund affected customers and pay a $3 million fine. The company said it will appeal.",
    "In the final match, the underdog team came back from two goals down to win 3-2 in extra time. Their captain scored the winning goal with a header in the 112th minute, sending fans into celebration.",
    "The recipe calls for flour, sugar, eggs, butter, and a pinch of salt. Mix the dry ingredients first, then fold in the wet ones. Bake at 180 degrees for 25 minutes or until golden brown.",
    "Volunteers planted more than 10,000 trees along the riverbank over the weekend. The project aims to reduce erosion and restore habitat for native birds. Organizers hope to double the number next year.",
]
SUMMARY_INSTR_EXTRA = [
    "Summarize this in two lines:", "Give me a quick summary:", "Can you sum this up?", "Short version please:",
    "What's this about? Summarize:", "Make this shorter:", "Key takeaways from the text below:", "Summarize for a busy executive:",
    "Write a brief abstract of this:", "In a nutshell, what does this say?", "Turn this into a few bullet points:",
    "Give me the highlights of this:", "Distill this into its main ideas:", "Please give a concise summary of the following article.",
]

TRANSLATE_EXTRA_FRAMES = [
    "Convert this to {lang}: {s}", "Put this into {lang}: {s}", "Say this in {lang}: {s}", "{s} -> {lang}",
    "in {lang} please: {s}", "Render this sentence in {lang}: {s}", "Could you give me the {lang} for '{s}'?",
    "What's the {lang} word for {w}?", "How do I say {w} in {lang}?",
]
TRANSLATE_WORDS = ["thank you", "goodbye", "friend", "cheers", "I'm sorry", "excuse me", "delicious", "beautiful", "water", "help"]
TRANSLATE_PARA_EXTRA_FRAMES = [
    "Convert this paragraph to {lang}:\n{p}", "Translate the text below into {lang}.\n{p}", "Can you translate this message to {lang}? {p}",
    "Rewrite this in {lang}:\n{p}", "I need this in {lang} for a client:\n{p}",
]

CREATIVE_OCCASIONS = ["my brother's wedding", "my dad's retirement", "a farewell party for a coworker", "my best friend's 30th birthday",
                      "our 10th anniversary", "a graduation ceremony", "a charity fundraiser", "my grandmother's funeral", "a team kickoff"]
CREATIVE_MID_EXTRA = [
    "Write a speech for {o}.", "Write a toast for {o}.", "Write a heartfelt card message for {o}.", "Draft a eulogy for {o}.",
    "Write a short poem to read at {o}.", "Write a rap about {s}.", "Write a children's story about {s}.",
    "Write an ad script for a new energy drink.", "Write a monologue for a villain who loves {s}.", "Write a diary entry from the perspective of {s}.",
    "Write a short scary story about {s}.", "Write wedding vows that mention {s}.", "Write a ballad about {s}.",
    "Write a letter from a soldier to his family about {s}.", "Write a scene where two old friends reunite at {o}.",
]
CREATIVE_SIMPLE_EXTRA = [
    "Give me {n} name ideas for a {biz}.", "Come up with a tagline for a {biz}.", "Write a one-liner about {s}.",
    "Suggest a title for a song about {s}.", "Write a tweet announcing our new {biz}.", "Give me a pickup line about {s}.",
    "Write a cute caption for a photo of {s}.", "Write a 2-sentence horror story about {s}.",
]
BUSINESSES = ["coffee shop", "bakery", "yoga studio", "tech startup", "dog grooming salon", "bookstore", "food truck", "gaming channel", "plant nursery"]
CREATIVE_HARD_EXTRA = [
    "Invent a complete fictional religion for a desert civilization, including its creation myth, rituals, clergy hierarchy and a schism.",
    "Create an original alien species with its biology, social structure, language rules, and how its environment shaped its culture.",
    "Write a three-act screenplay outline about {s} with character arcs, a midpoint reversal and thematic symbolism.",
    "Write a 5000-word novelette about {s} with an unreliable narrator and two interleaved timelines that converge at the end.",
    "Design a tabletop RPG setting about {s}: geography, factions, economy, magic or technology rules, and five adventure hooks.",
    "Write a sonnet sequence of seven connected sonnets about {s} where the last line of each becomes the first of the next.",
    "Build a detailed fictional city: its districts, history, politics, underground economy and three key characters who embody its conflicts.",
]

CODE_TOOLS_SIMPLE = [
    "undo the last git commit", "make a div fill the whole screen", "list running docker containers", "find files larger than 100MB in linux",
    "add a column to a SQL table", "create a python virtual environment", "install a package with npm", "write a regex for phone numbers",
    "make text bold in HTML", "rename a git branch", "kill the process using port 3000", "parse JSON in python", "center an image with CSS",
    "change the font of a webpage", "check my node version", "delete a branch on GitHub", "add a favicon to my site",
    "comment out multiple lines in VS Code", "make a button rounded in CSS", "concatenate strings in bash", "sum a column in Excel",
    "create a table in HTML", "count rows in a SQL table", "get the length of an array in JavaScript", "copy a file in linux",
    "set an environment variable on windows", "split a string by comma in python", "make a navbar sticky", "import a CSV in pandas",
]
CODE_TOOLS_MID = [
    "set up a CI pipeline with GitHub Actions that runs tests on every push", "write a docker-compose file for a web app with Postgres and Redis",
    "configure nginx as a reverse proxy with HTTPS", "make a responsive grid layout with CSS grid", "write a cron job that cleans old logs",
    "set up ESLint and Prettier in a TypeScript project", "deploy a Flask app to a Linux server with gunicorn", "write a pandas pipeline that cleans and merges two CSVs",
    "create a SQL view that joins orders and customers", "write a Makefile for a C project", "configure CORS on an Express server",
    "add pagination to a REST API", "implement dark mode toggle in React", "write a GitHub Actions workflow that builds a Docker image",
]
CODE_FRAMES_TOOLS = ["How do I {t}?", "how to {t}", "What's the command to {t}?", "Quick question, how can I {t}?", "{t} - how?",
                     "Show me how to {t}.", "What's the easiest way to {t}?"]
CODE_ERRORS = [
    "TypeError: Cannot read properties of undefined (reading 'map')", "ModuleNotFoundError: No module named 'requests'",
    "Segmentation fault (core dumped)", "Access to fetch has been blocked by CORS policy", "java.lang.NullPointerException at Main.main(Main.java:14)",
    "IndexError: list index out of range", "error[E0382]: borrow of moved value: `v`", "SyntaxError: Unexpected token '<' in JSON at position 0",
    "fatal: refusing to merge unrelated histories", "ERROR 1045 (28000): Access denied for user 'root'@'localhost'",
    "KeyError: 'id'", "npm ERR! code ERESOLVE unable to resolve dependency tree", "panic: runtime error: invalid memory address or nil pointer dereference",
    "UnboundLocalError: local variable 'count' referenced before assignment", "Uncaught (in promise) TypeError: Failed to fetch",
    "ConnectionRefusedError: [Errno 111] Connection refused", "Error: listen EADDRINUSE: address already in use :::3000",
]
CODE_ERROR_FRAMES = ["I'm getting this error: {e}. How do I fix it?", "{e}\nwhat does this mean?", "Help! {e}",
                     "Why am I seeing '{e}'?", "My app crashes with {e}", "how to fix {e}"]
CODE_REGEX = [r"^\d{3}-\d{3}-\d{4}$", r"(?<=@)[\w.]+", r"^[A-Z][a-z]+(\s[A-Z][a-z]+)*$", r"\b\w+@\w+\.\w{2,}\b", r"^(?:\d{1,3}\.){3}\d{1,3}$"]
CODE_EXTRA_HARD = [
    "Implement a bounded thread pool in {lang} with work stealing and graceful shutdown.",
    "Write a {lang} library for consistent hashing with replication and rebalancing.",
    "Implement an in-memory database with B-tree indexes and range queries in {lang}.",
    "Build a scheduler in {lang} that runs delayed and recurring jobs with persistence and retries.",
    "Implement a circuit breaker with half-open state and metrics in {lang}.",
]
CODE_EXPERT_PHRASES = [
    "Build a distributed {thing} with exactly-once delivery, leader election and durable storage in {lang}.",
    "Write a full compiler front-end in {lang}: tokenizer, recursive-descent parser, AST, type checking and scope analysis.",
    "Implement a replicated state machine in {lang} on top of Multi-Paxos, with log compaction and membership changes.",
    "Create a high-performance async runtime in {lang} with an epoll-based reactor and a work-stealing executor.",
    "Develop a database storage engine in {lang} with an LSM tree, compaction strategies and snapshot isolation.",
    "Build a container orchestrator scheduler in {lang} with bin-packing, preemption and failure recovery.",
    "Write a virtual machine with a bytecode interpreter, a mark-and-sweep GC and a REPL in {lang}.",
    "Engineer a sharded {thing} in {lang} with consistent hashing, hinted handoff and anti-entropy repair.",
]
CODE_EXTRA_EXPERT = [
    "Build a distributed {thing} in {lang} with replication, leader election, and linearizable reads.",
    "Write an optimizing compiler pass in {lang} that performs SSA construction and dead code elimination.",
    "Implement a production-grade {thing} in {lang} that survives node crashes and network partitions.",
]
EXPERT_THINGS = ["message queue", "lock service", "object store", "time-series database", "search index", "cache cluster"]

PROOF_STATEMENTS = [
    "the sum of two even numbers is even", "n^3 - n is divisible by 6 for every integer n", "1 + 2 + ... + n = n(n+1)/2",
    "2^n > n^2 for all n >= 5", "the square of an odd number is odd", "there is no rational number whose square is 2",
    "every integer greater than 1 has a prime factor", "the sum of the angles in a triangle is 180 degrees",
    "if a divides b and b divides c then a divides c", "the composition of two injective functions is injective",
    "sqrt(5) is irrational", "log2(3) is irrational", "the product of two consecutive integers is even",
    "every tree with n vertices has n - 1 edges", "a graph is bipartite iff it has no odd cycle",
    "the intersection of two subgroups is a subgroup", "the inverse of a bijection is a bijection",
    "the sum of the first n odd numbers is n^2", "for all real x, x^2 >= 0", "there are infinitely many primes of the form 4k + 3",
    "the limit of 1/n as n goes to infinity is 0", "every convergent sequence is bounded", "the determinant of a product is the product of determinants",
]
PROOF_FRAMES = ["Prove that {p}.", "Show that {p}.", "Prove by induction that {p}.", "Give a formal proof that {p}.",
                "Can you prove {p}?", "Demonstrate rigorously that {p}."]
MATH_WORD_MID = [
    lambda r: f"How many diagonals does a polygon with {r.randint(5, 20)} sides have?",
    lambda r: f"What is the sum of the interior angles of a {r.randint(5, 12)}-sided polygon?",
    lambda r: f"In how many ways can you choose {r.randint(2, 5)} students from a class of {r.randint(10, 30)}?",
    lambda r: f"A recipe needs {r.randint(2, 5)} cups of flour for {r.randint(8, 16)} cookies. How much flour for {r.randint(20, 60)} cookies?",
    lambda r: f"If a population grows {r.randint(2, 9)}% per year, how long until it doubles?",
    lambda r: f"A ladder {r.randint(5, 15)} m long leans against a wall with its base {r.randint(1, 4)} m away. How high does it reach?",
    lambda r: f"Two pipes fill a tank in {r.randint(2, 6)} and {r.randint(3, 9)} hours. How long together?",
    lambda r: f"What is the expected value of rolling two dice and taking the maximum?",
    lambda r: f"Find the volume of a cylinder with radius {r.randint(2, 10)} and height {r.randint(3, 20)}.",
]
MATH_SIMPLE_EXTRA = [
    lambda r: f"what's {r.randint(100, 999)} divided by {r.randint(2, 9)}", lambda r: f"Convert {r.randint(1, 9)}/{r.randint(10, 16)} to a decimal",
    lambda r: f"What is {r.randint(2, 9)} to the power of {r.randint(2, 5)}?", lambda r: f"How many minutes are in {r.randint(2, 30)} hours?",
    lambda r: f"Is {r.randint(100, 999)} divisible by 3?", lambda r: f"What is the perimeter of a square with side {r.randint(2, 50)}?",
    lambda r: f"{r.randint(10, 99)}% as a fraction", lambda r: f"What's the cube root of {r.choice([8, 27, 64, 125, 216, 343, 1000])}?",
]

PUZZLE_CLASSIC_HARD = [
    "There are three switches outside a closed room with three lamps inside. You may enter the room once. How do you match each switch to its lamp?",
    "One guard always lies and one always tells the truth. One door leads out, the other to doom. What single question finds the exit?",
    "You have two ropes that each burn in exactly an hour but unevenly. How do you measure 45 minutes?",
    "With a 3-litre and a 5-litre jug, how do you measure exactly 4 litres of water?",
    "Three people check into a hotel room for $30, the manager refunds $5 and the bellboy keeps $2. Where is the missing dollar?",
    "A brother and sister have a total of N siblings with the condition that each boy has twice as many sisters as brothers. Work out the family size.",
    "Ten pirates divide 100 gold coins by proposal and majority vote. What does the most senior pirate propose, and why?",
    "You must identify the one poisoned bottle among 1000 using 10 test strips that take a day to show results. How?",
    "Three logicians walk into a bar. The bartender asks if they all want beer. The first says I don't know, the second says I don't know, the third says yes. Explain the logic.",
]
RIDDLES = [
    "A man lives on the 10th floor but takes the elevator only to the 7th floor and walks the rest unless it's raining. Why?",
    "What has keys but can't open locks?", "The more you take, the more you leave behind. What am I?",
    "A woman shoots her husband, holds him underwater for five minutes, then hangs him. Later they go out to dinner. How?",
    "What can travel around the world while staying in a corner?", "I speak without a mouth and hear without ears. What am I?",
    "A man walks into a bar and asks for water. The bartender pulls out a gun. The man says thank you and leaves. Why?",
    "What gets wetter the more it dries?", "Forward I am heavy, backward I am not. What am I?",
    "A cowboy rode into town on Friday, stayed three days, and left on Friday. How?",
    "What comes once in a minute, twice in a moment, and never in a thousand years?",
    "Two fathers and two sons go fishing and catch three fish, yet each gets one. How?",
    "A rooster lays an egg on top of a barn roof. Which way does it roll?",
    "How can a man go eight days without sleep?", "What building has the most stories?",
]
FAMILY_PUZZLES = [
    lambda r: "Who is my mother's brother's son to me?", lambda r: "If Anna is Ben's sister and Ben is Carl's father, what is Anna to Carl?",
    lambda r: f"{r.choice(['Pointing to a photo', 'Looking at a portrait'])}, a man says: 'Brothers and sisters I have none, but that man's father is my father's son.' Who is in the photo?",
    lambda r: "A girl has as many brothers as sisters, but each brother has only half as many brothers as sisters. How many brothers and sisters are in the family?",
    lambda r: "How is my father's only daughter's son related to me if I am female?",
]
DIRECTION_PUZZLES = [
    lambda r: f"I walk {r.randint(2, 9)} km north, then {r.randint(2, 9)} km east, then {r.randint(2, 9)} km south. Which direction am I from the start?",
    lambda r: f"If you face {r.choice(['east', 'west', 'south', 'north'])} and turn {r.choice(['left', 'right'])} {r.randint(1, 3)} times, where are you facing?",
    lambda r: "A clock shows 3:15. What is the angle between the hour and minute hands?",
    lambda r: f"If the {r.randint(2, 9)}th of a month is a {r.choice(DAYS_)}, what day is the {r.randint(15, 28)}th?",
]
DAYS_ = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SEQ_PUZZLES = [
    lambda r: f"Find the odd one out: {', '.join(str(x) for x in r.sample([4, 9, 16, 25, 36, 49, 50, 64], 5))}",
    lambda r: f"What's the next number: {r.randint(1, 3)}, {r.randint(4, 6)}, {r.randint(9, 12)}, {r.randint(16, 20)}, ?",
    lambda r: "Which word doesn't belong: dog, cat, eagle, hamster?", lambda r: "Complete the pattern: A, C, F, J, O, ?",
    lambda r: "What comes next: J, F, M, A, M, J, ?",
]

ANALYSIS_PROJECTS = ["migrating to Kubernetes", "launching in a new country", "acquiring a competitor", "switching our CRM vendor",
                     "rewriting the backend in Rust", "opening a second restaurant", "moving the data center to the cloud",
                     "outsourcing customer support", "adopting a four-day week", "raising prices by 15%", "going IPO next year"]
ANALYSIS_EXTRA_MID = [
    "Should I {c}? Give me the pros and cons.", "Is it worth {c}? Weigh it up.", "Help me decide whether {c} makes sense.",
    "Review the advantages and disadvantages of {c}.", "What are the trade-offs of {c}?",
]
ANALYSIS_CHOICES = ["buy a used car or a new one", "learn Rust or Go next", "rent in the city or buy in the suburbs", "do an MBA",
                    "take a gap year", "switch careers into data science", "get a dog", "move abroad for work", "use Firebase for my startup"]
ANALYSIS_EXTRA_HARD = [
    "Assess the risks of {p} and propose mitigations.", "Evaluate the business case for {p}, including costs, risks and expected ROI.",
    "Critically examine our plan of {p}. What could go wrong?", "Analyze the stakeholder impact of {p}.",
    "Critique this statement and identify logical fallacies: '{claim}'", "Evaluate the evidence for the claim that {claim2}.",
    "Interpret these numbers and explain the trend: {d}", "Analyze customer churn given: {d}",
]
CLAIMS = ["Everyone who works hard becomes rich", "Social media is the main cause of teen depression", "AI will replace all programmers within five years",
          "Raising taxes always hurts the economy", "Organic food is healthier in every way", "Remote workers are less productive"]
CLAIMS2 = ["remote work increases productivity", "minimum wage increases cause unemployment", "screen time harms children's sleep",
           "electric vehicles are greener over their lifetime", "standing desks improve health"]
DATA_EXTRA = ["visits 10k, 12k, 15k, 9k, 16k over five weeks", "revenue up 20% but profit down 5% year over year",
              "NPS fell from 45 to 31 after the redesign", "support tickets doubled while sales grew 10%",
              "churn: Jan 3%, Feb 3.5%, Mar 5%, Apr 4.8%", "average order value 52, 49, 47, 44 dollars by quarter"]


BOOKS = ["War and Peace", "1984", "The Great Gatsby", "To Kill a Mockingbird", "Moby Dick", "Don Quixote", "The Hobbit",
         "Crime and Punishment", "Wuthering Heights", "The Catcher in the Rye", "One Hundred Years of Solitude", "Hamlet",
         "The Alchemist", "Brave New World", "Jane Eyre", "Frankenstein", "Dracula", "Les Miserables", "The Odyssey", "Beloved"]
MOVIES = ["Titanic", "Inception", "The Godfather", "Jaws", "Avatar", "Pulp Fiction", "Parasite", "The Matrix", "Casablanca",
          "Interstellar", "Gladiator", "Spirited Away", "Oppenheimer", "Schindler's List", "Psycho"]
EVENTS = ["the French Revolution", "the Moon landing", "the fall of the Berlin Wall", "the Chernobyl disaster",
          "the first World War", "the Apollo 11 mission", "the Wright brothers' first flight", "the signing of the Declaration of Independence",
          "the Battle of Hastings", "the Great Fire of London", "the 2008 financial crisis", "the launch of Sputnik",
          "the Voyager 1 launch", "the first Olympic Games", "the invention of the printing press", "the Cuban Missile Crisis"]
INVENTIONS = ["the telephone", "the airplane", "the World Wide Web", "the light bulb", "penicillin", "the printing press",
              "the steam engine", "the transistor", "the radio", "the vaccine for polio", "the bicycle", "the smartphone"]
PLACES = ["Machu Picchu", "the Taj Mahal", "Angkor Wat", "Petra", "Stonehenge", "the Sahara Desert", "Lake Baikal",
          "Mount Everest", "the Amazon rainforest", "the Dead Sea", "Easter Island", "the Colosseum", "Uluru", "Victoria Falls"]
COMPETITIONS = ["the World Cup", "the Champions League", "Wimbledon", "the Super Bowl", "the Tour de France", "the NBA Finals",
                "the Cricket World Cup", "the Nobel Prize in Physics", "the Oscar for Best Picture", "Eurovision"]
FACT_ENTITY_FRAMES = [
    lambda r: f"Who wrote {r.choice(BOOKS)}?", lambda r: f"who is the author of {r.choice(BOOKS)}",
    lambda r: f"Who directed {r.choice(MOVIES)}?", lambda r: f"What year did {r.choice(MOVIES)} come out?",
    lambda r: f"When did {r.choice(EVENTS)} happen?", lambda r: f"What year was {r.choice(EVENTS)}?",
    lambda r: f"When was {r.choice(INVENTIONS)} invented?", lambda r: f"Who invented {r.choice(INVENTIONS)}?",
    lambda r: f"Where is {r.choice(PLACES)}?", lambda r: f"Which country is {r.choice(PLACES)} in?",
    lambda r: f"Who won {r.choice(COMPETITIONS)} in {r.randint(1970, 2024)}?", lambda r: f"How many times has Brazil won {r.choice(COMPETITIONS)}?",
    lambda r: f"How many moons does {r.choice(['Mars', 'Saturn', 'Neptune', 'Uranus', 'Pluto'])} have?",
    lambda r: f"How tall is {r.choice(PLACES + ['the Burj Khalifa', 'the Statue of Liberty', 'Big Ben'])}?",
    lambda r: f"When was the first {r.choice(['iPod', 'Android phone', 'PlayStation', 'Tesla car', 'email', 'website', 'computer mouse'])} released?",
    lambda r: f"What does {r.choice(['NATO', 'UNESCO', 'SQL', 'USB', 'LASER', 'FIFA', 'WHO', 'GPU', 'AI', 'PDF'])} stand for?",
    lambda r: f"In what year did {r.choice(EVENTS)} take place?", lambda r: f"Who was the first {r.choice(['president of the United States', 'emperor of Rome', 'woman in space', 'person to climb Everest', 'prime minister of India'])}?",
]
LIFE_EVENTS = [
    "I got rejected from the job I really wanted", "my parents are getting divorced", "I lost my job last week",
    "my dog passed away", "I failed an important exam", "I didn't get into my top college", "my best friend moved abroad",
    "I got dumped after three years", "I'm being bullied at school", "my startup just failed", "I feel stuck in my career",
    "I have no friends in my new school", "my coworker humiliated me in a meeting", "I keep comparing myself to others online",
    "my grandfather is in the hospital", "I got a bad performance review", "I can't stop worrying about the future",
]
LIFE_ASKS = ["Can you help me get through this?", "How do I cope?", "I don't know what to do.", "Any words of advice?",
             "How do I stop feeling like a failure?", "Can you talk me through it?", "How do I move on?", "What would you do?"]


def extra_examples(r: random.Random, langs, human_langs, subjects, sentences, countries) -> Iterator[Raw]:
    for _ in range(260):
        roll = r.random()
        if roll < 0.18:
            yield r.choice(EXPLAIN_HOW_FRAMES).format(m=r.choice(MECHANISMS_BASIC)), "explanation", "simple", "medium", False
        elif roll < 0.52:
            yield r.choice(EXPLAIN_HOW_FRAMES).format(m=r.choice(MECHANISMS_MID)), "explanation", "moderate", "medium", False
        elif roll < 0.62:
            yield r.choice(EXPLAIN_DEEP_FRAMES).format(m=r.choice(MECHANISMS_DEEP)), "explanation", "complex", "long", True
        elif roll < 0.7:
            yield (r.choice(EXPLAIN_PLAIN_FRAMES).format(m=r.choice(MECHANISMS_BASIC + MECHANISMS_MID)),
                   "explanation", "simple", "medium", True)
        elif roll < 0.88:
            yield r.choice(WHY_FRAMES).format(c=r.choice(WHY_CLAUSES)), "explanation", "simple", "medium", False
        else:
            a, b = r.choice(DIFF_PAIRS)
            yield r.choice(DIFF_FRAMES).format(a=a, b=b), "explanation", "simple", "medium", False

    for _ in range(200):
        yield r.choice(FACT_ENTITY_FRAMES)(r), "factual", "simple", "short", False

    for _ in range(120):
        yield f"{r.choice(LIFE_EVENTS)} and I feel {r.choice(['awful', 'lost', 'like a failure', 'so alone', 'crushed', 'anxious'])}. {r.choice(LIFE_ASKS)}", "conversation", "moderate", "medium", False

    for _ in range(140):
        if r.random() < 0.65:
            yield r.choice(FACT_EXTRA), "factual", "simple", "short", False
        else:
            yield (r.choice(FACT_LIST_EXTRA).format(region=r.choice(REGIONS), country=r.choice(countries)),
                   "factual", "moderate", "medium", True)

    for _ in range(140):
        if r.random() < 0.55:
            yield r.choice(CHAT_EXTRA_SIMPLE), "conversation", "simple", "short", False
        else:
            yield (f"My {r.choice(CHAT_PEOPLE)} {r.choice(CHAT_BEHAVIORS)} and I {r.choice(CHAT_FEELINGS)}. "
                   f"{r.choice(['What should I do?', 'How do I handle this?', 'Any advice?', 'How would you approach it?'])}",
                   "conversation", "moderate", "medium", False)

    for _ in range(140):
        k = r.choices([1, 2, 3, 4], weights=[4, 3, 2, 1])[0]
        payload = (" " if r.random() < 0.5 else "\n\n").join(r.sample(SUMMARY_PARAS_EXTRA, k))
        words = len(payload.split())
        tier = "simple" if words < 110 else ("moderate" if words < 260 else "complex")
        instr = r.choice(SUMMARY_INSTR_EXTRA)
        text = f"{instr}\n{payload}" if r.random() < 0.6 else f"{instr} {payload}"
        yield text, "summarization", tier, "short" if words < 110 else "medium", True

    for _ in range(140):
        lang = r.choice(human_langs)
        if r.random() < 0.65:
            yield (r.choice(TRANSLATE_EXTRA_FRAMES).format(lang=lang, s=r.choice(sentences), w=r.choice(TRANSLATE_WORDS)),
                   "translation", "simple", "short", True)
        else:
            p = " ".join(r.sample(sentences, r.randint(3, 6)))
            yield r.choice(TRANSLATE_PARA_EXTRA_FRAMES).format(lang=lang, p=p), "translation", "moderate", "medium", True

    for _ in range(160):
        roll = r.random()
        s = r.choice(subjects)
        if roll < 0.3:
            yield (r.choice(CREATIVE_SIMPLE_EXTRA).format(n=r.randint(3, 10), biz=r.choice(BUSINESSES), s=s),
                   "creative", "simple", "short", True)
        elif roll < 0.8:
            yield r.choice(CREATIVE_MID_EXTRA).format(o=r.choice(CREATIVE_OCCASIONS), s=s), "creative", "moderate", "medium", True
        else:
            yield r.choice(CREATIVE_HARD_EXTRA).format(s=s), "creative", "complex", "long", True

    for _ in range(260):
        roll = r.random()
        lang = r.choice(langs)
        if roll < 0.32:
            yield r.choice(CODE_FRAMES_TOOLS).format(t=r.choice(CODE_TOOLS_SIMPLE)), "coding", "simple", "short", False
        elif roll < 0.48:
            yield r.choice(CODE_FRAMES_TOOLS).format(t=r.choice(CODE_TOOLS_MID)), "coding", "moderate", "medium", False
        elif roll < 0.7:
            yield r.choice(CODE_ERROR_FRAMES).format(e=r.choice(CODE_ERRORS)), "coding", "moderate", "medium", False
        elif roll < 0.78:
            yield f"{r.choice(['Explain this regex:', 'What does this regex match?', 'Break down this pattern:'])} {r.choice(CODE_REGEX)}", "coding", "simple", "short", False
        elif roll < 0.9:
            yield r.choice(CODE_EXTRA_HARD).format(lang=lang), "coding", "complex", "long", True
        else:
            pool = CODE_EXTRA_EXPERT if r.random() < 0.4 else CODE_EXPERT_PHRASES
            yield r.choice(pool).format(lang=lang, thing=r.choice(EXPERT_THINGS)), "coding", "expert", "long", True

    for _ in range(220):
        roll = r.random()
        if roll < 0.35:
            yield r.choice(PROOF_FRAMES).format(p=r.choice(PROOF_STATEMENTS)), "math", "expert", "long", False
        elif roll < 0.7:
            yield r.choice(MATH_WORD_MID)(r), "math", "moderate", "medium", False
        else:
            yield r.choice(MATH_SIMPLE_EXTRA)(r), "math", "simple", "short", False

    for _ in range(220):
        roll = r.random()
        if roll < 0.2:
            yield r.choice(PUZZLE_CLASSIC_HARD), "reasoning", "complex", "medium", False
        elif roll < 0.35:
            yield r.choice(RIDDLES), "reasoning", "moderate", "short", False
        elif roll < 0.6:
            yield r.choice(FAMILY_PUZZLES)(r), "reasoning", "moderate", "medium", False
        elif roll < 0.8:
            yield r.choice(DIRECTION_PUZZLES)(r), "reasoning", "simple", "short", False
        else:
            yield r.choice(SEQ_PUZZLES)(r), "reasoning", "simple", "short", False

    for _ in range(200):
        roll = r.random()
        if roll < 0.4:
            yield r.choice(ANALYSIS_EXTRA_MID).format(c=r.choice(ANALYSIS_CHOICES)), "analysis", "moderate", "medium", False
        else:
            yield (r.choice(ANALYSIS_EXTRA_HARD).format(p=r.choice(ANALYSIS_PROJECTS), claim=r.choice(CLAIMS),
                                                         claim2=r.choice(CLAIMS2), d=r.choice(DATA_EXTRA)),
                   "analysis", "complex", "long", True)
