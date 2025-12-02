from typing import Dict, Any, Optional, List
import asyncio
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent
from .literature_rag_agent import LiteratureRAGAgent
from .property_compatibility_agent import PropertyCompatibilityAgent
from .performance_prediction_agent import PerformancePredictionAgent
from .experiment_planning_agent import ExperimentPlanningAgent

# Query type constants
QUERY_TYPE_GREETING = "greeting"
QUERY_TYPE_HELP = "help"
QUERY_TYPE_OFF_TOPIC = "off_topic"
QUERY_TYPE_ELECTROLYTE_DESIGN = "electrolyte_design"
QUERY_TYPE_LITERATURE_ONLY = "literature_search"
QUERY_TYPE_PROPERTY_CHECK = "property_check"

class OrchestratorAgent(BaseAgent):
    """Main orchestrator agent that coordinates all other agents using GPT-4.1."""
    
    def __init__(self, vector_store=None):
        super().__init__(
            name="OrchestratorAgent",
            description="Interprets tasks and coordinates all other agents for electrolyte design using GPT-4.1"
        )
        
        # Initialize sub-agents
        self.literature_agent = LiteratureRAGAgent(vector_store)
        self.property_agent = PropertyCompatibilityAgent()
        self.prediction_agent = PerformancePredictionAgent()
        self.planning_agent = ExperimentPlanningAgent()
        
        self.agents = {
            "literature": self.literature_agent,
            "property": self.property_agent,
            "prediction": self.prediction_agent,
            "planning": self.planning_agent
        }
        
        # Initialize LLM service
        self.llm_service = None
        self._init_llm_service()
        
        # Pass LLM service to agents for chemistry-agnostic formulations and predictions
        if self.llm_service:
            self.prediction_agent.set_llm_service(self.llm_service)
            self.planning_agent.set_llm_service(self.llm_service)
    
    def _init_llm_service(self):
        """Initialize LLM service for GPT-4.1."""
        try:
            from services.llm_service import llm_service
            self.llm_service = llm_service
            self.log_action("LLM Service", "GPT-4.1 initialized successfully")
        except Exception as e:
            self.logger.warning(f"LLM service not available: {e}")
    
    def update_vector_store(self, vector_store):
        """Update the vector store for the literature agent."""
        self.literature_agent.set_vector_store(vector_store)
    
    async def _classify_query(self, query: str) -> Dict[str, Any]:
        """Use GPT-4.1 to classify the query type and determine routing."""
        
        # Quick heuristic checks for common simple queries
        query_lower = query.lower().strip()
        
        # Greeting patterns
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", 
                    "howdy", "greetings", "what's up", "sup", "yo"]
        if query_lower in greetings or any(query_lower.startswith(g) for g in greetings):
            return {
                "query_type": QUERY_TYPE_GREETING,
                "confidence": 0.95,
                "should_delegate": False,
                "reason": "Simple greeting detected"
            }
        
        # Help requests
        help_patterns = ["help", "what can you do", "how do i use", "what is this", 
                        "how does this work", "capabilities", "features"]
        if any(p in query_lower for p in help_patterns):
            return {
                "query_type": QUERY_TYPE_HELP,
                "confidence": 0.9,
                "should_delegate": False,
                "reason": "Help request detected"
            }
        
        # Use LLM for more complex classification if available
        if self.llm_service:
            try:
                classification = await self._llm_classify_query(query)
                return classification
            except Exception as e:
                self.logger.warning(f"LLM classification failed: {e}")
        
        # Default: assume electrolyte design query
        return {
            "query_type": QUERY_TYPE_ELECTROLYTE_DESIGN,
            "confidence": 0.7,
            "should_delegate": True,
            "reason": "Defaulting to electrolyte design workflow"
        }
    
    async def _llm_classify_query(self, query: str) -> Dict[str, Any]:
        """Use GPT-4.1 to classify the query."""
        system_prompt = """You are a query classifier for an electrolyte design system. 
Classify the user's query into one of these categories:

1. "greeting" - Simple greetings like "hello", "hi", casual conversation starters
2. "help" - Questions about how to use the system, what it can do
3. "off_topic" - Questions unrelated to batteries, electrolytes, or chemistry
4. "electrolyte_design" - Requests to design, formulate, or recommend electrolytes
5. "literature_search" - Questions about existing research, papers, or knowledge
6. "property_check" - Questions about specific component properties or compatibility

Return ONLY a JSON object with:
- query_type: one of the categories above
- confidence: 0.0 to 1.0
- reason: brief explanation
- should_delegate: true if specialized agents needed, false for direct response"""

        prompt = f'Classify this query: "{query}"'
        
        response = await self.llm_service.generate(prompt, system_prompt, temperature=0.1, max_tokens=200)
        
        # Parse the response
        import json
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # If parsing fails, default to electrolyte design
            return {
                "query_type": QUERY_TYPE_ELECTROLYTE_DESIGN,
                "confidence": 0.6,
                "should_delegate": True,
                "reason": "Classification parsing failed, defaulting to design workflow"
            }
    
    async def _handle_simple_query(self, query: str, query_type: str) -> Dict[str, Any]:
        """Handle simple queries that don't need agent delegation."""
        start_time = time.time()
        
        if query_type == QUERY_TYPE_GREETING:
            if self.llm_service:
                response = await self.llm_service.generate(
                    f"User said: '{query}'. Respond warmly and briefly introduce yourself as an AI assistant for electrolyte design. Mention you can help design battery electrolytes and generate experiment plans.",
                    "You are a friendly AI assistant specializing in lithium-ion battery electrolyte design.",
                    temperature=0.7,
                    max_tokens=150
                )
            else:
                response = "Hello! I'm the Electrolyte Design Assistant. I can help you design battery electrolytes, analyze component compatibility, predict performance, and generate detailed experiment plans. What would you like to work on today?"
            
            return {
                "query": query,
                "agent_responses": [{
                    "agent_type": "orchestrator",
                    "status": "success",
                    "message": "Direct response - greeting",
                    "data": {"response_type": "greeting"}
                }],
                "experiment_plans": [],
                "summary": response,
                "processing_time": round(time.time() - start_time, 2),
                "requirements_parsed": {}
            }
        
        elif query_type == QUERY_TYPE_HELP:
            help_text = """## Electrolyte Design System - Help

### What I Can Do:
I'm an AI-powered multi-agent system for lithium-ion battery electrolyte design. Here's how I can help:

**🔬 Design Electrolytes**
- Describe your requirements (high voltage, fast charging, long cycle life, etc.)
- Specify electrode materials (NMC, LFP, silicon anode, etc.)
- I'll generate optimized formulations with scientific rationale

**📚 Search Literature**
- Upload research papers (PDF) for me to index
- I'll search both uploaded documents and my knowledge base
- Get summaries of relevant electrolyte research

**⚗️ Check Compatibility**
- Ask about specific components (EC, DMC, LiPF6, VC, FEC, etc.)
- I'll identify compatibility issues and constraints
- Get recommendations for safe formulations

**📊 Predict Performance**
- Get predictions for capacity retention, cycle life, rate capability
- Understand temperature operating ranges
- Compare different formulation options

### Example Queries:
- "Design a high-voltage electrolyte for NMC cathode with silicon anode"
- "What additives improve cycle life for fast-charging applications?"
- "Check compatibility of LiPF6 with FEC at high temperatures"
- "Compare EC/DMC vs EC/EMC solvent systems"

### Getting Started:
Simply describe your electrolyte design requirements, and I'll coordinate multiple specialized agents to deliver three optimized experiment plans!

---
*Powered by GPT-4.1 and multi-agent AI*"""
            
            return {
                "query": query,
                "agent_responses": [{
                    "agent_type": "orchestrator",
                    "status": "success",
                    "message": "Direct response - help information",
                    "data": {"response_type": "help"}
                }],
                "experiment_plans": [],
                "summary": help_text,
                "processing_time": round(time.time() - start_time, 2),
                "requirements_parsed": {}
            }
        
        elif query_type == QUERY_TYPE_OFF_TOPIC:
            if self.llm_service:
                response = await self.llm_service.generate(
                    f"User asked: '{query}'. Politely explain that you specialize in battery electrolyte design and redirect them. Be helpful but brief.",
                    "You are an AI assistant specializing in lithium-ion battery electrolyte design. Politely redirect off-topic questions.",
                    temperature=0.7,
                    max_tokens=150
                )
            else:
                response = "I'm specialized in lithium-ion battery electrolyte design. I can help you design electrolyte formulations, check component compatibility, predict performance, and generate experiment plans. Would you like to explore any of these capabilities?"
            
            return {
                "query": query,
                "agent_responses": [{
                    "agent_type": "orchestrator",
                    "status": "success",
                    "message": "Direct response - redirected off-topic query",
                    "data": {"response_type": "off_topic_redirect"}
                }],
                "experiment_plans": [],
                "summary": response,
                "processing_time": round(time.time() - start_time, 2),
                "requirements_parsed": {}
            }
        
        # Default fallback
        return None
    
    async def process(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process user query with intelligent routing."""
        start_time = time.time()
        query = input_data.get("query", "")
        user_materials_input = input_data.get("user_materials_input", "")
        
        # Store user materials input for later use in _parse_query
        self._user_materials_input = user_materials_input
        
        self.log_action("Processing query", query)
        if user_materials_input:
            self.log_action("User-specified materials input", user_materials_input)
        
        # Step 0: Classify the query to determine routing
        classification = await self._classify_query(query)
        self.log_action("Query classified", f"{classification['query_type']} (confidence: {classification['confidence']:.2f})")
        
        # Handle simple queries directly without agent delegation
        if not classification.get("should_delegate", True):
            simple_response = await self._handle_simple_query(query, classification["query_type"])
            if simple_response:
                return simple_response
        
        # For literature-only queries, only invoke literature agent
        if classification["query_type"] == QUERY_TYPE_LITERATURE_ONLY:
            return await self._handle_literature_query(query, start_time)
        
        # For property-check queries, only invoke property agent
        if classification["query_type"] == QUERY_TYPE_PROPERTY_CHECK:
            return await self._handle_property_query(query, start_time)
        
        # Full electrolyte design workflow
        return await self._handle_design_query(query, start_time)
    
    async def _handle_literature_query(self, query: str, start_time: float) -> Dict[str, Any]:
        """Handle literature search queries."""
        self.log_action("Routing", "Literature search only")
        
        literature_result = await self.literature_agent.process({"query": query})
        
        # Enhance with LLM summarization
        if self.llm_service and literature_result.get("results"):
            try:
                summary = await self.llm_service.summarize_literature(
                    literature_result.get("results", []),
                    query
                )
                literature_result["llm_summary"] = summary
            except Exception as e:
                self.logger.warning(f"LLM summarization failed: {e}")
        
        response_summary = literature_result.get("llm_summary", literature_result.get("summary", ""))
        
        return {
            "query": query,
            "agent_responses": [{
                "agent_type": "literature_rag",
                "status": literature_result.get("status", "success"),
                "message": f"Found {literature_result.get('sources_count', 0)} relevant sources",
                "data": literature_result
            }],
            "experiment_plans": [],
            "summary": f"## Literature Search Results\n\n{response_summary}",
            "processing_time": round(time.time() - start_time, 2),
            "requirements_parsed": {}
        }
    
    async def _handle_property_query(self, query: str, start_time: float) -> Dict[str, Any]:
        """Handle property/compatibility check queries."""
        self.log_action("Routing", "Property check only")
        
        # Parse components from query
        requirements = self._parse_query(query)
        components = requirements.get("components", [])
        
        property_result = await self.property_agent.process({
            "components": components,
            "operating_conditions": requirements.get("operating_conditions", {}),
            "electrode_materials": requirements.get("electrode_materials", {})
        })
        
        # Enhance with LLM analysis
        if self.llm_service:
            try:
                llm_analysis = await self.llm_service.predict_compatibility(
                    components,
                    requirements.get("operating_conditions", {})
                )
                property_result["llm_analysis"] = llm_analysis.get("analysis", "")
            except Exception as e:
                self.logger.warning(f"LLM compatibility analysis failed: {e}")
        
        # Build summary
        summary_parts = [f"## Property & Compatibility Analysis\n"]
        summary_parts.append(f"**Components analyzed**: {', '.join(components)}\n")
        
        if property_result.get("compatibility_issues"):
            summary_parts.append("### Compatibility Issues:")
            for issue in property_result["compatibility_issues"]:
                summary_parts.append(f"- **{issue.get('severity', 'unknown').upper()}**: {issue.get('issue', '')}")
                summary_parts.append(f"  - Solution: {issue.get('solution', 'N/A')}")
        
        if property_result.get("recommendations"):
            summary_parts.append("\n### Recommendations:")
            for rec in property_result["recommendations"]:
                summary_parts.append(f"- {rec}")
        
        if property_result.get("llm_analysis"):
            summary_parts.append(f"\n### GPT-4.1 Analysis:\n{property_result['llm_analysis']}")
        
        return {
            "query": query,
            "agent_responses": [{
                "agent_type": "property_compatibility",
                "status": property_result.get("status", "success"),
                "message": f"Analyzed {len(components)} components",
                "data": property_result
            }],
            "experiment_plans": [],
            "summary": "\n".join(summary_parts),
            "processing_time": round(time.time() - start_time, 2),
            "requirements_parsed": requirements
        }
    
    async def _handle_design_query(self, query: str, start_time: float) -> Dict[str, Any]:
        """Handle full electrolyte design queries - coordinates all agents."""
        self.log_action("Routing", "Full design workflow")
        
        # Use GPT-4.1 to analyze the query
        requirements = await self._analyze_query_with_llm(query)
        
        agent_responses = []
        
        # Step 1: Literature search
        self.log_action("Step 1", "Literature and RAG search")
        literature_result = await self.literature_agent.process({"query": query})
        
        if self.llm_service and literature_result.get("results"):
            try:
                summary = await self.llm_service.summarize_literature(
                    literature_result.get("results", []),
                    query
                )
                literature_result["llm_summary"] = summary
            except Exception as e:
                self.logger.warning(f"LLM summarization failed: {e}")
        
        agent_responses.append({
            "agent_type": "literature_rag",
            "status": literature_result.get("status", "success"),
            "message": f"Found {literature_result.get('sources_count', 0)} relevant sources",
            "data": literature_result
        })
        
        # Step 2: Property and compatibility check
        self.log_action("Step 2", "Property and compatibility analysis")
        components = requirements.get("components", ["EC", "EMC", "LiPF6", "VC"])
        property_result = await self.property_agent.process({
            "components": components,
            "operating_conditions": requirements.get("operating_conditions", {}),
            "electrode_materials": requirements.get("electrode_materials", {})
        })
        
        if self.llm_service:
            try:
                llm_compatibility = await self.llm_service.predict_compatibility(
                    components,
                    requirements.get("operating_conditions", {})
                )
                property_result["llm_analysis"] = llm_compatibility.get("analysis", "")
            except Exception as e:
                self.logger.warning(f"LLM compatibility analysis failed: {e}")
        
        agent_responses.append({
            "agent_type": "property_compatibility",
            "status": property_result.get("status", "success"),
            "message": f"Analyzed {len(components)} components, found {len(property_result.get('compatibility_issues', []))} issues",
            "data": property_result
        })
        
        # Step 3: Experiment planning (MOVED BEFORE prediction)
        # ExperimentPlanningAgent creates the formulations FIRST
        self.log_action("Step 3", "Generating experiment plans with formulations")
        planning_result = await self.planning_agent.process({
            "query": query,
            "literature_data": literature_result,
            "property_data": property_result,
            "target_application": requirements.get("application", "general"),
            "battery_type": requirements.get("battery_type", ""),
            "operating_conditions": requirements.get("operating_conditions", {}),
            "electrode_materials": requirements.get("electrode_materials", {}),
            "user_specified_materials": requirements.get("user_specified_materials", []),
            "detected_components": requirements.get("components", [])
        })
        
        experiment_plans = planning_result.get("experiment_plans", [])
        
        agent_responses.append({
            "agent_type": "experiment_planning",
            "status": planning_result.get("status", "success"),
            "message": f"Generated {planning_result.get('total_plans', 0)} experiment plans with formulations",
            "data": planning_result
        })
        
        # Step 4: Performance prediction for EACH formulation created by ExperimentPlanningAgent
        self.log_action("Step 4", "Predicting performance for each formulation")
        all_predictions = []
        
        for i, plan in enumerate(experiment_plans):
            # Convert formulation from list format to dict format for prediction agent
            formulation_dict = self._convert_formulation_to_dict(plan.get("formulation", []))
            
            self.log_action(f"Step 4.{i+1}", f"Predicting performance for: {plan.get('title', f'Plan {i+1}')}")
            
            prediction_result = await self.prediction_agent.process({
                "formulation": formulation_dict,
                "operating_conditions": requirements.get("operating_conditions", {}),
                "electrode_materials": requirements.get("electrode_materials", {}),
                "battery_type": requirements.get("battery_type", ""),
                "query_context": query
            })
            
            # Attach the prediction results directly to the plan
            plan["predicted_performance"] = prediction_result.get("predictions", {})
            plan["prediction_confidence"] = prediction_result.get("confidence_score", 0.0)
            plan["prediction_notes"] = prediction_result.get("model_notes", [])
            
            all_predictions.append({
                "plan_id": plan.get("plan_id", f"plan_{i+1}"),
                "plan_title": plan.get("title", f"Plan {i+1}"),
                "predictions": prediction_result.get("predictions", {}),
                "confidence_score": prediction_result.get("confidence_score", 0.0)
            })
        
        # Calculate average confidence across all plans
        avg_confidence = sum(p.get("confidence_score", 0) for p in all_predictions) / len(all_predictions) if all_predictions else 0
        
        agent_responses.append({
            "agent_type": "performance_prediction",
            "status": "success",
            "message": f"Evaluated {len(experiment_plans)} formulations with {avg_confidence:.0%} average confidence",
            "data": {
                "predictions_per_plan": all_predictions,
                "average_confidence": round(avg_confidence, 2),
                "total_plans_evaluated": len(experiment_plans)
            }
        })
        
        # Generate LLM rationale for each plan (now with actual predictions)
        if self.llm_service:
            for plan in experiment_plans:
                try:
                    rationale = await self.llm_service.generate_formulation_rationale(
                        plan.get("formulation", []),
                        requirements
                    )
                    plan["llm_rationale"] = rationale
                except Exception as e:
                    self.logger.warning(f"LLM rationale generation failed: {e}")
        
        processing_time = time.time() - start_time
        
        summary = await self._generate_summary_with_llm(
            query, agent_responses, experiment_plans, requirements
        )
        
        return {
            "query": query,
            "agent_responses": agent_responses,
            "experiment_plans": experiment_plans,
            "summary": summary,
            "processing_time": round(processing_time, 2),
            "requirements_parsed": requirements
        }
    
    def _convert_formulation_to_dict(self, formulation_list: List[Dict[str, Any]]) -> Dict[str, float]:
        """Convert formulation from list format (ExperimentPlanningAgent) to dict format (PerformancePredictionAgent).
        
        Input format (from ExperimentPlanningAgent):
        [
            {"name": "Ethylene Carbonate", "abbreviation": "EC", "concentration": 30, "unit": "vol%", "role": "solvent"},
            ...
        ]
        
        Output format (for PerformancePredictionAgent):
        {"EC": 30, "EMC": 70, "LiPF6": 1.0, ...}
        """
        formulation_dict = {}
        for component in formulation_list:
            abbrev = component.get("abbreviation", "")
            concentration = component.get("concentration", 0)
            if abbrev:
                formulation_dict[abbrev] = concentration
        return formulation_dict
    
    async def _analyze_query_with_llm(self, query: str) -> Dict[str, Any]:
        """Use GPT-4.1 to analyze the query and extract requirements."""
        requirements = self._parse_query(query)
        
        if self.llm_service:
            try:
                llm_analysis = await self.llm_service.analyze_electrolyte_query(query)
                if llm_analysis.get("status") == "success":
                    requirements["llm_analysis"] = llm_analysis.get("analysis", "")
            except Exception as e:
                self.logger.warning(f"LLM query analysis failed: {e}")
        
        return requirements
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """Parse user query to extract requirements."""
        query_lower = query.lower()
        requirements = {
            "components": [],
            "operating_conditions": {},
            "electrode_materials": {},
            "application": "general",
            "battery_type": ""
        }
        
        # Detect battery chemistry type FIRST - this determines applicable components
        if any(kw in query_lower for kw in ["zinc", "zn-ion", "zn ion", "zinc-ion", "aqueous zinc", "zn metal", "zn anode", "zinc metal", "zinc anode"]):
            requirements["battery_type"] = "zinc"
        elif any(kw in query_lower for kw in ["sodium", "na-ion", "na ion", "sodium-ion", "na metal"]):
            requirements["battery_type"] = "sodium-ion"
        elif any(kw in query_lower for kw in ["magnesium", "mg-ion", "mg ion", "magnesium-ion", "mg metal"]):
            requirements["battery_type"] = "magnesium"
        elif any(kw in query_lower for kw in ["solid-state", "solid state", "all-solid", "solid electrolyte", "polymer electrolyte"]):
            requirements["battery_type"] = "solid-state"
        elif any(kw in query_lower for kw in ["lithium", "li-ion", "li ion", "lithium-ion", "lipf6", "lifsi"]):
            requirements["battery_type"] = "lithium-ion"
        elif any(kw in query_lower for kw in ["aqueous", "water-based", "water based"]):
            requirements["battery_type"] = "aqueous"
        else:
            # Let the agents infer from the query context
            requirements["battery_type"] = ""
        
        # Detect components based on battery type
        detected_battery = requirements["battery_type"]
        
        if detected_battery == "zinc":
            # Zinc battery components
            zn_salts = ["znso4", "zn(cf3so3)2", "zncl2", "zn triflate", "zinc triflate", "zinc sulfate"]
            for salt in zn_salts:
                if salt in query_lower:
                    requirements["components"].append(salt.upper())
            zn_additives = ["litfsi", "mno2", "mnso4"]
            for add in zn_additives:
                if add in query_lower:
                    requirements["components"].append(add.upper())
                    
        elif detected_battery == "sodium-ion":
            # Sodium battery components
            na_salts = ["napf6", "natfsi", "nafsi", "naclo4"]
            for salt in na_salts:
                if salt in query_lower:
                    requirements["components"].append(salt.upper())
            na_solvents = ["ec", "pc", "dme", "diglyme", "tetraglyme"]
            for solv in na_solvents:
                if solv in query_lower:
                    requirements["components"].append(solv.upper())
                    
        elif detected_battery == "magnesium":
            # Magnesium battery components
            mg_salts = ["mgcl2", "mg(tfsi)2", "mgtfsi2"]
            for salt in mg_salts:
                if salt in query_lower:
                    requirements["components"].append(salt.upper())
            mg_solvents = ["thf", "dme", "diglyme", "tetraglyme", "tegdme"]
            for solv in mg_solvents:
                if solv in query_lower:
                    requirements["components"].append(solv.upper())
                    
        else:
            # Lithium-ion or unspecified - detect Li-ion components
            solvents = ["EC", "DMC", "EMC", "DEC", "PC"]
            for solvent in solvents:
                if solvent.lower() in query_lower:
                    requirements["components"].append(solvent)
            
            salts = ["LiPF6", "LiFSI", "LiTFSI", "LiBF4"]
            for salt in salts:
                if salt.lower() in query_lower:
                    requirements["components"].append(salt)
            
            additives = ["VC", "FEC", "PS", "LiBOB", "DTD"]
            for additive in additives:
                if additive.lower() in query_lower:
                    requirements["components"].append(additive)
        
        # Extract ANY user-specified materials not in predefined lists
        # This allows users to specify custom electrolyte materials
        user_specified_materials = self._extract_user_materials(query)
        
        # Also extract materials from the dedicated user input field (frontend textarea)
        user_input_materials = []
        if hasattr(self, '_user_materials_input') and self._user_materials_input:
            user_input_materials = self._extract_user_materials(self._user_materials_input)
            # Also store the raw input for LLM context
            requirements["user_materials_raw_input"] = self._user_materials_input.strip()
        
        # Combine both sources
        all_user_materials = list(set(user_specified_materials + user_input_materials))
        
        if all_user_materials:
            requirements["user_specified_materials"] = all_user_materials
            # Add to components if not already there
            for material in all_user_materials:
                if material.upper() not in [c.upper() for c in requirements["components"]]:
                    requirements["components"].append(material)
        
        # DO NOT default to Li-ion components for non-Li-ion batteries
        # Let the ExperimentPlanningAgent generate appropriate formulations
        # Only default for lithium-ion when no components detected AND no user-specified materials
        if not requirements["components"] and not all_user_materials and detected_battery in ["lithium-ion", ""]:
            requirements["components"] = ["EC", "EMC", "LiPF6"]
        
        # Detect operating conditions based on battery type
        if detected_battery == "zinc":
            # Zinc batteries typically operate at lower voltages
            requirements["operating_conditions"]["max_voltage"] = 1.8  # Typical Zn voltage
            requirements["operating_conditions"]["max_temperature"] = 50
        elif detected_battery == "sodium-ion":
            requirements["operating_conditions"]["max_voltage"] = 4.0
            requirements["operating_conditions"]["max_temperature"] = 55
        elif detected_battery == "magnesium":
            requirements["operating_conditions"]["max_voltage"] = 3.0
            requirements["operating_conditions"]["max_temperature"] = 50
        else:
            # Li-ion voltage/temp detection
            if "high voltage" in query_lower or "high-voltage" in query_lower:
                requirements["operating_conditions"]["max_voltage"] = 4.5
            elif "4.5" in query_lower or "4.6" in query_lower:
                requirements["operating_conditions"]["max_voltage"] = 4.5
            elif "4.3" in query_lower or "4.4" in query_lower:
                requirements["operating_conditions"]["max_voltage"] = 4.35
            else:
                requirements["operating_conditions"]["max_voltage"] = 4.2
            
            if "high temp" in query_lower or "high-temp" in query_lower or "thermal" in query_lower:
                requirements["operating_conditions"]["max_temperature"] = 60
            elif "low temp" in query_lower or "cold" in query_lower:
                requirements["operating_conditions"]["min_temperature"] = -30
            else:
                requirements["operating_conditions"]["max_temperature"] = 45
        
        # Detect electrode materials based on battery type
        if detected_battery == "zinc":
            requirements["electrode_materials"]["anode"] = "zinc metal"
            if "mno2" in query_lower or "manganese" in query_lower:
                requirements["electrode_materials"]["cathode"] = "MnO2"
            elif "v2o5" in query_lower or "vanadium" in query_lower:
                requirements["electrode_materials"]["cathode"] = "V2O5"
            else:
                requirements["electrode_materials"]["cathode"] = "MnO2"  # Common Zn cathode
        elif detected_battery == "sodium-ion":
            requirements["electrode_materials"]["anode"] = "hard carbon"
            requirements["electrode_materials"]["cathode"] = "Na layered oxide"
        elif detected_battery == "magnesium":
            requirements["electrode_materials"]["anode"] = "magnesium metal"
            requirements["electrode_materials"]["cathode"] = "Mo6S8 (Chevrel)"
        else:
            # Li-ion electrode detection
            if "silicon" in query_lower or "si anode" in query_lower:
                requirements["electrode_materials"]["anode"] = "silicon-graphite"
                if "FEC" not in requirements["components"]:
                    requirements["components"].append("FEC")
            elif "graphite" in query_lower:
                requirements["electrode_materials"]["anode"] = "graphite"
            else:
                requirements["electrode_materials"]["anode"] = "graphite"
            
            if "nmc" in query_lower or "ncm" in query_lower:
                requirements["electrode_materials"]["cathode"] = "NMC"
            elif "lco" in query_lower or "licoo2" in query_lower:
                requirements["electrode_materials"]["cathode"] = "LCO"
            elif "lfp" in query_lower or "lifepo4" in query_lower:
                requirements["electrode_materials"]["cathode"] = "LFP"
            else:
                requirements["electrode_materials"]["cathode"] = "NMC"
        
        # Detect application
        if "ev" in query_lower or "electric vehicle" in query_lower:
            requirements["application"] = "electric_vehicle"
        elif "grid" in query_lower or "storage" in query_lower:
            requirements["application"] = "grid_storage"
        elif "consumer" in query_lower or "phone" in query_lower or "laptop" in query_lower:
            requirements["application"] = "consumer_electronics"
        elif "fast charg" in query_lower:
            requirements["application"] = "fast_charging"
        
        return requirements
    
    def _extract_user_materials(self, query: str) -> List[str]:
        """Extract any electrolyte materials mentioned in the user's query.
        
        This captures materials not in predefined lists, allowing users to specify
        custom electrolyte components like specific solvents, salts, or additives.
        """
        import re
        
        # Common patterns for chemical compounds
        # Matches: chemical formulas, abbreviations, and common names
        materials = []
        query_lower = query.lower()
        
        # Expanded list of known electrolyte materials (beyond predefined lists)
        # This helps identify materials the user explicitly mentions
        known_materials = {
            # Solvents
            "dmso": "DMSO", "acetonitrile": "ACN", "acn": "ACN", 
            "propylene carbonate": "PC", "ethylene carbonate": "EC",
            "dimethyl carbonate": "DMC", "diethyl carbonate": "DEC",
            "ethyl methyl carbonate": "EMC", "gamma-butyrolactone": "GBL",
            "gbl": "GBL", "sulfolane": "Sulfolane", "dmf": "DMF",
            "dimethylformamide": "DMF", "nmp": "NMP", "thf": "THF",
            "tetrahydrofuran": "THF", "dme": "DME", "dimethoxyethane": "DME",
            "diglyme": "Diglyme", "triglyme": "Triglyme", "tetraglyme": "Tetraglyme",
            "tegdme": "TEGDME", "dol": "DOL", "dioxolane": "DOL",
            "water": "H2O", "h2o": "H2O", "ionic liquid": "IL",
            
            # Lithium salts
            "lipf6": "LiPF6", "lifsi": "LiFSI", "litfsi": "LiTFSI",
            "libf4": "LiBF4", "libob": "LiBOB", "lidfob": "LiDFOB",
            "liclo4": "LiClO4", "lino3": "LiNO3", "liasf6": "LiAsF6",
            
            # Sodium salts
            "napf6": "NaPF6", "natfsi": "NaTFSI", "nafsi": "NaFSI",
            "naclo4": "NaClO4", "nabf4": "NaBF4",
            
            # Zinc salts
            "znso4": "ZnSO4", "zinc sulfate": "ZnSO4", "zncl2": "ZnCl2",
            "zinc chloride": "ZnCl2", "zn(cf3so3)2": "Zn(CF3SO3)2",
            "zinc triflate": "Zn(CF3SO3)2", "zn(tfsi)2": "Zn(TFSI)2",
            "zn(otf)2": "Zn(OTf)2", "znf2": "ZnF2",
            
            # Magnesium salts
            "mgcl2": "MgCl2", "mg(tfsi)2": "Mg(TFSI)2", "mgtfsi2": "Mg(TFSI)2",
            "mg(cb11h12)2": "Mg(CB11H12)2",
            
            # Additives
            "vc": "VC", "vinylene carbonate": "VC", "fec": "FEC",
            "fluoroethylene carbonate": "FEC", "ps": "PS", "propane sultone": "PS",
            "dtd": "DTD", "es": "ES", "ethylene sulfite": "ES",
            "peg": "PEG", "polyethylene glycol": "PEG", "pvdf": "PVDF",
            "tte": "TTE", "btfe": "BTFE",
            
            # Solid electrolytes
            "llzo": "LLZO", "lgps": "LGPS", "lipon": "LiPON",
            "nasicon": "NASICON", "lisicon": "LISICON",
            "peo": "PEO", "polyethylene oxide": "PEO",
        }
        
        # Check for known materials in query
        for pattern, canonical in known_materials.items():
            if pattern in query_lower:
                if canonical not in materials:
                    materials.append(canonical)
        
        # Also try to extract chemical formulas with regex
        # Pattern for common chemical formulas like LiPF6, ZnSO4, etc.
        formula_pattern = r'\b([A-Z][a-z]?(?:\d*[A-Z][a-z]?)*(?:\d+)?(?:\([^)]+\)\d*)?)\b'
        matches = re.findall(formula_pattern, query)
        for match in matches:
            # Filter out common words and short matches
            if len(match) >= 2 and match not in ["In", "If", "Is", "It", "An", "As", "At", "Be", "By", "Do", "Go", "He", "Me", "My", "No", "Of", "On", "Or", "So", "To", "Up", "Us", "We"]:
                if match not in materials:
                    materials.append(match)
        
        # Extract concentrations mentioned with materials (e.g., "1M ZnSO4", "2% VC")
        conc_pattern = r'(\d+(?:\.\d+)?)\s*(M|m|mol|wt%|vol%|%)\s+(\w+)'
        conc_matches = re.findall(conc_pattern, query)
        for conc, unit, material in conc_matches:
            if material not in materials and len(material) >= 2:
                materials.append(material)
        
        return materials
    
    async def _generate_summary_with_llm(
        self,
        query: str,
        agent_responses: List[Dict[str, Any]],
        experiment_plans: List[Dict[str, Any]],
        requirements: Dict[str, Any]
    ) -> str:
        """Generate summary for design queries."""
        summary_parts = [
            f"## Analysis Summary for Query: \"{query}\"\n",
            "### Interpreted Requirements:",
            f"- **Target voltage**: {requirements['operating_conditions'].get('max_voltage', 4.2)}V",
            f"- **Electrode system**: {requirements['electrode_materials'].get('cathode', 'NMC')} / {requirements['electrode_materials'].get('anode', 'graphite')}",
            f"- **Application**: {requirements.get('application', 'general').replace('_', ' ').title()}",
            f"- **Key components identified**: {', '.join(requirements['components'])}",
            "\n### Agent Analysis:",
        ]
        
        for response in agent_responses:
            agent_name = response["agent_type"].replace("_", " ").title()
            summary_parts.append(f"- **{agent_name}**: {response['message']}")
        
        summary_parts.append("\n### Recommended Experiments with Predicted Performance:")
        for i, plan in enumerate(experiment_plans[:3], 1):
            # Get predicted performance from PerformancePredictionAgent
            predictions = plan.get('predicted_performance', {})
            confidence = plan.get('prediction_confidence', 0)
            
            summary_parts.append(
                f"\n{i}. **{plan['title']}** (Priority: {plan['priority_score']:.2f}, Prediction Confidence: {confidence:.0%})\n"
                f"   - Cost: {plan['estimated_cost']}, Time: {plan['estimated_time']}"
            )
            
            # Add predicted performance metrics if available
            if predictions:
                summary_parts.append(f"   - **Predicted Performance:**")
                if 'capacity_retention_percent' in predictions:
                    summary_parts.append(f"     - Capacity Retention: {predictions['capacity_retention_percent']}%")
                if 'cycle_stability_cycles' in predictions:
                    summary_parts.append(f"     - Cycle Life: {predictions['cycle_stability_cycles']} cycles")
                if 'rate_capability_2C_percent' in predictions:
                    summary_parts.append(f"     - Rate Capability (2C): {predictions['rate_capability_2C_percent']}%")
                if 'ionic_conductivity_mS_cm' in predictions:
                    summary_parts.append(f"     - Ionic Conductivity: {predictions['ionic_conductivity_mS_cm']} mS/cm")
        
        summary_parts.append("\n---\n*Analysis powered by GPT-4.1 and multi-agent coordination*")
        
        return "\n".join(summary_parts)
    
    async def get_agent_status(self) -> Dict[str, str]:
        """Get status of all sub-agents."""
        status = {name: "active" for name in self.agents}
        status["llm"] = "active" if self.llm_service else "inactive"
        return status
