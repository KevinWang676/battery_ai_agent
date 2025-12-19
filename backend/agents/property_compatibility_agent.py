from typing import Dict, Any, Optional, List, Tuple
from .base_agent import BaseAgent

class PropertyCompatibilityAgent(BaseAgent):
    """Agent for tracking molecular properties and checking compatibility constraints."""
    
    def __init__(self):
        super().__init__(
            name="PropertyCompatibilityAgent",
            description="Tracks molecular properties and checks electrolyte component constraints"
        )
        self.property_database = self._initialize_property_database()
        self.compatibility_rules = self._initialize_compatibility_rules()
    
    def _initialize_property_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize molecular property database."""
        return {
            # Solvents
            "EC": {
                "molecular_weight": 88.06,
                "density": 1.32,
                "viscosity": 1.9,  # mPa·s at 40°C
                "dielectric_constant": 89.8,
                "melting_point": 36.4,
                "boiling_point": 248,
                "flash_point": 160,
                "oxidation_potential": 6.2,  # V vs Li/Li+
                "reduction_potential": 0.8,
                "category": "solvent"
            },
            "DMC": {
                "molecular_weight": 90.08,
                "density": 1.07,
                "viscosity": 0.59,
                "dielectric_constant": 3.1,
                "melting_point": 4.6,
                "boiling_point": 91,
                "flash_point": 18,
                "oxidation_potential": 6.7,
                "reduction_potential": 1.0,
                "category": "solvent"
            },
            "EMC": {
                "molecular_weight": 104.1,
                "density": 1.01,
                "viscosity": 0.65,
                "dielectric_constant": 2.9,
                "melting_point": -53,
                "boiling_point": 110,
                "flash_point": 25,
                "oxidation_potential": 6.7,
                "reduction_potential": 1.0,
                "category": "solvent"
            },
            "DEC": {
                "molecular_weight": 118.13,
                "density": 0.98,
                "viscosity": 0.75,
                "dielectric_constant": 2.8,
                "melting_point": -74.3,
                "boiling_point": 126,
                "flash_point": 31,
                "oxidation_potential": 6.7,
                "reduction_potential": 1.0,
                "category": "solvent"
            },
            "PC": {
                "molecular_weight": 102.09,
                "density": 1.20,
                "viscosity": 2.5,
                "dielectric_constant": 64.9,
                "melting_point": -48.8,
                "boiling_point": 242,
                "flash_point": 132,
                "oxidation_potential": 6.6,
                "reduction_potential": 0.9,
                "category": "solvent"
            },
            # Salts
            "LiPF6": {
                "molecular_weight": 151.91,
                "decomposition_temp": 80,
                "ionic_conductivity": 10.7,  # mS/cm in EC/DMC
                "thermal_stability": "moderate",
                "moisture_sensitivity": "high",
                "category": "salt"
            },
            "LiTFSI": {
                "molecular_weight": 287.09,
                "decomposition_temp": 360,
                "ionic_conductivity": 9.0,
                "thermal_stability": "excellent",
                "moisture_sensitivity": "low",
                "al_corrosion": True,
                "category": "salt"
            },
            "LiFSI": {
                "molecular_weight": 187.07,
                "decomposition_temp": 200,
                "ionic_conductivity": 12.0,
                "thermal_stability": "good",
                "moisture_sensitivity": "moderate",
                "category": "salt"
            },
            "LiBF4": {
                "molecular_weight": 93.75,
                "decomposition_temp": 293,
                "ionic_conductivity": 3.4,
                "thermal_stability": "good",
                "moisture_sensitivity": "high",
                "category": "salt"
            },
            # Additives
            "VC": {
                "molecular_weight": 86.05,
                "recommended_concentration": (1, 2),  # wt%
                "function": "SEI_former",
                "category": "additive"
            },
            "FEC": {
                "molecular_weight": 106.05,
                "recommended_concentration": (5, 10),
                "function": "SEI_former",
                "category": "additive"
            },
            "PS": {
                "molecular_weight": 122.14,
                "recommended_concentration": (1, 3),
                "function": "anode_passivation",
                "category": "additive"
            },
            "LiBOB": {
                "molecular_weight": 193.79,
                "recommended_concentration": (0.5, 1),
                "function": "cathode_stabilizer",
                "category": "additive"
            }
        }
    
    def _initialize_compatibility_rules(self) -> List[Dict[str, Any]]:
        """Initialize compatibility rules between components."""
        return [
            {
                "rule_id": "PC_graphite",
                "components": ["PC"],
                "condition": "PC concentration > 30%",
                "with_material": "graphite_anode",
                "issue": "PC causes graphite exfoliation due to co-intercalation",
                "severity": "critical",
                "solution": "Use EC-based electrolyte or add FEC (10%)"
            },
            {
                "rule_id": "LiTFSI_Al",
                "components": ["LiTFSI"],
                "condition": "voltage > 3.8V",
                "with_material": "aluminum_current_collector",
                "issue": "LiTFSI corrodes aluminum at high voltages",
                "severity": "high",
                "solution": "Add LiPF6 (50:50 ratio) or use LiTFSI concentration < 0.5M"
            },
            {
                "rule_id": "LiPF6_thermal",
                "components": ["LiPF6"],
                "condition": "temperature > 60°C",
                "issue": "LiPF6 decomposes, releasing HF",
                "severity": "high",
                "solution": "Use LiBF4 or LiFSI for high-temperature applications"
            },
            {
                "rule_id": "high_EC_viscosity",
                "components": ["EC"],
                "condition": "EC concentration > 50%",
                "issue": "High viscosity reduces rate capability",
                "severity": "medium",
                "solution": "Add linear carbonates (DMC, EMC, DEC) to reduce viscosity"
            },
            {
                "rule_id": "FEC_gas_generation",
                "components": ["FEC"],
                "condition": "concentration > 15%",
                "issue": "Excessive CO2 generation during cycling",
                "severity": "medium",
                "solution": "Keep FEC between 5-10 wt%"
            },
            {
                "rule_id": "high_voltage_cathode",
                "components": ["EC", "DMC", "EMC", "DEC"],
                "condition": "cathode voltage > 4.5V",
                "issue": "Carbonate solvents oxidize at high voltages",
                "severity": "high",
                "solution": "Add FEC, use fluorinated solvents, or consider high-concentration electrolyte"
            }
        ]
    
    async def process(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze properties and compatibility of proposed components."""
        components = input_data.get("components", [])
        operating_conditions = input_data.get("operating_conditions", {})
        electrode_materials = input_data.get("electrode_materials", {})
        
        self.log_action("Analyzing components", str(components))
        
        # Get properties for each component
        properties = self._get_component_properties(components)
        
        # Check compatibility
        compatibility_issues = self._check_compatibility(
            components, operating_conditions, electrode_materials
        )
        
        # Calculate aggregate properties
        aggregate = self._calculate_aggregate_properties(properties)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            components, compatibility_issues, operating_conditions
        )
        
        return {
            "status": "success",
            "component_properties": properties,
            "aggregate_properties": aggregate,
            "compatibility_issues": compatibility_issues,
            "recommendations": recommendations,
            "is_compatible": len([i for i in compatibility_issues if i["severity"] == "critical"]) == 0
        }
    
    def _get_component_properties(self, components: List[str]) -> Dict[str, Any]:
        """Retrieve properties for specified components."""
        properties = {}
        for comp in components:
            comp_upper = comp.upper()
            if comp_upper in self.property_database:
                properties[comp_upper] = self.property_database[comp_upper]
            else:
                properties[comp_upper] = {"status": "unknown", "note": "Not in database"}
        return properties
    
    def _check_compatibility(
        self, 
        components: List[str], 
        operating_conditions: Dict[str, Any],
        electrode_materials: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check for compatibility issues between components."""
        issues = []
        components_upper = [c.upper() for c in components]
        
        voltage = operating_conditions.get("max_voltage", 4.2)
        temperature = operating_conditions.get("max_temperature", 45)
        anode = electrode_materials.get("anode", "graphite")
        
        for rule in self.compatibility_rules:
            # Check if rule components are in our formulation
            rule_components = [c.upper() for c in rule["components"]]
            if any(rc in components_upper for rc in rule_components):
                # Evaluate condition
                triggered = False
                
                if "PC" in rule_components and "PC" in components_upper:
                    if "graphite" in anode.lower():
                        triggered = True
                
                if "LiTFSI" in rule_components and "LiTFSI" in components_upper:
                    if voltage > 3.8:
                        triggered = True
                
                if "LiPF6" in rule_components and "LiPF6" in components_upper:
                    if temperature > 60:
                        triggered = True
                
                if "cathode voltage" in rule.get("condition", ""):
                    if voltage > 4.5:
                        triggered = True
                
                if triggered:
                    issues.append({
                        "rule_id": rule["rule_id"],
                        "issue": rule["issue"],
                        "severity": rule["severity"],
                        "solution": rule["solution"]
                    })
        
        return issues
    
    def _calculate_aggregate_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate aggregate properties of the electrolyte mixture."""
        solvents = {k: v for k, v in properties.items() 
                   if v.get("category") == "solvent"}
        
        if not solvents:
            return {}
        
        # Simplified weighted average (assuming equal parts)
        n = len(solvents)
        
        avg_viscosity = sum(s.get("viscosity", 1.0) for s in solvents.values()) / n
        avg_dielectric = sum(s.get("dielectric_constant", 10) for s in solvents.values()) / n
        min_oxidation = min(s.get("oxidation_potential", 6.0) for s in solvents.values())
        max_reduction = max(s.get("reduction_potential", 0.5) for s in solvents.values())
        
        return {
            "estimated_viscosity_mPas": round(avg_viscosity, 2),
            "estimated_dielectric_constant": round(avg_dielectric, 1),
            "electrochemical_window": (round(max_reduction, 2), round(min_oxidation, 2)),
            "window_width_V": round(min_oxidation - max_reduction, 2)
        }
    
    def _generate_recommendations(
        self, 
        components: List[str],
        issues: List[Dict[str, Any]],
        operating_conditions: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Address critical issues first
        for issue in issues:
            if issue["severity"] in ["critical", "high"]:
                recommendations.append(f"PRIORITY: {issue['solution']}")
        
        # General recommendations based on operating conditions
        voltage = operating_conditions.get("max_voltage", 4.2)
        temp = operating_conditions.get("max_temperature", 45)
        
        if voltage > 4.3:
            recommendations.append("Consider adding VC or FEC for high-voltage stability")
        
        if temp > 50:
            recommendations.append("Consider LiFSI or LiBF4 instead of LiPF6 for thermal stability")
        
        # Check for missing components
        components_upper = [c.upper() for c in components]
        has_additive = any(c in self.property_database and 
                         self.property_database[c].get("category") == "additive" 
                         for c in components_upper)
        
        if not has_additive:
            recommendations.append("Consider adding VC (1-2 wt%) for improved cycle life")
        
        return recommendations if recommendations else ["Formulation appears compatible for intended use"]
    
    def get_property(self, component: str) -> Optional[Dict[str, Any]]:
        """Get properties for a single component."""
        return self.property_database.get(component.upper())
    
    def list_components_by_category(self, category: str) -> List[str]:
        """List all components of a specific category."""
        return [k for k, v in self.property_database.items() 
                if v.get("category") == category]



