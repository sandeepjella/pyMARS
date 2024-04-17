"""writes a solution object to a cantera cti file.

currently only works for Elementary, Falloff, Plog and ThreeBody Reactions
Cantera development version 2.3.0a2 required
"""

import os
import math
from textwrap import fill

import cantera as ct

# number of calories in 1000 Joules
CALORIES_CONSTANT = 4184.0

# Conversion from 1 debye to coulomb-meters
DEBEYE_CONVERSION = 3.33564e-30

indent = ['',
          ' ',
          '  ',
          '   ',
          '    ',
          '     ',
          '      ',
          '       ',
          '        ',
          '          ',
          '           ',
          '            ',
          '             ',
          '              ',
          '               ',
          '                '
          ]


def write(solution, output_filename='',path=''):
    """Function to write cantera solution object to cti file.

    Parameters
    ----------
    solution : cantera.Solution
        Model to be written
    output_filename : str, optional
        Name of file to be written; if not provided, use ``solution.name``
    path : str, optional
        Path for writing file.

    Returns
    -------
    output_filename : str
        Name of output model file (.cti)

    Examples
    --------
    >>> gas = cantera.Solution('gri30.cti')
    >>> soln2cti.write(gas, 'copy_gri30.cti')
    copy_gri30.cti

    """
    if output_filename:
        output_filename = os.path.join(path, output_filename)
    else:
        output_filename = os.path.join(path, f'{solution.name}.yaml')
    
    if os.path.isfile(output_filename):
        os.remove(output_filename)
        
    solution.write_yaml(output_filename,solution)    

   
    return output_filename
