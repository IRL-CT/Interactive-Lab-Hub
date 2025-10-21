Documentation Generation and Publishing
=============================================

For each package, the documentation is automatically generated and published using readthedocs.org. The documentation itself is generated using [Sphinx](http://www.sphinx-doc.org/), which creates the desired documentation HTML output based on source code comments and documentation structure files. 

The repository files used to define and create the documentation are the following:
```
Qwiic_Template_Py/
   +--- docs/
   |       +--- conf.py      - defines the input and output behavior of Sphinx
   |       +--- index.rst    - Top level documentation structure definition 
   |       +---     *.rst    - Defines additional pages for the documentation - index.rst references these files.
   |       +--- requirements.txt   - Lists the python modules the package depends on. 
   |       `--- _static/
   |                `--- favicon.ico    - the favicon to use for the generated HTML text
   |
   |--- .readthedocs.yml   - Defines how the ReadTheDocs environment is setup when building the documentation
```


To create a package's documentation, the general development pattern is as follows:
* Documentation is added to the python source code using [docstrings](https://www.python.org/dev/peps/pep-0257/)
* Documentation configuration is define in ```docs/conf.py```
* Package dependencies are added to ```docs/requirements.txt```
* The file ```index.rst``` is updated for the desired documentation structure. Additional ```.rst``` files are added as needed.
* Documentation is generated locally using Sphinx for testing
* Validated documentation files are checked into the GitHub repository.
* The GitHub repository is imported and linked to a project in ReadTheDocs.org
* ReadTheDocs generates and publishes the documentation.
    * The documentation is updated automatically when the project is updated on GitHub
    
___Python Docstrings___

Python has a built-in language feature used to embed documentation strings in code, a feature called _docstrings_.

From the docstring spec (PEP-0257):
> A docstring is a string literal that occurs as the first statement in a module, function, class, or method definition. Such a docstring becomes the \__doc__ special attribute of that object.

These strings are enclosed by triple quotes. While the format of the text is left to the user, the Sphinx system will honor reStructured text formatting. The qwiic system python documentation formats the docstrings as reStructure Text.

An example of a docstring is the class definition for the QwiicOTOS object. 
```python
class QwiicOTOS(object):
	"""
	QwiicOTOS

		:param address: The I2C address to use for the device. 
						If not provided, the default address is used.
		:param i2c_driver: An existing i2c driver object. If not provided 
						a driver object is created. 
		:return: The OTOS device object.
		:rtype: Object
	"""
```
Note that the docstring is the first statement after the class definition. 

Doc strings for methods following the method declaration statement:
```python
def setFilter(self, filterSetting):
		"""
		Set the filter bits in the OTOSs config register

		:param filterSetting: The filter bits for the OTOS. Acceptable values
						0 = filter off
	  					1 = coefficients = 2
	  					2 = coefficients = 4
	  					3 = coefficients = 8
	  					4 = coefficients = 16

		:return: No return value 

		"""
```

And you can even add docstrings to a module (file) - placing the docstring at the top (first non-comment) of the file.
```python
#==================================================================================

"""
qwiic_otos
============
Python module for the [SparkFun Optical Tracking Odometry Sensor - PAA5160E1 (Qwiic)](https://www.sparkfun.com/products/24904)

This python package is a port of the existing [SparkFun Optical Tracking Odometry Sensor Arduino Library](https://github.com/sparkfun/SparkFun_Qwiic_OTOS_Arduino_Library)

This package can be used in conjunction with the overall [SparkFun qwiic Python Package](https://github.com/sparkfun/Qwiic_Py)

New to qwiic? Take a look at the entire [SparkFun qwiic ecosystem](https://www.sparkfun.com/qwiic).

"""
#-----------------------------------------------------------------------------

import math
import qwiic_i2c
```

The Sphinx documentation package uses the values of the ```__doc___``` attribute of objects to locate and generate documentation. As such, the Sphinx system (either run locally or by ReadTheDocs.org) will instantiate the package as part of the documentation generation process. As such, the dependencies and needs of the package must be defined in the documentation configuration files.

___docs/conf.py___

The ````docs/conf.py``` file sets the configuration Sphinx will use when building the documentation set. Key areas of this file are:

*Project Information*

These are variables that describe the project. The key value being the name of the project, which should be in the form of **`'sparkfun_qwiic_`**`<package_name>'`. _(*Don't forget to update the copyright year.)_
```python
project = 'sparkfun_qwiic_otos'
copyright = '2019, SparkFun Electronics'
author = 'SparkFun Electronics'
```

*Project Extensions*

This is an array that contains the names of extensions to the Sphinx system to generate the documentation. These are python packages that should be installed on your system (for local documentation builds). For the qwiic python packages, the following statement is used:
```python
extensions = [ 
	'sphinx.ext.autodoc',
	'sphinx.ext.intersphinx',
	'sphinx.ext.viewcode',
	'm2r2'
	]
```
The unique package here is ```m2r2```, which converts markdown into reStructured text. This allows the documentation system to import the GitHub README.md files into the generated documentation page.

*master_doc*

This variable is set to the master documentation structure file being used. For the qwiic packages, this value is set to ```"index"```, which tells Sphinx to use ```index.rst``` to define the documentation structure. 
```python
master_doc = 'index'
```

*Static Values*

The last value worth noting is the static resources that should be used in documentation generation. For SparkFun documentation we include the favion.ico file from www.sparkfun.com. This file is located at ```docs/_static/favicon.ico``` and documented as follows in the conf.py file. 
```python
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_favicon = '_static/favicon.ico'
```

___docs/*.rst Files___

The structure and contents of the documentation is oulined using a set of reStructured text (```.rst```) files, with the starting definition contained in ```docs/index.rst```.

*docs/index.rst*

This file defines the entry page for the documentation. For the qwiic documentation, we include the GitHub README.md file, and define a table of contents, which defines other pages of the documentation. 

For the qwiic OTOS python package, this file contains the following:
```rst
.. mdinclude:: ../README.md

Table of Contents
=================

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   self


.. toctree:: 
   :caption: API Reference
   :maxdepth: 3

   apiref 

.. toctree:: 
   :caption: Examples

   ex1
   ex4
   ex5

.. toctree::
   :caption: Other Links

	SparkFun <https://sparkfun.com>
   SparkFun Optical Tracking Odometry Sensor - PAA5160E1 (Qwiic) <https://www.sparkfun.com/products/24904>
	GitHub <https://github.com/sparkfun/Qwiic_OTOS_Py>
	SparkFun qwiic <https://www.sparkfun.com/qwiic>
```

The key elements of this file:

**.. mdinclude:: ../README.md**

This includes the packages README.md file, with ```mdinclude``` noting that the file is formatted in markdown.

**.. toctree:: **

Defines an section in the table of contents, and the content of this section.

For the main page (index.rst):
```rst
.. toctree::
   :maxdepth: 4
   :caption: Contents:

   self
```
Note the section referances ```self```

For the package API:
```rst
.. toctree:: 
   :caption: API Reference
   :maxdepth: 3

   apiref 
```
This section links to the file ```apiref.rst```

And the examples section, which links to three example rst files: ```ex1.rst, ex4.rst, ex5.rst``` _(*The file names (i.e. `ex3.rst`) should match the link names (i.e. `ex3`).)_
```rst
.. toctree:: 
   :caption: Examples

   ex1
   ex4
   ex5
```

In the other links section, update the product name and the links to the product page and package's GitHub repo.
```rst
.. toctree::
   :caption: Other Links

	SparkFun <https://sparkfun.com>
   SparkFun Optical Tracking Odometry Sensor - PAA5160E1 (Qwiic) <https://www.sparkfun.com/products/24904>
	GitHub <https://github.com/sparkfun/OTOS>
	SparkFun qwiic <https://www.sparkfun.com/qwiic>
```

*API Documentation*

To document the projects API, the *autodoc* system of Sphinx is used. This system will crawl the specified files/packages and generate documention using the included *docstrings*. _(*The automodule should take the form of **`qwiic_`**`<package_name>`. For packages with underlying classes, see the `qwiic_mico_oled` example below.)_

For a moduled, like ```qwiic_otos```, the contents of ```apiref.rst``` is:
```rst
API Reference
==============

.. automodule:: qwiic_otos
   :members:
```
This specifies that Sphinx should inspect the qwiic_otos module, and document the package members. 

Got python packages, such as the ```qwiic_mico_oled``` package, the documentation is contained in module and underlying class, so the rst file takes a slightly different format:
```rst
API Reference
==============

.. automodule:: qwiic_micro_oled
   :members:


.. autoclass:: QwiicMicroOled
	:members:
```

The Sphinx autodoc feature is extemely useful, and fully documented by the [Sphinx project](http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html).

___Documenting Examples___

Any examples for a package are also included in the documentation. These are defined in individual rst files, which do nothing more than include the source of the example. 

The following shows the format of an an example rst file, which does nothing more than inline a file, add the filename as the caption of the inline, and formats the included file with line numbers. _(*The header/title is what will appear as the example code's title on the ReadtheDocs webpage and display the script from `/examples/qwiic_otos_ex1.py`.)_
```rst
Basic Operation
---------------------------
.. literalinclude:: ../examples/qwiic_otos_ex1.py
    :caption: examples/qwiic_otos_ex1.py
    :linenos:
```

___The .readthedocs.yml File___

This file defines the attributes and packages ReadTheDocs should use when creating the documentation generation environment. As noted above, Sphinx instantiates the contents of the package so that it can access the python docstrings during the generation process. The file ```.readthedocs.yml``` and it's associated file ```docs/requirements.txt``` define the environment to use. 

The contents of ```.readthedocs``` used by the qwiic modules is:
```yml
python:
   version: 3
   install:
      - requirements: docs/requirements.txt
   setup_py_install: true
```
This file tells ReadTheDocs the following:
* Use Python version 3 to generate the docs
* Install the modules contained in ```docs/requirements.txt```
* Install the package/module defined by this repository using a the contents of ```setup.py``` 

The ```docs/requirements.txt``` file contains the modules this package needs to generate documentation. This is used by Sphinx when generating local documentation, and by ReadTheDocs, as noted above in the contents of the ```.readthedocs.yml``` file.

For most qwiic driver packages, this file contains the following:
```txt
m2r2
sparkfun-qwiic-i2c
```
The contents specifically being:

* mr2 - the Markdown to reStructureText conversion module
* sparkfun-qwiic-i2 - the I2C driver package used by all qwiic packages.

Local Documentation Generation
_______________________________

Sphinx is used to test the documentation before uploading the contents to ReadTheDocs.org. To build locally, execute the following steps:

Insure the needed packages are installed, which are Sphinx, the sphinx read the docs theme and the markdown to reStructure Text conversion package m2r2.

```sh
sudo pip install Sphinx sphinx_rtd_theme m2r2
```
Additionally, the package being documented should be installed locally. Normally this is just done by running the following command in the root of the package directory. 
```sh
sudo python setup.py install
```

Once installed, the documentatin is created as follows:
```sh
cd docs
sphinx-build -E -b html . _build/html
```
The output of this process is placed in the directory ```docs/_build/html```. The generated documentation is visible by loading the file ```index.html``` in a browser.

Publishing to ReadTheDocs.org
-------------------------------

To publish the documentation on ReadTheDocs.org, you'll need an account. Once the account is created, it needs to be linked/connected to the your SFE GitHub account. This is a standard oAuth2 connection process, which is initiated in the the Account -> Settings -> Connected Services section of readthedocs.org.

To import a project the following steps are taken:
* First ensure the project contents are checked into GitHub and that the repository is public.
* View "My Projects" on ReadTheDocs.
* Select *Import a Project*
* Under **Filter repositories** on the right of the page, select "SparkFun Electronics"
* Either page through and find the project to import, or select "Import Manually" and enter the details of the target project.
* Once imported, ReadTheDocs will being the build process for the documentation. The progress of this is followed by selecting the project on the [My Projects](https://readthedocs.org/dashboard/) page, and selected the project and once in the project, selecting the "Builds" button.
* If the builds is successful, a link to the new documentation is made available. 

If a documentation build fails, the best method to debug is to dig into the specific build (The Project -> Builds) and review the build log. If more detail is needed, the __View raw__ link on the build page will display the raw logfile from the build run. 

#### Documentation Update

The update process for the documentation is automatic. Whenever the project's master branch on GitHub is updated, ReadTheDocs will initiate a documentation build using the new package content.
