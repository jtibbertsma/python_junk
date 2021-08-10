from collections import namedtuple, Counter
from copy import deepcopy

class MoleculeError(ValueError): pass
class InvalidBond(MoleculeError): pass
class UnlockedMolecule(MoleculeError): pass
class LockedMolecule(MoleculeError): pass
class EmptyMolecule(MoleculeError): pass

class Atom(object):
    AtomInfo = namedtuple(
        'AtomInfo',
        ('valence_number', 'atomic_weight'))
    InfoTable = {
        'H':  AtomInfo(1,  1.0),
        'B':  AtomInfo(3, 10.8),
        'C':  AtomInfo(4, 12.0),
        'N':  AtomInfo(3, 14.0),
        'O':  AtomInfo(2, 16.0),
        'F':  AtomInfo(1, 19.0),
        'Mg': AtomInfo(2, 24.3),
        'P':  AtomInfo(3, 31.0),
        'S':  AtomInfo(2, 32.1),
        'Cl': AtomInfo(1, 35.5),
        'Br': AtomInfo(1, 80.0),
    }

    def __init__ (self, element, id_):
        self.id = id_
        self._bound_atoms = []
        self.mutate(element)

    def mutate(self, element):
        new_info = self.InfoTable[element]
        if new_info.valence_number < len(self._bound_atoms):
            raise InvalidBond(f'mutating {self} to {element} with {self.num_bonds()} bonds')
        self._info = new_info
        self.element = element
    
    def num_bonds(self):
        """Get the number of atoms bound to this atom"""
        return len(self._bound_atoms)
    
    def remove_hydrogen_atoms(self):
        """Unbond this atom from any hydrogen atoms"""
        self._bound_atoms = [atom for atom in self._bound_atoms if atom.element != 'H']

    def ensure_can_bind(self):
        if self.valence_number == len(self._bound_atoms):
            raise InvalidBond(f'{self.element} atoms can only be '
                              f'bound to {self.valence_number} other atoms')

    @staticmethod
    def bond(a1, a2):
        if a1 == a2:
            raise InvalidBond(f'Cannot bond atom {a1} to itself')
        a1.ensure_can_bind()
        a2.ensure_can_bind()
        a1._bound_atoms.append(a2)
        a2._bound_atoms.append(a1)

    def _repr_helper(self):
        if self.element == 'H':
            return 'H'
        return f'{self.element}{self.id}'

    def __repr__(self):
        inner = f'{self.element}.{self.id}'
        if self._bound_atoms:
            self._bound_atoms.sort(key=lambda atom: atom.id)
            self._bound_atoms.sort(key=lambda atom: self.atomic_element_key(atom.element))
            self._bound_atoms.sort(key=self._hydrogen_last_key)
            inner += ': ' + ','.join(atom._repr_helper() for atom in self._bound_atoms)
        return f'Atom({inner})'

    @staticmethod
    def atomic_element_key(element):
        """Sort key to order elements so that CHO come first in that order, followed by
        other elements in alphabetical order
        """
        if element == 'C':
            return '0'
        if element == 'H':
            return '1'
        if element == 'O':
            return '2'
        return element
    
    @staticmethod
    def _hydrogen_last_key(atom):
        return 1 if atom.element == 'H' else 0

    def __getattr__(self, name):
        try:
            # Delegate to AtomInfo
            return getattr(self._info, name)
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __deepcopy__(self, memo):
        """Used by deepcopy(molecule)"""
        copy = type(self)(self.element, self.id)
        # Put ourself in memo before copying bound atoms, because each
        # atom in bound atoms has a reference to us
        memo[id(self)] = copy
        copy._bound_atoms = deepcopy(self._bound_atoms, memo=memo)
        return copy

    def __hash__(self):      return self.id
    def __eq__(self, other): return self.id == other.id

class Molecule(object):
    def __init__(self, name=''):
        self.name = name
        self._atoms = {}
        self._branches = {}
        self._next_branch_id = 1
        self._next_atom_id = 1
        self._formula = None
        self._molecular_weight = None
        self._locked = False

    def __repr__(self):
        return f'Molecule({repr(self.atoms)[1:-1]})'

    def brancher(self, *branches):
        self._ensure_unlocked()
        for branch in branches:
            self._build_branch(branch)
        return self

    def bounder(self, *bindings):
        self._ensure_unlocked()
        for binding in bindings:
            self._bind_atoms(*binding)
        return self

    def mutate(self, *mutations):
        self._ensure_unlocked()
        for mutation in mutations:
            self._mutate(*mutation)
        return self

    def add_chaining(self, nc, nb, *elements):
        self._ensure_unlocked()
        if len(elements) > 0:
            target = self._get_carbon_from_branch(nc, nb)
            copy = deepcopy(self) # Used to rollback if we hit an error after
                                  # constructing atoms
            try:
                first = current = self._build_atom(elements[0])
                for element in elements[1:]:
                    next = self._build_atom(element)
                    Atom.bond(current, next)
                    current = next
                Atom.bond(target, first)
            except MoleculeError as ex:
                # Rollback
                self.rollback(copy)
                raise ex
        return self

    def add(self, *additions):
        self._ensure_unlocked()
        for addition in additions:
            self._add(*addition)
        return self
    
    def closer(self):
        self._ensure_unlocked()
        self._bind_hydrogen_atoms()
        self._formula = self._compute_formula()
        self._molecular_weight = self._compute_molecular_weight()
        self._locked = True
        return self

    def unlock(self):
        self._ensure_locked()
        self._remove_hydrogen_atoms()
        self._prune_branches()
        self._locked = False
        return self

    @property
    def formula(self) -> str:
        self._ensure_locked()
        return self._formula

    @property
    def molecular_weight(self) -> float:
        self._ensure_locked()
        return self._molecular_weight
    
    @property
    def atoms(self):
        return list(self._atoms.values())

    def __deepcopy__(self, memo):
        """Used by `add_chaining` to save state and rollback on error"""
        copy = type(self)(self.name)
        copy._atoms = deepcopy(self._atoms, memo=memo)
        copy._branches = deepcopy(self._branches, memo=memo)
        copy._next_branch_id = self._next_branch_id
        copy._next_atom_id = self._next_atom_id
        copy._formula = self._formula
        copy._molecular_weight = self._molecular_weight
        copy._locked = self._locked
        return copy

    def rollback(self, copy):
        self._atoms = copy._atoms
        self._branches = copy._branches
        self._next_branch_id = copy._next_branch_id
        self._next_atom_id = copy._next_atom_id

    def _ensure_locked(self):
        if self._locked is False:
            raise UnlockedMolecule

    def _ensure_unlocked(self):
        if self._locked is True:
            raise LockedMolecule

    def _build_atom(self, elt):
        atom = Atom(elt, self._next_atom_id)
        self._next_atom_id += 1
        self._atoms[atom.id] = atom
        return atom

    def _build_branch(self, count):
        """Construct a branch with `count` carbon atoms"""
        branch = []
        if count > 0:
            branch.append(self._build_atom('C'))
            for _ in range(count - 1):
                prev_atom = branch[-1]
                next_atom = self._build_atom('C')
                Atom.bond(prev_atom, next_atom)
                branch.append(next_atom)
        self._branches[self._next_branch_id] = branch
        self._next_branch_id += 1
        return None

    def _get_carbon_from_branch(self, carbon, branchid):
        carbon_index = carbon - 1
        branch = self._branches.get(branchid, None)
        carbon = None
        if branch and carbon_index < len(branch):
            carbon = branch[carbon_index]
        if carbon is None:
            raise InvalidBond(f'invalid carbon index: {carbon} {branchid}')
        return carbon

    def _bind_atoms(self, c1, b1, c2, b2):
        carbon1 = self._get_carbon_from_branch(c1, b1)
        carbon2 = self._get_carbon_from_branch(c2, b2)
        Atom.bond(carbon1, carbon2)
    
    def _mutate(self, nc, nb, element):
        atom = self._get_carbon_from_branch(nc, nb)
        atom.mutate(element)

    def _add(self, nc, nb, element):
        target = self._get_carbon_from_branch(nc, nb)
        target.ensure_can_bind()
        atom = self._build_atom(element)
        Atom.bond(target, atom)

    def _bind_hydrogen_atoms(self):
        """Bind hydrogen atoms to atoms with remaining valence connections"""
        for atom in self.atoms:
            needed = atom.valence_number - atom.num_bonds()
            for _ in range(needed):
                hydrogen = self._build_atom('H')
                Atom.bond(atom, hydrogen)

    def _remove_hydrogen_atoms(self):
        """Delete all hydrogen atoms from the molecule, ensuring that ids of
        remaining atoms are sequential. Note that hydrogens might need to be
        removed from branches because carbons can be updated to hydrogens
        with `mutate`.
        """
        if len(self._atoms) > 0:
            new_atoms = {}
            id = 0  # Needed in case there are only hydrogens
            iterable = enumerate(atom for atom in self._atoms.values()
                                 if atom.element != 'H')
            for zeroid, atom in iterable:
                id = zeroid + 1
                atom.id = id
                atom.remove_hydrogen_atoms()
                new_atoms[id] = atom
            self._atoms = new_atoms
            self._next_atom_id = id + 1
        for branch_id in self._branches:
            self._branches[branch_id] = [atom for atom in self._branches[branch_id]
                                         if atom.element != 'H']

    def _prune_branches(self):
        """Remove empty branches, reordering branch ids; throw EmptyMolecule
        error if all branches are empty.
        """
        iterable = enumerate(branch for branch in self._branches.values()
                             if len(branch) > 0)
        new_branches = {}
        id = 0
        for zeroid, branch in iterable:
            id = zeroid + 1
            new_branches[id] = branch
        self._next_branch_id = id + 1
        self._branches = new_branches
        if id == 0:
            raise EmptyMolecule

    def _compute_formula(self) -> str:
        atom_counts = Counter(atom.element for atom in self._atoms.values())
        keys = sorted(atom_counts.keys(), key=Atom.atomic_element_key)
        return ''.join(key if atom_counts[key] == 1 else f'{key}{atom_counts[key]}'
                       for key in keys)

    def _compute_molecular_weight(self) -> float:
        return sum(atom.atomic_weight for atom in self._atoms.values())
