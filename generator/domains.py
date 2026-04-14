"""Shared domain constants for deadends.dev.

Single source of truth for domain keyword mapping and display names.
Used by mcp/server.py, api/mcp.py, and generator/build_site.py.
"""

# Keyword-to-domain mapping for error message classification.
# Used by MCP servers to suggest relevant domains based on error text.
KEYWORD_MAP: dict[str, list[str]] = {
    "python": ["python", "pip", "import", "module", "traceback", "def "],
    "node": ["node", "npm", "require", "module.exports", "package.json"],
    "docker": ["docker", "container", "image", "dockerfile", "daemon"],
    "git": ["git", "commit", "push", "merge", "branch", "repository"],
    "cuda": ["cuda", "gpu", "nvidia", "torch", "tensor", "nccl"],
    "typescript": ["typescript", "ts2", "ts7", "tsconfig", ".ts "],
    "rust": ["rust", "cargo", "borrow", "lifetime", "e0"],
    "go": ["go ", "golang", "goroutine", "go.mod", "go build"],
    "kubernetes": ["kubernetes", "k8s", "kubectl", "pod", "deploy"],
    "terraform": ["terraform", "tf ", "state", "provider", "hcl"],
    "aws": ["aws", "s3", "ec2", "iam", "lambda", "cloudformation"],
    "nextjs": [
        "next.js", "nextjs", "next/", "getserverside",
        "getstaticprops", "app router",
    ],
    "react": ["react", "usestate", "useeffect", "jsx", "component"],
    "pip": ["pip install", "pip3", "pypi", "wheel", "sdist"],
    "java": [
        "java", "jvm", "maven", "gradle", "classnotfound",
        "nullpointerexception", "spring", ".jar",
    ],
    "database": [
        "sql", "mysql", "postgres", "mongodb", "redis",
        "sqlite", "deadlock", "connection pool",
    ],
    "cicd": [
        "github actions", "jenkins", "gitlab ci", "circleci",
        "pipeline", "workflow", "deploy", "artifact",
    ],
    "php": [
        "php", "laravel", "composer", "symfony",
        "artisan", "eloquent",
    ],
    "dotnet": [
        ".net", "dotnet", "c#", "csharp", "nuget",
        "aspnet", "blazor", "entity framework",
    ],
    "networking": [
        "connection refused", "timeout", "dns", "ssl",
        "tls", "certificate", "econnrefused", "socket",
    ],
    # Robotics / Embedded / Vision
    "ros2": ["ros2", "ros ", "rclpy", "colcon", "ament"],
    "embedded": ["embedded", "firmware", "microcontroller", "stm32", "arduino"],
    "opencv": ["opencv", "cv2", "imshow", "videocapture"],
    "cmake": ["cmake", "cmakelist", "find_package"],
    # ML / AI
    "pytorch": ["pytorch", "torch.", "autograd", "dataloader"],
    "tensorflow": ["tensorflow", "tf.", "keras", "savedmodel"],
    "huggingface": ["huggingface", "transformers", "tokenizer", "from_pretrained"],
    "llm": ["llm", "large language", "prompt", "hallucination", "token limit"],
    # Infrastructure / Middleware
    "nginx": ["nginx", "reverse proxy", "upstream", "server block"],
    "redis": ["redis", "redis-cli", "jedis", "redisconnection"],
    "mongodb": ["mongodb", "mongo ", "mongoose", "bson"],
    "kafka": ["kafka", "consumer", "producer", "broker", "zookeeper"],
    "elasticsearch": ["elasticsearch", "elastic", "kibana", "lucene"],
    "grpc": ["grpc", "protobuf", "proto ", ".proto"],
    # Mobile / Cross-platform
    "android": ["android", "gradle", "apk", "activity", "intent"],
    "flutter": ["flutter", "dart", "widget", "pubspec"],
    "unity": ["unity", "gameobject", "monobehaviour", "prefab"],
    # Quirk domains
    "api": ["api ", "rest ", "endpoint", "rate limit", "429"],
    "cloud": ["cloud", "gcp", "azure", "heroku", "vercel"],
    "data": ["json", "csv", "xml", "yaml", "encoding", "utf-8"],
    "security": ["security", "vulnerability", "xss", "csrf", "injection"],
    "policy": ["policy", "terms of service", "rate limit", "quota"],
    "communication": ["email", "smtp", "webhook", "notification"],
    # Cultural norms
    "culture": ["culture", "etiquette", "taboo", "offensive", "sensitivity"],
    # Real-world safety / life-critical knowledge
    "safety": [
        "fire", "electric shock", "cpr", "choking", "first aid",
        "tourniquet", "heatstroke",
    ],
    "medical": [
        "drug interaction", "medication", "allergy", "anaphylaxis",
        "folk remedy", "dosage",
    ],
    "mental-health": [
        "suicide", "depression", "self-harm", "crisis",
        "mental health", "therapy",
    ],
    "food-safety": [
        "food poisoning", "raw chicken", "expired food",
        "room temperature", "cross contamination",
    ],
    "disaster": [
        "earthquake", "tornado", "hurricane", "wildfire",
        "tsunami", "evacuation",
    ],
    "legal": [
        "self defense", "copyright", "fair use", "defamation",
        "right to silence", "legal advice",
    ],
    "pet-safety": [
        "dog toxic", "cat toxic", "pet poison",
        "chocolate dog", "xylitol", "onion dog",
    ],
    # Country-specific real-world knowledge (jurisdiction/culture-bound)
    "visa": [
        "visa", "passport", "residency", "work permit",
        "immigration", "overstay", "esta", "schengen",
        "arc", "alien registration", "visa waiver",
    ],
    "banking": [
        "bank account", "open account", "foreigner account",
        "wire transfer", "iban", "swift", "routing number",
        "sort code", "bic", "ssn banking", "my number",
    ],
    "emergency": [
        "emergency number", "911", "112", "119", "999",
        "ambulance", "police non-emergency", "embassy emergency",
        "lost passport", "medical evacuation",
    ],
}

# Supplementary keywords for culture/legal/food-safety that reflect common
# country-specific taboos and norms. Used by the same suggest_domains()
# lookup to route cross-cultural queries to the right canon domain.
_EXTRA_CULTURE_KEYWORDS: list[str] = [
    "chopstick", "meishi", "business card japan", "shoes indoors",
    "genkan", "tiananmen", "taiwan independence", "送钟", "clock gift",
    "number four", "floor 4", "red ink name", "fan death",
    "lese majeste", "king of thailand", "head touch", "foot pointing",
    "monks thailand", "left hand eating", "cow sacred", "beef hindu",
    "caste", "head wobble", "american war vietnam",
    "ramadan", "alcohol saudi", "dress code abaya", "unmarried pda",
    "armenian genocide", "ataturk", "shabbat", "west bank settlement",
    "nazi salute", "hitlergruß", "bonjour", "tu vous", "cappuccino after",
    "pasta cut", "ok gesture brazil", "whistling indoors", "gringo",
    "holocaust joke", "yasukuni", "tibet dalai lama",
]
KEYWORD_MAP["culture"] = sorted(set(KEYWORD_MAP["culture"] + _EXTRA_CULTURE_KEYWORDS))

_EXTRA_LEGAL_KEYWORDS: list[str] = [
    "lese majeste article 112", "article 301 turkey", "stgb 86a",
    "holocaust denial", "blasphemy law", "apostasy law",
    "khat law", "cannabis singapore", "death penalty drugs",
    "fine spitting", "chewing gum singapore",
]
KEYWORD_MAP["legal"] = sorted(set(KEYWORD_MAP["legal"] + _EXTRA_LEGAL_KEYWORDS))

_EXTRA_FOODSAFETY_KEYWORDS: list[str] = [
    "halal", "haram", "kosher", "pork muslim", "pork indonesia",
    "beef india", "raw fish pregnant", "durian hotel ban",
]
KEYWORD_MAP["food-safety"] = sorted(
    set(KEYWORD_MAP["food-safety"] + _EXTRA_FOODSAFETY_KEYWORDS)
)

# Human-readable display names for domain slugs.
# Used by build_site.py and templates for UI rendering.
# Domains not listed here fall back to slug.replace("-", " ").title().
DOMAIN_DISPLAY_NAMES: dict[str, str] = {
    "aws": "AWS",
    "cuda": "CUDA",
    "cicd": "CI/CD",
    "php": "PHP",
    "dotnet": ".NET",
    "nextjs": "Next.js",
    "typescript": "TypeScript",
    "pip": "pip",
    # Robotics / Embedded / Vision
    "ros2": "ROS 2",
    "opencv": "OpenCV",
    "cmake": "CMake",
    # ML / AI
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "huggingface": "Hugging Face",
    "llm": "LLM",
    # Infrastructure / Middleware
    "grpc": "gRPC",
    "mongodb": "MongoDB",
    "elasticsearch": "Elasticsearch",
    # Mobile / Cross-platform
    "flutter": "Flutter",
    "unity": "Unity",
    # Quirk domains
    "api": "API",
    # Cultural norms
    "culture": "Culture",
    # Reserved
    "mcp": "MCP",
    "http": "HTTP",
    # Real-world safety
    "safety": "Safety",
    "medical": "Medical",
    "mental-health": "Mental Health",
    "food-safety": "Food Safety",
    "disaster": "Disaster",
    "legal": "Legal",
    "pet-safety": "Pet Safety",
    # Country-specific
    "visa": "Visa & Immigration",
    "banking": "Banking & Finance",
    "emergency": "Emergency",
}


def suggest_domains(error_message: str) -> str:
    """Suggest relevant domains based on keywords in an error message."""
    msg = error_message.lower()
    suggestions = []
    for domain, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in msg:
                suggestions.append(domain)
                break
    return ", ".join(suggestions) if suggestions else "unknown"


def domain_display_name(domain: str) -> str:
    """Return proper display name for a domain slug."""
    return DOMAIN_DISPLAY_NAMES.get(domain, domain.replace("-", " ").title())
