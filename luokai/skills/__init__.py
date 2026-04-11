#!/usr/bin/env python3
"""
LUOKAI Skills Engine — 4,146 Built-in Skills
=============================================
All skills live locally inside luokai/skills/library/.
No internet connection required. Ever.

Skills are indexed at startup from SKILL.md files.
Each SKILL.md has YAML frontmatter: name, description, domain, etc.
The full markdown body is the skill content served to the AI agent.

20 Domains · 4,146 Skills · 100% Local · No external calls

Created by Luo Kai (luokai25)
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# ── Path to local skills library ─────────────────────────────────────
LIBRARY_DIR = Path(__file__).parent / "library"

# ── Domain display names ──────────────────────────────────────────────
DOMAIN_LABELS = {
    "01-programming-languages":         "Programming Languages",
    "02-frontend-development":          "Frontend Development",
    "03-backend-development":           "Backend Development",
    "04-databases-and-storage":         "Databases & Storage",
    "05-devops-and-cloud":              "DevOps & Cloud",
    "06-security-and-auth":             "Security & Auth",
    "07-testing-and-quality":           "Testing & Quality",
    "08-architecture-and-patterns":     "Architecture & Patterns",
    "09-data-and-ai":                   "Data & AI",
    "10-mobile-development":            "Mobile Development",
    "11-specialized-coding":            "Specialized Coding",
    "12-finance-and-trading":           "Finance & Trading",
    "13-physics-and-mathematics":       "Physics & Mathematics",
    "14-chemistry-and-biology":         "Chemistry & Biology",
    "15-earth-and-space-sciences":      "Earth & Space Sciences",
    "16-engineering":                   "Engineering",
    "17-emerging-tech":                 "Emerging Tech",
    "18-ai-agents-and-automation":      "AI Agents & Automation",
    "19-business-and-entrepreneurship": "Business & Entrepreneurship",
    "20-health-and-wellness":           "Health & Wellness",
}


@dataclass
class Skill:
    """A single skill loaded from a SKILL.md file."""
    name:       str
    slug:       str
    description:str
    domain:     str
    subdomain:  str
    path:       Path
    author:     str           = "luo-kai"
    version:    str           = "1.0"
    tags:       List[str]     = field(default_factory=list)
    _content:   Optional[str] = field(default=None, repr=False)

    @property
    def content(self) -> str:
        """Lazy-load full skill markdown (strips frontmatter)."""
        if self._content is None:
            try:
                raw = self.path.read_text(encoding="utf-8", errors="replace")
                if raw.startswith("---"):
                    end = raw.find("---", 3)
                    self._content = raw[end + 3:].strip() if end != -1 else raw
                else:
                    self._content = raw
            except Exception:
                self._content = f"# {self.name}\n\n{self.description}"
        return self._content

    def to_dict(self, include_content: bool = False) -> Dict[str, Any]:
        d = {
            "name":         self.name,
            "slug":         self.slug,
            "description":  self.description,
            "domain":       self.domain,
            "domain_label": DOMAIN_LABELS.get(self.domain, self.domain),
            "subdomain":    self.subdomain,
            "author":       self.author,
            "version":      self.version,
            "tags":         self.tags,
        }
        if include_content:
            d["content"] = self.content
        return d


class SkillsEngine:
    """
    Indexes all 4,146 built-in skills at startup.
    All lookups are local — no network, no external calls.
    """

    def __init__(self):
        self._skills:    Dict[str, Skill]     = {}
        self._by_domain: Dict[str, List[str]] = {}
        self._by_sub:    Dict[str, List[str]] = {}
        self._loaded:    bool                 = False
        self._load_time: float                = 0.0

    def load(self) -> int:
        if self._loaded:
            return len(self._skills)
        t0 = time.time()
        if not LIBRARY_DIR.exists():
            print(f"[Skills] ⚠️  Library not found at {LIBRARY_DIR}")
            self._loaded = True
            return 0
        for skill_file in sorted(LIBRARY_DIR.rglob("SKILL.md")):
            try:
                skill = self._parse_skill(skill_file)
                if skill:
                    self._skills[skill.slug] = skill
                    self._by_domain.setdefault(skill.domain, []).append(skill.slug)
                    self._by_sub.setdefault(skill.subdomain, []).append(skill.slug)
            except Exception:
                pass
        self._loaded    = True
        self._load_time = time.time() - t0
        print(f"[Skills] ✅ {len(self._skills):,} skills indexed in {self._load_time:.2f}s")
        return len(self._skills)

    def _parse_skill(self, path: Path) -> Optional[Skill]:
        parts   = path.parts
        lib_idx = next((i for i, p in enumerate(parts) if p == "library"), None)
        if lib_idx is None or len(parts) < lib_idx + 4:
            return None

        domain_raw = parts[lib_idx + 1]
        subdomain  = parts[lib_idx + 2]
        skill_slug = parts[lib_idx + 3]
        domain     = re.sub(r"\s*\(by Luo Kai\)\s*$", "", domain_raw).strip()

        raw  = path.read_text(encoding="utf-8", errors="replace")
        meta = self._parse_frontmatter(raw)

        name        = meta.get("name", skill_slug).strip('"\'')
        description = meta.get("description", "").strip('"\'')
        author      = meta.get("author", "luo-kai")
        version     = str(meta.get("version", "1.0"))
        tags_raw    = meta.get("tags", [])
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.strip("[]").split(",") if t.strip()]
        elif isinstance(tags_raw, list):
            tags = [str(t).strip() for t in tags_raw]
        else:
            tags = []

        if not description:
            for line in raw.split("\n"):
                line = line.strip()
                if line and not line.startswith("---") and not line.startswith("#"):
                    description = line[:200]
                    break
            if not description:
                description = f"{name} skill"

        return Skill(
            name=name or skill_slug, slug=skill_slug,
            description=description[:500], domain=domain,
            subdomain=subdomain, path=path,
            author=author, version=version, tags=tags,
        )

    def _parse_frontmatter(self, text: str) -> Dict[str, Any]:
        meta = {}
        if not text.startswith("---"):
            return meta
        end = text.find("---", 3)
        if end == -1:
            return meta
        for line in text[3:end].splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if val.startswith("["):
                meta[key] = [i.strip().strip('"\'') for i in val.strip("[]").split(",") if i.strip()]
            else:
                meta[key] = val
        return meta

    # ── Public API ────────────────────────────────────────────────────

    def get(self, slug: str) -> Optional[Skill]:
        return self._skills.get(slug)

    def search(self, query: str, limit: int = 20) -> List[Skill]:
        q = query.lower().strip()
        if not q:
            return []
        results = []
        for skill in self._skills.values():
            score = 0
            if q in skill.slug.lower():              score += 10
            if q in skill.name.lower():              score += 8
            if skill.name.lower().startswith(q):     score += 5
            if q in skill.description.lower():       score += 3
            if any(q in t.lower() for t in skill.tags): score += 4
            if q in skill.domain:                    score += 2
            if q in skill.subdomain:                 score += 2
            if score > 0:
                results.append((score, skill))
        results.sort(key=lambda x: (-x[0], x[1].name))
        return [s for _, s in results[:limit]]

    def list_domain(self, domain: str) -> List[Skill]:
        return [self._skills[s] for s in self._by_domain.get(domain, []) if s in self._skills]

    def all_domains(self) -> Dict[str, Dict]:
        result = {}
        for domain, slugs in sorted(self._by_domain.items()):
            result[domain] = {
                "label": DOMAIN_LABELS.get(domain, domain),
                "count": len(slugs),
                "subdomains": sorted(set(
                    self._skills[s].subdomain for s in slugs if s in self._skills
                )),
            }
        return result

    def stats(self) -> Dict[str, Any]:
        return {
            "total":        len(self._skills),
            "domains":      len(self._by_domain),
            "subdomains":   len(self._by_sub),
            "load_time_s":  round(self._load_time, 3),
            "library_path": str(LIBRARY_DIR),
        }

    @property
    def count(self) -> int:
        return len(self._skills)


# ── Global engine (auto-loads on import) ─────────────────────────────
engine = SkillsEngine()
engine.load()


# ── Public helpers (used by luo_server.py) ────────────────────────────

def load_skills() -> int:
    return engine.load()

def get_skill(slug: str, with_content: bool = True) -> Optional[Dict]:
    skill = engine.get(slug)
    return skill.to_dict(include_content=with_content) if skill else None

def search_skills(query: str, limit: int = 20) -> List[Dict]:
    return [s.to_dict() for s in engine.search(query, limit)]

def list_domain(domain: str) -> List[Dict]:
    return [s.to_dict() for s in engine.list_domain(domain)]

def all_domains() -> Dict:
    return engine.all_domains()

def skills_stats() -> Dict:
    return engine.stats()

def list_all_skills() -> Dict[str, List[str]]:
    """Backwards-compatible: domain -> [name list]."""
    return {
        domain: [engine.get(s).name for s in slugs if engine.get(s)]
        for domain, slugs in engine._by_domain.items()
    }

def get_skill_help(slug: str) -> str:
    skill = engine.get(slug)
    if not skill:
        return f"Skill '{slug}' not found. Use search_skills(query) to find skills."
    return (
        f"Skill: {skill.name}\n"
        f"Domain: {DOMAIN_LABELS.get(skill.domain, skill.domain)}\n"
        f"Subdomain: {skill.subdomain}\n"
        f"Description: {skill.description}\n"
        f"Author: {skill.author}\n"
    )

# Backwards-compat
SKILL_COUNT = 4146
DOMAINS     = list(DOMAIN_LABELS.keys())

__all__ = [
    "SkillsEngine", "Skill", "engine",
    "load_skills", "get_skill", "search_skills",
    "list_domain", "all_domains", "skills_stats",
    "list_all_skills", "get_skill_help",
    "SKILL_COUNT", "DOMAINS", "DOMAIN_LABELS",
]
