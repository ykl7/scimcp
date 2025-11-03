# Material_Project_tool.py
import os, re, sys
from mp_api.client import MPRester
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Tools.Material_Project_search_tool_mapping import get_search_map

class MaterialProjectTool:

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MP_API_KEY")
        self.mpr = MPRester(self.api_key)
        self.search_map = get_search_map(self.mpr)
        self.formula_domains = {
            "summary", "thermo", "oxidation_states", "absorption", "task", "xas",
            "base_electrodes", "conversion_electrodes", "chemenv", "alloys", "synthesis"
        }
        self.material_id_domains = {
            "eos", "similarity", "grain_boundaries", "surface_properties", "phonon",
            "elasticity", "dielectric", "piezoelectric", "magnetism", "robocrys",
            "provenance", "bonds", "electronic_structure", "electronic_structure/bandstructure",
            "electronic_structure/dos"
        }
        self.other_domains = {"synthesis", "robocrys"} 

    def _mp_cleaner(self, summary, fields):
        return {field: getattr(summary, field, None) for field in fields}
    
    def _get_material_ids(self, mat_formula: str, top_k: int = 1):
        try:
            results = self.search_map["summary"](formula=mat_formula, fields=["material_id", "formula_pretty"])
            if not results:
                elements = "-".join(sorted(re.findall(r'[A-Z][a-z]*', mat_formula)))
                results = self.search_map["summary"](chemsys=elements, fields=["material_id", "formula_pretty"])
            return [r.material_id for r in results][:top_k]
        except Exception as e:
            return []
        
    def get_mat_properties(self, mat_formula: str,
                        fields: list = ["material_id", "band_gap", "formula_pretty", "theoretical", "volume", "density"],
                        domain: str = "summary", give_domain_list: bool = False, top_k: int = 1):

        if give_domain_list:
            return {
                "formula_query_domains": sorted(self.formula_domains),
                "material_id_query_domains": sorted(self.material_id_domains),
                "other_query_domains": sorted(self.other_domains),
                "all_domains": sorted(self.search_map.keys())
            }

        if domain not in self.search_map:
            return [{"error": f"Invalid domain '{domain}'. Choose from: {list(self.search_map.keys())}"}]

        search_fn = self.search_map[domain]

        try:
            # Case 1: Formula-based domains
            if domain in self.formula_domains:
                if domain == "summary":
                    results = search_fn(formula=mat_formula, fields=fields)
                    if not results:
                        elements = "-".join(sorted(re.findall(r'[A-Z][a-z]*', mat_formula)))
                        results = search_fn(chemsys=elements, fields=fields)
                    if not results:
                        return [{"error": f"No materials found for formula '{mat_formula}'"}]
                    return [self._mp_cleaner(r, fields) for r in results[:top_k]]

                else:
                    material_ids = self._get_material_ids(mat_formula, top_k)
                    if not material_ids:
                        return [{"error": f"Could not find any material_id for formula '{mat_formula}'"}]
                    results = search_fn(material_ids=material_ids, fields=fields)
                    if not results:
                        return [{"error": f"No data found in domain '{domain}' for material_id(s): {material_ids}"}]
                    return [self._mp_cleaner(r, fields) for r in results]

            # Case 2: Material-ID-based domains (always requires ID lookup)
            elif domain in self.material_id_domains:
                material_ids = self._get_material_ids(mat_formula, top_k)
                if not material_ids:
                    return [{"error": f"Could not find material_id for formula '{mat_formula}'"}]
                results = search_fn(material_ids=material_ids, fields=fields)
                if not results:
                    return [{"error": f"No data found for material_id(s) {material_ids} in domain '{domain}'"}]
                return [self._mp_cleaner(r, fields) for r in results]

            # Case 3: Other domains
            else:
                return [{"error": f"The domain '{domain}' may require special query types (e.g., keywords). Currently unsupported via formula-only interface."}]

        except Exception as e:
            return [{
                "error": f"Query failed: {e}",
                "valid_fields": f"Please try again with these valid fields for the domain :{getattr(search_fn, 'available_fields', [])}"
            }]


# Singleton instance
_mp_mat_tool = MaterialProjectTool()

def mp_manager(mcp):

    @mcp.tool(name="Get Material Properties from MP", enabled=True)
    def get_materials_properties(mat_formula: str, fields: list = ["material_id", "band_gap", "formula_pretty", "theoretical", "volume", "density"], domain: str = "summary", give_domain_list: bool = False):
        """
        This tool provides material properties from the Materials Project database.
        THE TOOL ALWAYS PROVIDES THE DOMAIN LIST IF THE give_domain_list INPUT IS SET TO TRUE. !! WHEN CALLING THIS TOOL FOR FIRST TIME, ALWAYS SET give_domain_list = TRUE!!
        !! ALWAYS INCLUDE THE DOMAIN OF THE PROPERTY SO THAT THE CORRECT ENDPOINT IS USED!!
        example: 
                - To get magnetic properties, set domain="magnetism"
                - To get Thermal properties, set domain="thermo"
                - summary domain is default for general properties
        !! ALWAYS USE THIS TOOL WHEN ANY PROPERTIES ARE ASKED ABOUT A MATERIAL !!

        Inputs:
            - mat_formula (str): Chemical formula (e.g., "NaCl", "LiFePO4")
            - fields (list[str]): Fields to retrieve (e.g., ["band_gap", "density"])
            - domain (str): Which MP endpoint to query (default="summary")

        Output:
            - A list of dicts with the requested fields
        """
        return _mp_mat_tool.get_mat_properties(mat_formula, fields, domain, give_domain_list)


# if __name__ == "__main__":
#     fields = ['builder_meta', 'alloy_pair', 'pair_id']
#     matp = MaterialProjectTool()
#     results = matp.get_mat_properties("NaCl", fields, domain="summary")
#     print(results)
