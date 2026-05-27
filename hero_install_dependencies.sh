#!/bin/bash

cd "$HOME"
sudo apt update
sudo apt install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
libffi-dev liblzma-dev git
curl https://pyenv.run | bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
pyenv install 3.11.9
cd "$PYENV_ROOT/versions/3.11.9/bin"
./python pip uninstall protobuf urllib3
./python pip install mediapipe==0.10.11 vosk pyaudio pyttsx3 opencv-python \
langchain langchain_openai langchain_ollama langchain_huggingface python-dotenv \
chromadb langchain_community sentence-transformers PyOpenGL PyOpenGL_accelerate PySDL3 \
"protobuf>=3.20.3,<4.21.0" "urllib3<2.0" requests piper-tts
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama.service
ollama run llama3.2:1b