"""
Tests the DrawIOXMLTree class in the way it would be used when running
draw_io_parser.py
"""

from pathlib import Path
from unittest import TestCase

from draw_io_parser import (
    DEFAULT_CAPITALISATION_SCHEME, DEFAULT_INDENTATION, DEFAULT_MAX_GAP,
    DrawIOXMLTree, SerialisationConfig, individual_blocks, serialise)

_examples_directory = Path.cwd() / "examples"

_serialisation_config = SerialisationConfig(
    infer_type_of_literals=True,
    include_preamble=False,
    ontology_iri=None,
    prefix=None,
    prefix_iri=None,
    indentation=DEFAULT_INDENTATION,
    include_label=True)

_metacharacters = [(",", "-"), ("[", "{"), ("]", "}")]


class TestDrawIOParser(TestCase):
    """
    Tests that the parsing of the .drawio files in the examples/ directory
    gives the expected results
    """

    def test_examples_without_preamble(self) -> None:
        """
        Tests, for each .drawio file in the examples/ directory, that the OWL
        generated (without preamble) is equal to that contained in the
        corresponding _without_preamble.owl file
        """
        self.maxDiff = None  # pylint: disable=invalid-name
        for path in _examples_directory.iterdir():
            if path.suffix != ".drawio":
                continue
            with open(path, "r", encoding="utf-8") as draw_io_file:
                draw_io_xml_tree = DrawIOXMLTree(draw_io_file.read())
            blocks = individual_blocks(
                draw_io_xml_tree.individuals_and_arrows(
                    False, DEFAULT_MAX_GAP),
                _metacharacters,
                "",
                DEFAULT_CAPITALISATION_SCHEME)
            owl = serialise(blocks, _serialisation_config)
            with open(
                    _examples_directory / f"{path.stem}_without_preamble.owl",
                    "r",
                    encoding="utf-8") as owl_file:
                self.assertEqual(owl.strip(), owl_file.read().strip())

    def test_example_with_preamble(self) -> None:
        """
        Tests, for one of the .drawio files in the examples/ directory, that the
        OWL generated is equal to that contained in the corresponding
        .owl file with the correct preamble (with the ontology IRI specified
        here to be the same as that in the .owl file)
        """
        self.maxDiff = None  # pylint: disable=invalid-name
        path = _examples_directory / "koronakommisjonen.drawio"
        with open(path, "r", encoding="utf-8") as draw_io_file:
            draw_io_xml_tree = DrawIOXMLTree(draw_io_file.read())
        blocks = individual_blocks(
            draw_io_xml_tree.individuals_and_arrows(False, DEFAULT_MAX_GAP),
            [],
            "",
            DEFAULT_CAPITALISATION_SCHEME)
        serialisation_config = SerialisationConfig(
            infer_type_of_literals=True,
            include_preamble=True,
            ontology_iri="ontology://generated-from-draw-io/2024-04-26T01-31-21",
            prefix=None,
            prefix_iri=None,
            indentation=DEFAULT_INDENTATION,
            include_label=True)
        owl = serialise(blocks, serialisation_config)
        with open(
                _examples_directory / f"{path.stem}.owl",
                "r",
                encoding="utf-8") as owl_file:
            self.assertEqual(owl.strip(), owl_file.read().strip())
