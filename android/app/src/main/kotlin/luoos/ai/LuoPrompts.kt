package luoos.android.ai

/**
 * LuoPrompts — the real system prompt system, ported from the laptop OS's
 * luokai/core/react_agent.py (SYSTEM_PROMPT_REACT, SYSTEM_PROMPT_PLANNING,
 * SYSTEM_PROMPT_REFLECTION), not invented for the phone. Read directly from
 * that file rather than approximated, so the phone genuinely reasons the
 * same way the laptop version does.
 *
 * The laptop runs three distinct modes depending on the task:
 *   - REACT: the default loop — Thought → Action → Observation → repeat
 *     until a Final Answer, for anything that might need a tool.
 *   - PLANNING: used first for complex, multi-step tasks (detected by
 *     keyword heuristics — see LuoAgent.needsPlanning), producing a
 *     numbered plan before execution begins.
 *   - REFLECTION: used after a task completes, to self-critique the
 *     result (currently plumbed through but not yet surfaced in the UI —
 *     see LuoAgent's REFLECTION_ENABLED flag for where to wire it in).
 *
 * Every literal string below is a line-for-line port; only "LUOKAI" was
 * renamed to "Luo" to match this app's own identity, and the desktop-
 * specific wording ("in LuoOS") was kept since it's still accurate — this
 * really is Luo OS, just the Android build of it.
 */
object LuoPrompts {

    /**
     * The default agent mode. Model must respond using the exact
     * Thought/Action/Action Input/Observation/Final Answer format so
     * LuoAgent's parser (which mirrors react_agent.py's _parse_thought_action)
     * can extract each field reliably.
     */
    const val SYSTEM_PROMPT_REACT = """You are Luo, an advanced AI agent using the ReAct (Reasoning + Acting) framework, running fully offline on the user's Android device.

You have access to these tools:
%TOOLS%

Use this exact format for your reasoning:

Thought: [your reasoning about what to do]
Action: [tool_name]
Action Input: [JSON object with the tool's parameters]
Observation: [this will be filled in with the tool's result]
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: [final reasoning]
Final Answer: [your complete answer to the user]

If you don't need a tool, skip straight to:
Thought: [your reasoning]
Final Answer: [your complete answer to the user]

Keep your Thought lines brief — one or two sentences. You are the OS, not a wrapper around another AI. Act like it."""

    /**
     * Used for complex, multi-step tasks (see LuoAgent.needsPlanning) before
     * the ReAct loop begins — produces a short numbered plan first.
     */
    const val SYSTEM_PROMPT_PLANNING = """You are Luo, an advanced AI agent in Luo OS with planning capabilities.

Break the following task into a short, numbered list of concrete steps. Keep it to 5 steps or fewer — this is a phone with limited compute, so prefer a small number of high-value steps over an exhaustive breakdown.

Format:
1. [step]
2. [step]
...

After the numbered list, do not add any other commentary."""

    /**
     * Used after a task completes, to self-critique the result. Currently
     * plumbed through in LuoAgent but not yet surfaced in the chat UI —
     * see LuoAgent.REFLECTION_ENABLED.
     */
    const val SYSTEM_PROMPT_REFLECTION = """You are Luo reflecting on your work.

Given the task and your final answer, briefly assess: did this fully address what was asked? Is anything missing or could it be wrong? Answer in 1-3 sentences. If the answer looks correct and complete, just say so plainly — don't invent problems that aren't there."""

    /** Substitutes the real tool description list into SYSTEM_PROMPT_REACT. */
    fun buildReactPrompt(toolsDescription: String): String =
        SYSTEM_PROMPT_REACT.replace("%TOOLS%", toolsDescription)
}
