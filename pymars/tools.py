"""Module with miscellanous tools.
"""
import os
from operator import attrgetter
import logging

import numpy as np
import cantera as ct
#from cantera import ck2cti
from cantera import ck2yaml
from cantera import yaml2ck
from . import soln2ck


def compare_models(model1, model2):
    """Checks whether two Cantera models are equivalent.

    Parameters
    ----------
    model1 : cantera.Solution
        First Cantera model object
    model2 : cantera.Solution
        Second Cantera model object

    Returns
    -------
    bool
        ``True`` if models match, ``False`` if models disagree
    
    """
    # at minimum, numbers of species and reactions should be the same
    if model1.n_species != model2.n_species:
        return False
    if model1.n_reactions != model2.n_reactions:
        return False

    for sp1, sp2 in zip(
        sorted(model1.species(), key=attrgetter('name')), 
        sorted(model2.species(), key=attrgetter('name'))
        ):
        if sp1.name != sp2.name:
            return False

        if sp1.composition != sp2.composition:
            return False
        
        if sp1.thermo.n_coeffs == sp2.thermo.n_coeffs:
            if any(sp1.thermo.coeffs != sp2.thermo.coeffs):
                return False
        else:
            return False
        
        if hasattr(sp1, 'transport') or hasattr(sp2, 'transport'):
            if hasattr(sp1, 'transport') and hasattr(sp2, 'transport'):
                # iterate over transport parameters
                params = [a for a in dir(sp1.transport) 
                          if not a.startswith('__') and 
                          not callable(getattr(sp1.transport, a))
                          ]
                for attr in params:
                    if getattr(sp1.transport, attr) != getattr(sp2.transport, attr, 0.0):
                        return False
            else:
                return False

    for rxn1, rxn2 in zip(
        sorted(model1.reactions(), key=attrgetter('equation')), 
        sorted(model2.reactions(), key=attrgetter('equation'))
        ):
        if type(rxn1) != type(rxn2):
            return False
        
        if rxn1.reactants != rxn2.reactants:
            return False
        if rxn1.products != rxn2.products:
            return False

        if rxn1.duplicate != rxn2.duplicate:
            return False

        # Check rate parameters for elementary and third-body reactions
        if hasattr(rxn1, 'rate') or hasattr(rxn2, 'rate'):
            if hasattr(rxn1, 'rate') and hasattr(rxn2, 'rate'):
                if type(rxn1.rate) != type(rxn2.rate):
                    return False
                if len(dir(rxn1.rate)) != len(dir(rxn2.rate)):
                    return False
                params = [
                    a for a in dir(rxn1.rate) 
                    if not a.startswith('__') and not callable(getattr(rxn1.rate, a))
                    ]
                for attr in params:
                    if getattr(rxn1.rate, attr) != getattr(rxn2.rate, attr, 0.0):
                        return False
            else:
                return False
        
        # For falloff and chemically activated reactions, check low and high rates
        if hasattr(rxn1, 'low_rate') or hasattr(rxn2, 'low_rate'):
            if hasattr(rxn1, 'low_rate') and hasattr(rxn2, 'low_rate'):
                if type(rxn1.low_rate) != type(rxn2.low_rate):
                    return False
                if len(dir(rxn1.low_rate)) != len(dir(rxn2.low_rate)):
                    return False
                params = [
                    a for a in dir(rxn1.low_rate) 
                    if not a.startswith('__') and not callable(getattr(rxn1.low_rate, a))
                    ]
                for attr in params:
                    if getattr(rxn1.low_rate, attr) != getattr(rxn2.low_rate, attr, 0.0):
                        return False
            else:
                return False

        if hasattr(rxn1, 'high_rate') or hasattr(rxn2, 'high_rate'):
            if hasattr(rxn1, 'high_rate') and hasattr(rxn2, 'high_rate'):
                if type(rxn1.high_rate) != type(rxn2.high_rate):
                    return False
                if len(dir(rxn1.high_rate)) != len(dir(rxn2.high_rate)):
                    return False
                params = [
                    a for a in dir(rxn1.high_rate) 
                    if not a.startswith('__') and not callable(getattr(rxn1.high_rate, a))
                    ]
                for attr in params:
                    if getattr(rxn1.high_rate, attr) != getattr(rxn2.high_rate, attr, 0.0):
                        return False
            else:
                return False
        
        # check Plog rates
        if hasattr(rxn1, 'rates') or hasattr(rxn2, 'rates'):
            if hasattr(rxn1, 'rates') and hasattr(rxn2, 'rates'):
                if len(rxn1.rates) != len(rxn2.rates):
                    return False
                for rate1, rate2 in zip(
                    sorted(rxn1.rates, key=lambda rate: rate[0]),
                    sorted(rxn2.rates, key=lambda rate: rate[0]),
                    ):
                    if not np.allclose(rate1[0], rate2[0]):
                        return False
                    params = ['activation_energy', 'pre_exponential_factor', 'temperature_exponent']
                    for param in params:
                        if getattr(rate1[1], param, 0.0) != getattr(rate2[1], param, 0.0):
                            return False
            
        # check Chebyshev parameters
        if hasattr(rxn1, 'coeffs') or hasattr(rxn2, 'coeffs'):
            if hasattr(rxn1, 'coeffs') and hasattr(rxn2, 'coeffs'):
                if rxn1.nPressure != rxn2.nPressure:
                    return False
                if rxn1.nTemperature != rxn2.nTemperature:
                    return False
                if (rxn1.Pmax != rxn2.Pmax) or (rxn1.Pmin != rxn1.Pmin):
                    return False
                if (rxn1.Tmax != rxn2.Tmax) or (rxn1.Tmin != rxn1.Tmin):
                    return False
                if not np.allclose(rxn1.coeffs, rxn2.coeffs):
                    return False
        
        # ensure matching default efficiencies, if present
        if getattr(rxn1, 'default_efficiency', 1.0) != getattr(rxn2, 'default_efficiency', 1.0):
            return False
        
        if hasattr(rxn1, 'efficiencies') or hasattr(rxn2, 'efficiencies'):
            if hasattr(rxn1, 'efficiencies') and hasattr(rxn2, 'efficiencies'):
                if rxn1.efficiencies != rxn2.efficiencies:
                    return False
            else:
                return False
        
        # Check falloff parameters if any
        if hasattr(rxn1, 'falloff') or hasattr(rxn2, 'falloff') :
            if hasattr(rxn1, 'falloff') and hasattr(rxn2, 'falloff'):
                if len(rxn1.falloff.parameters) == len(rxn2.falloff.parameters):
                    if any(rxn1.falloff.parameters != rxn2.falloff.parameters):
                        return False
                else:
                    return False
            else:
                return False

    return True


def convert(model_file, thermo_file=None, transport_file=None, path=''):
    """Function to convert between Cantera and Chemkin model formats.

    Parameters
    ----------
    model_file : str
        Input model file (Cantera .cti or Chemkin)
    thermo_file : str, optional
        Chemkin thermodynamic properties file
    transport_file : str, optional
        Chemkin transport data file
    path : str, optional
        Path for writing file

    Returns
    -------
    str or list
        Path to converted file, or list of files (for Chemkin)

    Example
    -------
    >>> convert('gri30.inp')
    gri30.cti

    >>> convert('gri30.cti')
    [gri30.inp, gri30_thermo.dat, gri30_transport.dat]

    """
    # check whether Chemkin or Cantera model
    basename = os.path.splitext(os.path.basename(model_file))[0]
    extension = os.path.splitext(os.path.basename(model_file))[1]

    # Chemkin files can have multiple extensions, so easier to check if Cantera
    if extension == '.cti':
        # Convert from Cantera to Chemkin format.
        print('Converter detected CTI Cantera input model: ' + model_file)
        print('Converting to Chemkin format.')

        solution = ct.Solution(model_file)
        converted_files = soln2ck.write(solution, basename + '.inp', path=path)
        return converted_files
    else:
        # Convert from Chemkin to Cantera format.
        print('Converter detected Chemkin input model: ' + model_file)
        print('Converting to Cantera format.')

        converted_file = os.path.join(path, basename + '.yaml')

        # calls ck2yaml based on given files
        args = [f'--input={model_file}']
        if thermo_file:
            args.append(f'--thermo={thermo_file}')
        if transport_file:
            args.append(f'--transport={transport_file}')
        args.append(f'--output={converted_file}')
        
        # generally Chemkin files have issues (redundant species, etc.) that require this argument
        args.append('--permissive')

        ck2yaml.main(args)
        return converted_file