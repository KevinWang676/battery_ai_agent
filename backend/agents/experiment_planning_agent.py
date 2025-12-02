from typing import Dict, Any, Optional, List
import uuid
import json
import re
from .base_agent import BaseAgent

class ExperimentPlanningAgent(BaseAgent):
    """Agent for suggesting electrolyte formulations for ANY battery chemistry.
    
    This agent uses LLM to generate chemistry-appropriate formulations based on:
    - The detected battery type (Li-ion, Zn, Na-ion, Mg, solid-state, etc.)
    - The user's specific requirements
    - Literature data from RAG
    """
    
    def __init__(self, llm_service=None):
        super().__init__(
            name="ExperimentPlanningAgent",
            description="Generates electrolyte formulations and experimental plans for any battery chemistry"
        )
        self.llm_service = llm_service
        self.base_protocols = self._initialize_protocols()
    
    def set_llm_service(self, llm_service):
        """Set the LLM service for generating formulations."""
        self.llm_service = llm_service
        self.log_action("LLM Service set")
    
    def _initialize_protocols(self) -> Dict[str, Any]:
        """Initialize standard experimental protocols (chemistry-agnostic)."""
        return {
            "cell_assembly": {
                "name": "Cell Assembly",
                "steps": [
                    "Prepare electrodes according to battery type specifications",
                    "Dry components under vacuum at appropriate temperature",
                    "Transfer to controlled atmosphere environment",
                    "Stack electrodes with appropriate separator",
                    "Add electrolyte with precise volume",
                    "Seal cell according to cell format",
                    "Rest before testing"
                ],
                "duration": "1-2 days",
                "equipment": ["Glovebox/dry room", "Cell assembly tools", "Vacuum oven"]
            },
            "cycling_test": {
                "name": "Galvanostatic Cycling",
                "steps": [
                    "Connect cell to battery cycler",
                    "Set voltage window appropriate for battery chemistry",
                    "Perform formation cycles at low rate",
                    "Run regular cycling at specified rate",
                    "Record capacity, efficiency, voltage profiles"
                ],
                "duration": "1-4 weeks depending on cycle number",
                "equipment": ["Battery cycler", "Temperature chamber"]
            },
            "rate_capability": {
                "name": "Rate Capability Test",
                "steps": [
                    "Complete formation cycles",
                    "Cycle at progressively higher rates",
                    "Return to low rate for recovery check",
                    "Plot capacity vs rate"
                ],
                "duration": "3-5 days",
                "equipment": ["Battery cycler"]
            },
            "impedance_spectroscopy": {
                "name": "Electrochemical Impedance Spectroscopy (EIS)",
                "steps": [
                    "Equilibrate cell at desired state of charge",
                    "Apply small AC perturbation",
                    "Sweep frequency range",
                    "Analyze impedance response"
                ],
                "duration": "2-4 hours per measurement",
                "equipment": ["Potentiostat/Galvanostat", "Frequency response analyzer"]
            },
            "conductivity_measurement": {
                "name": "Ionic Conductivity Measurement",
                "steps": [
                    "Prepare electrolyte sample",
                    "Fill conductivity cell",
                    "Measure impedance",
                    "Calculate conductivity",
                    "Optional: temperature-dependent measurements"
                ],
                "duration": "1-2 hours",
                "equipment": ["Conductivity cell", "Impedance analyzer"]
            }
        }
    
    async def process(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate experiment plans based on battery type and query context."""
        query = input_data.get("query", "")
        literature_data = input_data.get("literature_data", {})
        property_data = input_data.get("property_data", {})
        target_application = input_data.get("target_application", "general")
        battery_type = input_data.get("battery_type", "")
        operating_conditions = input_data.get("operating_conditions", {})
        electrode_materials = input_data.get("electrode_materials", {})
        user_specified_materials = input_data.get("user_specified_materials", [])
        detected_components = input_data.get("detected_components", [])
        
        self.log_action("Generating experiment plans", query)
        
        # Log user-specified materials if any
        if user_specified_materials:
            self.log_action("User-specified materials", str(user_specified_materials))
        
        # Detect battery type if not provided
        if not battery_type:
            battery_type = self._detect_battery_type(query)
        
        self.log_action("Battery type detected", battery_type)
        
        # Generate formulations using LLM for chemistry-appropriate results
        if self.llm_service:
            plans = await self._generate_plans_with_llm(
                query, battery_type, literature_data, property_data,
                target_application, operating_conditions, electrode_materials,
                user_specified_materials, detected_components
            )
        else:
            # Fallback to template-based generation
            plans = self._generate_fallback_plans(query, battery_type)
        
        # Add protocols to each plan
        for plan in plans:
            plan["protocols"] = self._select_protocols(plan, battery_type)
        
        return {
            "status": "success",
            "experiment_plans": plans,
            "total_plans": len(plans),
            "battery_type": battery_type,
            "recommendation": self._generate_recommendation(plans, battery_type)
        }
    
    def _detect_battery_type(self, query: str) -> str:
        """Detect battery type from query."""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ["zinc", "zn-ion", "zn ion", "zn metal", "zn anode", "aqueous zinc"]):
            return "zinc"
        elif any(kw in query_lower for kw in ["sodium", "na-ion", "na ion", "sodium-ion"]):
            return "sodium-ion"
        elif any(kw in query_lower for kw in ["magnesium", "mg-ion", "mg ion", "mg metal"]):
            return "magnesium"
        elif any(kw in query_lower for kw in ["solid-state", "solid state", "all-solid", "solid electrolyte", "polymer electrolyte"]):
            return "solid-state"
        elif any(kw in query_lower for kw in ["aqueous", "water-based", "water based"]):
            return "aqueous"
        elif any(kw in query_lower for kw in ["lithium", "li-ion", "li ion", "lithium-ion", "lipf6", "lifsi"]):
            return "lithium-ion"
        else:
            return "lithium-ion"  # Default
    
    async def _generate_plans_with_llm(
        self,
        query: str,
        battery_type: str,
        literature_data: Dict[str, Any],
        property_data: Dict[str, Any],
        target_application: str,
        operating_conditions: Dict[str, Any],
        electrode_materials: Dict[str, Any],
        user_specified_materials: List[str] = None,
        detected_components: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Use LLM to generate chemistry-appropriate experiment plans."""
        
        user_specified_materials = user_specified_materials or []
        detected_components = detected_components or []
        
        # Build context from literature and property data
        lit_summary = literature_data.get("summary", "")
        if literature_data.get("results"):
            lit_context = "\n".join([
                f"- {r.get('title', 'Source')}: {r.get('content', '')[:200]}..."
                for r in literature_data.get("results", [])[:3]
            ])
        else:
            lit_context = "No specific literature references available."
        
        # Build user-specified materials section
        user_materials_section = ""
        if user_specified_materials or detected_components:
            all_user_materials = list(set(user_specified_materials + detected_components))
            if all_user_materials:
                user_materials_section = f"""
## USER-SPECIFIED MATERIALS (MUST BE INCLUDED)
The user has explicitly mentioned these materials in their query:
{', '.join(all_user_materials)}

**CRITICAL**: At least one of your experiment plans MUST include these user-specified materials.
If the user specified a salt, solvent, or additive, incorporate it into the formulation.
"""
        
        prompt = f"""Generate 3 electrolyte formulation plans for the following battery research:

## User Query
{query}

## Battery Chemistry
{battery_type.upper() if battery_type else "Infer from query"} battery system
{user_materials_section}
## Target Application
{target_application}

## Operating Conditions
{json.dumps(operating_conditions, indent=2) if operating_conditions else "Standard conditions"}

## Electrode Materials
{json.dumps(electrode_materials, indent=2) if electrode_materials else "Not specified"}

## Literature Context
{lit_context}

## Requirements
Generate THREE distinct experiment plans with formulations:

1. **User-Specified Formulation**: If the user specified any materials, create a plan using those exact materials
2. **Optimized Plan**: Enhanced formulation addressing the specific requirements  
3. **Alternative Plan**: Different approach or cutting-edge formulation

For each plan, provide:
- A specific electrolyte formulation with exact components and concentrations
- Components must be appropriate for the battery chemistry
- Rationale explaining the choices
- Experimental steps
- Safety considerations
- Estimated cost and time

CRITICAL RULES:
1. If user specified materials like "ZnCl2", "DMSO", "acetonitrile", etc. - USE THEM in at least one plan
2. Use components appropriate for {battery_type.upper() if battery_type else "the detected"} batteries
3. Do NOT ignore user-specified materials in favor of "standard" formulations

Respond in JSON format:
{{
    "plans": [
        {{
            "title": "Plan title",
            "formulation": [
                {{"name": "Full chemical name", "abbreviation": "ABBREV", "concentration": number, "unit": "M or vol% or wt%", "role": "salt/solvent/additive"}}
            ],
            "rationale": "Explanation of formulation choices for {battery_type}",
            "experimental_steps": ["step1", "step2", ...],
            "safety_considerations": ["consideration1", ...],
            "estimated_cost": "$X-Y",
            "estimated_time": "X weeks",
            "priority_score": 0.85-0.95
        }}
    ]
}}"""

        system_prompt = f"""You are an expert electrochemist specializing in {battery_type} battery electrolyte design.

Your task is to generate practical, chemistry-appropriate electrolyte formulations.

CRITICAL RULES:
1. ONLY use components appropriate for {battery_type.upper()} chemistry
2. Do NOT default to lithium-ion components for non-lithium batteries
3. Include specific concentrations and units
4. Consider the operating conditions and application requirements
5. Base recommendations on established electrochemistry principles

For {battery_type.upper()} batteries, typical components include:
{"- Zinc salts: ZnSO4, Zn(CF3SO3)2 (zinc triflate), ZnCl2" + chr(10) + "- Solvents: Water (aqueous), acetonitrile, DMSO" + chr(10) + "- Additives: LiTFSI (anti-dendrite), MnSO4, polyethylene glycol" if battery_type == "zinc" else ""}
{"- Sodium salts: NaPF6, NaTFSI, NaClO4, NaFSI" + chr(10) + "- Solvents: EC, PC, DME, diglyme" + chr(10) + "- Additives: FEC, VC" if battery_type == "sodium-ion" else ""}
{"- Magnesium salts: MgCl2, Mg(TFSI)2, Mg(CB11H12)2" + chr(10) + "- Solvents: THF, DME, diglyme, TEGDME" + chr(10) + "- Additives: AlCl3 (for APC electrolyte)" if battery_type == "magnesium" else ""}
{"- Lithium salts: LiPF6, LiFSI, LiTFSI, LiBOB" + chr(10) + "- Solvents: EC, DMC, EMC, DEC, PC" + chr(10) + "- Additives: VC, FEC, PS, DTD" if battery_type == "lithium-ion" else ""}

Respond ONLY with valid JSON."""

        try:
            response = await self.llm_service.generate(
                prompt,
                system_prompt,
                temperature=0.4,
                max_tokens=3000
            )
            
            plans = self._parse_llm_plans(response, battery_type)
            if plans:
                return plans
            else:
                return self._generate_fallback_plans(query, battery_type)
                
        except Exception as e:
            self.logger.error(f"LLM plan generation failed: {e}")
            return self._generate_fallback_plans(query, battery_type)
    
    def _parse_llm_plans(self, response: str, battery_type: str) -> Optional[List[Dict[str, Any]]]:
        """Parse LLM response to extract experiment plans."""
        try:
            # Try direct JSON parse
            try:
                data = json.loads(response)
                if "plans" in data:
                    plans = data["plans"]
                    for plan in plans:
                        plan["plan_id"] = str(uuid.uuid4())[:8]
                        plan["battery_type"] = battery_type
                    return plans
            except json.JSONDecodeError:
                pass
            
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*"plans"[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group(0))
                plans = data.get("plans", [])
                for plan in plans:
                    plan["plan_id"] = str(uuid.uuid4())[:8]
                    plan["battery_type"] = battery_type
                return plans
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to parse LLM plans: {e}")
            return None
    
    def _generate_fallback_plans(self, query: str, battery_type: str) -> List[Dict[str, Any]]:
        """Generate fallback plans when LLM is not available."""
        
        # Chemistry-specific templates
        templates = {
            "zinc": {
                "baseline": {
                    "title": "Baseline Aqueous Zinc Electrolyte",
                    "formulation": [
                        {"name": "Zinc Sulfate", "abbreviation": "ZnSO4", "concentration": 2.0, "unit": "M", "role": "salt"},
                        {"name": "Water", "abbreviation": "H2O", "concentration": 100, "unit": "vol%", "role": "solvent"},
                        {"name": "Manganese Sulfate", "abbreviation": "MnSO4", "concentration": 0.1, "unit": "M", "role": "additive"}
                    ],
                    "rationale": "Standard aqueous zinc electrolyte with MnSO4 to suppress Mn dissolution from cathode.",
                    "priority_score": 0.85
                },
                "optimized": {
                    "title": "Optimized Zinc Triflate Electrolyte",
                    "formulation": [
                        {"name": "Zinc Trifluoromethanesulfonate", "abbreviation": "Zn(CF3SO3)2", "concentration": 3.0, "unit": "M", "role": "salt"},
                        {"name": "Water", "abbreviation": "H2O", "concentration": 100, "unit": "vol%", "role": "solvent"},
                        {"name": "Lithium bis(trifluoromethanesulfonyl)imide", "abbreviation": "LiTFSI", "concentration": 0.5, "unit": "M", "role": "additive"}
                    ],
                    "rationale": "High-concentration zinc triflate with LiTFSI for improved Zn plating/stripping reversibility.",
                    "priority_score": 0.90
                },
                "advanced": {
                    "title": "Water-in-Salt Zinc Electrolyte",
                    "formulation": [
                        {"name": "Zinc Trifluoromethanesulfonate", "abbreviation": "Zn(CF3SO3)2", "concentration": 4.0, "unit": "M", "role": "salt"},
                        {"name": "Lithium bis(trifluoromethanesulfonyl)imide", "abbreviation": "LiTFSI", "concentration": 21.0, "unit": "M", "role": "salt"},
                        {"name": "Water", "abbreviation": "H2O", "concentration": 100, "unit": "vol%", "role": "solvent"}
                    ],
                    "rationale": "Water-in-salt electrolyte with expanded electrochemical stability window and dendrite suppression.",
                    "priority_score": 0.88
                }
            },
            "sodium-ion": {
                "baseline": {
                    "title": "Baseline Sodium-ion Electrolyte",
                    "formulation": [
                        {"name": "Ethylene Carbonate", "abbreviation": "EC", "concentration": 50, "unit": "vol%", "role": "solvent"},
                        {"name": "Propylene Carbonate", "abbreviation": "PC", "concentration": 50, "unit": "vol%", "role": "solvent"},
                        {"name": "Sodium Hexafluorophosphate", "abbreviation": "NaPF6", "concentration": 1.0, "unit": "M", "role": "salt"}
                    ],
                    "rationale": "Standard carbonate-based electrolyte for sodium-ion batteries.",
                    "priority_score": 0.85
                },
                "optimized": {
                    "title": "Optimized Ether-based Na Electrolyte",
                    "formulation": [
                        {"name": "Diethylene Glycol Dimethyl Ether", "abbreviation": "Diglyme", "concentration": 100, "unit": "vol%", "role": "solvent"},
                        {"name": "Sodium bis(trifluoromethanesulfonyl)imide", "abbreviation": "NaTFSI", "concentration": 1.0, "unit": "M", "role": "salt"}
                    ],
                    "rationale": "Ether-based electrolyte with improved Na metal compatibility and lower viscosity.",
                    "priority_score": 0.90
                },
                "advanced": {
                    "title": "Advanced Concentrated Na Electrolyte",
                    "formulation": [
                        {"name": "Dimethoxyethane", "abbreviation": "DME", "concentration": 100, "unit": "vol%", "role": "solvent"},
                        {"name": "Sodium bis(fluorosulfonyl)imide", "abbreviation": "NaFSI", "concentration": 4.0, "unit": "M", "role": "salt"}
                    ],
                    "rationale": "High-concentration NaFSI in ether for stable Na metal anode performance.",
                    "priority_score": 0.88
                }
            },
            "lithium-ion": {
                "baseline": {
                    "title": "Baseline Commercial-type Electrolyte",
                    "formulation": [
                        {"name": "Ethylene Carbonate", "abbreviation": "EC", "concentration": 30, "unit": "vol%", "role": "solvent"},
                        {"name": "Ethyl Methyl Carbonate", "abbreviation": "EMC", "concentration": 70, "unit": "vol%", "role": "solvent"},
                        {"name": "Lithium Hexafluorophosphate", "abbreviation": "LiPF6", "concentration": 1.0, "unit": "M", "role": "salt"},
                        {"name": "Vinylene Carbonate", "abbreviation": "VC", "concentration": 2, "unit": "wt%", "role": "additive"}
                    ],
                    "rationale": "Industry-standard EC:EMC electrolyte with VC additive for SEI formation.",
                    "priority_score": 0.85
                },
                "optimized": {
                    "title": "Optimized Li-ion Electrolyte",
                    "formulation": [
                        {"name": "Ethylene Carbonate", "abbreviation": "EC", "concentration": 30, "unit": "vol%", "role": "solvent"},
                        {"name": "Dimethyl Carbonate", "abbreviation": "DMC", "concentration": 40, "unit": "vol%", "role": "solvent"},
                        {"name": "Ethyl Methyl Carbonate", "abbreviation": "EMC", "concentration": 30, "unit": "vol%", "role": "solvent"},
                        {"name": "Lithium bis(fluorosulfonyl)imide", "abbreviation": "LiFSI", "concentration": 1.2, "unit": "M", "role": "salt"},
                        {"name": "Vinylene Carbonate", "abbreviation": "VC", "concentration": 1.5, "unit": "wt%", "role": "additive"},
                        {"name": "Fluoroethylene Carbonate", "abbreviation": "FEC", "concentration": 5, "unit": "wt%", "role": "additive"}
                    ],
                    "rationale": "Ternary solvent with LiFSI for improved conductivity and thermal stability.",
                    "priority_score": 0.90
                },
                "advanced": {
                    "title": "Advanced Dual-Salt Li Electrolyte",
                    "formulation": [
                {"name": "Ethylene Carbonate", "abbreviation": "EC", "concentration": 30, "unit": "vol%", "role": "solvent"},
                {"name": "Dimethyl Carbonate", "abbreviation": "DMC", "concentration": 35, "unit": "vol%", "role": "solvent"},
                {"name": "Ethyl Methyl Carbonate", "abbreviation": "EMC", "concentration": 35, "unit": "vol%", "role": "solvent"},
                {"name": "Lithium Hexafluorophosphate", "abbreviation": "LiPF6", "concentration": 0.8, "unit": "M", "role": "salt"},
                {"name": "Lithium bis(fluorosulfonyl)imide", "abbreviation": "LiFSI", "concentration": 0.2, "unit": "M", "role": "salt"},
                {"name": "Vinylene Carbonate", "abbreviation": "VC", "concentration": 2, "unit": "wt%", "role": "additive"},
                {"name": "1,3,2-Dioxathiolane 2,2-dioxide", "abbreviation": "DTD", "concentration": 1, "unit": "wt%", "role": "additive"}
                    ],
                    "rationale": "Dual-salt system with synergistic SEI formation from VC and DTD.",
                    "priority_score": 0.88
                }
            },
            "magnesium": {
                "baseline": {
                    "title": "Baseline APC Magnesium Electrolyte",
                    "formulation": [
                        {"name": "Magnesium Chloride", "abbreviation": "MgCl2", "concentration": 0.25, "unit": "M", "role": "salt"},
                        {"name": "Aluminum Chloride", "abbreviation": "AlCl3", "concentration": 0.5, "unit": "M", "role": "Lewis acid"},
                        {"name": "Tetrahydrofuran", "abbreviation": "THF", "concentration": 100, "unit": "vol%", "role": "solvent"}
                    ],
                    "rationale": "All-phenyl complex (APC) type electrolyte, well-established for Mg batteries.",
                    "priority_score": 0.85
                },
                "optimized": {
                    "title": "Optimized Mg(TFSI)2 Electrolyte",
                    "formulation": [
                        {"name": "Magnesium bis(trifluoromethanesulfonyl)imide", "abbreviation": "Mg(TFSI)2", "concentration": 0.5, "unit": "M", "role": "salt"},
                        {"name": "Dimethoxyethane", "abbreviation": "DME", "concentration": 50, "unit": "vol%", "role": "solvent"},
                        {"name": "Tetraglyme", "abbreviation": "TEGDME", "concentration": 50, "unit": "vol%", "role": "solvent"}
                    ],
                    "rationale": "Non-corrosive Mg(TFSI)2 salt in glyme-based solvents for wider compatibility.",
                    "priority_score": 0.88
                },
                "advanced": {
                    "title": "Advanced Mg Electrolyte with Boron Cluster",
                    "formulation": [
                        {"name": "Magnesium Carborane", "abbreviation": "Mg(CB11H12)2", "concentration": 0.5, "unit": "M", "role": "salt"},
                        {"name": "Tetraglyme", "abbreviation": "TEGDME", "concentration": 100, "unit": "vol%", "role": "solvent"}
                    ],
                    "rationale": "Carborane-based anion provides high oxidative stability and non-nucleophilic character.",
                    "priority_score": 0.82
                }
            }
        }
        
        # Get templates for detected battery type
        chem_templates = templates.get(battery_type, templates["lithium-ion"])
        
        plans = []
        for plan_type in ["advanced", "optimized", "baseline"]:
            template = chem_templates[plan_type]
            plans.append({
            "plan_id": str(uuid.uuid4())[:8],
                "title": template["title"],
                "formulation": template["formulation"],
                "rationale": template["rationale"],
                "battery_type": battery_type,
            "experimental_steps": [
                    f"Prepare electrolyte for {battery_type} battery",
                    "Verify purity and water content",
                    "Assemble test cells",
                    "Perform formation cycles",
                    "Run cycling tests",
                    "Conduct EIS measurements",
                    "Analyze results"
            ],
            "safety_considerations": [
                    "Handle all chemicals with appropriate PPE",
                    "Work in appropriate atmosphere (glovebox for air-sensitive)",
                    "Follow MSDS guidelines for all components"
                ],
                "estimated_cost": "$300-600",
                "estimated_time": "4-8 weeks",
                "priority_score": template["priority_score"]
            })
        
        return plans
    
    def _select_protocols(self, plan: Dict[str, Any], battery_type: str) -> List[Dict[str, Any]]:
        """Select relevant protocols for the experiment plan."""
        return [
            self.base_protocols["cell_assembly"],
            self.base_protocols["cycling_test"],
            self.base_protocols["rate_capability"],
            self.base_protocols["impedance_spectroscopy"],
            self.base_protocols["conductivity_measurement"]
        ]
    
    def _generate_recommendation(self, plans: List[Dict[str, Any]], battery_type: str) -> str:
        """Generate an overall recommendation."""
        if not plans:
            return f"Unable to generate recommendations for {battery_type} battery. Please provide more context."
        
        top_plan = plans[0]
        return (
            f"Recommended for {battery_type.upper()} battery: '{top_plan['title']}' (priority: {top_plan.get('priority_score', 0.85):.2f}). "
            f"This formulation uses components specifically selected for {battery_type} chemistry. "
            f"Estimated cost: {top_plan.get('estimated_cost', 'TBD')}, timeline: {top_plan.get('estimated_time', 'TBD')}."
        )
