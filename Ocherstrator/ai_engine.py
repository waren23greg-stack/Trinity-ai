"""
Trinity-ai Cognitive Engine
Uses LangChain ReAct pattern to diagnose infrastructure faults.
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Pinecone
from langchain.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

class NightingaleEngine:
    """
    The reasoning brain of Trinity.
    Ingests telemetry, retrieves past incidents, and selects remediation scripts.
    """
    
    def __init__(self, llm_backend="ollama", model="llama3.1:70b"):
        # Initialize LLM (local Ollama for HIPAA compliance)
        self.llm = Ollama(model=model, temperature=0.1)  # Low temp = deterministic reasoning
        
        # Connect to vector DB of past incidents
        self.vector_store = Pinecone.from_existing_index(
            index_name="nightingale-incidents",
            embedding=self.llm
        )
        
        # Register available "Tools" the AI can call
        self.tools = self._register_tools()
        
        # Build the ReAct agent
        self.agent = self._build_agent()
    
    def _register_tools(self) -> list:
        """
        Tools are the AI's 'hands.' Each tool maps to a Python function
        or an Ansible playbook that the agent can invoke.
        """
        return [
            Tool(
                name="check_device_status",
                func=self._check_device_status,
                description="Pings a device or queries its SNMP OID. Use this FIRST to confirm the device is actually offline."
            ),
            Tool(
                name="query_past_incidents",
                func=self._query_past_incidents,
                description="Searches the vector database for similar past incidents and their resolutions."
            ),
            Tool(
                name="execute_remediation_script",
                func=self._execute_script,
                description="Executes an Ansible playbook or PowerShell script. WARNING: Only call after confirming root cause."
            ),
            Tool(
                name="check_network_topology",
                func=self._check_topology,
                description="Returns the current network topology and health of all upstream switches."
            ),
            Tool(
                name="escalate_to_human",
                func=self._escalate,
                description="Use this ONLY after 3 failed remediation attempts. Generates a Waren Packet."
            )
        ]
    
    def _build_agent(self):
        """Builds the ReAct agent with strict guardrails."""
        prompt = PromptTemplate.from_template("""
        You are Trinity, an autonomous IT operations agent for a hospital.
        
        CURRENT TELEMETRY:
        {telemetry}
        
        REASONING RULES:
        1. NEVER execute a destructive script (format, delete, factory_reset) without human approval.
        2. ALWAYS confirm the device is actually offline before assuming hardware failure.
        3. If 4+ devices fail simultaneously, suspect an upstream cause (switch, router, ISP).
        4. Maximum 3 remediation attempts. After that, escalate to Warren.
        
        Use the following tools to diagnose and fix the issue:
        {tools}
        
        Use this format:
        Thought: [your reasoning]
        Action: [tool name]
        Action Input: [tool input]
        Observation: [tool output]
        ... (repeat Thought/Action/Observation)
        Final Answer: [JSON with root_cause, script, confidence, should_escalate]
        
        Begin!
        """)
        
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,  # Prevent infinite loops
            handle_parsing_errors=True,
            early_stopping_method="generate"
        )
    
    def diagnose(self, telemetry: dict) -> dict:
        """
        Main entry point. Called by triage_loop.py.
        Returns a dict with root_cause, recommended_script, and confidence.
        """
        logger.info(f"Diagnosing telemetry: {telemetry}")
        
        try:
            result = self.agent.invoke({"telemetry": telemetry})
            return self._parse_agent_output(result)
        except Exception as e:
            logger.error(f"Agent failed: {e}")
            return {
                "root_cause": "unknown",
                "script": None,
                "confidence": 0.0,
                "should_escalate": True,
                "error": str(e)
            }
    
    def _parse_agent_output(self, raw_output: dict) -> dict:
        """Extracts the Final Answer JSON from the agent's verbose output."""
        # In production: parse JSON from the 'output' field
        # For now, return a structured stub
        return {
            "root_cause": "network_loop",
            "script": "stp_recalculate.yml",
            "confidence": 0.92,
            "should_escalate": False
        }
    
    # ===== TOOL IMPLEMENTATIONS =====
    
    def _check_device_status(self, device_id: str) -> str:
        """Pings device or queries SNMP. Returns 'online' or 'offline'."""
        # Implementation: use subprocess to ping, or pysnmp for OID query
        pass
    
    def _query_past_incidents(self, query: str) -> str:
        """Semantic search over past incidents."""
        results = self.vector_store.similarity_search(query, k=5)
        return "\n".join([r.page_content for r in results])
    
    def _execute_script(self, script_name: str) -> str:
        """Triggers Ansible AWX or runs a local script."""
        # Implementation: call Ansible AWX API
        pass
    
    def _check_topology(self) -> str:
        """Returns current network topology map."""
        pass
    
    def _escalate(self, reason: str) -> str:
        """Triggers Warren Packet generation."""
        from .warren_packet import generate_packet
        return generate_packet(reason)
