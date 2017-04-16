# sources.sh
# aoneill - 04/16/17

# This pulls the sources for running the rackets program

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

function tell() { echo "$@"; $@; }

LIBS=libs
BUILD=build
PATCHES=patches

PYTHON_INCLUDE_DIR=/usr/include/python2.7
PYTHON_INCLUDE_PATH=$PYTHON_INCLUDE_DIR

PSMOVELIB=psmoveapi

function patch_psmoveapi() {
  cd $LIBS/$PSMOVELIB

  tell patch -p1 -i "$DIR/$PATCHES/fix-opencv-headers.patch"
  tell patch -p1 -i "$DIR/$PATCHES/add-libv4l2-module.patch"
}

function psmoveapi() {
  [[ ! -d "$DIR/$LIBS" ]] && tell mkdir -p "$DIR/$LIBS"
  tell cd "$DIR/$LIBS"

  if [[ ! -d $PSMOVELIB ]]; then
    tell git clone --recursive git://github.com/thp/psmoveapi.git
    tell cd $PSMOVELIB

    [[ "$1" == "--patch" ]] && patch_psmoveapi
  else
    tell cd $PSMOVELIB
  fi

  [[ ! -d $BUILD ]] && tell mkdir $BUILD
  tell cd $BUILD

  tell cmake .. \
    -DPYTHON_INCLUDE_DIR=$PYTHON_INCLUDE_DIR \
    -DPYTHON_INCLUDE_PATH=$PYTHON_INCLUDE_PATH \
    -DPSMOVE_BUILD_EXAMPLES=OFF \
    -DPSMOVE_BUILD_OPENGL_EXAMPLES=OFF \
    -DPSMOVE_BUILD_TESTS=OFF \
    && make || return

  cd ../../..
}

function main() {
  psmoveapi $@
}

main $@
