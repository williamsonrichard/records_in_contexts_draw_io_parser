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
    "resultedFromTheMergerOf",
    "resultedFromTheSplitOf",
    "resultsOrResultedFrom",
    "resultsOrResultedIn",
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

Blocks = dict[str, dict[str, set[str]]]
Cell = Element
CellID = str
XCoordinate = float
YCoordinate = float
Width = float
Height = float
ArrowStart = tuple[XCoordinate, YCoordinate]
ArrowEnd = tuple[XCoordinate, YCoordinate]
Label = str
ArrowData = tuple[Cell, ArrowStart, ArrowEnd, Label]
Dimensions = tuple[XCoordinate, YCoordinate, Width, Height]

DEFAULT_INDENTATION = 2
DEFAULT_MAX_GAP = 10


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


class LiteralNodeHTMLParser(HTMLParser):
    """
    Subclasses HTMLParser to define its behaviour with respect to 'handle_data'
    (this is the usage pattern expected by HTMLParser): we implement it to
    simply store the raw data (text) in a snippet of HTML so that it can fetched
    by other code.
    """

    def __init__(self):
        super().__init__()
        self.raw_data = ""

    def handle_data(self, data: str) -> None:
        """
        Overrides a function in HTMLParser, storing the raw data (text) inside
        the HTML snippet 'data' in the instance variable 'raw_data'.
        """
        self.raw_data = data

    def clear_raw_data(self) -> None:
        """
        Sets the instance variable 'raw_data' to the empty string.
        """
        self.raw_data = ""


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


@dataclass(frozen=True)
class DrawIOXMLTree:
    """
    The purpose of this class is to parse a raw draw.io XML to a list of
    instances of the Individual and Arrow classes, corresponding respectively to
    nodes and arrows in the graph which the  XML defines. The constructor takes
    such an XML string, and part of the parsing is already carried out upon
    calling the constructor, for effectivity. The method
    'individuals_and_arrows' can then be called to complete the parsing and
    return the obtained Individual and Arrow instances as a generator
    """
    draw_io_xml_tree: Element = field(init=False)
    literal_node_html_parser: LiteralNodeHTMLParser = field(init=False)
    individual_cells: list[tuple[Cell, Individual,
                                 Dimensions]] = field(init=False)
    arrow_cells: list[ArrowData] = field(init=False)

    raw_xml: InitVar[str]

    def __post_init__(self, raw_xml):
        object.__setattr__(self, "literal_node_html_parser",
                           LiteralNodeHTMLParser())
        object.__setattr__(self, "draw_io_xml_tree", fromstring(raw_xml))
        object.__setattr__(self, "individual_cells", [])
        object.__setattr__(self, "arrow_cells", [])
        self._extract_individual_and_arrow_cells()

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
        self.literal_node_html_parser.clear_raw_data()
        self.literal_node_html_parser.feed(value)
        return self.literal_node_html_parser.raw_data

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
    def _arrow_start_or_end(arrow_cell: Element, as_attribute: str) -> tuple[
            XCoordinate, YCoordinate]:
        geometry = DrawIOXMLTree._geometry(arrow_cell)
        if not geometry:
            raise ParseException(
                "Expecting the mxGeometry element of the cell with the "
                "following id to have sub-elements, but has no sub-elements "
                f"at all: {arrow_cell.attrib['id']}")
        for element in geometry:
            if element.tag != "mxPoint":
                continue
            try:
                if element.attrib["as"] != as_attribute:
                    continue
            except KeyError as key_error:
                raise ParseException(
                    "Expecting the following mxPoint element to have an 'as' "
                    f"attribute, but it does not: {element}"
                ) from key_error
            try:
                x = float(element.attrib["x"])
            except KeyError as key_error:
                raise ParseException(
                    "Expecting the following mxPoint element to have an 'x' "
                    f"attribute, but it does not: {element}"
                ) from key_error
            try:
                y = float(element.attrib["y"])
            except KeyError as key_error:
                raise ParseException(
                    "Expecting the following mxPoint element to have a 'y' "
                    f"attribute, but it does not: {element}"
                ) from key_error
            return x, y
        raise ParseException(
            "Expecting the mxGeometry element of the cell with the following "
            "id to have an mxPoint sub-element with 'as' attribute having "
            f"value 'sourcePoint', but it does not: {arrow_cell.attrib['id']}")

    @staticmethod
    def _arrow_start(arrow_cell: Element) -> ArrowStart:
        return DrawIOXMLTree._arrow_start_or_end(arrow_cell, "sourcePoint")

    @staticmethod
    def _arrow_end(arrow_cell: Element) -> ArrowEnd:
        return DrawIOXMLTree._arrow_start_or_end(arrow_cell, "targetPoint")

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

    def _arrow_label(self, arrow_cell: Element) -> str:
        for cell in self._child_of(arrow_cell.attrib["id"]):
            try:
                style = cell.attrib["style"]
            except KeyError:
                continue
            if "edgeLabel" in style:
                return self._value_of(cell)
        raise _NoValueException

    def _extract_individual_and_arrow_cells(self) -> None:
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
                continue
            if not cell_value.startswith("rico:"):
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
            individual = Individual(
                individual_identifier, cell_value.split("rico:")[1].strip())
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
        raise _NoCellCloseEnoughException

    def _source_or_target(self, source_or_target_cell: Element) -> str:
        try:
            value = self._value_of(source_or_target_cell)
        except KeyError as key_error:
            raise _NoValueException from key_error
        if value.startswith("rico:"):
            return self._value_of(self._parent_of(source_or_target_cell))
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
            if strict_mode:
                raise NoSourceException(
                    f"The mxCell element with label '{arrow_label}' seems to "
                    "be an arrow, but has no source"
                ) from key_error
            try:
                source_cell = self._cell_close_to(arrow_start, max_gap)
            except _NoCellCloseEnoughException as not_close_enough_exception:
                raise NoSourceException(
                    f"The mxCell element with label '{arrow_label}' seems to "
                    "be an arrow, but has no source"
                ) from not_close_enough_exception
        source = self._source_or_target(source_cell)
        try:
            target_cell = self._cell_with_id(arrow_cell.attrib["target"])
        except KeyError as key_error:
            if strict_mode:
                raise NoSourceException(
                    f"The mxCell element with label '{arrow_label}' seems to "
                    "be an arrow, but has no target"
                ) from key_error
            try:
                target_cell = self._cell_close_to(arrow_end, max_gap)
            except _NoCellCloseEnoughException as not_close_enough_exception:
                raise NoSourceException(
                    f"The mxCell element with label '{arrow_label}' seems to "
                    "be an arrow, but has no target"
                ) from not_close_enough_exception
        target = self._source_or_target(target_cell)
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
        raise ParseException(f"Not a RiC class: {ric_class}")


def _to_upper_camel_case(identifier: str) -> str:
    return "".join([word[0].upper() + word[1:] for word in identifier.split()])


def _replace_metacharacters(identifier: str) -> str:
    return identifier.replace("(", "⟨").replace(")", "⟩").replace(
        "/", "∕").replace(", ", "|").replace(",", "|")


def _add_individual_type(blocks: Blocks, individual: Individual) -> None:
    _verify_is_ric_class(individual.ric_class)
    individual_identifier = _to_upper_camel_case(
        _replace_metacharacters(individual.identifier))
    try:
        block = blocks[individual_identifier]
    except KeyError:
        blocks[individual_identifier] = {"Types": {individual.ric_class}}
        return
    try:
        block["Types"].add(individual.ric_class)
    except KeyError:
        block["Types"] = {individual.ric_class}


def individual_blocks(
        individuals_and_arrows: Iterator[Individual | Arrow]) -> Blocks:
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
            _add_individual_type(blocks, individual_or_arrow)
            continue
        if individual_or_arrow.identifier in _ric_object_properties:
            target_identifier = _to_upper_camel_case(
                _replace_metacharacters(individual_or_arrow.target))
        elif individual_or_arrow.identifier in _ric_datatype_properties:
            target_identifier = individual_or_arrow.target
        else:
            raise NotInRiCException(
                f"An arrow has label rico:'{individual_or_arrow.identifier}', "
                "which is not an object property or datatype property in RiC-O")
        source_identifier = _to_upper_camel_case(individual_or_arrow.source)
        try:
            block = blocks[source_identifier]
        except KeyError:
            blocks[source_identifier] = {
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
        for value in values:
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
        types_and_facts: dict[str, set[str]],
        serialisation_config: SerialisationConfig) -> str:
    prefix = serialisation_config.prefix
    indentation = serialisation_config.indentation
    infer_type_of_literals = serialisation_config.infer_type_of_literals
    if prefix:
        prefix_string = prefix + ":"
    else:
        prefix_string = ""
    types_string = ", ".join(
        f"rico:{_type}" for _type in types_and_facts["Types"])
    facts = types_and_facts.copy()
    del facts["Types"]
    if not facts:
        return f"""Individual: {prefix_string}{individual_identifier}
{' '*indentation}Types: {types_string}

"""
    serialised_facts = list(_serialise_facts(
        facts, infer_type_of_literals, prefix))
    facts_string = f",\n{' '*(indentation*2)}".join(serialised_facts[:-1])
    facts_string += f",\n{' '*(indentation*2)}{serialised_facts[-1]}" if len(
        serialised_facts) > 1 else f"{serialised_facts[-1]}"
    return f"""Individual: {prefix_string}{individual_identifier}
{' '*indentation}Types: {types_string}
{' '*indentation}Facts:
{' '*(indentation*2)}{facts_string}

"""


def _preamble(serialisation_config: SerialisationConfig) -> str:
    ontology_iri = serialisation_config.ontology_iri
    prefix = serialisation_config.prefix
    prefix_iri = serialisation_config.prefix_iri
    indentation = serialisation_config.indentation
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
    return f"""Prefix: rico: <https://www.ica.org/standards/RiC/ontology#>
Prefix: {prefix_string}: {prefix_iri}
Ontology: <{ontology_iri_string}>
{' '*indentation}Import: <https://raw.githubusercontent.com/ICA-EGAD/RiC-O/master/ontology/current-version/RiC-O_1-0.rdf>

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
    for individual_identifier, types_and_facts in blocks.items():
        serialised += _serialise_block(individual_identifier,
                                       types_and_facts, serialisation_config)
    return serialised


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
    return argument_parser


def _run() -> None:
    arguments = _arguments_parser().parse_args()
    serialisation_config = SerialisationConfig(
        infer_type_of_literals=not arguments.infer_types_disable,
        include_preamble=not arguments.preamble_disable,
        ontology_iri=arguments.ontology_iri,
        prefix=arguments.prefix,
        prefix_iri=arguments.prefix_iri,
        indentation=arguments.indentation)
    max_gap = arguments.max_gap
    strict_mode = arguments.strict_mode
    try:
        draw_io_xml_tree = DrawIOXMLTree(stdin.read())
    except NothingToParseException:
        sys_exit("The draw IO XML graph passed in appears to be empty")
    try:
        blocks = individual_blocks(
            draw_io_xml_tree.individuals_and_arrows(strict_mode, max_gap))
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
                "XML could be edited to indicate the source")
        sys_exit(message)
    except NotInRiCException as exception:
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
