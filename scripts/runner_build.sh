#!/usr/bin/env bash
##===============================================
## GitLab runner build script for loki
##
## First build the dist and html.
## Then restructure into format expected on server
##
## Place build and html here:
##   data/dist/loki-<VER>.tar.gz
##   data/html/html-<VER>
## Create Links here:
##   data/dist/loki-current.tar.gz -> data/dist/loki-<VER>.tar.gz
##   main -> data/html/html-<VER>
##
## This is all packaged up into the 'public'
## folder, where the runner searches for output.
##===============================================
# build dist and sphinx docs
python setup.py develop
python setup.py sdist
sphinx-build -b html -W docs html
# move to required output locations
LOKIVER="$(loki --version 2>&1)" #2>&1 hack b/c argparse --version goes to stderr!
mkdir -p public/data/html
mv dist public/data/.
sh -c "cd public/data/dist && ln -sf loki-${LOKIVER}.tar.gz loki-current.tar.gz"
mv html public/data/html/html-${LOKIVER}
sh -c "cd public && ln -sf data/html/html-${LOKIVER} main"