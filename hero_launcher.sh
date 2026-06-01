#!/bin/bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
DIR="$(dirname "$(realpath "$0")")"
"$PYENV_ROOT/versions/3.11.9/bin/python" "$DIR/main.py"