#!/bin/bash

PRJ_NAME="twinpigs-architecture-compiler"
MAIN_FILE="puml2graphml.py"
EXEC_FILE="puml2graphml"

check_res_and_popd_on_exit () {
  if [[ $? -ne 0 ]]; then
    echo "Something has utterly failed!"
    popd
    echo "TERMINATING"
    exit 2
  fi
}

create_venv () {
  echo "Creating venv"
  VENV_PATH=`pwd`/venv
  pushd src
  python -m venv "${VENV_PATH}"
  check_res_and_popd_on_exit
  popd
}

set_version () {
  if [ "${PROGRAM_VERSION}" != "" ]; then
    echo "VERSION = \"${PROGRAM_VERSION}\"" >src/current_version.py
    cat src/current_version.py
  fi
}

activate_venv () {
  if [ "$OSTYPE" == "linux-gnu" ]; then
    echo "Linux venv activation"
    source venv/bin/activate
    PYSCRIPTS=`pwd`/venv/bin
  else
    echo "Windows venv activation"

    # Check if activator.py is missing in Scripts
    if [ ! -f venv/Scripts/activator.py ]; then
      # Try to copy from Scripts/nt if it exists
      if [ -f venv/Scripts/nt/activator.py ]; then
        cp venv/Scripts/nt/activator.py venv/Scripts/
      else
        # Fallback: copy your custom activator
        cp utils/activator.py venv/Scripts/activator.py
      fi
    fi

    venv/Scripts/python venv/Scripts/activator.py
    PYSCRIPTS="`pwd`/venv/Scripts"
  fi
}

install_requirements () {
  pushd .
  echo "Installing requirements"
  "${PYSCRIPTS}/pip" install -r requirements.txt
  check_res_and_popd_on_exit
  popd
}

prepare_gettext() {
  pushd venv
  if [[ "$OSTYPE" == "win32" || "$OSTYPE" == "msys" ]]; then
    echo "Preparing gettext tools for Windows..."

    if [[ ! -f gettext.zip ]]; then
      echo "Downloading gettext tools..."
      curl -L -o gettext.zip https://github.com/vslavik/gettext-tools-windows/releases/download/v0.26/gettext-tools-windows-0.26.zip
      check_res_and_popd_on_exit
    else
      echo "gettext.zip already exists, skipping download."
    fi

    echo "Extracting gettext tools..."
    unzip -o -q gettext.zip -d gettext-bin
    check_res_and_popd_on_exit

    export PATH="$(pwd)/gettext-bin/bin:$PATH"
    echo "Gettext tools added to PATH"
  fi
  popd
}

build_msgs () {
  echo "Building message files"
  pushd src
  find . -path './tests' -prune -o -name '*.py' -print0 | xargs -0 xgettext -n -o locales/messages.pot
  find locales -type f -name 'messages.po' | while read -r po_file; do
    # Получаем путь к .mo-файлу
    mo_file="${po_file%.po}.mo"

    # Обновляем .po из .pot
    msgmerge -N -U --backup=t "$po_file" locales/messages.pot

    # Компилируем .mo
    msgfmt -o "$mo_file" "$po_file"
  done
  check_res_and_popd_on_exit
  popd
}

run_tests () {
  echo "Running tests"
  pushd src/tests
  "${PYSCRIPTS}/python" run_tests.py
  check_res_and_popd_on_exit
  popd
}

run_mypy () {
  echo "Running Mypy"
  pushd src
  "${PYSCRIPTS}/mypy" --config-file mypy.ini .
  check_res_and_popd_on_exit
  popd
}

run_black() {
  echo "Reformatting the code with black"
  pushd src
  "${PYSCRIPTS}/black" .
  check_res_and_popd_on_exit
  popd
}

run_linter() {
  echo "Linting with flake8"
  pushd src
  "${PYSCRIPTS}/flake8" .
  check_res_and_popd_on_exit
  popd
}

pyinstaller_build () {
  echo "Building a PyInstaller executable"
  S=':'
  if [[ "$OSTYPE" == "win32" || "$OSTYPE" == "msys" ]]; then
       S=';'
  fi
  mkdir out
  pushd src
  rm -rf ../out/distr/${PRJ_NAME}
  rm -rf ../out/temp
  S=":"
  [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]] && S=";"
  DIST="../out/distr/${PRJ_NAME}"
  WORK="../out/temp"
  ADD_DATA=()
  while IFS= read -r -d '' f; do
    rel_dir="$(dirname "${f#./}")"
    ADD_DATA+=("--add-data" "$f${S}$rel_dir")
  done < <(find ./templates -type f -print0)

  while IFS= read -r -d '' f; do

    rel_dir="$(dirname "${f#./}")"
    ADD_DATA+=("--add-data" "$f${S}$rel_dir")
  done < <(find ./locales -type f -name '*.mo' -print0)

  echo "${PYSCRIPTS}/pyinstaller" -F --paths . \
    "${ADD_DATA[@]}" \
    --noconfirm \
    --distpath "${DIST}" \
    -p . \
    --workpath "${WORK}" \
    --clean "$MAIN_FILE"

  "${PYSCRIPTS}/pyinstaller" -F --paths . \
    "${ADD_DATA[@]}" \
    --noconfirm \
    --distpath "${DIST}" \
    -p . \
    --workpath "${WORK}" \
    --clean "${MAIN_FILE}"
  check_res_and_popd_on_exit
  popd
}

build_samples() {
  echo "Building samples"
  pushd samples
  run_prog="../out/distr/${PRJ_NAME}/$(basename "${MAIN_FILE%.*}")"
  while SRC= read -r -d '' f; do
    outfile="../out/distr/${PRJ_NAME}/$(basename "${f%.*}").graphml"
    echo "Compiling ${f} to ${outfile}"
    "${run_prog}" "$f" "${outfile}"
  done < <(find . -type f -name '*.puml' -print0)
  check_res_and_popd_on_exit
  popd
}
