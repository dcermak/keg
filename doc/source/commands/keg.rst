keg
===

.. _keg_synopsis:

SYNOPSIS
--------

.. code:: bash

   keg (-l|--list-recipes) (-r RECIPES_ROOT|--recipes-root=RECIPES_ROOT)

   keg (-r RECIPES_ROOT|--recipes-root=RECIPES_ROOT)
       [--format-xml|--format-yaml] [--dump-dict]
       [-a ADD_DATA_ROOT] ... [-d DEST_DIR] [-fv]
       SOURCE

   keg -h | --help

DESCRIPTION
-----------

`Keg` is a tool which helps to create and manage image descriptions suitable
for the `KIWI <https://osinside.github.io/kiwi/>`__ appliance builder.
While `keg` can be used to manage a single image definition the tool provides
no considerable advantage in such a use case. The primary use case for `keg`
are situations where many image descriptions must be managed and the
image descriptions have considerable overlap with respect to content
and setup.

`Keg` requires source data called `recipes` which provides all information
necessary for `keg` to create KIWI image descriptions. See
:ref:`recipes_basics` for more information about `recipes`.

The `recipes` used for generating SUSE Public Cloud image descriptions
can be found in the
`Public Cloud Keg Recipes <https://github.com/SUSE-Enceladus/keg-recipes>`__
repository.

.. _keg_options:

ARGUMENTS
---------

SOURCE

  Path to image source, expected under RECIPES_ROOT/images

OPTIONS
-------

-r RECIPES_ROOT, --recipes-root=RECIPES_ROOT

  Root directory of Keg recipes

-a ADD_DATA_ROOT, --add-data-root=ADD_DATA_ROOT

  Additional data root directory of recipes (multiples allowed)

-d DEST_DIR, --dest-dir=DEST_DIR

  Destination directory for generated description, default cwd

-l, --list-recipes

  List available images that can be created with the current recipes

-f, --force

  Force mode (ignore errors, overwrite files)

--format-yaml

  Format/Update Keg written image description to installed
  KIWI schema and write the result description in YAML markup.

  .. note::

     Currently no translation of comment blocks from the Keg
     generated KIWI description to the YAML markup will be
     performed

--format-xml

  Format/Update Keg written image description to installed
  KIWI schema and write the result description in XML markup

  .. note::

     Currently only toplevel header comments from the Keg
     written image description will be preserved into the
     formatted/updated KIWI XML file. Inline comments will
     not be preserved.

--dump-dict

  Parse input data and build image data dictionary, but instead
  of running the generator, dump data dictionary and exit. Useful
  for debugging.

-v, --verbose

  Enable verbose output

EXAMPLE
-------

.. code:: bash

   $ git clone https://github.com/SUSE-Enceladus/keg-recipes.git

   $ keg --recipes-root keg-recipes --dest-dir leap_description leap/jeos/15.2
