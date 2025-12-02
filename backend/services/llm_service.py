import os
import asyncio
from typing import Dict, Any, List, Optional
import logging
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with GPT-4.1 API."""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        logger.info(f"LLM Service initialized with model: {self.model}")
    
    def _sync_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Synchronous generation using GPT-4.1."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate a response using GPT-4.1 (async wrapper)."""
        try:
            # Run synchronous OpenAI call in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._sync_generate(prompt, system_prompt, temperature, max_tokens)
            )
            return response
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    async def analyze_electrolyte_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze an electrolyte design query using GPT-4.1."""
        system_prompt = """You are an expert electrochemist specializing in lithium-ion battery electrolyte design.
Analyze the user's query and extract:
1. Target application (EV, consumer electronics, grid storage, etc.)
2. Desired properties (high voltage, fast charging, long cycle life, etc.)
3. Specific components mentioned (solvents, salts, additives)
4. Operating conditions (temperature, voltage range)
5. Electrode materials mentioned

Return your analysis as a structured JSON object."""

        context_str = ""
        if context:
            context_str = f"\n\nAdditional context from RAG:\n{context}"
        
        prompt = f"""Analyze this electrolyte design query:

Query: {query}
{context_str}

Provide a detailed analysis in JSON format."""

        try:
            response = await self.generate(prompt, system_prompt, temperature=0.3)
            return {"analysis": response, "status": "success"}
        except Exception as e:
            return {"analysis": None, "status": "error", "error": str(e)}
    
    async def generate_formulation_rationale(
        self,
        formulation: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> str:
        """Generate scientific rationale for a proposed formulation using GPT-4.1."""
        system_prompt = """You are an expert electrochemist. Provide a clear, scientific rationale
for the proposed electrolyte formulation. Explain:
1. Why each component was chosen
2. Expected synergistic effects
3. Potential concerns and mitigations
4. Comparison to standard formulations

Be concise but scientifically rigorous."""

        formulation_str = "\n".join([
            f"- {comp['name']} ({comp.get('abbreviation', '')}): {comp.get('concentration', '')} {comp.get('unit', '')}"
            for comp in formulation
        ])
        
        requirements_str = f"""
- Application: {requirements.get('application', 'general')}
- Target voltage: {requirements.get('operating_conditions', {}).get('max_voltage', 4.2)}V
- Anode: {requirements.get('electrode_materials', {}).get('anode', 'graphite')}
- Cathode: {requirements.get('electrode_materials', {}).get('cathode', 'NMC')}
"""

        prompt = f"""Generate a scientific rationale for this electrolyte formulation:

Formulation:
{formulation_str}

Requirements:
{requirements_str}

Provide a concise but comprehensive rationale."""

        try:
            return await self.generate(prompt, system_prompt, temperature=0.5, max_tokens=500)
        except Exception as e:
            logger.error(f"Failed to generate rationale: {e}")
            return "Rationale generation failed. Please review formulation manually."
    
    async def summarize_literature(self, documents: List[Dict[str, Any]], query: str) -> str:
        """Summarize relevant literature findings using GPT-4.1."""
        system_prompt = """You are an expert at summarizing scientific literature on battery electrolytes.
Synthesize the key findings from the provided documents, focusing on:
1. Relevant formulations mentioned
2. Performance data and benchmarks
3. Key insights for electrolyte design
4. Any contradicting findings or debates in the field

Be concise and cite specific findings where relevant."""

        docs_text = "\n\n".join([
            f"Document {i+1} (Source: {doc.get('source', 'unknown')}):\n{doc.get('content', '')[:1000]}"
            for i, doc in enumerate(documents[:5])
        ])
        
        prompt = f"""Summarize these documents in relation to the query: "{query}"

Documents:
{docs_text}

Provide a synthesized summary of the key findings."""

        try:
            return await self.generate(prompt, system_prompt, temperature=0.3, max_tokens=800)
        except Exception as e:
            logger.error(f"Failed to summarize literature: {e}")
            return "Unable to summarize literature. Please review documents manually."
    
    async def predict_compatibility(
        self,
        components: List[str],
        conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use GPT-4.1 to predict compatibility issues."""
        system_prompt = """You are an expert electrochemist. Analyze the compatibility of the given
electrolyte components under the specified conditions. Identify:
1. Known compatibility issues
2. Potential degradation pathways
3. Temperature-dependent concerns
4. Electrode material interactions

Provide specific, actionable insights based on electrochemistry principles."""

        prompt = f"""Analyze compatibility for these electrolyte components:

Components: {', '.join(components)}

Operating Conditions:
- Max voltage: {conditions.get('max_voltage', 4.2)}V
- Temperature range: {conditions.get('min_temperature', -20)}°C to {conditions.get('max_temperature', 45)}°C

Identify any compatibility concerns and suggest mitigations."""

        try:
            response = await self.generate(prompt, system_prompt, temperature=0.3)
            return {"analysis": response, "status": "success"}
        except Exception as e:
            return {"analysis": None, "status": "error", "error": str(e)}


# Global instance
llm_service = LLMService()

