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


# Unique, hand-written overview for each domain hub page. These give the
# /{domain}/ landing pages genuine editorial prose instead of a bare link
# list - the "thin list page" profile that search engines are slow to index.
# One to two domain-specific sentences each; no shared boilerplate suffix.
DOMAIN_INTROS: dict[str, str] = {
    "android": (
        "Android failures cluster around Gradle builds, SDK and manifest mismatches, "
        "and device-specific behavior that only shows up on real hardware. Each entry "
        "records the fix that holds and the workarounds that quietly break other things."
    ),
    "api": (
        "Most REST and web-API dead ends come from authentication, rate limits, CORS, "
        "and silent version drift between client and server. These entries separate the "
        "integration fixes that survive production from the ones that only pass a demo."
    ),
    "aws": (
        "AWS errors span IAM permissions, S3 access, Lambda limits, EC2 networking, and "
        "region quirks - where the message rarely names the real cause. Each page documents "
        "the misleading fixes to skip and the configuration that actually clears the error."
    ),
    "banking": (
        "Opening and using a bank account as a foreigner runs into residency proof, ID "
        "rules, and transfer limits that generic advice ignores. These entries map which "
        "requirements are hard blocks and which have a documented workaround, by country."
    ),
    "cicd": (
        "CI/CD pipelines fail on runners, cache invalidation, leaked or missing secrets, "
        "and YAML that is valid but wrong. Each entry captures the green-locally-red-in-CI "
        "traps and the pipeline changes that fix them without disabling the check."
    ),
    "cloud": (
        "Cloud provisioning breaks on quotas, region availability, credential scope, and "
        "eventual-consistency delays that look like outright failures. These entries show "
        "what to stop retrying and which corrective step the platform actually respects."
    ),
    "cmake": (
        "CMake configuration fails on toolchain detection, find_package resolution, and "
        "target and linker ordering that compiles on one machine and not the next. Each "
        "entry records the CMakeLists fix that generalizes instead of the local patch."
    ),
    "communication": (
        "Staying connected across borders runs into SIM registration, roaming charges, "
        "blocked VoIP, and messaging apps that are restricted or banned outright. These "
        "entries note which assumptions are wrong by country and what still works there."
    ),
    "cuda": (
        "CUDA and GPU errors trace back to driver and toolkit mismatches, out-of-memory "
        "conditions, and compute-architecture flags that silently disable acceleration. "
        "Each page separates the reinstall-everything myths from the real fix."
    ),
    "culture": (
        "Cultural etiquette is where confidently generic advice most often offends or "
        "backfires - gestures, gifts, dress, and address forms that invert across borders. "
        "These entries record the norm that actually applies and the assumption that fails."
    ),
    "data": (
        "Data pipelines break on encoding, delimiter and schema drift, timezone handling, "
        "and silent type coercion that corrupts rows without erroring. Each entry documents "
        "the transform that looks correct but loses data and the one that holds."
    ),
    "database": (
        "Relational database errors come from connection pools, lock contention, migration "
        "ordering, and constraints that reject data the app thought was valid. These entries "
        "show the query or config change that fixes the cause, not just the symptom."
    ),
    "disaster": (
        "Disaster-response folklore is where 'common sense' safety advice measurably raises "
        "risk - the doorway myth, the overpass myth, and similar dangerous defaults. Each "
        "entry cites what the guidance gets wrong and what emergency agencies advise instead."
    ),
    "docker": (
        "Docker breaks on image layering, build context, networking between containers, "
        "and volume permissions that differ across hosts. Each entry records the Dockerfile "
        "or runtime fix that ports cleanly and the hack that only works on your machine."
    ),
    "dotnet": (
        ".NET errors surface through NuGet resolution, runtime and target-framework "
        "mismatches, and assembly binding that fails only at load time. These entries "
        "separate the fix that survives a clean build from the one that masks the conflict."
    ),
    "elasticsearch": (
        "Elasticsearch problems concentrate in mapping conflicts, shard allocation, heap "
        "pressure, and queries that are slow rather than wrong. Each entry documents the "
        "index or cluster change that resolves it without reindexing everything blindly."
    ),
    "embedded": (
        "Embedded and firmware work fails on cross-toolchains, flashing and bootloader "
        "steps, tight memory, and peripheral timing. These entries record the fix that "
        "matches the hardware instead of the desktop-oriented advice that bricks the board."
    ),
    "emergency": (
        "Emergency numbers and procedures differ sharply by country, and a wrong assumption "
        "costs minutes that matter. These entries record the correct local number, when it "
        "reaches help, and the common myth (like a single universal number) that fails."
    ),
    "flutter": (
        "Flutter errors come from package and plugin conflicts, platform-channel wiring, "
        "and rendering or build issues that hit one target only. Each entry captures the "
        "fix that works across iOS and Android rather than the one that shifts the bug."
    ),
    "food-safety": (
        "Food-safety dead ends are where intuition and generic advice mislead - storage "
        "temperatures, reheating, and country rules on what is safe to eat or import. These "
        "entries cite the guidance that prevents illness and the shortcut that risks it."
    ),
    "git": (
        "Git trips developers on merges and rebases, remote tracking, detached HEAD, and "
        "history rewrites that are easy to make unrecoverable. Each entry records the safe "
        "recovery path and the destructive command people reach for by reflex."
    ),
    "go": (
        "Go compile and runtime errors come from module resolution, interface satisfaction, "
        "goroutine and channel misuse, and build tags. These entries separate the idiomatic "
        "fix from the workaround that compiles but reintroduces the race or leak."
    ),
    "grpc": (
        "gRPC fails on status-code mapping, deadlines, proto and version mismatches, and "
        "channel and connection management. Each entry documents the client or server change "
        "that clears the error instead of the retry loop that hides it."
    ),
    "huggingface": (
        "Hugging Face errors show up in model and tokenizer loading, authentication and "
        "gated repos, and memory during inference or training. These entries record the fix "
        "that loads the model correctly and the config that only appears to."
    ),
    "java": (
        "Java errors trace to classpath and dependency conflicts, JVM version mismatches, "
        "and initialization order that fails only at runtime. Each entry captures the build "
        "or config fix that resolves the clash rather than shading over it."
    ),
    "kafka": (
        "Kafka problems concentrate in broker connectivity, partition and consumer-group "
        "rebalancing, offset management, and serialization. These entries document the fix "
        "that preserves ordering and delivery guarantees instead of silently dropping them."
    ),
    "kubernetes": (
        "Kubernetes errors span pod scheduling, RBAC, networking, storage, and probes that "
        "restart healthy workloads. Each entry records the manifest or cluster change that "
        "addresses the cause, not the kubectl delete that only resets the symptom."
    ),
    "legal": (
        "Legal dead ends turn on rules that vary by jurisdiction and catch travelers and "
        "newcomers off guard - registration deadlines, permits, and prohibited acts. These "
        "entries cite the rule that actually applies and the assumption that invites a fine."
    ),
    "llm": (
        "LLM integrations fail on context-window limits, tool-call formatting, streaming, "
        "and rate limits that surface as truncated or malformed output. These entries "
        "separate the prompt-or-config fix that works from the retry that burns budget."
    ),
    "medical": (
        "Cross-border medical dead ends involve prescriptions, controlled substances, "
        "insurance coverage, and care-access rules that differ by country. Each entry records "
        "what is actually permitted and the assumption that leaves you without treatment."
    ),
    "mental-health": (
        "Mental-health guidance is a domain where confidently generic advice can do harm. "
        "These entries flag responses that escalate risk and point to the safer, "
        "evidence-based approach and appropriate local support."
    ),
    "mongodb": (
        "MongoDB errors come from connection strings and auth, index and aggregation "
        "pitfalls, and replica-set elections. Each entry documents the query or "
        "configuration change that fixes the behavior instead of masking it with a retry."
    ),
    "networking": (
        "Network failures hide behind DNS resolution, TLS handshakes, port and firewall "
        "rules, proxies, and timeouts that all present as 'connection refused.' These "
        "entries isolate which layer is actually failing and the fix that layer needs."
    ),
    "nextjs": (
        "Next.js errors come from the server/client component boundary, routing and data "
        "fetching, build output, and hydration mismatches. Each entry records the fix that "
        "respects the rendering model rather than the 'use client' sprinkle that hides it."
    ),
    "nginx": (
        "NGINX breaks on config syntax and precedence, upstream and proxy settings, TLS "
        "certificates, and file permissions. These entries document the directive change "
        "that fixes routing or access instead of the reload that changes nothing."
    ),
    "node": (
        "Node.js errors trace to module resolution (ESM vs CommonJS), async and promise "
        "handling, version mismatches, and native-addon builds. Each entry separates the "
        "fix that resolves the cause from the flag that only silences the warning."
    ),
    "opencv": (
        "OpenCV problems concentrate in build and codec support, color-space and channel "
        "order, and GPU acceleration that silently falls back to CPU. These entries record "
        "the fix that matches your build rather than the reinstall that changes nothing."
    ),
    "pet-safety": (
        "Pet-safety dead ends are foods, plants, medications, and home remedies that are "
        "harmless to people but toxic to animals. Each entry cites the hazard, the species "
        "affected, and the safe alternative that generic advice leaves out."
    ),
    "php": (
        "PHP errors surface through Composer resolution, missing or mismatched extensions, "
        "version incompatibilities, and runtime configuration. These entries document the "
        "fix that works with your PHP version instead of the one written for another."
    ),
    "pip": (
        "pip and Python packaging fail on dependency resolution, wheel and build issues, "
        "and environment confusion between system, venv, and user installs. Each entry "
        "records which environment the fix belongs in and the reinstall that just repeats it."
    ),
    "policy": (
        "Policy and compliance dead ends turn on rules that vary by jurisdiction and change "
        "without notice - data handling, cross-border transfer, and reporting. These entries "
        "cite the requirement that actually applies and the assumption that risks a breach."
    ),
    "python": (
        "Python errors cluster around imports and packaging, environment and version "
        "mismatches, and dynamic-typing surprises that only fail at runtime. Each entry "
        "separates the fix that addresses the cause from the one that moves the traceback."
    ),
    "pytorch": (
        "PyTorch errors come from CUDA and device placement, tensor shape and dtype "
        "mismatches, autograd, and memory during training. These entries record the fix that "
        "keeps the graph correct instead of the .to(device) scattered until it stops erroring."
    ),
    "react": (
        "React errors trace to hook rules, render and effect timing, stale state and "
        "closures, and build configuration. Each entry documents the fix that respects the "
        "render model rather than the dependency-array edit that hides the real bug."
    ),
    "redis": (
        "Redis problems concentrate in connection and auth, memory limits and eviction, "
        "persistence, and cluster mode. These entries record the configuration change that "
        "fixes durability or latency instead of the flush that loses data."
    ),
    "ros2": (
        "ROS 2 errors come from node discovery, topic and QoS mismatches, DDS transport, and "
        "colcon builds. Each entry documents the fix that matches your middleware and QoS "
        "profile rather than the rebuild that leaves the mismatch in place."
    ),
    "rust": (
        "Rust errors are mostly the borrow checker, lifetimes, trait bounds, and Cargo "
        "feature resolution - strict by design. These entries record the fix that satisfies "
        "the compiler's real requirement instead of the clone-and-unwrap that defeats it."
    ),
    "safety": (
        "Personal-safety dead ends are situations where popular advice increases danger "
        "rather than reducing it. Each entry cites what the common guidance gets wrong and "
        "the response that safety authorities actually recommend."
    ),
    "security": (
        "Security dead ends live in authentication and session handling, secret management, "
        "TLS, and misconfigurations that feel fixed but are not. These entries separate the "
        "change that closes the hole from the one that only hides it from the scanner."
    ),
    "tensorflow": (
        "TensorFlow errors trace to graph and eager mode, GPU and CUDA setup, version "
        "incompatibilities, and shape mismatches. Each entry records the fix that matches "
        "your TF version rather than the code snippet written for a different major release."
    ),
    "terraform": (
        "Terraform errors come from state drift and locking, provider versions, plan/apply "
        "mismatches, and resources changed outside Terraform. These entries document the fix "
        "that reconciles state safely instead of the destroy-and-recreate that loses data."
    ),
    "typescript": (
        "TypeScript errors concentrate in type inference and narrowing, module resolution, "
        "config strictness, and build output. Each entry separates the fix that models the "
        "type correctly from the any-cast that silences the compiler and keeps the bug."
    ),
    "unity": (
        "Unity errors come from build and platform targets, scene and asset references, "
        "package versions, and script-compilation order. These entries record the fix that "
        "survives a platform switch rather than the reimport that only sometimes helps."
    ),
    "visa": (
        "Visa and immigration dead ends turn on entry rules, exemption conditions, and "
        "overstay and re-entry traps that vary by passport and destination. Each entry cites "
        "the rule that actually applies and the confident assumption that gets travelers denied."
    ),
}


def domain_intro(domain: str) -> str:
    """Return the editorial intro for a domain hub, or an empty string."""
    return DOMAIN_INTROS.get(domain, "")


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
