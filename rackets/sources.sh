# sources.sh
# aoneill - 04/16/17

# This pulls the sources for running the rackets program

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function tell() { echo "$@"; $@; }

# Directories
LIBS="$DIR/libs"
LIBS_DRIVER="$LIBS/__init__.py"
PATCHES="$DIR/patches"

# Python configuration
PYTHON_INCLUDE_DIR=/usr/include/python2.7
PYTHON_INCLUDE_PATH=$PYTHON_INCLUDE_DIR

# Libraries
PSMOVEAPI="$LIBS/psmoveapi"
PSMOVEAPI_BUILD="$PSMOVEAPI/build"
PSMOVEAPI_PY_BIND="$PSMOVEAPI/bindings/python"

function lib_driver() {
  # Make the libraries directory
  [[ ! -d "$LIBS" ]] && tell mkdir -p "$LIBS"
  tell cd "$LIBS"

  # Make the Python driver
  if [[ ! -f "$LIBS_DRIVER" ]]; then
    echo "cat << EOF > $LIBS_DRIVER ..."

    cat << EOF > $LIBS_DRIVER
import os
import sys

PSMOVEAPI_BUILD = os.path.join(os.path.dirname(__file__),
    'psmoveapi', 'build'
  )
PSMOVEAPI_BINDS = os.path.join(os.path.dirname(__file__),
    'psmoveapi', 'bindings', 'python'
  )

sys.path.insert(0, PSMOVEAPI_BUILD)
sys.path.insert(1, PSMOVEAPI_BINDS)
os.putenv('PSMOVEAPI_LIBRARY_PATH', PSMOVEAPI_BUILD)

import psmove
import psmoveapi

__all__ = [psmove, psmoveapi]
EOF
  fi
}

# Apply patches to the psmoveapi
# From: https://aur.archlinux.org/packages/psmoveapi-git/
function patch_psmoveapi() {
  cd "$PSMOVEAPI"

  tell patch -p1 -Ni "$PATCHES/fix-opencv-headers.patch"
  tell patch -p1 -Ni "$PATCHES/add-libv4l2-module.patch"
}

# Apply patches to the psmoveapi for Python2 compatibility
function patch_psmoveapi_py2() {
  cd "$PSMOVEAPI"

  tell patch -p1 -Ni "$PATCHES/fix-python2.patch"
}

# Install the psmoveapi
function psmoveapi() {
  # Get the source code
  if [[ ! -d "$PSMOVEAPI" ]]; then
    tell git clone --recursive git://github.com/thp/psmoveapi.git
  fi

  # Patch if asked
  [[ "$1" == "--patch" ]] && patch_psmoveapi
  tell cd "$PSMOVEAPI"

  # Make a build directory
  [[ ! -d "$PSMOVEAPI_BUILD" ]] && tell mkdir "$PSMOVEAPI_BUILD"
  tell cd "$PSMOVEAPI_BUILD"

  # Make the psmoveapi
  tell cmake .. \
    -DPYTHON_INCLUDE_DIR=$PYTHON_INCLUDE_DIR \
    -DPYTHON_INCLUDE_PATH=$PYTHON_INCLUDE_PATH \
    -DPSMOVE_BUILD_EXAMPLES=OFF \
    -DPSMOVE_BUILD_OPENGL_EXAMPLES=OFF \
    -DPSMOVE_BUILD_TESTS=OFF \
    -DPSMOVE_USE_DEBUG=1 \
    && make || return

  # Fix Python2 issues
  patch_psmoveapi_py2
}

function main() {
  # Install the library driver code
  lib_driver $@

  # Install the psmoveapi
  psmoveapi $@
}

main $@
