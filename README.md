Records in Contexts parser for draw.io
======================================

Contents
-----------------

* [Overview](#overview)
* [Examples](#examples)
* [Requirements](#requirements)
* [How to use](#how-to-use)
    * [Using an executable file from a release](#using-an-executable-file-from-a-release)
        * [Preliminaries for Windows](#preliminaries-for-windows)
        * [Preliminaries for Mac or Linux](#preliminaries-for-mac-or-linux)
    * [Using Python directly](#using-python-directly)
* [Running](#running)
    * [Basic use](#basic-use)
    * [Making use of the outputted OWL](#making-use-of-the-outputted-owl)
    * [Configuration of the parser via command line arguments](#configuration-of-the-parser-via-command-line-arguments)
        * [Example](#example)
        * [Overview of all command line arguments](#overview-of-all-command-line-arguments)
* [Documentation](#documentation)
* [Considerations when drawing graphs](#considerations-when-drawing-graphs)
* [Feedback, bugs, suggestions](#feedback-bugs-suggestions)
* [Typical uses](#typical-uses)
* [For developers](#for-developers)
* [Thanks](#thanks)
* [License](#license)



Overview
--------

Defines a command line Python application for parsing a [draw.io](https://draw.io) graph created using the [Records in Contexts shape library](https://github.com/williamsonrichard/records_in_contexts_draw_io_shape_library), or at least according to the graphical semantics defined in that library, to an OWL ontology (in Manchester syntax). See [Typical uses](#typical-uses).

The parser tries to be tolerant of small imperfections in the graph creation, attempting a little guesswork, for example if arrows are not quite 'locked' to nodes. The parameters used in the guesswork can be configured by various arguments that can be passed to the command line application, and it is also possible to configure it to run in 'strict mode', where no guessing will be attempted.

It will attempt to infer the types of any integer or date literals, rather than regard them as strings. Again, a parameter can be used to disable this.

By default, the parser outputs a complete, self-contained ontology. This can be tweaked in various ways through command line arguments: for instance all preamble can be omitted, and only individual blocks outputted, which may be convenient if the output will be used to make additions to existing data.

See [Considerations when drawing graphs](#considerations-when-drawing-graphs) for a few points to keep in mind when constructing graphs which you intend to feed through the parser.

Release notes: v0.2 adds several features and fixes a number of bugs/scenarios that were not handled in v0.1. Please upgrade if you are currently using v0.1!


Examples
--------

The 'examples' folder in this repository contains:

* the XML of a couple of graphs (the files with suffix `.drawio`) constructed in draw.io
* screenshots of the actual graphs (the files with suffix `.drawio.png`)
* the complete, self-contained OWL (which can be opened in Protégé or other tools) that the command line application outputs in each case with default options (the files with suffix `.owl` which do not contain `without_preamble`)
* the OWL (only individual blocks)  that the command line application outputs in each case with the `-d/--preamble-disable` option (the files with suffix `.owl` which contain `without_preamble`).


Requirements
------------

None if using an executable file from a [release](https://github.com/williamsonrichard/records_in_contexts_draw_io_parser/releases) (`.exe` file on Windows, binary executable on Mac or Linux).

Python, version 3.10 or later, if running `python draw_io_parser.py` directly.


How to use
----------

There are two options: to use an executable (`.exe` file on Windows, binary executable on Mac or Linux) from a [release](https://github.com/williamsonrichard/records_in_contexts_draw_io_parser/releases), or to run `python draw_io_parser.py` directly. Both are covered below. If you have any trouble running the parser, feel free to contact me directly at ricwil (at) arkivverket.no, or to use the RiC-O mailing list.

### Using an executable file from a release

#### Preliminaries for Windows

Carry out the following steps.

* Download a Windows [release](https://github.com/williamsonrichard/records_in_contexts_draw_io_parser/releases) (likely the latest one): find the release, open 'Assets', and download 'Source code (zip)'.
* Unzip the download on your machine. You will obtain a folder `draw_io_parser`.
* Open this folder in File Explorer.
* In the 'address pane' in File Explorer (towards the top, where the file path is), type `cmd` and press Enter. This will open up a `cmd` terminal which should be located in the `draw_io_parser` folder; you could also obtain a `cmd` terminal by other means, but will then need to navigate (using `cd`) to the `draw_io_parser` folder.
* Follow the instructions in the section [Running](#running).

#### Preliminaries for Mac or Linux

* Download a Mac or Linux [release](https://github.com/williamsonrichard/records_in_contexts_draw_io_parser/releases) (likely the latest one): find the release, open 'Assets', and download 'Source code (zip)' or 'Source code (tar.gz)'.
* Unzip the download on your machine. You will obtain a folder `draw_io_parser`.
* Open a terminal, and navigate into this folder.
* Follow the instructions in the section [Running](#running).

### Using Python directly

* Ensure that you have Python version 3.10 installed on your machine.
* Download the file `draw_io_parser.py` from this repository to your machine.
* In a terminal (if unsure how to do it in Windows, adapt the instructions above), navigate to the folder in which `draw_io_parser.py` lives
* Follow the instructions in the section [Running](#running).


Running
-------

#### Basic use


Given a graph constructed in [draw.io](https://draw.io) graph created using the [Records in Contexts shape library](https://github.com/williamsonrichard/records_in_contexts_draw_io_shape_library) or adhering to the same graphical semantics, proceed as follows:

* Download the underlying XML to your machine (File -> Save As). Let us suppose that the downloaded file has name `example.drawio` (feel free to use one of the `.drawio` files in the `examples` folder in this repository).
* Carry out the [preliminary steps](#how-to-use) described above, depending on whether you wish to use an executable file from a release, or use Python directly.
* Pipe the contents of `example.drawio` into the parser, in the terminal you opened in the preliminary steps [above](#how-to-use). For example, if using an executable file from a release in Windows, proceed as follows (replacing `example.drawio` by a path to it if it is not in the same folder as `draw_io_parser.exe`).

   ```
   type example.drawio | draw_io_parser.exe
   ```

   If on a Mac or in Linux, proceed as follows.

   ```
   cat example.drawio | ./draw_io_parser
   ```

   If using Python directly, run the following in Windows...

   ```
   type example.drawio | python draw_io_parser.py
   ```

   ...or the following on a Mac or in Linux.

   ```
   cat example.drawio | python draw_io_parser.py
   ```

In all cases, the generated OWL (in Manchester syntax) will be outputted on stdout. See the next section for suggestions for what to do with this output.


#### Making use of the outputted OWL


The generated OWL outputted by the parser can for example be directed into a file, say with name `example.owl`. This would be as follows on Windows using an executable from a release...

```
type example.drawio | draw_io_parser.exe > example.owl
```

...or as follows on a Mac or in Linux...

```
cat example.drawio | ./draw_io_parser.py > example.owl
```

...or as follows if using Python directly on a Mac or in Linux (on Windows replace `cat` by `type`).

```
cat example.drawio | python draw_io_parser.py > example.owl
```

Then the file `example.owl` can be imported into Protégé, or worked with in another OWL tool. Protégé and other OWL tools will be able to output the OWL in another syntax, should this be desired.


#### Configuration of the parser via command line arguments


A number of command line arguments can be passed to the parser, rather than only using it in its most basic form as [above](#basic-use).


##### Example

The following will run the application in 'strict mode' (no attempt made to fix imperfections in the graph XML), and will use four spaces when indenting the outputted OWL.

Using an executable from a release on Windows:

```
type example.drawio | draw_io_parser.exe -s -n 4
```

...or equivalently the following.

```
type example.drawio | draw_io_parser.exe --strict-mode --indentation 4
```

On a Mac or in Linux:

```
cat example.drawio | ./draw_io_parser -s -n 4
```

...or equivalently the following.

```
cat example.drawio | ./draw_io_parser --strict-mode --indentation 4
```

If using Python directly on a Mac or in Linux (on Windows replace `cat` by `type):

```
cat example.drawio | python draw_io_parser.py -s -n 4
```

...or equivalently the following.

```
cat example.drawio | python draw_io_parser.py --strict-mode --indentation 4
```

##### Overview of all command line arguments

Run one of the following for an overview of all the possible command line arguments and an explanation of them. From an executable from a release in Windows:

```
draw_io_parser.exe --help
```

On a Mac or in Linux:

```
./draw_io_parser --help
```

If using Python directly:

```
python draw_io_parser.py --help
```


Documentation
-------------

Using `--help` as above will output quite thorough documentation of the possible command line arguments. If trying to understand the code, see the docstrings in `draw_io_parser.py`.


Considerations when drawing graphs
----------------------------------

* In the parsing of multi-line text  whether within literal nodes or within the upper half of individual nodes, two or more consecutive line-breaks will be treated as indicating a new paragraph, but single line-breaks will be ignored, that is to say, the two lines will be concatenated without any space being added. Thus, if one wishes to describe a list in a literal node, for instance, which would visually look fine with only a single line-break between items, one should include some kind of separator (a comma plus a single space, or a semi-colon plus a single space, etc), so that the list aspect is not upon parsing.
* OWL has certain metacharacters that cannot be used in the IRI for an individual (coming from the upper half of an individual node). This includes spaces. The command line option `-m/--metacharacter-substitute` can be used (more than once if necessary) to define substitutes for these metacharacters or to remove them: use `--help` as described in the section [Overview of all command line arguments](#overview-of-all-command-line-arguments) for more details.

  If the parser encounters a metacharacter for which a substitute has not been defined, it will cease parsing and protest! For convenience, you may wish to use `-m remove`, which will simply remove all metacharacters (including spaces) for which you do not specify a substitute (by means of further uses of `-m/--metacharacter-substitute`).

  The handling of capitalisation in connection with replacing or removing spaces can be configured/homogenised using the `-c/--capitalisation-scheme` option. Again, see `--help` for details.

  In all cases, by default, an `rdfs:label` annotation property will be included in the outputted OWL block which records the original text, before it was parsed. In Protégé, this human-readable label is what will typically be displayed; it is only in the actual IRI for an individual that the parsed form is necessary. If you wish to disable the inclusion of the `rdfs:label` annotation property, include the `-l/--label-disable` option when running the script.



Feedback, bugs, suggestions
---------------------------

All very welcome! The 'Issues' tab in github can be used for bugs and suggestions. Otherwise I can be contacted at ricwil (at) arkivverket.no.


Typical uses
------------

Typical reasons for wishing to work graphically with Records in Contexts are described at the [Records in Contexts shape library](https://github.com/williamsonrichard/records_in_contexts_draw_io_shape_library). This parser bridges the gap between a graph created this way and formal OWL.

Somebody with technical expertises, e.g. an ontologist or software engineer, can take a graph created in draw.io using the shape library, and apply the parser to obtain something which can be quickly be incorporated into a triple store, or otherwise studied/worked with formally.

Somebody comfortable with the idea of a subject-predicate-object triple, but not familiar with the finer details of OWL syntax, might find the parser helpful as a ready source of examples.

There are many ways in which the tool might be built upon, e.g. it could be hosted on a server (or rewritten into Javascript) and used within a web application in which users can define or edit Records in Contexts metadata graphically 'live'.


For developers
--------------

A github action will be run for every commit or pull request which carries out a few checks. Locally, one can achieve the same by setting up a virtual environment with `mypy`, `pylint`, and `autopep8` installed, and running the following:

* `mypy draw_io_parser.py` for type-checking
* `pylint draw_io_parser.py` for linting
* `autopep8 --in-place draw_io_parser.py` to format the code in-place (replace `--in-place` by `--diff` to see divergences from the PEP 8 style guide)


Thanks
------

I am very grateful to Aaron Hope from the Archives of Ontario for engaging with the parser and the shape library, and for an extremely useful example breaking many things in v0.1 of the parser!


License
-------

The parser is made available without any restrictions at all, except that this unrestrictedness is not permitted to be invalidated/superseded/overridden in any way or to any degree.
