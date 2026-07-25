{ pkgs, ... }:

let 
  pname = "tornium_oc_graph";
  version = "0.2.0";
in {
  tornium_oc_graph_pkg = pkgs.python313Packages.buildPythonPackage rec {
    inherit pname version;
    pyproject = true;

    src = pkgs.fetchFromGitHub {
      owner = "Tornium";
      repo = "tornium_oc_graph";
      rev = "v0.2.0";
      hash = "sha256-YVgJp68mQFthOQe6hh8+u6ysDQAHlPLwiBa0Nj0l3FI=";
    };

    buildInputs = [
      pkgs.python313Packages.scikit-build-core
      pkgs.stdenv.cc.cc.lib
    ];
    nativeBuildInputs = [
      pkgs.autoPatchelfHook
      pkgs.python313Packages.scikit-build-core
      pkgs.cmake
      pkgs.ninja
    ];

    build-system = with pkgs.python313Packages; [ scikit-build-core ];

    # Disable CMake phases from nixpkgs
    dontUseCmakeConfigure = true;
    dontUseCmakeBuild = true;
    dontUseCmakeInstall = true;

    propagatedBuildInputs = [ pkgs.stdenv.cc.cc.lib ];
    pythonImportCheck = [ "tornium_oc_graph" ];
  };
}
