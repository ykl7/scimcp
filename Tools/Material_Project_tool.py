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

    def get_mat_summary(self,mat_formula:str, fields:list = ["material_id", "formula_pretty", "theoretical", "volume", "density"]):

        invalid = [f for f in fields if f != "material_id" and f not in self.Valid_fields]
        if invalid:
            print(f"Invalid field(s): {invalid}\n Please choose from: {self.Valid_fields}")
            return []
        
        summary = self.mpr.materials.summary.search(formula=mat_formula,fields=fields)
        cleaned = [self._mp_cleaner(s, fields) for s in summary]

        return cleaned
    
_mp_mat_sum = MaterialProjectTool()

def mp_manager(mcp):

    @mcp.tool(name="MaterialProject Material Summary", enabled=True)
    def mp_material_sum(mat_formula:str, fields:list = ["material_id", "formula_pretty", "theoretical", "volume", "density"]):
        """
        This tool provides material properties from the Materials Project database. 
        The agent should always use this tool when the user asks about a material's properties 
        (e.g., band gap, volume, density, formation energy, stability, etc.), or any other 
        quantitative/material-specific information.

        Inputs:
            - mat_formula (str): The chemical formula of the material (e.g., "NaCl", "LiFePO4").
            - fields (list[str]): A list of property fields to retrieve 
                                (e.g., ["band_gap", "density", "volume"]).

        Output:
            - A list of dictionaries, where each dictionary contains the requested property values 
            for the material.
        """

        return _mp_mat_sum.get_mat_summary(mat_formula, fields)



# if __name__ == "__main__":
#     fields = ["material_id","theoretical", "volume", "density"]
#     results = get_mat_summary("NdGaO3", fields)

#     print(results)






# from mp_api.client import MPRester
# import os

# api_key = os.getenv("MP_API") 
# exp = "NdGaO3"

# def exp_obs(search_formula, api_key):
#     mpr = MPRester(api_key)
#     try:
#         realstrcs = mpr.materials.summary.search(
#             formula=search_formula,
#             fields=["theoretical"]
#         )
#     except:
#         response = f'No entry found in Materials Project for {search_formula}.'
#         return response
        

#     if realstrcs == []:
#         response = f"There are no experimentally observed or theoretical structures with the formula {search_formula}."

#     elif len(realstrcs) == 1:
#         if hasattr(realstrcs[0], "theoretical") and realstrcs[0].theoretical is False:
#             response = f"There is one experimentally observed stucture with the formula {search_formula}."
    
#     else:
#         count = 0
#         for entry in realstrcs:
#             if hasattr(entry, "theoretical") and entry.theoretical is False:
#                 count += 1

#         if count != 0:
#             response = f"There are {count} experimentally observed structures with the formula {search_formula}."
#         elif count == 0:
#             response = f"There are no experimentally observed structures with the formula {search_formula}, but there are some theoretical ones."

#     return response

# def exp_obs2(search_formula, api_key, n_chars=10000):
#     mpr = MPRester(api_key)
#     try:
#         strcs = mpr.materials.summary.search(
#             formula=search_formula,
#         )
#     except:
#         response = f'No entry found in Materials Project for {search_formula}.'
#         summary_info = ''
#         return response, summary_info

#     if strcs == []:
#         response = f"There are no experimentally observed or theoretical structures with the formula {search_formula}."

#     realstrcs = [x for x in strcs if x.theoretical is False]


#     if len(realstrcs) == 1:
#         if hasattr(realstrcs[0], "theoretical") and realstrcs[0].theoretical is False:
#             response = f"There is one experimentally observed stucture with the formula {search_formula}."
    
#     else:
#         count = 0
#         for entry in realstrcs:
#             if hasattr(entry, "theoretical") and entry.theoretical is False:
#                 count += 1

#         if count != 0:
#             response = f"There are {count} experimentally observed structures with the formula {search_formula}."
#         elif count == 0:
#             response = f"There are no experimentally observed structures with the formula {search_formula}, but there are some theoretical ones."

#     realstrcs = realstrcs[:10]
#     summary_info = []
#     # limit to 10 materials
#     for i, r in enumerate(strcs[0:10], 1):
#         summary_info.append(f'Summary for material #{i} returned for {search_formula}')
#         summary_info.append(str(r))
#         summary_info.append('\n')

#     # for ease, just take the first n_chars
#     full_summary = '\n'.join(summary_info)
#     abbreviated_summary = full_summary[0:n_chars]
#     return response, '\n'.join(summary_info)


# if __name__ == "__main__":
#     print(exp_obs2(exp, api_key))