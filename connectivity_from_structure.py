__author__ = 'Tina'


from pymatgen.core.structure import Structure
from pymatgen import PeriodicSite
from effective_coordination import calculate_bond_weight, EffectiveCoordFinder
import math
import numpy


"""
Finds the connectivities between polyhedra within a structure, where we define connectivity by the number of shared
peripheral ions between two polyhedra. 0 shared peripheral ions indicates that there is no connectivity between the
two polyhedra; 1 shared peripheral ion indicates that there is point-sharing connectivity between the polyhedra; 2
shared peripheral ions indicate that there is edge-sharing connectivity between the polyhedra; 3 or more shared
peripheral ions indicate that there is face-sharing connectivity between the polyhedra.

For the purpose of this code, the peripheral ions will be defined by the ions surrounding a central site as given by
structure's get_neighbors function.

"""

class Polyhedra(object, object):

    """
    Object representing a polyhedra in a structure with central ion site "cation" and surrounding ions site
    "peripheralIons"

    """

    def __init__(self, cation, peripheralIons):
        self._center = cation
        self._peripheralIons = peripheralIons

    def get_central_name(self):
        return self._center.species_string

    def get_peripheral_sites(self):
        return self._peripheralIons

    def get_central_site(self):
        return self._center

    def get_connectivity(self, polyhedra2):
        """
        Gives the connectivity between the given polyhedra and another polyhedra by counting the number of atoms shared
        between the two polyhedra

        :param polyhedra2: (Polyhedra) target Polyhedra against which we are checking for connectivity with the current
        polyhedra
        :return: (int) Integer giving the number of peripheral ions shared by the current polyhedra and the target
        polyhedra; returns -1 if the same polyhedra is being compared to itself
        """

        if self._center == polyhedra2.get_central_site():
            return -1

        connections = 0
        for site1 in self._peripheralIons:
            for site2 in polyhedra2.get_peripheral_sites():
                if site1[0] == site2[0]:
                    connections += 1
                    break

        return connections

    def get_peripheral_distances(self):
        """
        Gives the distances between the central site and the peripheral ion sites (for determining bond weights)

        :return: (list) list of distances between the central ion site and the peripheral ion sites
        """
        peripheralDistances = []
        for peripheral in self._peripheralIons:
            peripheralDistances.append(peripheral.distance(self._center))

        return peripheralDistances


def get_connection(polyhedra1, polyhedra2):
    """
    Determines whether two polyhedra are connected (i.e. if they share any peripheral ions)

    :param polyhedra1: (Polyhedra) target polyhedra
    :param polyhedra2: (Polyhedra) target polyhedra we're getting connectivity with polyhedra1
    :return: (int) Integer giving the number of peripheral ions shared by the current polyhedra and the target
    polyhedra; returns -1 if the same polyhedra is being compared to itself
    """

    return polyhedra1.getConnectivity(polyhedra2)

    return connections

def get_surrounding_connectivity(structure, polyhedra):
    """
    Gives the surrounding connectivity of a specific polyhedra in a given structure

    :param structure: (Structure) target structure
    :param polyhedra: (Polyhedra) target polyhedra
    :return: (list) list of polyhedra that are connected to the target polyhedra in the target structure
    """

    polyhedraList = getAllCationPolyhedralWReflections(structure)

    connectedPolyhedra = []
    for otherPolyhedra in polyhedraList:
        connection = polyhedra.get_connection(otherPolyhedra)
        if connection > 0:
            connectedPolyhedra.append([otherPolyhedra, connection])

    return connectedPolyhedra

def get_polyhedra(structure, site, radius=3.2):
    """
    Gives a polyhedra in a structure based on the site, where nearby atoms are considered peripheral ions to the site
    if their bond weights (as defined by Hoppe, 1979) are greater than given value (i.e. the atoms contribute to the
    ECoN)

    :param structure: (Structure) target structure
    :param site: (PeriodicSite) target site
    :param radius: (float) largest possible distance within which peripheral ions can be obtained
    :return: (Polyhedra) polyhedra object representing the polyhedra around the target site in the target structure
    """
    anions = ['O2-', 'O', 'F-', 'F', 'Cl-', 'Cl', 'I-', 'I', 'Br-', 'Br', 'S2-', 'S']

    anionSites = []
    bondlengths = []
    peripheralSites = []

    for entry in structure.get_neighbors(site, radius):
        if entry[0].species_string in anions and entry[1] < radius:
            anionSites.append(entry)
            bondlengths.append(entry[1])
    for potentialPeripheralIons in anionSites:
        if calculate_bond_weight(potentialPeripheralIons[1], bondlengths) > 10.0**-5: #do not count nearby anions that do not contribute
            peripheralSites.append(potentialPeripheralIons)

    return Polyhedra(site, peripheralSites)

def count_connectivity(structure):

    """
    Gives the total counts of each type of connectivity (point-sharing, edge-sharing, face-sharing, as well as polyhedra
    that do not have sharing with any other polyhedra) within a given structure

    :param structure: (Structure) target structure
    :return: (dict) dictionary of all connectivity counts for each cation, where connectivity of 0 implies no
    connectivity, 1 implies point connectivity, 2 implies edge connectivity, and 3 or above implies face connectivity;
    the keys of the dict contain a cation while the values of the dict are the counts of each type of
    connectivity in a list, dict(cation) = [no-connectivity counts, point-connectivity counts, edge-connectivity counts,
    face-connectivity counts]
    """

    #need to fix getAllCationPolyhedralWReflections - make supercell and keep track of original cation polyhedra
    polyhedraList = getAllCationPolyhedralWReflections(structure)
    print len(polyhedraList)

    connections = {}
    for polyhedra1 in polyhedraList:
        cation = polyhedra1.get_central_name()
        connected = False #keep track of whether a polyhedra is not connected to any other polyhedra
        if not cation in connections.keys():
            connections[cation] = [0,0,0,0]
        for polyhedra2 in polyhedraList:
            connection = polyhedra1.get_connection(polyhedra2)
            if connection < 0:
                continue
            if connection == 1:
                connections[cation][1] += 1
                connected = True
            if connection == 2:
                connections[cation][2] += 1
                connected = True
            if connection >= 3:
                connections[cation][3] += 1
                connected = True
        if connected == False:
            connections[cation][0] += 1

    return connections

def get_cation_polyhedra_for_connectivity(structure, radius = 3.2):
    """
    Obtains all cation polyhedra needed to describe connectivity by creating a supercell and converting sites in the
    structure to cation polyhedra

    :param structure: (Structure) target structure
    :param radius: (float) radius within which to determine whether a nearby atom is a peripheral ion
    :return: (list) list of Polyhedra objects in supercell large enough to determine connectivities between polyhedra
    """



    anions = ['O2-', 'O', 'F-', 'F', 'Cl-', 'Cl', 'I-', 'I', 'Br-', 'Br', 'S2-', 'S']

    cationSites = []
    #include_index = True
    #for site in structure.get_all_neighbors(radius, include_index):
        #structure.get_all_neighbors returns list of list of neighbors:
        #   [[(site, dist, index of site in original cell)...], ...]
    structure.make_supercell(3)

def get_connectivity_matrix(structure, radius = 3.2):
    """
    Creates a connectivity matrix to describe the connectivity between cations in a structure; connections between
    cation polyhedra and reflections of itself (and reflections of other cation polyhedra) are also counted

    :param structure: (Structure) target structure
    :param radius: (float) radius within which to determine whether a nearby atom is a peripheral ion
    :return: (dict) dictionary of dictionaries, with the first set of keys being the specified (unreflected) Polyhedra
    sites, the second (inner) set of keys being the specified (unreflected) Polyhedra sites which we are comparing
    connectivity to, and the values being a list [x, y, z] which give the numbers of [point-sharing, edge-sharing, and
    face-sharing] instances between the first Polyhedra and all of the reflections of the second Polyhedra
    """




#use structure.get_all_neighbors(self, r, include_index=False) for finding neighbors in structure
def getAllCationPolyhedralWReflections(structure, margin = 0.05, radius = 3.0):

    anions = ['O2-', 'O', 'F-', 'F', 'Cl-', 'Cl', 'I-', 'I', 'Br-', 'Br', 'S2-', 'S']

    cationSites = []
    for site in structure.sites:
        if not site.species_string in anions:
            cationSites.append(site)
    reflections = []
    for site in cationSites:
        reflections = reflections + checkReflections(site, margin)
    useTemp = False
    if len(reflections) > 0:
        for site in reflections:
            cationSites.append(site)
        useTemp = True
        tempspecies = []
        tempfraccoords = []
        for site in structure.sites:
            tempspecies.append(site.species_string)
            tempfraccoords.append(site.frac_coords)
        for reflection in reflections:
            tempspecies.append(reflection.species_string)
            tempfraccoords.append(reflection.frac_coords)
        tempstruct = Structure(structure.lattice, tempspecies, tempfraccoords)
    if useTemp:
        structure = tempstruct
    print structure.formula
    polyhedralList = [] #list of polyhedrals with cations at the center
    for site in cationSites:
        sites = [site] #list of sites that will be in polyhedral
        anionSites = [] # list of all neighboring anions
        bondlengths = [] #list of bondslengths of anions
        bondweights = []
        for entry in structure.get_neighbors(site, radius):
            if entry[0].species_string in anions and entry[1] < radius:
                # sites.append(entry)
                anionSites.append(entry)
                bondlengths.append(entry[1])

        for bond in anionSites:
            if site.species_string == 'Rn':
                sites.append(bond)
                bondweights.append(1.0)
            else:
                if calculate_bond_weight(bond[1], bondlengths) > 0: #do not count nearby anions that do not contribute
                    sites.append(bond)
                    bondweights.append(calculate_bond_weight(bond[1], bondlengths))
                    #print bond
        #print "next central site"
        polyhedralList.append([sites, round(sum(bondweights))])
        #polyhedralList.append(sites)
            # list of polyhedral (-> list of list of sites) + coordnum

    return polyhedralList

def checkReflections(site, margin):
    x = 0
    y = 0
    z = 0
    reflections = []
    toReflect = site
    if toReflect.frac_coords[0] >= 0.0 and toReflect.frac_coords[0] <= margin:
        x = 1
    if toReflect.frac_coords[0] <= 1.0 and toReflect.frac_coords[0] >= 1.0 - margin:
        x = -1
    if toReflect.frac_coords[1] >= 0.0 and toReflect.frac_coords[1] <= margin:
        y = 1
    if toReflect.frac_coords[1] <= 1.0 and toReflect.frac_coords[1] >= 1.0 - margin:
        y = -1
    if toReflect.frac_coords[2] >= 0.0 and toReflect.frac_coords[2] <= margin:
        z = 1
    if toReflect.frac_coords[2] <= 1.0 and toReflect.frac_coords[2] >= 1.0 - margin:
        z = -1

    if x != 0:
        reflections.append(PeriodicSite(site.species_string, site.frac_coords + [x*1.0, 0, 0],
                                            site.lattice))
        if y != 0:
            reflections.append(PeriodicSite(site.species_string, site.frac_coords + [x*1.0, y*1.0, 0],
                                                site.lattice))
            if z != 0:
                reflections.append(PeriodicSite(site.species_string, site.frac_coords + [x*1.0, y*1.0, z*1.0],
                                                site.lattice))
        if z != 0:
            reflections.append(PeriodicSite(site.species_string, site.frac_coords + [x*1.0, 0, z*1.0],
                                            site.lattice))

    if y != 0:
        reflections.append(PeriodicSite(site.species_string, site.frac_coords + [0, y*1.0, 0],
                                            site.lattice))
        if z != 0:
            reflections.append(PeriodicSite(site.species_string, site.frac_coords + [0, y*1.0, z*1.0],
                                                site.lattice))

    if z != 0:
        reflections.append(PeriodicSite(site.species_string, site.frac_coords + [0, 0, z*1.0],
                                            site.lattice))

    return reflections

if __name__ == '__main__':
    s = Structure.from_file('LiCoO2.cif', True, False)
    print s
    print calculateConnectivity(s)