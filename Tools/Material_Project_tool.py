# Material_Project_tool
import os, sys
from mp_api.client import MPRester

class MaterialProjectTool:

    Valid_fields = ['builder_meta', 'nsites', 'elements', 'nelements', 'composition', 'composition_reduced', 'formula_pretty', 'formula_anonymous', 'chemsys', 'volume', 'density', 'density_atomic', 'symmetry', 'property_name', 'deprecated', 'deprecation_reasons', 'last_updated', 'origins', 'warnings', 'structure', 'task_ids', 'uncorrected_energy_per_atom', 'energy_per_atom', 'formation_energy_per_atom', 'energy_above_hull', 'is_stable', 'equilibrium_reaction_energy_per_atom', 'decomposes_to', 'xas', 'grain_boundaries', 'band_gap', 'cbm', 'vbm', 'efermi', 'is_gap_direct', 'is_metal', 'es_source_calc_id', 'bandstructure', 'dos', 'dos_energy_up', 'dos_energy_down', 'is_magnetic', 'ordering', 'total_magnetization', 'total_magnetization_normalized_vol', 'total_magnetization_normalized_formula_units', 'num_magnetic_sites', 'num_unique_magnetic_sites', 'types_of_magnetic_species', 'bulk_modulus', 'shear_modulus', 'universal_anisotropy', 'homogeneous_poisson', 'e_total', 'e_ionic', 'e_electronic', 'n', 'e_ij_max', 'weighted_surface_energy_EV_PER_ANG2', 'weighted_surface_energy', 'weighted_work_function', 'surface_anisotropy', 'shape_factor', 'has_reconstructed', 'possible_species', 'has_props', 'theoretical', 'database_IDs']
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MP_API")
        self.mpr = MPRester(self.api_key)

    def _mp_cleaner(self,summary, fields):
        final_output = {}

        for field in fields:
            if hasattr(summary, field):
                final_output[field] = getattr(summary, field)
        
        return final_output

    def get_mat_summary(self,mat_formula:str, fields:list = ["material_id","band_gap", "formula_pretty", "theoretical", "volume", "density"]):

        invalid = [f for f in fields if f != "material_id" and f not in self.Valid_fields]
        if invalid:
            fields = [f"Invalid field(s): {invalid}\n Please choose from: {self.Valid_fields}"]
            return fields
        
        summary = self.mpr.materials.summary.search(formula=mat_formula,fields=fields)
        if not summary:
            try:
                elements = "-".join(sorted(["".join(g) for g in __import__('re').findall(r'[A-Z][a-z]*', mat_formula)]))
                summary = self.mpr.materials.summary.search(chemsys=elements, fields=fields)
            except Exception as e:
                return [{"error": f"No materials found and fallback failed: {e}"}]

        if not summary:
            return [{"error": f"No materials found for formula '{mat_formula}'"}]
        cleaned = [self._mp_cleaner(s, fields) for s in summary]

        return cleaned
    
_mp_mat_sum = MaterialProjectTool()

def mp_manager(mcp):

    @mcp.tool(name="Get Material Properties from MP", enabled=True)
    def get_materials_properties(mat_formula:str, fields:list = ["material_id","band_gap", "formula_pretty", "theoretical", "volume", "density"]):
        """
        This tool provides material properties from the Materials Project database. !! ALWAYS USE THIS TOOL WHEN ANY PROPERTIES ARE ASKED ABOUT A MATERIAL !!
        (e.g., band gap, volume, density, formation energy, etc.), or any other 
        quantitative/material-specific information.

        ALWAYS PROVIDE THE MATERIAL FORMULA WHEN ASKING FOR PROPERTIES.
        Inputs:
            - mat_formula (str): The chemical formula of the material (e.g., "NaCl", "LiFePO4").
            - fields (list[str]): A list of property fields to retrieve 
                                (e.g., ["band_gap", "density", "volume"]).

        Output:
            - A list of dictionaries, where each dictionary contains the requested property values 
            for the material.
        """

        return _mp_mat_sum.get_mat_summary(mat_formula, fields)



if __name__ == "__main__":
    fields = ["material_id",'formula_pretty', 'density', 'volume', 'formation_energy_per_atom']
    matp = MaterialProjectTool()
    results = matp.get_mat_summary("Al2Fe", fields)

    print(results)
