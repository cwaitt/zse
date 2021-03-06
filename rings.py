'''
The goal of this module is to identify the rings associated with an oxygen or
tsite in any given zeolite framework. This method uses graph theory to find
neighbors of the specified atom, and then a depth first search for a cycle back
to that atom. To make the code as efficient as possible, its important to
include what types are rings are possible in that framework. This information is
stored within the collections module of this package. Check the examples page on
github (github.com/jtcrum/zse/examples) for specifics on how to use.
'''

__all__ = ['get_orings','get_trings','get_fwrings']

from zse.collections import get_ring_sizes, framework
from zse.ring_utilities import *
from zse.utilities import *

# get_orings

def get_orings(atoms,index,code):
    '''
    Function to find all the rings asssociated with an oxygen atom in a zeolite
    framework.

    INPUTS:
    atoms:      (ASE atoms object) the zeolite framework to be analyzed
                works best if you remove any adsorbates first
    index:      (integer) index of the atom that you want to classify
    code:       (str) IZA code for the zeolite you are using (i.e. 'CHA')

    OUTPUTS:
    ring_list:      (list) The size of rings associated with the oxygen.
    paths:      (2d array) The actual atom indices that compose found rings.
    ring_atoms: (ASE atoms object) all the rings found
    '''
    # get possible rings, and max ring size
    ring_sizes = get_ring_sizes(code)*2
    max_ring = max(ring_sizes)

    # repeat the unit cell so it is large enough to capture the max ring size
    # also turn this new larger unit cell into a graph
    G, large_atoms, repeat = atoms_to_graph(atoms,index,max_ring)

    # get the closest neighbor of the oxygen, and find all possible rings
    # between that oxygen and its neighbor
    paths = get_paths(G,index,ring_sizes)

    # now we want to remove all the non ring paths
    paths = remove_non_rings(large_atoms, paths)

    # finally organize all outputs: list of ring sizes, atom indices that make
    # ring paths, and an atoms object that shows all those rings
    ring_list = [int(len(p)/2) for p in paths]
    paths = [x for _,x in sorted(zip(ring_list,paths),reverse=True)]
    ring_list.sort(reverse=True)

    ring_atoms = paths_to_atoms(large_atoms,paths)

    return ring_list, paths, ring_atoms

# get_trings
def get_trings(atoms,index,code):
    '''
    Function to find all the rings asssociated with a T-site in a zeolite
    framework.

    INPUTS:
    atoms:      (ASE atoms object) the zeolite framework to be analyzed
                works best if you remove any adsorbates first
    index:      (integer) index of the atom that you want to classify
    code:       (str) IZA code for the zeolite you are using (i.e. 'CHA')

    OUTPUTS:
    ring_list:      (list) The size of rings associated with the oxygen.
    paths:      (2d array) The actual atom indices that compose found rings.
    ring_atoms: (ASE atoms object) all the rings found
    '''
    #get possible rings, and max rings size
    ring_sizes = get_ring_sizes(code)*2
    max_ring = max(ring_sizes)

    # repeat the unit cell so it is large enough to capture the max ring size
    # also turn this new larger unit cell into a graph
    G, large_atoms, repeat = atoms_to_graph(atoms,index,max_ring)

    # to find all the rings associated with a T site, we need all the rings
    # associated with each oxygen bound to that T site. We will use networkx
    # neighbors to find those oxygens
    import networkx as nx
    paths = []
    for n in nx.neighbors(G,index):
        paths = paths+get_paths(G,n,ring_sizes)

    # now we want to remove all the non ring paths
    paths = remove_non_rings(large_atoms, paths)

    # finally organize all outputs: list of ring sizes, atom indices that make
    # ring paths, and an atoms object that shows all those rings
    ring_list = [int(len(p)/2) for p in paths]
    paths = [x for _,x in sorted(zip(ring_list,paths),reverse=True)]
    ring_list.sort(reverse=True)

    ring_atoms = paths_to_atoms(large_atoms,paths)

    return ring_list, paths, ring_atoms

# get_fwrings
def get_fwrings(code):
    '''
    Function to find all the unique rings in a zeolite framework.

    INPUTS:
    code:       (str) IZA code for the zeolite you are using (i.e. 'CHA')

    OUTPUTS:
    index_paths:    (dictionary) {ring length : indices of atoms in ring}
    label_paths:    (dictionary) {ring length : site labels of atoms in ring}
    trajectories:   (dictionary of atoms objects)  -
                    {ring length : [atoms objects for that size ring]}
    '''

    # First, get some basic info we will need about the framework
    # atoms object, possible ring sizes, and the index of each o-site type
    atoms = framework(code)
    ring_sizes = get_ring_sizes(code)
    osites,omults,oinds = get_osites(code)

    # now we find all the rings associated with each oxygen type in the fw
    # this in theory should find us every possible type of ring in the fw
    paths = []
    for o in oinds:
        paths += get_orings(atoms,o,code)[1]
    paths = remove_dups(paths)

    # now we want to get the t-site and o-site labels
    repeat = atoms_to_graph(atoms,0,max(ring_sizes)*2)[2]
    atoms = atoms.repeat(repeat)
    labels = site_labels(atoms,code)

    # now convert all the paths from index form into site label form
    index_paths = paths
    label_paths = []
    for path in index_paths:
        l = []
        for p in path:
            l.append(labels[p])
        label_paths.append(l)

    # now we want to remove duplicate rings based on the label_paths
    # this will also give us the paths in a conveinent dictionary
    index_paths, label_paths = remove_labeled_dups(index_paths, label_paths, ring_sizes)

    # last but not least, let's make an atoms object for each ring type so that
    # we can visualize them later
    # this will be a dictionary of trajectories
    trajectories = dict_to_atoms(index_paths,atoms)

    return index_paths, label_paths, trajectories
