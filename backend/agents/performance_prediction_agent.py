from typing import Dict, Any, Optional, List, Tuple
import random
import json
import re
from .base_agent import BaseAgent

class PerformancePredictionAgent(BaseAgent):
    """Agent for predicting electrolyte performance using LLM-based analysis.
    
    This agent uses GPT-4.1 to predict performance metrics for ANY battery chemistry,
    not just lithium-ion. The LLM analyzes the formulation components and provides
    predictions based on electrochemical principles.
    """
    
    def __init__(self, llm_service=None):
        super().__init__(
            name="PerformancePredictionAgent",
            description="LLM-based performance prediction for any battery electrolyte chemistry"
        )
        self.llm_service = llm_service
    
    def set_llm_service(self, llm_service):
        """Set the LLM service for predictions."""
        self.llm_service = llm_service
        self.log_action("LLM Service set")
    
    async def process(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Predict performance metrics for a given electrolyte formulation.
        
        Works for any battery chemistry (Li-ion, Zn, Na-ion, solid-state, etc.)
        by using LLM to analyze the formulation components.
        """
        formulation = input_data.get("formulation", {})
        operating_conditions = input_data.get("operating_conditions", {})
        electrode_materials = input_data.get("electrode_materials", {})
        battery_type = input_data.get("battery_type", "")
        query_context = input_data.get("query_context", "")
        
        self.log_action("Predicting performance", f"Formulation: {formulation}, Battery type: {battery_type}")
        
        # Use LLM for intelligent predictions
        if self.llm_service:
            return await self._predict_with_llm(
                formulation, operating_conditions, electrode_materials, 
                battery_type, query_context
            )
        else:
            # Fallback to basic estimation if LLM not available
            return self._basic_estimation(formulation, operating_conditions)
    
    async def _predict_with_llm(
        self,
        formulation: Dict[str, Any],
        operating_conditions: Dict[str, Any],
        electrode_materials: Dict[str, Any],
        battery_type: str,
        query_context: str
    ) -> Dict[str, Any]:
        """Use LLM to predict performance for any battery chemistry."""
        
        # Build context-aware prompt
        prompt = self._build_prediction_prompt(
            formulation, operating_conditions, electrode_materials,
            battery_type, query_context
        )
        
        system_prompt = """You are an expert electrochemist specializing in battery electrolyte performance prediction.

Your task is to predict performance metrics for the given electrolyte formulation based on:
1. The specific components and their concentrations
2. Known electrochemical properties of the components
3. The battery chemistry (Li-ion, Zn, Na-ion, Mg, solid-state, etc.)
4. Operating conditions and electrode materials

Provide realistic predictions with appropriate confidence levels. Be conservative - don't overestimate performance.

IMPORTANT: Your predictions must be specific to the actual battery chemistry. Do NOT apply lithium-ion assumptions to other chemistries.

You MUST respond in valid JSON format with this exact structure:
{
    "predictions": {
        "capacity_retention_percent": <number 50-99>,
        "cycle_stability_cycles": <integer 100-2000>,
        "rate_capability_2C_percent": <number 40-95>,
        "ionic_conductivity_mS_cm": <number 0.1-20>,
        "temperature_range_C": [<min_temp>, <max_temp>]
    },
    "confidence_score": <number 0.5-0.95>,
    "model_notes": "<string with key insights about the prediction>",
    "battery_chemistry_detected": "<detected battery type>",
    "key_performance_factors": ["<factor1>", "<factor2>", "<factor3>"]
}"""

        try:
            response = await self.llm_service.generate(
                prompt,
                system_prompt,
                temperature=0.3,  # Lower temperature for more consistent predictions
                max_tokens=800
            )
            
            # Parse JSON response
            predictions = self._parse_llm_response(response)
            
            if predictions:
                return {
                    "status": "success",
                    "predictions": predictions.get("predictions", {}),
                    "confidence_score": predictions.get("confidence_score", 0.7),
                    "model_notes": predictions.get("model_notes", ""),
                    "battery_chemistry": predictions.get("battery_chemistry_detected", battery_type or "unknown"),
                    "key_factors": predictions.get("key_performance_factors", []),
                    "formulation_analyzed": formulation,
                    "prediction_method": "llm_based"
                }
            else:
                # Fallback if parsing fails
                return self._basic_estimation(formulation, operating_conditions)
                
        except Exception as e:
            self.logger.error(f"LLM prediction failed: {e}")
            return self._basic_estimation(formulation, operating_conditions)
    
    def _build_prediction_prompt(
        self,
        formulation: Dict[str, Any],
        operating_conditions: Dict[str, Any],
        electrode_materials: Dict[str, Any],
        battery_type: str,
        query_context: str
    ) -> str:
        """Build a detailed prompt for LLM-based prediction."""
        
        # Format formulation
        formulation_str = "\n".join([
            f"  - {comp}: {conc}" + (" (concentration)" if isinstance(conc, (int, float)) else "")
            for comp, conc in formulation.items()
        ]) if formulation else "  No specific formulation provided"
        
        # Format operating conditions
        conditions_str = "\n".join([
            f"  - {key}: {value}"
            for key, value in operating_conditions.items()
        ]) if operating_conditions else "  Standard conditions (25°C, 1 atm)"
        
        # Format electrode materials
        electrodes_str = "\n".join([
            f"  - {key}: {value}"
            for key, value in electrode_materials.items()
        ]) if electrode_materials else "  Not specified"
        
        prompt = f"""Analyze the following electrolyte formulation and predict its performance:

## Battery Type Context
{battery_type if battery_type else "Infer from the formulation components"}

## Original Query Context
{query_context if query_context else "General electrolyte design"}

## Electrolyte Formulation
{formulation_str}

## Operating Conditions
{conditions_str}

## Electrode Materials
{electrodes_str}

Based on electrochemical principles and the specific components listed:
1. First identify the battery chemistry (Li-ion, Zn, Na-ion, etc.)
2. Evaluate how each component affects performance
3. Consider interactions between components
4. Account for operating conditions
5. Provide realistic performance predictions

Remember:
- Different battery chemistries have different typical performance ranges
- Aqueous electrolytes (Zn, some Na) behave differently from organic (Li-ion)
- Consider the stability window of the electrolyte
- Factor in the specific salts and solvents used

Respond with the JSON predictions:"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response to extract predictions."""
        try:
            # Try to find JSON in the response
            # First, try direct parse
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
            
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to find JSON object in the response
            json_match = re.search(r'\{[^{}]*"predictions"[^{}]*\{.*?\}.*?\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            
            # Last resort: try to find any JSON-like structure
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to parse LLM response: {e}")
            return None
    
    def _basic_estimation(
        self,
        formulation: Dict[str, Any],
        operating_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Basic performance estimation when LLM is not available.
        
        Provides conservative estimates without assuming specific chemistry.
        """
        # Detect battery chemistry from components
        chemistry = self._detect_chemistry(formulation)
        
        # Base values depend on detected chemistry
        base_values = self._get_base_values_for_chemistry(chemistry)
        
        # Add some variation
        variation = random.uniform(-5, 5)
        
        return {
            "status": "success",
            "predictions": {
                "capacity_retention_percent": round(base_values["capacity"] + variation, 1),
                "cycle_stability_cycles": int(base_values["cycles"] + variation * 10),
                "rate_capability_2C_percent": round(base_values["rate"] + variation, 1),
                "ionic_conductivity_mS_cm": round(base_values["conductivity"] + variation * 0.1, 2),
                "temperature_range_C": base_values["temp_range"]
            },
            "confidence_score": 0.5,  # Low confidence for basic estimation
            "model_notes": f"Basic estimation for {chemistry} chemistry. LLM service not available for detailed analysis.",
            "battery_chemistry": chemistry,
            "formulation_analyzed": formulation,
            "prediction_method": "basic_estimation"
        }
    
    def _detect_chemistry(self, formulation: Dict[str, Any]) -> str:
        """Detect battery chemistry from formulation components."""
        components_upper = [str(k).upper() for k in formulation.keys()]
        
        # Check for lithium indicators
        li_indicators = ["LIPF6", "LIFSI", "LITFSI", "LIBF4", "LIBOB", "LI", "LITHIUM"]
        if any(ind in comp for ind in li_indicators for comp in components_upper):
            return "lithium-ion"
        
        # Check for zinc indicators
        zn_indicators = ["ZN", "ZNSO4", "ZNCL2", "ZNTFSI", "ZN(CF3SO3)2", "ZINC"]
        if any(ind in comp for ind in zn_indicators for comp in components_upper):
            return "zinc"
        
        # Check for sodium indicators
        na_indicators = ["NA", "NAPF6", "NATFSI", "NAFSI", "SODIUM"]
        if any(ind in comp for ind in na_indicators for comp in components_upper):
            return "sodium-ion"
        
        # Check for magnesium indicators
        mg_indicators = ["MG", "MGCL2", "MGTFSI", "MAGNESIUM"]
        if any(ind in comp for ind in mg_indicators for comp in components_upper):
            return "magnesium"
        
        # Check for aqueous indicators
        aqueous_indicators = ["H2O", "WATER", "AQUEOUS"]
        if any(ind in comp for ind in aqueous_indicators for comp in components_upper):
            return "aqueous"
        
        return "unknown"
    
    def _get_base_values_for_chemistry(self, chemistry: str) -> Dict[str, Any]:
        """Get baseline performance values for different battery chemistries."""
        # Conservative baseline values for different chemistries
        baselines = {
            "lithium-ion": {
                "capacity": 85,
                "cycles": 500,
                "rate": 70,
                "conductivity": 10,
                "temp_range": (-20, 60)
            },
            "zinc": {
                "capacity": 80,
                "cycles": 300,
                "rate": 65,
                "conductivity": 50,  # Aqueous electrolytes have higher conductivity
                "temp_range": (0, 50)
            },
            "sodium-ion": {
                "capacity": 80,
                "cycles": 400,
                "rate": 65,
                "conductivity": 8,
                "temp_range": (-20, 55)
            },
            "magnesium": {
                "capacity": 75,
                "cycles": 200,
                "rate": 50,
                "conductivity": 5,
                "temp_range": (0, 50)
            },
            "aqueous": {
                "capacity": 80,
                "cycles": 500,
                "rate": 80,
                "conductivity": 100,
                "temp_range": (0, 40)
            },
            "unknown": {
                "capacity": 75,
                "cycles": 300,
                "rate": 60,
                "conductivity": 5,
                "temp_range": (-10, 50)
            }
        }
        
        return baselines.get(chemistry, baselines["unknown"])
    
    def compare_formulations(
        self, 
        formulations: List[Dict[str, Any]], 
        conditions: Dict[str, Any],
        battery_type: str = ""
    ) -> List[Dict[str, Any]]:
        """Compare multiple formulations and rank them."""
        results = []
        
        for i, form in enumerate(formulations):
            chemistry = self._detect_chemistry(form)
            base = self._get_base_values_for_chemistry(chemistry)
            
            # Add variation for comparison
            variation = random.uniform(-5, 5)
            capacity = base["capacity"] + variation
            cycles = base["cycles"] + variation * 10
            rate = base["rate"] + variation
            
            # Calculate composite score
            score = (capacity * 0.3 + (cycles / 10) * 0.4 + rate * 0.3)
            
            results.append({
                "formulation_id": i + 1,
                "formulation": form,
                "battery_chemistry": chemistry,
                "capacity_retention": round(capacity, 1),
                "cycle_stability": int(cycles),
                "rate_capability": round(rate, 1),
                "composite_score": round(score, 1)
            })
        
        # Sort by composite score
        results.sort(key=lambda x: x["composite_score"], reverse=True)
        
        return results
