# pylint: disable=too-many-lines

"""
Constructs individuals in OWL with respect to the ontology Records in Contexts
from a draw.io graph.

Intended to be run as a script: the underlying XML of the graph should be sent
into the script via stdin. A number of command line parameters are available for
configuration: run

python draw_io_parser.py --help

for a full list.

Codewise, the DrawIOXMLTree class takes a raw drawio XML string in its
constructor, and exposes only one method, 'individuals_and_arrows', which
returns as a generator all RiC-O individuals and properties (arrows) that it
finds upon parsing the tree, including, for arrows, the data of which
individuals are the source and target of the arrow. Part of the parsing is
already carried out upon calling the constructor, for effectivity.

Two further functions are exposed by the module. The method 'individual_blocks'
takes an iterator of individuals and arrows such as that outputted by the
'individuals_and_arrows' method of a DrawIOXMLTree instance, and assembles them
into a dictionary whose keys are individual IRIs. The value for a given key is
itself a dictionary, collecting together the facts and types for that individual
IRI which were defined by some Individual or Arrow instance in the iterator (the
individual IRI may occur many times in Individual instances with differing
values for the 'class' variable).

The method 'serialise' takes such a dictionary of individuals and their facts
and types, arranges each pair of a key (individual) and its values (facts and
types) into an Individual block in OWL Manchester syntax, and concatenates all
of these into one large string.
"""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass, field, InitVar
from datetime import datetime
from html.parser import HTMLParser
from sys import exit as sys_exit, stdin
from typing import Generator, Iterator
from xml.etree.ElementTree import Element, fromstring
from typing import Optional
import urllib.parse

_ric_classes = [
    "AccumulationRelation",
    "Activity",
    "ActivityDocumentationRelation",
    "ActivityType",
    "Agent",
    "AgentControlRelation",
    "AgentHierarchicalRelation",
    "AgentName",
    "AgentTemporalRelation",
    "AgentToAgentRelation",
    "Appellation",
    "AppellationRelation",
    "AuthorityRelation",
    "AuthorshipRelation",
    "CarrierExtent",
    "CarrierType",
    "ChildRelation",
    "Concept",
    "ContentType",
    "Coordinates",
    "CorporateBody",
    "CorporateBodyType",
    "CorrespondenceRelation",
    "CreationRelation",
    "Date",
    "DateType",
    "DemographicGroup",
    "DerivationRelation",
    "DescendanceRelation",
    "DocumentaryFormType",
    "Event",
    "EventRelation",
    "EventType",
    "Extent",
    "ExtentType",
    "Family",
    "FamilyRelation",
    "FamilyType",
    "FunctionalEquivalenceRelation",
    "Group",
    "GroupSubdivisionRelation",
    "Identifier",
    "IdentifierType",
    "Instantiation",
    "InstantiationExtent",
    "InstantiationToInstantiationRelation",
    "IntellectualPropertyRightsRelation",
    "KnowingOfRelation",
    "KnowingRelation",
    "Language",
    "LeadershipRelation",
    "LegalStatus",
    "ManagementRelation",
    "Mandate",
    "MandateRelation",
    "MandateType",
    "Mechanism",
    "MembershipRelation",
    "MigrationRelation",
    "Name",
    "OccupationType",
    "OrganicOrFunctionalProvenanceRelation",
    "OrganicProvenanceRelation",
    "OwnershipRelation",
    "PerformanceRelation",
    "Person",
    "PhysicalLocation",
    "Place",
    "PlaceName",
    "PlaceRelation",
    "PlaceType",
    "Position",
    "PositionHoldingRelation",
    "PositionToGroupRelation",
    "ProductionTechniqueType",
    "Proxy",
    "Record",
    "RecordPart",
    "RecordResource",
    "RecordResourceExtent",
    "RecordResourceGeneticRelation",
    "RecordResourceHoldingRelation",
    "RecordResourceToInstantiationRelation",
    "RecordResourceToRecordResourceRelation",
    "RecordSet",
    "RecordSetType",
    "RecordState",
    "Relation",
    "RepresentationType",
    "RoleType",
    "Rule",
    "RuleRelation",
    "RuleType",
    "SequentialRelation",
    "SiblingRelation",
    "SpouseRelation",
    "TeachingRelation",
    "TemporalRelation",
    "Thing",
    "Title",
    "Type",
    "TypeRelation",
    "UnitOfMeasurement",
    "WholePartRelation",
    "WorkRelation"
]

_ric_object_properties = [
    "affectsOrAffected",
    "agentHasOrHadLocation",
    "authorizedBy",
    "authorizes",
    "contained",
    "containsOrContained",
    "containsTransitive",
    "describesOrDescribed",
    "directlyContains",
    "directlyFollowsInSequence",
    "directlyIncludes",
    "directlyPrecedesInSequence",
    "documentedBy",
    "documents",
    "existsOrExistedIn",
    "expressesOrExpressed",
    "followedInSequence",
    "followsInSequenceTransitive",
    "followsInTime",
    "followsOrFollowed",
    "hadComponent",
    "hadConstituent",
    "hadPart",
    "hadSubdivision",
    "hadSubevent",
    "hadSubordinate",
    "hasAccumulator",
    "hasActivityType",
    "hasAddressee",
    "hasAncestor",
    "hasAuthor",
    "hasBeginningDate",
    "hasBirthDate",
    "hasBirthPlace",
    "hasCarrierType",
    "hasChild",
    "hasCollector",
    "hasComponentTransitive",
    "hasConstituentTransitive",
    "hasContentOfType",
    "hasCopy",
    "hasCreationDate",
    "hasCreator",
    "hasDateType",
    "hasDeathDate",
    "hasDeathPlace",
    "hasDescendant",
    "hasDestructionDate",
    "hasDirectComponent",
    "hasDirectConstituent",
    "hasDirectPart",
    "hasDirectSubdivision",
    "hasDirectSubevent",
    "hasDirectSubordinate",
    "hasDocumentaryFormType",
    "hasDraft",
    "hasEndDate",
    "hasEventType",
    "hasExtent",
    "hasExtentType",
    "hasFamilyAssociationWith",
    "hasFamilyType",
    "hasGeneticLinkToRecordResource",
    "hasIdentifierType",
    "hasModificationDate",
    "hasOrHadAgentName",
    "hasOrHadAllMembersWithCategory",
    "hasOrHadAllMembersWithContentType",
    "hasOrHadAllMembersWithCreationDate",
    "hasOrHadAllMembersWithDocumentaryFormType",
    "hasOrHadAllMembersWithLanguage",
    "hasOrHadAllMembersWithLegalStatus",
    "hasOrHadAllMembersWithRecordState",
    "hasOrHadAnalogueInstantiation",
    "hasOrHadAppellation",
    "hasOrHadAuthorityOver",
    "hasOrHadCategory",
    "hasOrHadComponent",
    "hasOrHadConstituent",
    "hasOrHadController",
    "hasOrHadCoordinates",
    "hasOrHadCorporateBodyType",
    "hasOrHadCorrespondent",
    "hasOrHadDemographicGroup",
    "hasOrHadDerivedInstantiation",
    "hasOrHadDigitalInstantiation",
    "hasOrHadEmployer",
    "hasOrHadHolder",
    "hasOrHadIdentifier",
    "hasOrHadInstantiation",
    "hasOrHadIntellectualPropertyRightsHolder",
    "hasOrHadJurisdiction",
    "hasOrHadLanguage",
    "hasOrHadLeader",
    "hasOrHadLegalStatus",
    "hasOrHadLocation",
    "hasOrHadMainSubject",
    "hasOrHadManager",
    "hasOrHadMandateType",
    "hasOrHadMember",
    "hasOrHadMostMembersWithCreationDate",
    "hasOrHadName",
    "hasOrHadOccupationOfType",
    "hasOrHadOwner",
    "hasOrHadPart",
    "hasOrHadParticipant",
    "hasOrHadPhysicalLocation",
    "hasOrHadPlaceName",
    "hasOrHadPlaceType",
    "hasOrHadPosition",
    "hasOrHadRuleType",
    "hasOrHadSomeMembersWithCategory",
    "hasOrHadSomeMembersWithContentType",
    "hasOrHadSomeMembersWithCreationDate",
    "hasOrHadSomeMembersWithLanguage",
    "hasOrHadSomeMembersWithLegalStatus",
    "hasOrHadSomeMembersWithRecordState",
    "hasOrHadSomeMemberswithDocumentaryFormType",
    "hasOrHadSpouse",
    "hasOrHadStudent",
    "hasOrHadSubdivision",
    "hasOrHadSubevent",
    "hasOrHadSubject",
    "hasOrHadSubordinate",
    "hasOrHadTeacher",
    "hasOrHadTitle",
    "hasOrHadWorkRelationWith",
    "hasOrganicOrFunctionalProvenance",
    "hasOrganicProvenance",
    "hasOriginal",
    "hasPartTransitive",
    "hasProductionTechniqueType",
    "hasPublicationDate",
    "hasPublisher",
    "hasReceiver",
    "hasRecordSetType",
    "hasRecordState",
    "hasReply",
    "hasRepresentationType",
    "hasSender",
    "hasSibling",
    "hasSubdivisionTransitive",
    "hasSubeventTransitive",
    "hasSubordinateTransitive",
    "hasSuccessor",
    "hasUnitOfMeasurement",
    "hasWithin",
    "included",
    "includesOrIncluded",
    "includesTransitive",
    "intersects",
    "isAccumulatorOf",
    "isActivityTypeOf",
    "isAddresseeOf",
    "isAgentAssociatedWithAgent",
    "isAgentAssociatedWithPlace",
    "isAssociatedWithDate",
    "isAssociatedWithEvent",
    "isAssociatedWithPlace",
    "isAssociatedWithRule",
    "isAuthorOf",
    "isBeginningDateOf",
    "isBirthDateOf",
    "isBirthPlaceOf",
    "isCarrierTypeOf",
    "isChildOf",
    "isCollectorOf",
    "isComponentOfTransitive",
    "isConstituentOfTransitive",
    "isContainedByTransitive",
    "isContentTypeOf",
    "isCopyOf",
    "isCreationDateOf",
    "isCreatorOf",
    "isDateAssociatedWith",
    "isDateOfOccurrenceOf",
    "isDateTypeOf",
    "isDeathDateOf",
    "isDeathPlaceOf",
    "isDestructionDateOf",
    "isDirectComponentOf",
    "isDirectConstituentOf",
    "isDirectPartOf",
    "isDirectSubdivisionOf",
    "isDirectSubeventOf",
    "isDirectSubordinateTo",
    "isDirectlyContainedBy",
    "isDirectlyIncludedIn",
    "isDocumentaryFormTypeOf",
    "isDraftOf",
    "isEndDateOf",
    "isEquivalentTo",
    "isEventAssociatedWith",
    "isEventTypeOf",
    "isExtentOf",
    "isExtentTypeOf",
    "isFamilyTypeOf",
    "isFromUseDateOf",
    "isFunctionallyEquivalentTo",
    "isIdentifierTypeOf",
    "isIncludedInTransitive",
    "isInstantiationAssociatedWithInstantiation",
    "isLastUpdateDateOf",
    "isModificationDateOf",
    "isOrWasAdjacentTo",
    "isOrWasAffectedBy",
    "isOrWasAgentNameOf",
    "isOrWasAnalogueInstantiationOf",
    "isOrWasAppellationOf",
    "isOrWasCategoryOf",
    "isOrWasCategoryOfAllMembersOf",
    "isOrWasCategoryOfSomeMembersOf",
    "isOrWasComponentOf",
    "isOrWasConstituentOf",
    "isOrWasContainedBy",
    "isOrWasContentTypeOfAllMembersOf",
    "isOrWasContentTypeOfSomeMembersOf",
    "isOrWasControllerOf",
    "isOrWasCoordinatesOf",
    "isOrWasCorporateBodyTypeOf",
    "isOrWasCreationDateOfAllMembersOf",
    "isOrWasCreationDateOfMostMembersOf",
    "isOrWasCreationDateOfSomeMembersOf",
    "isOrWasDemographicGroupOf",
    "isOrWasDerivedFromInstantiation",
    "isOrWasDescribedBy",
    "isOrWasDigitalInstantiationOf",
    "isOrWasDocumentaryFormTypeOfAllMembersOf",
    "isOrWasDocumentaryFormTypeOfSomeMembersOf",
    "isOrWasEmployerOf",
    "isOrWasEnforcedBy",
    "isOrWasExpressedBy",
    "isOrWasHolderOf",
    "isOrWasHolderOfIntellectualPropertyRightsOf",
    "isOrWasIdentifierOf",
    "isOrWasIncludedIn",
    "isOrWasInstantiationOf",
    "isOrWasJurisdictionOf",
    "isOrWasLanguageOf",
    "isOrWasLanguageOfAllMembersOf",
    "isOrWasLanguageOfSomeMembersOf",
    "isOrWasLeaderOf",
    "isOrWasLegalStatusOf",
    "isOrWasLegalStatusOfAllMembersOf",
    "isOrWasLegalStatusOfSomeMembersOf",
    "isOrWasLocationOf",
    "isOrWasLocationOfAgent",
    "isOrWasMainSubjectOf",
    "isOrWasManagerOf",
    "isOrWasMandateTypeOf",
    "isOrWasMemberOf",
    "isOrWasNameOf",
    "isOrWasOccupationTypeOf",
    "isOrWasOccupiedBy",
    "isOrWasOwnerOf",
    "isOrWasPartOf",
    "isOrWasParticipantIn",
    "isOrWasPerformedBy",
    "isOrWasPhysicalLocationOf",
    "isOrWasPlaceNameOf",
    "isOrWasPlaceTypeOf",
    "isOrWasRecordStateOfAllMembersOf",
    "isOrWasRecordStateOfSomeMembersOf",
    "isOrWasRegulatedBy",
    "isOrWasResponsibleForEnforcing",
    "isOrWasRuleTypeOf",
    "isOrWasSubdivisionOf",
    "isOrWasSubeventOf",
    "isOrWasSubjectOf",
    "isOrWasSubordinateTo",
    "isOrWasTitleOf",
    "isOrWasUnderAuthorityOf",
    "isOrganicOrFunctionalProvenanceOf",
    "isOrganicProvenanceOf",
    "isOriginalOf",
    "isPartOfTransitive",
    "isPlaceAssociatedWith",
    "isPlaceAssociatedWithAgent",
    "isProductionTechniqueTypeOf",
    "isPublicationDateOf",
    "isPublisherOf",
    "isReceiverOf",
    "isRecordResourceAssociatedWithRecordResource",
    "isRecordSetTypeOf",
    "isRecordStateOf",
    "isRelatedTo",
    "isReplyTo",
    "isRepresentationTypeOf",
    "isResponsibleForIssuing",
    "isRuleAssociatedWith",
    "isSenderOf",
    "isSubdivisionOfTransitive",
    "isSubeventOfTransitive",
    "isSubordinateToTransitive",
    "isSuccessorOf",
    "isToUseDateOf",
    "isUnitOfMeasurementOf",
    "isWithin",
    "issuedBy",
    "knownBy",
    "knows",
    "knowsOf",
    "migratedFrom",
    "migratedInto",
    "occupiesOrOccupied",
    "occurredAtDate",
    "overlapsOrOverlapped",
    "performsOrPerformed",
    "precededInSequence",
    "precedesInSequenceTransitive",
    "precedesInTime",
    "precedesOrPreceded",
    "proxyFor",
    "proxyIn",
    "regulatesOrRegulated",
    "relationHasTarget",
    "resultedFromTheMergerOf",
    "resultedFromTheSplitOf",
    "resultsOrResultedFrom",
    "resultsOrResultedIn",
    "thingIsSourceOfRelation",
    "wasComponentOf",
    "wasConstituentOf",
    "wasContainedBy",
    "wasIncludedIn",
    "wasLastUpdatedAtDate",
    "wasMergedInto",
    "wasPartOf",
    "wasSplitInto",
    "wasSubdivisionOf",
    "wasSubeventOf",
    "wasSubordinateTo",
    "wasUsedFromDate",
    "wasUsedToDate"
]

_ric_datatype_properties = [
    "accruals",
    "accrualsStatus",
    "altimetricSystem",
    "altitude",
    "authenticityNote",
    "authorizingMandate",
    "beginningDate",
    "birthDate",
    "carrierExtent",
    "classification",
    "conditionsOfAccess",
    "conditionsOfUse",
    "creationDate",
    "date",
    "dateQualifier",
    "deathDate",
    "destructionDate",
    "endDate",
    "expressedDate",
    "generalDescription",
    "geodesicSystem",
    "geographicalCoordinates",
    "height",
    "history",
    "identifier",
    "instantiationExtent",
    "instantiationStructure",
    "integrityNote",
    "lastModificationDate",
    "latitude",
    "length",
    "location",
    "longitude",
    "measure",
    "modificationDate",
    "name",
    "normalizedDateValue",
    "normalizedValue",
    "physicalCharacteristicsNote",
    "physicalOrLogicalExtent",
    "productionTechnique",
    "publicationDate",
    "qualityOfRepresentationNote",
    "quantity",
    "recordResourceExtent",
    "recordResourceStructure",
    "referenceSystem",
    "relationCertainty",
    "relationSource",
    "relationState",
    "ruleFollowed",
    "scopeAndContent",
    "structure",
    "technicalCharacteristics",
    "textualValue",
    "title",
    "type",
    "unitOfMeasurement",
    "usedFromDate",
    "usedToDate",
    "width"
]

Blocks = dict[tuple[str, str], dict[str, set[str]]]
Cell = Element
CellID = str
XCoordinate = float
YCoordinate = float
Width = float
Height = float
ArrowStart = tuple[XCoordinate, YCoordinate]
ArrowEnd = tuple[XCoordinate, YCoordinate]
Label = str
ArrowData = tuple[Cell, Optional[ArrowStart], Optional[ArrowEnd], Label]
Dimensions = tuple[XCoordinate, YCoordinate, Width, Height]
Paragraph = str
Metacharacter = str
Replacement = str

DEFAULT_CAPITALISATION_SCHEME = "upper-camel"
DEFAULT_INDENTATION = 2
DEFAULT_MAX_GAP = 10
OWL_METACHARACTERS = ["(", ")", "[", "]", "/", ",", ":", ".", "'", '"']


class NothingToParseException(Exception):
    """
    Can be thrown when calling the constructor of the DrawIOXMLTree class if the
    passed-in XML appears to define an empty graph
    """


class NotInRiCException(Exception):
    """
    Can be thrown if an arrow has a label which does not correspond to an
    object or datatype property in RiC-O, and if it has been specified that this
    is not to be permitted
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class _NoCellCloseEnoughException(Exception):
    pass


class NoSourceException(Exception):
    """
    Can be thrown when calling the 'individuals_and_arrows' function if a given
    arrow has no source that can be identified
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class NoTargetException(Exception):
    """
    Can be thrown when calling the 'individuals_and_arrows' function if a given
    arrow has no target that can be identified
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class _NoValueException(Exception):
    pass


class _SourceNotIndividualException(Exception):
    pass


class ArrowWithoutIndividualAsSourceException(Exception):
    """
    Can be thrown when calling the 'individuals_and_arrows' function if a given
    arrow has a source that appears not to be an individual node
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class _MetacharacterSubstituteParseException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class MetacharacterException(Exception):
    """
    Can be thrown when calling the 'individual_blocks' function if an individual
    has an identifier (the text in the upper half of an individual node)
    containing an OWL metacharacter
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class _InvalidCapitalisationSchemeException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ParseException(Exception):
    """
    Can be thrown if the XML being parsed does not have the anticipated
    structure in some respect
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


@dataclass(frozen=True)
class Individual:
    """
    Represents an OWL individual with type a RiC-O class, coming from a node in
    the parsed graph
    """
    identifier: str
    ric_class: str


@dataclass(frozen=True)
class Arrow:
    """
    Represents an OWL object or datatype property with type a RiC-O class,
    coming from an arrow in the parsed graph
    """
    identifier: str
    source: str
    target: str


class NodeHTMLParser(HTMLParser):
    """
    Subclasses HTMLParser to define its behaviour with respect to 'handle_data',
    'handle_starttag', and 'handle_endtag' (this is the usage pattern expected
    by HTMLParser). It seems that text, including multi-line text, in draw.io
    may come in three forms: as a simple string; as a string within a blockquote
    element; or as a sequence of strings inside divs inside a blockquote. In
    the simple string case, our subclassing of the three afore-mentioned methods
    is such as to discard all information except these strings, and to collect
    them, in the sequence they are encountered in, into a list.

    The 'content' function takes such a list and collects the strings together
    into paragraphs. Single line-breaks in the original graph (corresponding
    usually to three consecutive divs, the middle one of which contains no
    string) are ignored; two or more line-breaks in the original graph will lead
    to a paragraph break.

    The 'clear' function resets the internal state of the class, and should be
    called before parsing a new chunk of HTML.
    """

    def __init__(self):
        super().__init__()
        self._chunks = []
        self._within_tag = False
        self._raw_data = ""

    def handle_starttag(self, tag: str, _: list[tuple[str, str | None]]) -> None:
        if tag in ["div", "blockquote"]:
            self._chunks.append(self._raw_data)
            self._within_tag = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ["div", "blockquote"]:
            self._chunks.append(self._raw_data)
            self._raw_data = ""
            self._within_tag = False

    def handle_data(self, data: str) -> None:
        """
        Overrides a function in HTMLParser, storing the raw data (text) inside
        a HTML element in the instance variable 'raw_data'.
        """
        self._raw_data = data

    def _prettify_linebreaks(self) -> Generator[Paragraph, None, None]:
        previous_was_empty = False
        paragraph_already_handled = False
        current = ""
        for chunk in self._chunks:
            if not chunk:
                if current:
                    yield current
                current = ""
                if previous_was_empty and not paragraph_already_handled:
                    yield "\n\n"
                    paragraph_already_handled = True
                else:
                    previous_was_empty = True
                continue
            current += chunk
            previous_was_empty = False
            paragraph_already_handled = False
        if current:
            yield current

    def content(self) -> str:
        """
        Takes all of the string chunks (within divs and blockquotes) obtained
        during the current run of the parser, and collects them together
        into paragraphs, handling line breaks as described in the docstring
        for this class
        """
        if self._raw_data:
            return self._raw_data
        return "".join(self._prettify_linebreaks()).strip()

    def clear(self) -> None:
        """
        Clears the internal state of the parser so that it is as though newly
        constructed
        """
        self._chunks = []
        self._raw_data = ""
        self._within_tag = False


@dataclass(frozen=True)
class SerialisationConfig:
    """
    Holds various user-configurable parameters for configuring the serialisation
    to OWL outputted by the 'serialise' function
    """
    infer_type_of_literals: bool
    include_preamble: bool
    ontology_iri: str | None
    prefix: str | None
    prefix_iri: str | None
    indentation: int
    include_label: bool


@dataclass(frozen=True)
class DrawIOXMLTree:
    """
    The purpose of this class is to parse a raw draw.io XML to a list of
    instances of the Individual and Arrow classes, corresponding respectively to
    nodes and arrows in the graph which the  XML defines. The constructor takes
    such an XML string, and part of the parsing is already carried out upon
    calling the constructor, for effectivity (elements which will be looped
    over are extracted once and for all). The method
    'individuals_and_arrows' can then be called to complete the parsing and
    return the obtained Individual and Arrow instances as a generator
    """
    draw_io_xml_tree: Element = field(init=False)
    literal_node_html_parser: NodeHTMLParser = field(init=False)
    individual_cells: list[
        tuple[Cell, Individual, Dimensions]] = field(init=False)
    arrow_cells: list[ArrowData] = field(init=False)
    literal_cells: list[tuple[Cell, Dimensions]] = field(init=False)

    raw_xml: InitVar[str]

    def __post_init__(self, raw_xml):
        object.__setattr__(self, "literal_node_html_parser", NodeHTMLParser())
        object.__setattr__(self, "draw_io_xml_tree", fromstring(raw_xml))
        object.__setattr__(self, "individual_cells", [])
        object.__setattr__(self, "arrow_cells", [])
        object.__setattr__(self, "literal_cells", [])
        self._extract_individual_and_arrow_and_literal_cells()

    def _cell_with_id(self, _id: str) -> Element:
        cell = self.draw_io_xml_tree.find(f".//*[@id='{_id}']")
        if cell is None:
            raise ValueError(f"No cell with id: {_id}")
        return cell

    def _value_of(self, cell: Element) -> str:
        try:
            value = cell.attrib["value"].strip()
        except KeyError as key_error:
            raise _NoValueException from key_error
        self.literal_node_html_parser.clear()
        self.literal_node_html_parser.feed(value)
        return self.literal_node_html_parser.content()

    def _parent_of(self, cell: Element) -> Element:
        try:
            parent_id = cell.attrib["parent"]
        except KeyError as key_error:
            raise ParseException(
                "Could not parse XML tree: found an 'mxCell' element with "
                "the following id which has value beginning with 'rico:' but "
                f"with no parent: {cell.attrib['id']}"
            ) from key_error
        return self._cell_with_id(parent_id)

    def _child_of(self, parent_id: str) -> Generator[Element, None, None]:
        yield from self.draw_io_xml_tree.findall(f".//*[@parent='{parent_id}']")

    @staticmethod
    def _geometry(cell: Element) -> Element:
        try:
            for element in cell:
                if element.tag == "mxGeometry":
                    return element
        except IndexError as index_error:
            raise ParseException(
                "Expecting the cell with the following id to have an "
                "mxGeometry sub-element, but has no sub-elements at all: "
                f"{cell.attrib['id']}"
            ) from index_error
        raise ParseException(
            "Expecting the cell with the following id to have an mxGeometry "
            f"sub-element: {cell.attrib['id']}")

    @staticmethod
    def _x_and_y_in_geometry(geometry: Element, cell_id: str) -> tuple[
            XCoordinate, YCoordinate]:
        try:
            x = float(geometry.attrib["x"])
        except KeyError as key_error:
            raise ParseException(
                "Encountered an mxGeometry element of the cell with the "
                f"following id without an 'x' attribute: {cell_id}"
            ) from key_error
        try:
            y = float(geometry.attrib["y"])
        except KeyError as key_error:
            raise ParseException(
                "Encountered an mxGeometry element of the cell with the "
                f"following id without a 'y' attribute: {cell_id}"
            ) from key_error
        return x, y

    @staticmethod
    def _has_correct_as_attribute(
            element: Element, as_attribute: str, cell_id: str) -> bool:
        try:
            return element.attrib["as"] == as_attribute
        except KeyError as key_error:
            raise ParseException(
                "Encountered an mxPoint element of the cell with the "
                f"following id without an 'as' attribute: {cell_id}"
            ) from key_error

    @staticmethod
    def _is_locked(cell: Element, as_attribute: str) -> bool:
        if as_attribute == "sourcePoint" and ("source" in cell.attrib):
            return True
        if as_attribute == "targetPoint" and ("target" in cell.attrib):
            return True
        return False

    def _start_or_end(self, cell: Element, as_attribute: str | None) -> tuple[
            XCoordinate, YCoordinate] | None:
        """
        The cell can be part of a group (have another 'parent' than that of the
        top-level graph), in which case the immediate x and y coordinates will
        be relative to the parent in the group rather than absolute; recursion
        is used here to obtain absolute coordinates
        """
        geometry = DrawIOXMLTree._geometry(cell)
        if as_attribute is None:
            return self._x_and_y_in_geometry(geometry, cell.attrib["id"])
        if not geometry:
            raise ParseException(
                "Expecting the mxGeometry element of the cell with the "
                "following id to have sub-elements, but has no sub-elements "
                f"at all: {cell.attrib['id']}")
        for element in geometry:
            if element.tag != "mxPoint" or not self._has_correct_as_attribute(
                    element, as_attribute, cell.attrib["id"]):
                continue
            try:
                x = float(element.attrib["x"])
            except KeyError as key_error:
                if self._is_locked(cell, as_attribute):
                    return None
                raise ParseException(
                    "Encountered an mxPoint element of the cell with the "
                    "following id without an 'x' attribute: "
                    f"{cell.attrib['id']}"
                ) from key_error
            try:
                y = float(element.attrib["y"])
            except KeyError as key_error:
                if self._is_locked(cell, as_attribute):
                    return None
                raise ParseException(
                    "Encountered an mxPoint element of the cell with the "
                    "following id without a 'y' attribute: "
                    f"{cell.attrib['id']}"
                ) from key_error
            parent_id = cell.attrib["parent"]
            if parent_id == "1":
                return x, y
            parent_coordinates = self._start_or_end(
                self._parent_of(cell), None)
            if parent_coordinates is None:
                raise ValueError
            parent_x, parent_y = parent_coordinates
            return x + parent_x, y + parent_y
        raise ParseException(
            "Expecting the mxGeometry element of the cell with the following "
            "id to have an mxPoint sub-element with 'as' attribute having "
            f"value 'sourcePoint', but it does not: {cell.attrib['id']}")

    def _arrow_start(self, arrow_cell: Element) -> ArrowStart | None:
        return self._start_or_end(arrow_cell, "sourcePoint")

    def _arrow_end(self, arrow_cell: Element) -> ArrowEnd | None:
        return self._start_or_end(arrow_cell, "targetPoint")

    @staticmethod
    def _dimensions(individual_cell: Element) -> Dimensions:
        geometry = DrawIOXMLTree._geometry(individual_cell)
        try:
            x = float(geometry.attrib["x"])
        except KeyError as key_error:
            raise ParseException(
                "Expecting the mxGeometry element of the cell with the "
                "following id to have an 'x' attribute, but it does not: "
                f"{individual_cell.attrib['id']}"
            ) from key_error
        try:
            y = float(geometry.attrib["y"])
        except KeyError as key_error:
            raise ParseException(
                "Expecting the mxGeometry element of the cell with the "
                "following id to have a 'y' attribute, but it does not: "
                f"{individual_cell.attrib['id']}"
            ) from key_error
        try:
            width = float(geometry.attrib["width"])
        except KeyError as key_error:
            raise ParseException(
                "Expecting the mxGeometry element of the cell with the "
                "following id to have a 'width' attribute, but it does not: "
                f"{individual_cell.attrib['width']}"
            ) from key_error
        try:
            height = float(geometry.attrib["height"])
        except KeyError as key_error:
            raise ParseException(
                "Expecting the mxGeometry element of the cell with the "
                "following id to have a 'height' attribute, but it does not: "
                f"{individual_cell.attrib['height']}"
            ) from key_error
        return x, y, width, height

    @staticmethod
    def _is_possible_literal(cell: Element) -> bool:
        try:
            if cell.attrib["parent"] != "1":
                return False
            return "rounded=1" in cell.attrib["style"]
        except KeyError:
            return False

    def _arrow_label(self, arrow_cell: Element) -> str:
        for cell in self._child_of(arrow_cell.attrib["id"]):
            try:
                style = cell.attrib["style"]
            except KeyError:
                continue
            if "edgeLabel" in style:
                return self._value_of(cell)
        raise _NoValueException

    def _add_arrow_if_find_label(self, cell: Element) -> None:
        try:
            label = self._arrow_label(cell)
            arrow_data = (
                cell,
                self._arrow_start(cell),
                self._arrow_end(cell),
                label
            )
            self.arrow_cells.append(arrow_data)
        except _NoValueException:
            pass

    def _extract_individual_and_arrow_and_literal_cells(self) -> None:
        try:
            if not self.draw_io_xml_tree[0][0][0]:
                raise NothingToParseException
        except IndexError as key_error:
            raise NothingToParseException from key_error
        for cell in self.draw_io_xml_tree[0][0][0]:
            if cell.tag != "mxCell":
                raise ParseException(
                    "Could not parse XML tree: expecting an element with tag "
                    f"'mxCell', but had tag '{cell.tag}'")
            try:
                cell_value = self._value_of(cell)
            except _NoValueException:
                continue
            if not cell_value:
                self._add_arrow_if_find_label(cell)
                continue
            if not cell_value.startswith("rico:"):
                if self._is_possible_literal(cell):
                    self.literal_cells.append((cell, self._dimensions(cell)))
                continue
            try:
                parent = self._parent_of(cell)
                individual_identifier = self._value_of(parent)
            except _NoValueException:
                try:
                    arrow_data = (
                        cell,
                        self._arrow_start(cell),
                        self._arrow_end(cell),
                        cell.attrib["value"]
                    )
                    self.arrow_cells.append(arrow_data)
                except _NoValueException:
                    pass
                continue
            if not individual_identifier:
                continue
            for ric_class in cell_value.split("rico:")[1:]:
                ric_class = ric_class.strip()
                _verify_is_ric_class(ric_class)
                individual = Individual(individual_identifier, ric_class)
                self.individual_cells.append(
                    (cell, individual, self._dimensions(parent)))

    @staticmethod
    def _close_enough(
            arrow_endpoint: ArrowStart | ArrowEnd,
            cell_dimensions: Dimensions,
            max_gap: float) -> bool:
        endpoint_x, endpoint_y = arrow_endpoint
        cell_x, cell_y, cell_width, cell_height = cell_dimensions
        return (
            cell_x - max_gap <= endpoint_x <= cell_x + cell_width + max_gap
        ) and (
            cell_y - max_gap <= endpoint_y <= cell_y + cell_height + max_gap
        )

    def _cell_close_to(
            self,
            arrow_endpoint: ArrowStart | ArrowEnd,
            max_gap: float) -> Element:
        for cell, _, dimensions in self.individual_cells:
            if self._close_enough(arrow_endpoint, dimensions, max_gap):
                return cell
        for cell, dimensions in self.literal_cells:
            if self._close_enough(arrow_endpoint, dimensions, max_gap):
                return cell
        raise _NoCellCloseEnoughException

    def _defines_individual(self, identifier: str) -> bool:
        for _, individual, _ in self.individual_cells:
            if individual.identifier == identifier:
                return True
        return False

    def _source_or_target(
            self,
            source_or_target_cell: Element,
            must_be_individual: bool) -> str:
        try:
            value = self._value_of(source_or_target_cell)
        except KeyError as key_error:
            raise _NoValueException from key_error
        if value.startswith("rico:"):
            return self._value_of(self._parent_of(source_or_target_cell))
        if must_be_individual and not self._defines_individual(value):
            raise _SourceNotIndividualException
        return value

    def _arrow(
            self,
            arrow_data: ArrowData,
            strict_mode: bool,
            max_gap: float) -> Arrow:
        arrow_cell, arrow_start, arrow_end, arrow_label = arrow_data
        try:
            source_cell = self._cell_with_id(arrow_cell.attrib["source"])
        except KeyError as key_error:
            if strict_mode or arrow_start is None:
                raise NoSourceException(
                    f"The mxCell element with label '{arrow_label}' and id "
                    f"{arrow_cell.attrib['id']} seems to be an arrow, but its "
                    "source was not able to be determined"
                ) from key_error
            try:
                source_cell = self._cell_close_to(arrow_start, max_gap)
            except _NoCellCloseEnoughException as not_close_enough_exception:
                raise NoSourceException(
                    f"The mxCell element with label '{arrow_label}' and id "
                    f"{arrow_cell.attrib['id']} seems to be an arrow, but its "
                    "source was not able to be determined"
                ) from not_close_enough_exception
        try:
            source = self._source_or_target(source_cell, True)
        except _SourceNotIndividualException as exception:
            raise ArrowWithoutIndividualAsSourceException(
                f"The arrow with id {arrow_cell.attrib['id']} and label "
                f"{arrow_label} has a source which appears not to be a node "
                "defining a RiC-O individual"
            ) from exception
        try:
            target_cell = self._cell_with_id(arrow_cell.attrib["target"])
        except KeyError as key_error:
            if strict_mode or arrow_end is None:
                raise NoSourceException(
                    f"The mxCell element with label '{arrow_label}' and id "
                    f"{arrow_cell.attrib['id']} seems to be an arrow, but its "
                    "target was not able to be determined"
                ) from key_error
            try:
                target_cell = self._cell_close_to(arrow_end, max_gap)
            except _NoCellCloseEnoughException as not_close_enough_exception:
                raise NoSourceException(
                    f"The mxCell element with label '{arrow_label}' and id "
                    f"{arrow_cell.attrib['id']} seems to be an arrow, but its "
                    "target was not able to be determined"
                ) from not_close_enough_exception
        target = self._source_or_target(target_cell, False)
        return Arrow(arrow_label.strip().split("rico:")[1], source, target)

    def individuals_and_arrows(
            self, strict_mode: bool, max_gap: float) -> Generator[
            Individual | Arrow, None, None]:
        """
        Returns as a generator all Individual and Arrow instances obtained
        when parsing the nodes and arrows of the draw.io XML graph fed into the
        DrawIOXMLTree instance upon its construction
        """
        for _, individual, _ in self.individual_cells:
            yield individual
        for arrow_data in self.arrow_cells:
            yield self._arrow(arrow_data, strict_mode, max_gap)


def _verify_is_ric_class(ric_class: str):
    if not ric_class in _ric_classes:
        raise NotInRiCException(f"Not a RiC class: {ric_class}")


def _handle_spaces(
        identifier: str,
        space_substitute: Replacement,
        capitalisation_scheme: str) -> str:
    if capitalisation_scheme == "upper-camel":
        return f"{space_substitute}".join(
            word[0].upper() + word[1:] for word in identifier.split())
    if capitalisation_scheme == "lower-camel":
        words = identifier.split()
        return f"{space_substitute}".join(
            [words[0][0].lower() + words[0][1:]] + [
                word[0].upper() + word[1:] for word in words[1:]])
    if capitalisation_scheme == "flat":
        return f"{space_substitute}".join(
            word[0].lower() + word[1:] for word in identifier.split())
    if capitalisation_scheme == "none":
        return f"{space_substitute}".join(identifier.split())
    raise ValueError


def _replace_metacharacter(
        metacharacter: str, identifier: str, metacharacter_substitutes: list[
        tuple[Metacharacter, Replacement]]) -> str:
    if metacharacter not in identifier:
        return identifier
    for to_replace, replacement in metacharacter_substitutes:
        if metacharacter == to_replace:
            return identifier.replace(to_replace, replacement)
    raise MetacharacterException(
        f"The following contains the OWL metacharacter '{metacharacter}': "
        f"'{identifier}'. Use the -m/--metacharacter-substitute option, more "
        "than once if necessary, to define a character or string to substitute "
        "it with, or to specify that it should be removed")


def _replace_metacharacters(
        identifier: str,
        metacharacter_substitutes: list[tuple[Metacharacter, Replacement]],
        space_substitute: Replacement | None,
        capitalisation_scheme: str) -> str:
    if ' ' in identifier:
        if space_substitute is None:
            raise MetacharacterException(
                "The following contains a space, but how to handle spaces in "
                "individual nodes has not been specified (spaces cannot be "
                f"used in OWL IRIs): '{identifier}'. Use the "
                "-m/--metacharacter-substitute and -c/--capitalisation-scheme "
                "options to define how to handle spaces")
        identifier = _handle_spaces(
            identifier, space_substitute, capitalisation_scheme)
    elif capitalisation_scheme in ["lower-camel", "flat"]:
        identifier = identifier[0].lower() + identifier[1:]
    for metacharacter in OWL_METACHARACTERS:
        identifier = _replace_metacharacter(
            metacharacter, identifier, metacharacter_substitutes)
    return identifier


def _add_individual_type(
        blocks: Blocks,
        individual: Individual,
        metacharacter_substitutes: list[tuple[Metacharacter, Replacement]],
        space_substitute: Replacement | None,
        capitalisation_scheme: str) -> None:
    individual_id = _replace_metacharacters(
        individual.identifier,
        metacharacter_substitutes,
        space_substitute,
        capitalisation_scheme)
    try:
        block = blocks[(individual_id, individual.identifier)]
    except KeyError:
        blocks[(individual_id, individual.identifier)] = {
            "Types": {individual.ric_class}}
        return
    try:
        block["Types"].add(individual.ric_class)
    except KeyError:
        block["Types"] = {individual.ric_class}


def individual_blocks(
        individuals_and_arrows: Iterator[Individual | Arrow],
        metacharacter_substitutes: list[tuple[Metacharacter, Replacement]],
        space_substitute: Replacement | None,
        capitalisation_scheme: str) -> Blocks:
    """
    Takes an iterator of Individual and Arrow instances, such as that outputted
    by the 'individuals_and_arrows' method of a DrawIOXMLTree instance, and
    assembles them into adictionary whose keys are individual IRIs. The value
    for a given key is itself a dictionary, collecting together the facts and
    types for that individual IRI which were defined by some Individual or Arrow
    instance in the iterator (the individual IRI may occur many times in
    Individual instances with differing values for the 'class' variable).
    """
    blocks: Blocks = {}
    for individual_or_arrow in individuals_and_arrows:
        if isinstance(individual_or_arrow, Individual):
            _add_individual_type(
                blocks,
                individual_or_arrow,
                metacharacter_substitutes,
                space_substitute,
                capitalisation_scheme)
            continue
        if individual_or_arrow.identifier in _ric_object_properties:
            target_identifier = _replace_metacharacters(
                individual_or_arrow.target,
                metacharacter_substitutes,
                space_substitute,
                capitalisation_scheme)
        elif individual_or_arrow.identifier in _ric_datatype_properties:
            target_identifier = individual_or_arrow.target
        else:
            raise NotInRiCException(
                f"An arrow has label rico:'{individual_or_arrow.identifier}', "
                "which is not an object property or datatype property in RiC-O")
        source_identifier = _replace_metacharacters(
            individual_or_arrow.source,
            metacharacter_substitutes,
            space_substitute,
            capitalisation_scheme)
        try:
            block = blocks[(source_identifier, individual_or_arrow.source)]
        except KeyError:
            blocks[(source_identifier, individual_or_arrow.source)] = {
                individual_or_arrow.identifier: {target_identifier}}
            continue
        try:
            block[individual_or_arrow.identifier].add(target_identifier)
        except KeyError:
            block[individual_or_arrow.identifier] = {target_identifier}
    return blocks


def _infer_type(literal: str) -> str:
    if literal.isnumeric():
        return "\"" + literal + "\"^^xsd:integer"
    try:
        datetime.strptime(literal, "%Y-%m-%d")
        return "\"" + literal + "\"^^xsd:date"
    except ValueError:
        pass
    if literal[-1] == "Z":
        try:
            datetime.strptime(literal[-1], "%Y-%m-%dT%H-%M-%S")
            return "\"" + literal + "\"^^xsd:dateTime"
        except ValueError:
            pass
    elif literal[-6] == "+" or literal[-6] == "-":
        try:
            datetime.strptime(literal[:-6], "%Y-%m-%dT%H-%M-%S")
            datetime.strptime(literal[-5:], "%H:%M")
            return "\"" + literal + "\"^^xsd:dateTime"
        except ValueError:
            pass
    else:
        try:
            datetime.strptime("%Y-%m-%dT%H-%M-%S", literal)
            return "\"" + literal + "\"^^xsd:dateTime"
        except ValueError:
            pass
    return "\"" + literal + "\""


def _serialise_facts(
        facts: dict[str, set[str]],
        infer_type_of_literals: bool = True,
        prefix: str | None = None) -> Generator[str, None, None]:
    if prefix:
        prefix_string = prefix + ":"
    else:
        prefix_string = ""
    for _property, values in facts.items():
        for value in sorted(values):
            if _property in _ric_datatype_properties:
                if infer_type_of_literals:
                    formatted_value = _infer_type(value)
                else:
                    formatted_value = "\"" + value + "\""
            else:
                formatted_value = prefix_string + value
            yield f"rico:{_property} {formatted_value}"


def _serialise_block(
        individual_identifier: str,
        individual_label: str,
        types_and_facts: dict[str, set[str]],
        serialisation_config: SerialisationConfig) -> str:
    prefix = serialisation_config.prefix
    indentation = serialisation_config.indentation
    infer_type_of_literals = serialisation_config.infer_type_of_literals
    include_label = serialisation_config.include_label
    if prefix:
        prefix_string = prefix + ":"
    else:
        prefix_string = ""
    header = f"Individual: {prefix_string}{individual_identifier}"
    if include_label:
        header += f"\n{' '*indentation}Annotations:"
        header += f"\n{' '*(indentation*2)}rdfs:label \"{individual_label}\""
    types_string = ", ".join(
        f"rico:{_type}" for _type in sorted(types_and_facts["Types"]))
    facts = types_and_facts.copy()
    del facts["Types"]
    if not facts:
        return f"""{header}
{' '*indentation}Types: {types_string}

"""
    serialised_facts = list(_serialise_facts(
        facts, infer_type_of_literals, prefix))
    facts_string = f",\n{' '*(indentation*2)}".join(serialised_facts[:-1])
    facts_string += f",\n{' '*(indentation*2)}{serialised_facts[-1]}" if len(
        serialised_facts) > 1 else f"{serialised_facts[-1]}"
    return f"""{header}
{' '*indentation}Types: {types_string}
{' '*indentation}Facts:
{' '*(indentation*2)}{facts_string}

"""


def _preamble(serialisation_config: SerialisationConfig) -> str:
    ontology_iri = serialisation_config.ontology_iri
    prefix = serialisation_config.prefix
    prefix_iri = serialisation_config.prefix_iri
    indentation = serialisation_config.indentation
    include_label = serialisation_config.include_label
    if ontology_iri:
        ontology_iri_string = ontology_iri
    else:
        current_time = datetime.strftime(datetime.now(), "%Y-%m-%dT%H-%M-%S")
        ontology_iri_string = f"ontology://generated-from-draw-io/{current_time}"
    if prefix:
        prefix_string = prefix
    else:
        prefix_string = ""
    if prefix_iri:
        prefix_iri = f"<{prefix_iri}>"
    else:
        prefix_iri = f"<{ontology_iri_string}#>"
    if include_label:
        preamble = "Prefix: rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
    else:
        preamble = ""
    return preamble + f"""Prefix: rico: <https://www.ica.org/standards/RiC/ontology#>
Prefix: {prefix_string}: {prefix_iri}
Ontology: <{ontology_iri_string}>
{' '*indentation}Import: <https://www.ica.org/standards/RiC/ontology>

"""


def serialise(blocks: Blocks, serialisation_config: SerialisationConfig) -> str:
    """
    Takes such a dictionary of individuals and their facts and types such as
    that outputted by the 'individual_blocks' function, arranges each pair of a
    key (individual) and its values (facts and types) into an Individual block
    in OWL Manchester syntax, and concatenates all of these into one large
    string.
    """
    if serialisation_config.include_preamble:
        serialised = _preamble(serialisation_config)
    else:
        serialised = ""
    for individual, types_and_facts in blocks.items():
        individual_id, individual_label = individual
        serialised += _serialise_block(
            individual_id,
            individual_label,
            types_and_facts,
            serialisation_config)
    return serialised


def _parse_space_substitute(
        metacharacter_substitutes: list[str]) -> str | None:
    has_remove = False
    has_url = False
    for substitution_definition in metacharacter_substitutes:
        if substitution_definition == "remove":
            has_remove = True
            if not has_url:
                continue
        if substitution_definition == "url":
            has_url = True
            if not has_remove:
                continue
        if substitution_definition[0] != ' ':
            if not has_url:
                continue
        if substitution_definition[1] != "=":
            raise _MetacharacterSubstituteParseException(
                "The second character of a string other than 'remove' or 'url' "
                "passed into the -m/--metadata-substitute option must be '='. This is "
                f"not the case for: {substitution_definition}")
        return substitution_definition.split("=")[1]
    if has_remove:
        return ""
    elif has_url:
        return "%20"
    return None


def _parse_metacharacter_substitutes(
        metacharacter_substitutes: list[str]) -> Generator[
        tuple[Metacharacter, Replacement], None, None]:
    has_remove = False
    has_url = False
    handled = []
    for substitution_definition in metacharacter_substitutes:
        if substitution_definition[0] == ' ':
            continue
        if substitution_definition == "remove":
            has_remove = True
            if not has_url:
                continue
        if substitution_definition == "url":
            has_url = True
            if not has_remove:
                continue
        if substitution_definition[0] not in OWL_METACHARACTERS:
            metacharacters = ', '.join(
                f"'{character}'" for character in OWL_METACHARACTERS)
            raise _MetacharacterSubstituteParseException(
                "The first character of a string other than 'remove' or 'url' "
                "passed into the -m/--metadata-substitute option must be an OWL "
                f"metacharacter, namely one of the following: {metacharacters}"
                f". This is not the case for: {substitution_definition}")
        if substitution_definition[1] != "=":
            raise _MetacharacterSubstituteParseException(
                "The second character of a string other than 'remove' passed "
                "into the -m/--metadata-substitute option must be '='. This is "
                f"not the case for: {substitution_definition}")
        metacharacter, replacement = substitution_definition.split("=", 1)
        handled.append(metacharacter)
        yield metacharacter, replacement
    for metacharacter in OWL_METACHARACTERS:
        if metacharacter not in handled:
            if has_url:
                yield metacharacter, urllib.parse.quote(metacharacter, safe='')
            else:
                yield metacharacter, ""
    if not has_remove:
        return


def _parse_capitalisation_scheme(capitalisation_scheme: str) -> None:
    if capitalisation_scheme not in [
            "upper-camel", "lower-camel", "flat", "none"]:
        raise _InvalidCapitalisationSchemeException(
            "The following was passed into the -c/--capitalisation-scheme "
            f"option, which is not a permitted value: "
            f"{capitalisation_scheme}. See the documentation of the "
            "-c/--capitalisation-scheme option for the permitted values")


def _arguments_parser():
    argument_parser = ArgumentParser(
        description=(
            "Constructs individuals in OWL with respect to the ontology "
            "Records in Contexts from a draw.io graph. The underlying XML of "
            "the graph should be sent into the script via stdin.")
    )
    argument_parser.add_argument(
        "-d",
        "--preamble-disable",
        action="store_true",
        help=(
            "Disable inclusion of a preamble (defining prefix and ontology "
            "IRIs and imports)"))
    argument_parser.add_argument(
        "-g",
        "--max-gap",
        type=float,
        default=DEFAULT_MAX_GAP,
        help=(
            "only taken into account if the '-s/--strict-mode' flag is not "
            "used. In this case, when parsing an arrow whose source or target "
            "is not locked to a node, the geometry of the graph will be taken "
            "into consideration, and a node regarded as the source or target "
            "respectively if the gap (in pixels) between the node and the "
            "start or target of the arrow is less than the max gap defined "
            "here. Can be an integer or a decimal. If not specified, a default "
            f"value of {DEFAULT_MAX_GAP} will be used"))
    argument_parser.add_argument(
        "-i",
        "--infer-types-disable",
        action="store_true",
        help="disable attempted inference of the type of literals")
    argument_parser.add_argument(
        "-n",
        "--indentation",
        type=int,
        default=DEFAULT_INDENTATION,
        help=(
            "the number of spaces to indent by in the outputted OWL syntax. "
            f"If not specified, a default value of {DEFAULT_INDENTATION} will "
            "be used"))
    argument_parser.add_argument(
        "-o",
        "--ontology-iri",
        type=str,
        help=(
            "an IRI to use to define the ontology. By default an IRI, a priori "
            "non-dereferenceable, will be generated, and will include a "
            "current timestamp"))
    argument_parser.add_argument(
        "-p",
        "--prefix-iri",
        type=str,
        help=(
            "an IRI to use with the prefix used for generated individuals, or "
            "the default one if none is specified using the '-x/--prefix' "
            "flag. By default, the ontology IRI will be used with the symbol "
            "'#' appended"))
    argument_parser.add_argument(
        "-s",
        "--strict-mode",
        action="store_true",
        help=(
            "parse arrows in 'strict mode': both the source and the target "
            "must be locked to a node, and no attempt will made to guess them "
            "from the graph geometry if they are not present"))
    argument_parser.add_argument(
        "-x",
        "--prefix",
        type=str,
        help=(
            "a prefix to use with all generated individuals when defining "
            "their IRIs. By default no prefix is used"))
    metacharacters = ', '.join(
        f"'{character}'" for character in OWL_METACHARACTERS)
    argument_parser.add_argument(
        "-m",
        "--metacharacter-substitute",
        type=str,
        nargs='*',
        default=[],
        action="extend",
        help=(
            "defines a substitute for an OWL metacharacter, namely for a space "
            f"character ' ' or one of the following: {metacharacters}. This "
            "option can be used multiple times, for each metacharacter one "
            "wishes to handle. The string passed into the option must "
            "be 'remove' or 'url'; otherwise., the syntax 'c=d' must be used, "
            "where c is the metacharacter and d is its substitute, which can "
            "consist of zero, one, or more characters. The case of zero characters, "
            "that is to say when the syntax reads 'c=', has the effect of simply "
            "removing any occurrence of c. In several cases it will be "
            "necessary to include the quotation marks in the syntax, and "
            "indeed doing so in all cases will not harm. In the special case "
            "of the metacharacter ' ', that is to say a space, any consecutive "
            "chain of spaces will be treated as one, i.e. the entire chain "
            "will be replaced by the character/string d or removed. If the "
            "special string 'remove' is used, all metacharacters will simply "
            "be removed except for those for which a replacement has been "
            "defined by means of a separate use of the "
            "-m/--metacharacter-substitute option. "
            "If the special string 'url' is used, all metacharacters will simply "
            "be replaced with corresponding URL entities except for those "
            "for which a replacement has been defined by means of a separate use "
            "of the -m/--metacharacter-substitute option."))
    argument_parser.add_argument(
        "-l",
        "--label-disable",
        action="store_true",
        help=(
            "disable the inclusion in the outputted OWL individual blocks of "
            "an rdfs:label annotation property recording the original text "
            "in a node of the graph from which the IRI of the individual is "
            "constructed (if spaces and other metacharacters are present in "
            "the original text, these will need to be handled by means of the "
            "-m/--metacharacter-substitute and -c/--capitalisation-scheme "
            "options"))
    argument_parser.add_argument(
        "-c",
        "--capitalisation-scheme",
        type=str,
        default=DEFAULT_CAPITALISATION_SCHEME,
        help=(
            "spaces are not permitted in OWL individual IRIs, and thus a "
            "choice of how to separate multiple words is needed. The "
            "-m/--metacharacter-substitute option allows for specification "
            "of which character or string to replace spaces by, or whether "
            "to simply remove spaces. The option documented here allows in "
            "addition for adjusting the capitalisation of the words now "
            "combined by the replacing of/removal of spaces. The option "
            "accepts one of the following strings: 'upper-camel', "
            "'lower-camel', 'flat', 'none', of which the default is "
            "'upper-camel'. Here 'upper-camel' capitalises the first letter "
            "of every word; 'lower-camel' capitalises the first letter of "
            "every word except the first, which is made lower-case; 'flat' "
            "makes every word lower-case; and 'none' leaves the words "
            "untouched"))
    return argument_parser


def _run() -> None:
    arguments = _arguments_parser().parse_args()
    serialisation_config = SerialisationConfig(
        infer_type_of_literals=not arguments.infer_types_disable,
        include_preamble=not arguments.preamble_disable,
        ontology_iri=arguments.ontology_iri,
        prefix=arguments.prefix,
        prefix_iri=arguments.prefix_iri,
        indentation=arguments.indentation,
        include_label=not arguments.label_disable)
    max_gap = arguments.max_gap
    strict_mode = arguments.strict_mode
    capitalisation_scheme = arguments.capitalisation_scheme
    try:
        space_substitute = _parse_space_substitute(
            arguments.metacharacter_substitute)
        metacharacter_substitutes = list(_parse_metacharacter_substitutes(
            arguments.metacharacter_substitute))
        _parse_capitalisation_scheme(capitalisation_scheme)
    except (
            _MetacharacterSubstituteParseException,
            _InvalidCapitalisationSchemeException) as exception:
        sys_exit(f"{exception}")
    try:
        draw_io_xml_tree = DrawIOXMLTree(stdin.read())
    except NothingToParseException:
        sys_exit("The draw IO XML graph passed in appears to be empty")
    except NotInRiCException as exception:
        sys_exit(f"{exception}")
    try:
        blocks = individual_blocks(
            draw_io_xml_tree.individuals_and_arrows(strict_mode, max_gap),
            metacharacter_substitutes,
            space_substitute,
            capitalisation_scheme)
    except NoSourceException as exception:
        if arguments.strict_mode:
            message = (
                f"{exception}. If so, try to lock the arrow to an individual "
                "node in the original graph; or the underlying XML could be "
                "edited to indicate the source. Alternatively, try running the "
                "parser in non-strict mode (without the '-s/--strict-mode' "
                "flag), optionally making use of the '-g/--max-gap' option")
        else:
            message = (
                f"{exception}. If so, consider using the '-g/--max gap' option "
                "when running the script to increase the max recognised gap "
                "between a node and an arrow end; or try to lock the arrow to "
                "an individual node in the original graph; or the underlying "
                "XML could be edited")
        sys_exit(message)
    except (
            NotInRiCException,
            ArrowWithoutIndividualAsSourceException,
            MetacharacterException) as exception:
        sys_exit(f"{exception}")
    print(serialise(blocks, serialisation_config).rstrip())


def _main() -> None:
    try:
        _run()
    except ParseException as exception:
        sys_exit(str(exception))
    except Exception as exception:  # pylint: disable=broad-exception-caught
        sys_exit(f"An unexpected error occurred: {exception}")


if __name__ == "__main__":
    _main()
