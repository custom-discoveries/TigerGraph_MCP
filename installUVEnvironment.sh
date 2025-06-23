#!/bin/bash
#******************************************************************************
# Copyright (c) 2025, Custom Discoveries Inc.
# All rights reserved.
#installUVEnvironment.sh: Bash shell seteup python3 Virtual Environment
#******************************************************************************
version=3.12
echo "************************************************"
echo "Installing Python Environment $version (.venv)"
echo "************************************************"

echo `python$version -V`

if [ -d `pwd`/.venv ]; then
  #echo "run at command prompt: source \`pwd\`/.venv/bin/activate"
  source `pwd`/.venv/bin/activate
else
  echo "***************************************"
  echo "Creating .venv Environment...for Python Verson: $version"
  echo "Installing requirements.txt"
  echo "***************************************"
  uv init --bare
  uv venv
  source `pwd`/.venv/bin/activate
  uv pip install --upgrade pip
  uv pip install -U -r requirements.txt
fi
