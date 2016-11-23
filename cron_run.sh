#!/bin/sh -eux

THIS_SCRIPT=$0
THIS_DIR=$(dirname ${THIS_SCRIPT})

DATA_REPO="${THIS_DIR}/../liverpool-planning-data"

pull_data_repo() {
  cd "${DATA_REPO}"
  git fetch
  git checkout master
  git reset --hard origin/master
  cd -
}

activate_virtualenv() {
    set +u
    . "${THIS_DIR}/venv/bin/activate"
    set -u

    pip install -r "${THIS_DIR}/requirements.txt"
}

make_database_if_missing() {
  if [ ! -s "${THIS_DIR}/db.sqlite" ]; then
    cd "${THIS_DIR}"
    make createdb
    cd -
  fi
}


run() {
    export PATH=${THIS_DIR}/vendor/firefox-45.0.2:$PATH

    FIREFOX_VERSION=$(xvfb-run firefox --version)
    if [ "${FIREFOX_VERSION}" != "Mozilla Firefox 45.0.2" ]; then
      echo "Unsupported Firefox version, sorry"
      exit 2
    fi

    cd "${THIS_DIR}"
    xvfb-run make run
}

push_data_repo() {
  cd "${DATA_REPO}"
  git add --all .
  git commit -m "Update CSV files."
  git push origin master:master
  cd -
}

pull_data_repo
activate_virtualenv
make_database_if_missing
run
push_data_repo
