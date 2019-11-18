with import <nixpkgs> {};
with pkgs.python36Packages;

stdenv.mkDerivation {
  name = "impurePythonEnv";
  buildInputs = [
    # install python and virtualenv
    python36Full
    python36Packages.virtualenv
    python36Packages.setuptools
    freetype
    git
    openssl
    libffi
    libpng12
    libzip
    lxml
    nodejs-10_x
    stdenv
    taglib
    zlib
    # ide stuff
    python36Packages.jedi
    python36Packages.importmagic
    python36Packages.autopep8
    python36Packages.flake8
    python36Packages.pyflakes
  ];
  src = null;
  shellHook = ''
    ## set SOURCE_DATE_EPOCH so that we can use python wheels
    SOURCE_DATE_EPOCH=$(date +%s)
    virtualenv --no-setuptools _virtualenv >&2
    export PATH=$PWD/_virtualenv/bin:$PATH
    pip install $(cat requirements.txt)
  '';
}
