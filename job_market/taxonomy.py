"""Small versioned seed taxonomy; expand through reviewed changes, not ad-hoc strings."""

TAXONOMY_VERSION = "2026-01"

SKILLS: dict[str, dict[str, object]] = {
    "Python": {"category": "programming_language", "aliases": ("python",)},
    "Java": {"category": "programming_language", "aliases": ("java",)},
    "JavaScript": {"category": "programming_language", "aliases": ("javascript", "js")},
    "TypeScript": {"category": "programming_language", "aliases": ("typescript", "ts")},
    "C#": {"category": "programming_language", "aliases": ("c#", "c sharp")},
    "Go": {"category": "programming_language", "aliases": ("golang", "go")},
    "SQL": {"category": "fundamentals", "aliases": ("sql",)},
    "React": {"category": "frontend", "aliases": ("react", "react.js", "reactjs")},
    "Angular": {"category": "frontend", "aliases": ("angular", "angular.js")},
    "Vue": {"category": "frontend", "aliases": ("vue", "vue.js")},
    "Spring Boot": {"category": "backend", "aliases": ("spring boot",)},
    "Node.js": {"category": "backend", "aliases": ("node.js", "nodejs", "node")},
    "Django": {"category": "backend", "aliases": ("django",)},
    "FastAPI": {"category": "backend", "aliases": ("fastapi",)},
    "PostgreSQL": {"category": "database", "aliases": ("postgresql", "postgres",)},
    "MySQL": {"category": "database", "aliases": ("mysql",)},
    "MongoDB": {"category": "database", "aliases": ("mongodb", "mongo",)},
    "Redis": {"category": "database", "aliases": ("redis",)},
    "AWS": {"category": "cloud", "aliases": ("aws", "amazon web services")},
    "Azure": {"category": "cloud", "aliases": ("azure", "microsoft azure")},
    "Google Cloud": {"category": "cloud", "aliases": ("google cloud", "gcp")},
    "Docker": {"category": "devops", "aliases": ("docker",)},
    "Kubernetes": {"category": "devops", "aliases": ("kubernetes", "k8s")},
    "Terraform": {"category": "devops", "aliases": ("terraform",)},
    "Git": {"category": "fundamentals", "aliases": ("git",)},
    "REST APIs": {"category": "fundamentals", "aliases": ("rest api", "restful api", "rest")},
    "Testing": {"category": "fundamentals", "aliases": ("testing", "unit testing",)},
}


def taxonomy_records() -> list[dict[str, object]]:
    return [
        {
            "canonical_name": name,
            "category": values["category"],
            "aliases": list(values["aliases"]),
            "taxonomy_version": TAXONOMY_VERSION,
        }
        for name, values in SKILLS.items()
    ]
