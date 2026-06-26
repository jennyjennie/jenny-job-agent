SEARCH_KEYWORDS = [
    "ML Engineer",
    "Machine Learning Engineer",
    "AI Engineer",
    "LLM Engineer",
    "Research Engineer",
    "Applied Scientist",
    "NLP Engineer",
    "Software Engineer Machine Learning",
    "Software Engineer AI",
    "Backend Engineer",
    "Software Developer",
]

LOCATIONS = [
    "Remote",
    "Los Angeles, CA",
    "San Francisco, CA",
    "Seattle, WA",
    "New York, NY",
    "Austin, TX",
]

JOB_SITES = ["linkedin", "indeed", "zip_recruiter"]

RESULTS_PER_SITE = 50
HOURS_OLD = 26  # slightly over 24h to avoid gaps at cron boundary

EXCLUDE_PHRASES = [
    "us citizen only",
    "u.s. citizen only",
    "citizenship required",
    "must be a us citizen",
    "must be a u.s. citizen",
    "security clearance",
    "top secret",
    "secret clearance",
    "ts/sci",
    "no sponsorship",
    "will not sponsor",
    "sponsorship not available",
    "unable to sponsor",
    "cannot sponsor",
    "must be authorized to work in the us without",
    "must be authorized to work in the united states without",
    "no visa sponsorship",
    "10+ years",
    "10 or more years",
    "8+ years",
    "7+ years",
    "senior staff engineer",
    "principal engineer",
    "distinguished engineer",
    "staff research scientist",
    "green card holder",
    "permanent resident only",
]

VISA_POSITIVE_SIGNALS = [
    "opt",
    "cpt",
    "opt/cpt",
    "sponsorship available",
    "will sponsor",
    "visa sponsorship",
    "h1b",
    "h-1b",
    "open to international",
    "international candidates welcome",
    "f-1",
    "f1 visa",
    "entry level",
    "new grad",
    "new graduate",
    "junior",
    "0-2 years",
    "0-3 years",
    "1-3 years",
    "recent graduate",
]

JENNY_SKILLS = [
    # Languages
    "python", "c++", "java", "javascript", "sql", "bash", "shell",
    # ML / DL frameworks
    "pytorch", "tensorflow", "tflite", "hugging face", "huggingface",
    "scikit-learn", "sklearn", "transformers",
    # LLM / AI
    "llm", "large language model", "fine-tuning", "fine tuning",
    "inference optimization", "quantization", "distillation",
    "prompt engineering", "rag", "retrieval augmented generation",
    "tool calling", "function calling", "claude", "anthropic",
    "openai", "gpt", "chatgpt", "llama",
    # MLOps / Infra
    "mlflow", "wandb", "weights & biases", "experiment tracking",
    "training pipeline", "data pipeline", "model serving",
    "fastapi", "docker", "linux", "git", "android",
    # Research
    "neurips", "acl", "emnlp", "iclr", "icml",
    "research", "publication", "paper", "first author",
    # Soft/general
    "machine learning", "deep learning", "natural language processing", "nlp",
    "computer vision", "reinforcement learning", "multimodal",
]

ML_ROLE_SIGNALS = [
    "machine learning", "deep learning", "artificial intelligence",
    "large language model", "llm", "foundation model", "generative ai",
    "nlp", "natural language", "computer vision", "reinforcement learning",
    "model training", "model serving", "model deployment", "mlops",
    "ml platform", "ml infrastructure", "applied scientist",
    "research engineer", "research scientist", "ai research",
    "recommendation system", "search ranking", "multimodal",
]
