from typing import Dict, Any, Optional, List
import os
from .base_agent import BaseAgent

class LiteratureRAGAgent(BaseAgent):
    """Agent for searching and summarizing electrolyte/additive papers using RAG."""
    
    def __init__(self, vector_store=None):
        super().__init__(
            name="LiteratureRAGAgent",
            description="Searches and summarizes electrolyte/additive literature using RAG"
        )
        self.vector_store = vector_store
        self.knowledge_base = self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize with foundational electrolyte knowledge."""
        return {
            "common_solvents": {
                "EC": {
                    "name": "Ethylene Carbonate",
                    "properties": "High dielectric constant (~90), high melting point (36°C)",
                    "use_case": "Primary solvent for lithium-ion batteries, excellent SEI former"
                },
                "DMC": {
                    "name": "Dimethyl Carbonate",
                    "properties": "Low viscosity, low dielectric constant",
                    "use_case": "Co-solvent to reduce viscosity, improves ion mobility"
                },
                "EMC": {
                    "name": "Ethyl Methyl Carbonate",
                    "properties": "Low viscosity, good low-temperature performance",
                    "use_case": "Co-solvent for improved rate capability"
                },
                "DEC": {
                    "name": "Diethyl Carbonate",
                    "properties": "Very low viscosity, wide liquid range",
                    "use_case": "Co-solvent for high-rate applications"
                },
                "PC": {
                    "name": "Propylene Carbonate",
                    "properties": "High dielectric constant, low melting point (-49°C)",
                    "use_case": "Single solvent for some applications, graphite incompatible"
                }
            },
            "common_salts": {
                "LiPF6": {
                    "name": "Lithium Hexafluorophosphate",
                    "properties": "High ionic conductivity, thermally unstable above 60°C",
                    "use_case": "Most common commercial lithium salt"
                },
                "LiTFSI": {
                    "name": "Lithium bis(trifluoromethanesulfonyl)imide",
                    "properties": "Thermally stable, corrosive to aluminum at high voltage",
                    "use_case": "Solid-state and high-temperature applications"
                },
                "LiFSI": {
                    "name": "Lithium bis(fluorosulfonyl)imide",
                    "properties": "High ionic conductivity, better thermal stability than LiPF6",
                    "use_case": "High-performance liquid electrolytes"
                },
                "LiBF4": {
                    "name": "Lithium Tetrafluoroborate",
                    "properties": "Lower conductivity, better thermal stability",
                    "use_case": "High-temperature applications"
                }
            },
            "common_additives": {
                "VC": {
                    "name": "Vinylene Carbonate",
                    "properties": "Polymerizes on anode surface",
                    "use_case": "SEI stabilizer, improves cycle life (1-2 wt%)"
                },
                "FEC": {
                    "name": "Fluoroethylene Carbonate",
                    "properties": "Forms fluorinated SEI components",
                    "use_case": "Silicon anode stabilizer, high-voltage stabilizer (5-10 wt%)"
                },
                "PS": {
                    "name": "Propane Sultone",
                    "properties": "Forms sulfur-containing SEI",
                    "use_case": "Anode passivation, reduces gas generation (1-3 wt%)"
                },
                "LiBOB": {
                    "name": "Lithium bis(oxalato)borate",
                    "properties": "Forms protective cathode film",
                    "use_case": "High-voltage cathode stabilizer (0.5-1 wt%)"
                },
                "DTD": {
                    "name": "1,3,2-Dioxathiolane 2,2-dioxide",
                    "properties": "Sulfur-containing additive",
                    "use_case": "SEI former, capacity retention improvement (1-2 wt%)"
                }
            },
            "recent_trends": [
                "High-concentration electrolytes (>3M) for extended voltage windows",
                "Localized high-concentration electrolytes with diluents",
                "Fluorinated solvents for high-voltage stability",
                "Ionic liquid electrolytes for safety",
                "Solid-state electrolytes: sulfides, oxides, polymers",
                "Dual-salt electrolytes for synergistic effects",
                "Weakly-coordinating anions for improved kinetics"
            ]
        }
    
    async def process(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search literature and provide relevant information."""
        query = input_data.get("query", "")
        self.log_action("Processing query", query)
        
        results = []
        
        # Search vector store if available
        if self.vector_store:
            try:
                rag_results = await self._search_vector_store(query)
                results.extend(rag_results)
            except Exception as e:
                self.logger.error(f"Vector store search failed: {e}")
        
        # Search knowledge base
        kb_results = self._search_knowledge_base(query)
        results.extend(kb_results)
        
        # Generate summary
        summary = self._generate_summary(query, results)
        
        return {
            "status": "success",
            "query": query,
            "results": results,
            "summary": summary,
            "sources_count": len(results)
        }
    
    async def _search_vector_store(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the vector store for relevant documents with relevance scores."""
        if not self.vector_store:
            return []
        
        try:
            import asyncio
            # Run synchronous similarity_search_with_score in thread pool for real scores
            loop = asyncio.get_event_loop()
            
            # Try similarity_search_with_score first for relevance scores
            try:
                docs_with_scores = await loop.run_in_executor(
                    None,
                    lambda: self.vector_store.similarity_search_with_score(query, k=k)
                )
                
                results = []
                for doc, score in docs_with_scores:
                    # Convert distance to similarity score (lower distance = higher similarity)
                    # ChromaDB returns L2 distance, convert to 0-1 similarity
                    similarity = max(0, min(1, 1 - (score / 2)))  # Normalize score
                    
                    results.append({
                        "title": doc.metadata.get("source", "Uploaded Document"),
                        "content": doc.page_content,
                        "relevance_score": round(similarity, 2),
                        "source": "uploaded_document",
                        "page": doc.metadata.get("page"),
                        "chunk_id": doc.metadata.get("chunk_id"),
                        "metadata": {
                            k: v for k, v in doc.metadata.items() 
                            if k not in ["source"]
                        }
                    })
                
                return results
                
            except Exception:
                # Fallback to regular similarity_search without scores
                docs = await loop.run_in_executor(
                    None,
                    lambda: self.vector_store.similarity_search(query, k=k)
                )
                return [
                    {
                        "title": doc.metadata.get("source", "Uploaded Document"),
                        "content": doc.page_content,
                        "relevance_score": 0.85,  # Default score when not available
                        "source": "uploaded_document",
                        "page": doc.metadata.get("page"),
                        "metadata": doc.metadata
                    }
                    for doc in docs
                ]
                
        except Exception as e:
            self.logger.error(f"Vector search error: {e}")
            return []
    
    def _search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """Search the internal knowledge base."""
        results = []
        query_lower = query.lower()
        
        # Search solvents
        for abbr, info in self.knowledge_base["common_solvents"].items():
            if abbr.lower() in query_lower or info["name"].lower() in query_lower:
                results.append({
                    "title": f"Solvent: {info['name']} ({abbr})",
                    "content": f"Properties: {info['properties']}. Use case: {info['use_case']}",
                    "relevance_score": 0.9,
                    "source": "knowledge_base"
                })
        
        # Search salts
        for abbr, info in self.knowledge_base["common_salts"].items():
            if abbr.lower() in query_lower or info["name"].lower() in query_lower:
                results.append({
                    "title": f"Salt: {info['name']} ({abbr})",
                    "content": f"Properties: {info['properties']}. Use case: {info['use_case']}",
                    "relevance_score": 0.9,
                    "source": "knowledge_base"
                })
        
        # Search additives
        for abbr, info in self.knowledge_base["common_additives"].items():
            if abbr.lower() in query_lower or info["name"].lower() in query_lower:
                results.append({
                    "title": f"Additive: {info['name']} ({abbr})",
                    "content": f"Properties: {info['properties']}. Use case: {info['use_case']}",
                    "relevance_score": 0.9,
                    "source": "knowledge_base"
                })
        
        # Add relevant trends based on keywords
        trend_keywords = ["high-voltage", "safety", "solid-state", "silicon", "fast-charging", "concentration"]
        for keyword in trend_keywords:
            if keyword in query_lower:
                for trend in self.knowledge_base["recent_trends"]:
                    if keyword in trend.lower():
                        results.append({
                            "title": "Recent Research Trend",
                            "content": trend,
                            "relevance_score": 0.75,
                            "source": "knowledge_base"
                        })
        
        return results
    
    def _generate_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate a summary of the search results."""
        if not results:
            return f"No specific literature found for query: '{query}'. Consider refining your search or uploading relevant documents."
        
        summary_parts = [f"Found {len(results)} relevant sources for '{query}':\n"]
        
        for i, result in enumerate(results[:5], 1):
            summary_parts.append(f"{i}. {result['title']}: {result['content'][:200]}...")
        
        return "\n".join(summary_parts)
    
    def set_vector_store(self, vector_store):
        """Update the vector store reference."""
        self.vector_store = vector_store
        self.log_action("Vector store updated")

