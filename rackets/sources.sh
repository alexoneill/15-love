# sources.sh
# aoneill - 04/16/17

# This pulls the sources for running the rackets program

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function tell() { echo "$@"; $@; }

# Directories
LIBS=libs
BUILD=build
PATCHES=patches

# Python configuration
PYTHON_INCLUDE_DIR=/usr/include/python2.7
PYTHON_INCLUDE_PATH=$PYTHON_INCLUDE_DIR

# Libraries
PSMOVELIB=psmoveapi

# Apply patches to the psmoveapi
# From: https://aur.archlinux.org/packages/psmoveapi-git/
function patch_psmoveapi() {
  cd $LIBS/$PSMOVELIB

  tell patch -p1 -i "$DIR/$PATCHES/fix-opencv-headers.patch"
  tell patch -p1 -i "$DIR/$PATCHES/add-libv4l2-module.patch"
}

# Install the psmoveapi
function psmoveapi() {
  # Make the libraries directory
  [[ ! -d "$DIR/$LIBS" ]] && tell mkdir -p "$DIR/$LIBS"
  tell cd "$DIR/$LIBS"

  # Get the source code
  if [[ ! -d $PSMOVELIB ]]; then
    tell git clone --recursive git://github.com/thp/psmoveapi.git
    tell cd $PSMOVELIB

    # Patch if asked
    [[ "$1" == "--patch" ]] && patch_psmoveapi
  else
    tell cd $PSMOVELIB
  fi

  # Make a build directory
  [[ ! -d $BUILD ]] && tell mkdir $BUILD
  tell cd $BUILD

  # Make the psmoveapi
  tell cmake .. \
    -DPYTHON_INCLUDE_DIR=$PYTHON_INCLUDE_DIR \
    -DPYTHON_INCLUDE_PATH=$PYTHON_INCLUDE_PATH \
    -DPSMOVE_BUILD_EXAMPLES=OFF \
    -DPSMOVE_BUILD_OPENGL_EXAMPLES=OFF \
    -DPSMOVE_BUILD_TESTS=OFF \
    && make || return
}

function main() {
  # Install the psmoveapi
  psmoveapi $@
}

main $@
