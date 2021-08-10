import re
from abc import ABCMeta, abstractclassmethod, abstractmethod
from collections import namedtuple, defaultdict
from operator import ior as setmerge, isub as setsubtract
from functools import cached_property

COUNTRIES = [
    'Arstotzka',
    'Antegria',
    'Impor',
    'Kolechia',
    'Obristan',
    'Republia' ,
    'United Federation',
    None,
]
ARSTOTZKA = COUNTRIES[0]

class Papers(dict):
    PASSPORT = 'passport'
    ACCESS_PERMIT = 'access_permit'
    IDCARD = 'ID_card'
    VACCINATION = 'vaccination'
    VACCINATION_CERT = 'certificate_of_vaccination'
    VACCINES = 'VACCINES'
    DIPLOMAT = 'diplomatic_authorization'
    ASYLUM = 'grant_of_asylum'
    ACCESS = 'ACCESS'
    NAME = 'NAME'
    BIRTHDAY = 'DOB'
    ID = 'ID#'
    EXPIRATION = 'EXP'
    NATION = 'NATION'
    PURPOSE = 'PURPOSE'
    WORK = 'WORK'

    def __init__(self, entrant):
        for key, value in entrant.items():
            self[key] = self.parse_info(value)

    @staticmethod
    def parse_info(infostr):
        info = {}
        for line in infostr.splitlines():
            key, value = line.split(': ')
            info[key] = value
        return info
    
    @classmethod
    def iterate_documents(cls, requiredset):
        """Hack: vaccines and other docs are unordered in requiredset,
        but we want to fail for missing document before missing vaccine.
        Yield everything in requiredset, but ensure that vaccines come
        last.
        """
        defer = None
        for document in requiredset:
            if document.endswith(cls.VACCINATION):
                if defer is None:
                    defer = [cls.VACCINATION_CERT]
                defer.append(document)
            else:
                yield document
        if defer is not None:
            yield from defer

    @cached_property
    def name(self):
        return self._lookup_attr(self.NAME)

    @cached_property
    def nation(self):
        nation = self._lookup_attr(self.NATION)
        if nation is None:
            if self.IDCARD in self:
                return ARSTOTZKA
        return nation
    
    def _lookup_attr(self, attr):
        for paper in self.values():
            if attr in paper:
                return paper[attr]
        return None

    @cached_property
    def worker(self):
        if self.ACCESS_PERMIT in self:
            return self[self.ACCESS_PERMIT][self.PURPOSE] == self.WORK
        return False

    @cached_property
    def certificate_of_vaccination(self):
        if self.VACCINATION_CERT in self:
            vaccinestr = self[self.VACCINATION_CERT][self.VACCINES]
            return set(vaccinestr.split(', '))
        return None

    @cached_property
    def diplomatic_countries(self):
        if self.DIPLOMAT in self:
            if self.ACCESS in self[self.DIPLOMAT]:
                return set(self[self.DIPLOMAT][self.ACCESS].split(', '))
        return set()

    def document_present(self, document: str) -> bool:
        """Ensure the required document is present. If the required
        document is a proof of vaccination, we need to check the
        `certificate_of_vaccination` for the required vaccination.
        """
        if document != self.VACCINATION_CERT and document.endswith(self.VACCINATION):
            if self.certificate_of_vaccination is not None:
                if (match := re.search(r'(\w+)_vaccination', document)):
                    disease = match[1].replace('_', ' ')
                    return disease in self.certificate_of_vaccination
        return document in self

class RuleMeta(ABCMeta):
    """Store all Rule classes in a list so that we can iterate over
    them via RuleMeta.rules()
    """
    _rules = []

    def __new__(meta, *args):
        cls = super().__new__(meta, *args)
        setattr(cls, 'name', cls.__name__)
        meta._rules.append(cls)
        return cls

    @classmethod
    def rules(meta):
        """Return an iterable over derived rules"""
        return meta._rules[1:] # index 0 would be class Rule which
                               # we don't want to return

Rules = RuleMeta.rules
Judgement = namedtuple('Judgement',
                       ['detain', 'deny', 'reason'],
                       defaults=[False, False, ''])
Allow = Judgement()

class Rule(metaclass=RuleMeta):
    @abstractclassmethod
    def matches(cls, rule: str) -> bool:
        return NotImplemented

    @abstractclassmethod
    def parse(cls, rule: str):
        """Create an instance from the rule string"""
        return NotImplemented

    @abstractmethod
    def update(self, other):
        return NotImplemented

    @abstractmethod
    def judge(self, papers: Papers) -> Judgement:
        return NotImplemented

    @classmethod
    def parse_error(cls, rule):
        """Raise a value error if parse is unable to create a new instance.
        Used for debugging.
        """
        raise ValueError(f"{cls.__name__}: couldn't parse rule `{rule}`")
        
    @staticmethod
    def document_name_for_display(name):
        """Replace underscores with spaces. If name is a vaccination, return 'vaccination'
        instead of the full string.
        """
        if name != Papers.VACCINATION_CERT and name.endswith(Papers.VACCINATION):
            return Papers.VACCINATION
        return name.replace('_', ' ')
    
class WantedCriminals(Rule):
    """Detain wanted criminals"""

    REASON = 'Entrant is a wanted criminal'
    
    def __init__(self):
        self.name = ''

    def __repr__(self):
        return f'WantedCriminals(name={self.name})'
    
    @classmethod
    def matches(cls, rule: str) -> bool:
        return rule.startswith('Wanted')

    @classmethod
    def parse(cls, rule: str):
        if (match := re.search(r':\s+(\w+)\s+(\w+)', rule)):
            instance = cls()
            first_name = match[1]
            last_name = match[2]
            instance.name = f'{last_name}, {first_name}'
            return instance
        cls.parse_error(rule)

    def update(self, other):
        self.name = other.name

    def judge(self, papers: Papers) -> Judgement:
        if papers.name == self.name:
            return Judgement(detain=True, reason=self.REASON)
        return Allow

class ValidDocuments(Rule):
    """Ensure that documents are valid; check for expiration and conflicts"""

    MISMATCH_FIELDS = {
        Papers.BIRTHDAY: 'date of birth',
        Papers.NATION: 'nationality',
        Papers.ID: 'ID number',
        Papers.NAME: 'name',
    }
    
    EARLIEST_INVALID_DATE = '1982.11.22'
    
    def __repr__(self):
        return 'ValidDocuments()'
    
    @classmethod
    def matches(cls, rule: str) -> bool:
        return False

    @classmethod
    def parse(cls, rule: str):
        cls.parse_error(rule)

    def update(self, other):
        pass

    def judge(self, papers: Papers) -> Judgement:
        if (mismatched_field := self.check_mismatches(papers)):
            return Judgement(detain=True, reason=f'{mismatched_field} mismatch')
        if (expired_document := self.check_expiration_dates(papers)):
            return Judgement(deny=True, reason=f'{expired_document} expired')
        if Papers.DIPLOMAT in papers:
            if not self.validate_diplomatic_authorization(papers):
                return Judgement(deny=True, reason='invalid diplomatic authorization')
        return Allow
    
    def check_mismatches(self, papers):
        sofar = {}
        for key, field in self.MISMATCH_FIELDS.items():
            for paper in papers.values():
                if key in paper:
                    info = paper[key]
                    if key in sofar and sofar[key] != info:
                        return field
                    sofar[key] = info
        return None
    
    def check_expiration_dates(self, papers):
        for document, paper in papers.items():
            if Papers.EXPIRATION in paper:
                if paper[Papers.EXPIRATION] <= self.EARLIEST_INVALID_DATE:
                    return self.document_name_for_display(document)
        return None
    
    def validate_diplomatic_authorization(self, papers):
        return ARSTOTZKA in papers.diplomatic_countries

class RequiredDocuments(Rule):
    """Ensure entrants have all required documents/vaccinations"""
    
    ENTRANTS = 'Entrants'
    FOREIGNERS = 'Foreigners'
    WORKERS = 'Workers'

    def __init__(self):
        self.categories = defaultdict(set)
        self.nolonger = False

    def __repr__(self):
        return f'RequiredDocuments(categories={self.categories})'

    @classmethod
    def matches(cls, rule: str) -> bool:
        return 'require' in rule

    @classmethod
    def parse(cls, rule: str):
        if (match := re.search(r'(.+?)\s+(no\s+longer)?\s*require\s+(.+)', rule)):
            instance = cls()
            categories = [match[1]]
            nolonger = match[2] is not None
            documents = set(s.replace(' ', '_') for s in match[3].split(', '))
            if (match := re.search(r'Citizens of (.+)', categories[0])):
                categories = match[1].split(', ')
            instance.nolonger = nolonger
            for category in categories:
                instance.categories[category] = documents
            instance._merge_categories()
            return instance
        cls.parse_error(rule)
    
    def _merge_categories(self):
        """Handle special categories `Entrants` and `Foreigners`"""
        if self.ENTRANTS in self.categories:
            entrants = self.categories.pop(self.ENTRANTS)
            for country in COUNTRIES:
                setmerge(self.categories[country], entrants)
        if self.FOREIGNERS in self.categories:
            foreigners = self.categories.pop(self.FOREIGNERS)
            for country in COUNTRIES[1:]:
                setmerge(self.categories[country], foreigners)

    def update(self, other):
        operation = setsubtract if other.nolonger else setmerge
        for category in other.categories:
            operation(self.categories[category], other.categories[category])

    def judge(self, papers: Papers) -> Judgement:
        if Papers.ASYLUM in papers and Papers.PASSPORT in papers:
            return Allow
        if Papers.DIPLOMAT in papers and Papers.PASSPORT in papers:
            return Allow
        required = self.categories[papers.nation]
        if papers.worker:
            required = required | self.categories[self.WORKERS]
        for document in Papers.iterate_documents(required):
            if not papers.document_present(document):
                return Judgement(
                         deny=True,
                         reason=f"missing required {self.document_name_for_display(document)}")
        return Allow

class AllowedNations(Rule):
    """Allow only citizens of whitelisted nations"""
    
    REASON = 'citizen of banned nation'

    def __init__(self):
        self.whitelist = set()
        self.deny = False
    
    def __repr__(self):
        return f'AllowedNations(whitelist={self.whitelist})'

    @classmethod
    def matches(cls, rule: str) -> bool:
        return 'citizens of' in rule

    @classmethod
    def parse(cls, rule: str):
        if (match := re.search(r'(Allow|Deny)\s+citizens\s+of\s+(.+)', rule)):
            instance = cls()
            deny = match[1] == 'Deny'
            countrys = match[2].split(', ')
            instance.whitelist = set(countrys)
            instance.deny = deny
            return instance
        cls.parse_error(rule)

    def update(self, other):
        operation = setsubtract if other.deny else setmerge
        operation(self.whitelist, other.whitelist)

    def judge(self, papers: Papers) -> Judgement:
        if papers.nation in self.whitelist:
            return Allow
        return Judgement(deny=True, reason=self.REASON)

class Inspector:
    CITIZEN_ENTRY_MESSAGE = f'Glory to {ARSTOTZKA}.'
    FOREIGNER_ENTRY_MESSAGE = 'Cause no trouble.'
    DENY_MESSAGE = 'Entry denied: {}.'
    DETAIN_MESSAGE = 'Detainment: {}.'    

    def __init__(self):
        # rules are ordered by priority
        self.rules = {
            WantedCriminals.name: WantedCriminals(),
            ValidDocuments.name: ValidDocuments(),
            RequiredDocuments.name: RequiredDocuments(),
            AllowedNations.name: AllowedNations(),
        }

    def receive_bulletin(self, bulletinstr):
        for rulestr in bulletinstr.splitlines():
            for Rule in Rules():
                if Rule.matches(rulestr):
                    rule = Rule.parse(rulestr)
                    self.rules[Rule.name].update(rule)
                    break # Go to next rulestr

    def inspect(self, entrant):
        papers = Papers(entrant)
        for rule in self.rules.values():
            judgement = rule.judge(papers)
            if judgement.detain:
                return self.detain_message(judgement.reason)
            if judgement.deny:
                return self.deny_message(judgement.reason)
        return self.entry_message(papers.nation)

    @classmethod
    def entry_message(cls, nation: str) -> str:
        return (cls.CITIZEN_ENTRY_MESSAGE
                    if nation == ARSTOTZKA
                    else cls.FOREIGNER_ENTRY_MESSAGE)

    @classmethod
    def deny_message(cls, reason: str) -> str:
        return cls.DENY_MESSAGE.format(reason)

    @classmethod
    def detain_message(cls, reason: str) -> str:
        return cls.DETAIN_MESSAGE.format(reason)