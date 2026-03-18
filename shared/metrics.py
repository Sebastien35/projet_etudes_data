from prometheus_client import Counter, Histogram

VERDICT_COUNTER = Counter(
    "fakenews_verdict_total",
    "Fact-check verdicts by label",
    ["verdict"],
)

RETRIEVAL_COUNTER = Counter(
    "fakenews_retrieval_total",
    "RAG retrieval source: rag | general_knowledge | error",
    ["source"],
)

LLM_LATENCY = Histogram(
    "fakenews_llm_latency_seconds",
    "End-to-end LLM call duration (RAG retrieval + generation)",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0],
)

RAG_CONTEXT_CHARS = Histogram(
    "fakenews_rag_context_chars",
    "Total characters in RAG context chunks passed to the LLM",
    buckets=[0, 100, 300, 500, 1000, 2000, 5000],
)
