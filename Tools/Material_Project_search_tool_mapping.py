#Material_Project_search_tool_mapping
import os, sys, time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mp_api.client import MPRester
from mp_api.client.routes.materials.alloys import AlloysRester

def get_search_map(mpr: MPRester):
    return {
        # MATERIALS ENDPOINTS
        "summary": mpr.materials.summary.search,
        "absorption": mpr.materials.absorption.search,
        "dielectric": mpr.materials.dielectric.search,
        "elasticity": mpr.materials.elasticity.search,
        "alloys": AlloysRester().search,
        "bonds": mpr.materials.bonds.search,
        "chemenv": mpr.materials.chemenv.search,
        # "core": mpr.materials.core.search,
        "bandstructure": mpr.materials.electronic_structure_bandstructure.search,
        "dos": mpr.materials.electronic_structure_dos.search,
        "electronic_structure": mpr.materials.electronic_structure.search,
        "eos": mpr.materials.eos.search,
        # "grain_boundaries": mpr.materials.grain_boundaries.search,
        "insertion_electrodes": mpr.materials.insertion_electrodes.search,
        "magnetism": mpr.materials.magnetism.search,
        "oxidation_states": mpr.materials.oxidation_states.search,
        "phonon": mpr.materials.phonon.search,
        "piezoelectric": mpr.materials.piezoelectric.search,
        "provenance": mpr.materials.provenance.search,
        "robocrys": mpr.materials.robocrys.search,
        "similarity": mpr.materials.similarity.search,
        "substrates": mpr.materials.substrates.search,
        "surface_properties": mpr.materials.surface_properties.search,
        "synthesis": mpr.materials.synthesis.search,
        "tasks": mpr.materials.tasks.search,
        "thermo": mpr.materials.thermo.search,
        "xas": mpr.materials.xas.search,

        # DOI
        "doi": mpr.doi.search,

        # MOLECULES
        "molecule_summary": mpr.molecules.summary.search,
        # "molecule_assoc": mpr.molecules.assoc.search,
        # "molecule_bonding": mpr.molecules.bonding.search,
        # "molecule_core": mpr.molecules.core.search,
        # "molecule_jcesr": mpr.molecules.jcesr.search,
        # "molecule_orbitals": mpr.molecules.orbitals.search,
        # "molecule_partial_charges": mpr.molecules.partial_charges.search,
        # "molecule_partial_spins": mpr.molecules.partial_spins.search,
        # "molecule_redox": mpr.molecules.redox.search,
        # "molecule_summary": mpr.molecules.summary.search,
        # "molecule_tasks": mpr.molecules.tasks.search,
        # "molecule_thermo": mpr.molecules.thermo.search,
        # "molecule_vibrations": mpr.molecules.vibrations.search,
    }
