#!/usr/bin/env python3
"""
LUOKAI Skills Library — Real, Functional Skills
Each skill is a self-contained capability the agent can use.

Skills are organized by domain:
- code: Code generation, analysis, debugging
- web: Web browsing, searching, scraping
- files: File operations, project management
- system: System control, monitoring
- creative: Writing, content generation
- analysis: Data analysis, visualization
- communication: Chat, messaging, summaries
- planning: Task planning and breakdown

Created by Luo Kai (luokai25) — Enhanced by Claude Code
"""
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from pathlib import Path
import json
import re
import os

@dataclass
class Skill:
    """A skill the agent can use."""
    name: str
    description: str
    domain: str
    execute: Callable
    parameters: Dict[str, str]  # param_name -> description
    examples: List[str] = None
    requires_permission: bool = False


class SkillRegistry:
    """Registry of all available skills."""

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._domains: Dict[str, List[str]] = {}  # domain -> skill names

    def register(self, skill: Skill):
        """Register a skill."""
        self._skills[skill.name] = skill
        if skill.domain not in self._domains:
            self._domains[skill.domain] = []
        self._domains[skill.domain].append(skill.name)

    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)

    def list_skills(self, domain: str = None) -> List[Skill]:
        """List skills, optionally filtered by domain."""
        if domain:
            names = self._domains.get(domain, [])
            return [self._skills[n] for n in names if n in self._skills]
        return list(self._skills.values())

    def get_domains(self) -> List[str]:
        """Get all domains."""
        return list(self._domains.keys())

    def execute(self, name: str, **kwargs) -> Any:
        """Execute a skill."""
        skill = self.get(name)
        if not skill:
            return f"Error: Skill '{name}' not found"
        return skill.execute(**kwargs)


# Global registry
registry = SkillRegistry()


# ═══════════════════════════════════════════════════════════════════
# CODE SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_code_explain(code: str, language: str = "auto") -> str:
    """Explain what a piece of code does."""
    return f"Explain this {language} code step by step:\n\n```\n{code}\n```"


def skill_code_refactor(code: str, goal: str = "improve readability") -> str:
    """Suggest refactoring for code."""
    return f"Refactor this code to {goal}. Show the before/after:\n\n```\n{code}\n```"


def skill_code_debug(code: str, error: str = None) -> str:
    """Debug code with optional error message."""
    prompt = f"Debug this code:\n\n```\n{code}\n```"
    if error:
        prompt += f"\n\nError encountered:\n```\n{error}\n```"
    return prompt


def skill_code_test(code: str, language: str = "python") -> str:
    """Generate tests for code."""
    return f"Generate comprehensive unit tests for this {language} code:\n\n```\n{code}\n```"


def skill_code_review(code: str, focus: str = "general") -> str:
    """Review code for issues and improvements."""
    return f"Review this code for {focus}. List issues with severity and suggest fixes:\n\n```\n{code}\n```"


def skill_code_generate(description: str, language: str = "python") -> str:
    """Generate code from description."""
    return f"Write {language} code that: {description}\n\nInclude error handling and comments."


def skill_code_optimize(code: str, goal: str = "performance") -> str:
    """Optimize code for specific goal."""
    return f"Optimize this code for {goal}:\n\n```\n{code}\n```\n\nExplain the optimizations made."


def skill_code_convert(code: str, from_lang: str, to_lang: str) -> str:
    """Convert code between languages."""
    return f"Convert this {from_lang} code to {to_lang}:\n\n```\n{code}\n```"


# Register code skills
registry.register(Skill(
    name="code_explain",
    description="Explain what a piece of code does",
    domain="code",
    execute=skill_code_explain,
    parameters={"code": "The code to explain", "language": "Programming language (default: auto-detect)"}
))

registry.register(Skill(
    name="code_refactor",
    description="Suggest refactoring improvements",
    domain="code",
    execute=skill_code_refactor,
    parameters={"code": "The code to refactor", "goal": "Refactoring goal (e.g., 'improve readability')"}
))

registry.register(Skill(
    name="code_debug",
    description="Debug code and find issues",
    domain="code",
    execute=skill_code_debug,
    parameters={"code": "The code to debug", "error": "Optional error message"}
))

registry.register(Skill(
    name="code_test",
    description="Generate unit tests for code",
    domain="code",
    execute=skill_code_test,
    parameters={"code": "The code to test", "language": "Programming language"}
))

registry.register(Skill(
    name="code_review",
    description="Review code for issues",
    domain="code",
    execute=skill_code_review,
    parameters={"code": "The code to review", "focus": "Review focus (e.g., 'security', 'performance')"}
))

registry.register(Skill(
    name="code_generate",
    description="Generate code from description",
    domain="code",
    execute=skill_code_generate,
    parameters={"description": "What the code should do", "language": "Programming language"}
))

registry.register(Skill(
    name="code_optimize",
    description="Optimize code for performance or other goals",
    domain="code",
    execute=skill_code_optimize,
    parameters={"code": "Code to optimize", "goal": "Optimization goal"}
))

registry.register(Skill(
    name="code_convert",
    description="Convert code between languages",
    domain="code",
    execute=skill_code_convert,
    parameters={"code": "Code to convert", "from_lang": "Source language", "to_lang": "Target language"}
))


# ═══════════════════════════════════════════════════════════════════
# WEB SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_web_summarize(url: str, focus: str = "main points") -> str:
    """Summarize web content."""
    return f"Summarize the {focus} from this URL: {url}"


def skill_web_compare(urls: List[str], aspect: str = "general") -> str:
    """Compare multiple web pages."""
    return f"Compare these URLs on {aspect}: " + ", ".join(urls)


def skill_web_extract(url: str, data_type: str) -> str:
    """Extract specific data from a web page."""
    return f"Extract all {data_type} from this URL: {url}"


def skill_web_search(query: str, max_results: int = 5) -> str:
    """Search the web."""
    return f"Search the web for: {query}. Show the top {max_results} most relevant results."


def skill_web_research(topic: str, depth: str = "medium") -> str:
    """Research a topic online."""
    return f"Research {topic} in {depth} depth. Gather information from multiple sources and synthesize key findings."


registry.register(Skill(
    name="web_summarize",
    description="Summarize web content",
    domain="web",
    execute=skill_web_summarize,
    parameters={"url": "URL to summarize", "focus": "What to focus on"}
))

registry.register(Skill(
    name="web_compare",
    description="Compare multiple web pages",
    domain="web",
    execute=skill_web_compare,
    parameters={"urls": "List of URLs", "aspect": "Aspect to compare"}
))

registry.register(Skill(
    name="web_extract",
    description="Extract specific data from web page",
    domain="web",
    execute=skill_web_extract,
    parameters={"url": "URL to extract from", "data_type": "Type of data to extract"}
))

registry.register(Skill(
    name="web_search",
    description="Search the web for information",
    domain="web",
    execute=skill_web_search,
    parameters={"query": "Search query", "max_results": "Maximum results to return"}
))

registry.register(Skill(
    name="web_research",
    description="Research a topic in depth",
    domain="web",
    execute=skill_web_research,
    parameters={"topic": "Topic to research", "depth": "Research depth (shallow/medium/deep)"}
))


# ═══════════════════════════════════════════════════════════════════
# FILE SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_file_analyze(path: str) -> str:
    """Analyze a file's structure and content."""
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return f"File not found: {path}"

        content = p.read_text(errors="replace")
        lines = content.count('\n') + 1
        chars = len(content)

        result = [f"File: {path}", f"Lines: {lines}", f"Characters: {chars}"]

        if p.suffix == '.py':
            imports = re.findall(r'^(?:import|from)\s+(\S+)', content, re.MULTILINE)
            functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
            classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            result.append(f"Imports: {len(imports)}")
            result.append(f"Functions: {', '.join(functions[:10])}")
            result.append(f"Classes: {', '.join(classes[:10])}")

        return '\n'.join(result)
    except Exception as e:
        return f"Error: {e}"


def skill_file_summarize(path: str, max_points: int = 5) -> str:
    """Generate a summary prompt for file content."""
    return f"Summarize the main points (max {max_points}) of this file: {path}"


def skill_file_find_pattern(directory: str, pattern: str) -> str:
    """Find files matching a pattern."""
    return f"Find all files matching '{pattern}' in {directory}"


def skill_file_diff(file1: str, file2: str) -> str:
    """Compare two files."""
    return f"Compare files {file1} and {file2}, highlight differences and explain changes."


def skill_file_merge(files: List[str], output: str) -> str:
    """Merge multiple files."""
    return f"Merge these files into {output}: " + ", ".join(files)


registry.register(Skill(
    name="file_analyze",
    description="Analyze file structure",
    domain="files",
    execute=skill_file_analyze,
    parameters={"path": "File path"}
))

registry.register(Skill(
    name="file_summarize",
    description="Summarize file content",
    domain="files",
    execute=skill_file_summarize,
    parameters={"path": "File path", "max_points": "Maximum summary points"}
))

registry.register(Skill(
    name="file_find_pattern",
    description="Find files by pattern",
    domain="files",
    execute=skill_file_find_pattern,
    parameters={"directory": "Directory to search", "pattern": "Pattern to match"}
))

registry.register(Skill(
    name="file_diff",
    description="Compare two files",
    domain="files",
    execute=skill_file_diff,
    parameters={"file1": "First file", "file2": "Second file"}
))

registry.register(Skill(
    name="file_merge",
    description="Merge multiple files",
    domain="files",
    execute=skill_file_merge,
    parameters={"files": "List of files to merge", "output": "Output file path"}
))


# ═══════════════════════════════════════════════════════════════════
# SYSTEM SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_system_health() -> str:
    """Check system health."""
    import subprocess
    try:
        cpu = subprocess.run(["nproc"], capture_output=True, text=True).stdout.strip()
        mem = subprocess.run(["free", "-h"], capture_output=True, text=True).stdout.strip()
        disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.strip()
        return f"CPU cores: {cpu}\n\nMemory:\n{mem}\n\nDisk:\n{disk}"
    except Exception as e:
        return f"Error checking health: {e}"


def skill_system_processes(filter_name: str = None) -> str:
    """List running processes."""
    import subprocess
    try:
        cmd = ["ps", "aux"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if filter_name:
            lines = [l for l in lines if filter_name.lower() in l.lower()]
        return '\n'.join(lines[:30])
    except Exception as e:
        return f"Error: {e}"


def skill_system_logs(service: str = None, lines: int = 50) -> str:
    """View system logs."""
    if service:
        return f"Show last {lines} logs for service: {service}"
    return f"Show last {lines} system logs"


def skill_system_diagnose(issue: str) -> str:
    """Diagnose system issue."""
    return f"Diagnose this system issue and suggest solutions: {issue}"


registry.register(Skill(
    name="system_health",
    description="Check system health",
    domain="system",
    execute=skill_system_health,
    parameters={}
))

registry.register(Skill(
    name="system_processes",
    description="List running processes",
    domain="system",
    execute=skill_system_processes,
    parameters={"filter_name": "Filter by process name"}
))

registry.register(Skill(
    name="system_logs",
    description="View system logs",
    domain="system",
    execute=skill_system_logs,
    parameters={"service": "Service name", "lines": "Number of lines"}
))

registry.register(Skill(
    name="system_diagnose",
    description="Diagnose system issues",
    domain="system",
    execute=skill_system_diagnose,
    parameters={"issue": "Description of the issue"}
))


# ═══════════════════════════════════════════════════════════════════
# CREATIVE SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_write_article(topic: str, style: str = "informative", length: int = 500) -> str:
    """Generate an article prompt."""
    return f"Write a {style} article about {topic} in approximately {length} words. Include an introduction, main points, and conclusion."


def skill_write_email(subject: str, recipient: str, purpose: str) -> str:
    """Generate an email prompt."""
    return f"Write a professional email to {recipient} about {subject}. Purpose: {purpose}"


def skill_write_code_doc(code: str, format: str = "docstring") -> str:
    """Generate documentation prompt for code."""
    return f"Write {format} documentation for this code:\n\n```\n{code}\n```"


def skill_brainstorm(topic: str, count: int = 10) -> str:
    """Generate brainstorming prompt."""
    return f"Brainstorm {count} creative ideas for: {topic}. Be innovative and varied."


def skill_write_story(genre: str, length: str = "short") -> str:
    """Write a story."""
    return f"Write a {length} {genre} story with compelling characters and a surprising twist."


def skill_write_poem(topic: str, style: str = "free verse") -> str:
    """Write a poem."""
    return f"Write a {style} poem about {topic}."


registry.register(Skill(
    name="write_article",
    description="Write an article",
    domain="creative",
    execute=skill_write_article,
    parameters={"topic": "Article topic", "style": "Writing style", "length": "Word count"}
))

registry.register(Skill(
    name="write_email",
    description="Write an email",
    domain="creative",
    execute=skill_write_email,
    parameters={"subject": "Email subject", "recipient": "Recipient", "purpose": "Email purpose"}
))

registry.register(Skill(
    name="write_code_doc",
    description="Document code",
    domain="creative",
    execute=skill_write_code_doc,
    parameters={"code": "Code to document", "format": "Documentation format"}
))

registry.register(Skill(
    name="brainstorm",
    description="Brainstorm ideas",
    domain="creative",
    execute=skill_brainstorm,
    parameters={"topic": "Topic to brainstorm", "count": "Number of ideas"}
))

registry.register(Skill(
    name="write_story",
    description="Write a story",
    domain="creative",
    execute=skill_write_story,
    parameters={"genre": "Story genre", "length": "Story length"}
))

registry.register(Skill(
    name="write_poem",
    description="Write a poem",
    domain="creative",
    execute=skill_write_poem,
    parameters={"topic": "Poem topic", "style": "Poetry style"}
))


# ═══════════════════════════════════════════════════════════════════
# ANALYSIS SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_analyze_data(data: str, analysis_type: str = "summary") -> str:
    """Analyze data prompt."""
    return f"Perform a {analysis_type} analysis on this data:\n\n{data}"


def skill_find_patterns(text: str, pattern_type: str = "any") -> str:
    """Find patterns in text."""
    return f"Find {pattern_type} patterns in this text:\n\n{text}"


def skill_compare_items(items: List[str], criteria: List[str]) -> str:
    """Compare items prompt."""
    return f"Compare these items on criteria {criteria}: " + ", ".join(items)


def skill_analyze_sentiment(text: str) -> str:
    """Analyze sentiment of text."""
    return f"Analyze the sentiment of this text, identifying emotions and tone:\n\n{text}"


def skill_analyze_arguments(text: str) -> str:
    """Analyze arguments in text."""
    return f"Analyze the arguments in this text. Identify premises, conclusions, and logical fallacies:\n\n{text}"


registry.register(Skill(
    name="analyze_data",
    description="Analyze data",
    domain="analysis",
    execute=skill_analyze_data,
    parameters={"data": "Data to analyze", "analysis_type": "Type of analysis"}
))

registry.register(Skill(
    name="find_patterns",
    description="Find patterns in text",
    domain="analysis",
    execute=skill_find_patterns,
    parameters={"text": "Text to analyze", "pattern_type": "Type of pattern"}
))

registry.register(Skill(
    name="compare_items",
    description="Compare multiple items",
    domain="analysis",
    execute=skill_compare_items,
    parameters={"items": "Items to compare", "criteria": "Comparison criteria"}
))

registry.register(Skill(
    name="analyze_sentiment",
    description="Analyze sentiment of text",
    domain="analysis",
    execute=skill_analyze_sentiment,
    parameters={"text": "Text to analyze"}
))

registry.register(Skill(
    name="analyze_arguments",
    description="Analyze arguments in text",
    domain="analysis",
    execute=skill_analyze_arguments,
    parameters={"text": "Text containing arguments"}
))


# ═══════════════════════════════════════════════════════════════════
# COMMUNICATION SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_summarize_text(text: str, length: str = "brief") -> str:
    """Summarize text prompt."""
    return f"Provide a {length} summary of:\n\n{text}"


def skill_translate_text(text: str, target_language: str) -> str:
    """Translate text prompt."""
    return f"Translate to {target_language}:\n\n{text}"


def skill_improve_writing(text: str, focus: str = "clarity") -> str:
    """Improve writing prompt."""
    return f"Improve this text for {focus}:\n\n{text}"


def skill_generate_questions(topic: str, count: int = 5) -> str:
    """Generate questions prompt."""
    return f"Generate {count} thoughtful questions about: {topic}"


def skill_explain_concept(concept: str, audience: str = "general") -> str:
    """Explain a concept."""
    return f"Explain {concept} for a {audience} audience. Use clear examples and analogies."


def skill_create_outline(topic: str, sections: int = 5) -> str:
    """Create an outline."""
    return f"Create a detailed outline with {sections} sections for: {topic}"


registry.register(Skill(
    name="summarize_text",
    description="Summarize text",
    domain="communication",
    execute=skill_summarize_text,
    parameters={"text": "Text to summarize", "length": "Summary length (brief/medium/detailed)"}
))

registry.register(Skill(
    name="translate_text",
    description="Translate text",
    domain="communication",
    execute=skill_translate_text,
    parameters={"text": "Text to translate", "target_language": "Target language"}
))

registry.register(Skill(
    name="improve_writing",
    description="Improve writing",
    domain="communication",
    execute=skill_improve_writing,
    parameters={"text": "Text to improve", "focus": "Improvement focus"}
))

registry.register(Skill(
    name="generate_questions",
    description="Generate questions about a topic",
    domain="communication",
    execute=skill_generate_questions,
    parameters={"topic": "Topic", "count": "Number of questions"}
))

registry.register(Skill(
    name="explain_concept",
    description="Explain a concept clearly",
    domain="communication",
    execute=skill_explain_concept,
    parameters={"concept": "Concept to explain", "audience": "Target audience"}
))

registry.register(Skill(
    name="create_outline",
    description="Create an outline",
    domain="communication",
    execute=skill_create_outline,
    parameters={"topic": "Topic to outline", "sections": "Number of sections"}
))


# ═══════════════════════════════════════════════════════════════════
# PLANNING SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_create_plan(goal: str, timeframe: str = "unspecified") -> str:
    """Create a plan prompt."""
    return f"Create a detailed plan to: {goal}. Timeframe: {timeframe}. Include steps, resources needed, and potential obstacles."


def skill_breakdown_task(task: str) -> str:
    """Break down a task prompt."""
    return f"Break down this task into subtasks: {task}. For each subtask, specify dependencies and estimated effort."


def skill_prioritize_tasks(tasks: List[str]) -> str:
    """Prioritize tasks prompt."""
    return f"Prioritize these tasks by importance and urgency:\n" + "\n".join(f"- {t}" for t in tasks)


def skill_create_schedule(tasks: List[str], duration: str = "week") -> str:
    """Create a schedule."""
    return f"Create a {duration} schedule for these tasks:\n" + "\n".join(f"- {t}" for t in tasks)


def skill_estimate_effort(task: str) -> str:
    """Estimate effort for a task."""
    return f"Estimate the effort (time, resources, complexity) for: {task}"


registry.register(Skill(
    name="create_plan",
    description="Create an action plan",
    domain="planning",
    execute=skill_create_plan,
    parameters={"goal": "Goal to achieve", "timeframe": "Time frame"}
))

registry.register(Skill(
    name="breakdown_task",
    description="Break down task into subtasks",
    domain="planning",
    execute=skill_breakdown_task,
    parameters={"task": "Task to break down"}
))

registry.register(Skill(
    name="prioritize_tasks",
    description="Prioritize a list of tasks",
    domain="planning",
    execute=skill_prioritize_tasks,
    parameters={"tasks": "List of tasks"}
))

registry.register(Skill(
    name="create_schedule",
    description="Create a schedule",
    domain="planning",
    execute=skill_create_schedule,
    parameters={"tasks": "Tasks to schedule", "duration": "Schedule duration"}
))

registry.register(Skill(
    name="estimate_effort",
    description="Estimate effort for a task",
    domain="planning",
    execute=skill_estimate_effort,
    parameters={"task": "Task to estimate"}
))


# ═══════════════════════════════════════════════════════════════════
# REASONING SKILLS
# ═══════════════════════════════════════════════════════════════════

def skill_analyze_problem(problem: str, depth: str = "medium") -> str:
    """Analyze a problem."""
    return f"Analyze this problem in {depth} depth. Identify root causes, effects, and potential solutions:\n\n{problem}"


def skill_make_decision(options: List[str], criteria: List[str]) -> str:
    """Make a decision between options."""
    return f"Make a decision between these options based on criteria {criteria}. Show reasoning:\n" + "\n".join(f"- {o}" for o in options)


def skill_create_argument(claim: str, audience: str = "general") -> str:
    """Create an argument for a claim."""
    return f"Create a compelling argument for this claim for a {audience} audience:\n\n{claim}"


def skill_find_assumptions(text: str) -> str:
    """Find assumptions in text."""
    return f"Identify all explicit and implicit assumptions in this text:\n\n{text}"


registry.register(Skill(
    name="analyze_problem",
    description="Analyze a problem",
    domain="reasoning",
    execute=skill_analyze_problem,
    parameters={"problem": "Problem to analyze", "depth": "Analysis depth"}
))

registry.register(Skill(
    name="make_decision",
    description="Make a decision between options",
    domain="reasoning",
    execute=skill_make_decision,
    parameters={"options": "Options to choose from", "criteria": "Decision criteria"}
))

registry.register(Skill(
    name="create_argument",
    description="Create an argument for a claim",
    domain="reasoning",
    execute=skill_create_argument,
    parameters={"claim": "Claim to argue for", "audience": "Target audience"}
))

registry.register(Skill(
    name="find_assumptions",
    description="Find assumptions in text",
    domain="reasoning",
    execute=skill_find_assumptions,
    parameters={"text": "Text to analyze"}
))


# ═══════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════

__all__ = [
    'Skill', 'SkillRegistry', 'registry',
    'DOMAINS', 'SKILL_COUNT', 'list_all_skills', 'get_skill_help'
]

# Domain list for reference
DOMAINS = [
    "code", "web", "files", "system",
    "creative", "analysis", "communication", "planning", "reasoning"
]

# Skill count
SKILL_COUNT = len(registry._skills)


def list_all_skills() -> Dict[str, List[str]]:
    """List all skills organized by domain."""
    return {domain: registry._domains.get(domain, []) for domain in DOMAINS}


def get_skill_help(skill_name: str) -> str:
    """Get help text for a skill."""
    skill = registry.get(skill_name)
    if not skill:
        return f"Skill '{skill_name}' not found"

    lines = [
        f"Skill: {skill.name}",
        f"Domain: {skill.domain}",
        f"Description: {skill.description}",
        "",
        "Parameters:"
    ]
    for param, desc in skill.parameters.items():
        lines.append(f"  - {param}: {desc}")

    if skill.examples:
        lines.append("")
        lines.append("Examples:")
        for ex in skill.examples:
            lines.append(f"  - {ex}")

    return '\n'.join(lines)