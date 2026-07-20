{
  lib,
  beamPackages,
  cmake,
  extend,
  lexbor,
  fetchFromGitHub,
  oniguruma,
  overrides ? (x: y: { }),
  overrideFenixOverlay ? null,
  rustlerPrecompiledOverrides ? { },
  pkg-config,
  vips,
  writeText,
}:

let
  buildMix = lib.makeOverridable beamPackages.buildMix;
  buildRebar3 = lib.makeOverridable beamPackages.buildRebar3;

  workarounds = {
    portCompiler = _unusedArgs: old: {
      buildPlugins = [ beamPackages.pc ];
    };

    rustlerPrecompiled =
      {
        toolchain ? null,
        buildInputs ? [ ],
        nativeBuildInputs ? [ ],
        env ? { },
        ...
      }:
      old:
      let
        extendedPkgs = extend fenixOverlay;
        fenixOverlay =
          if overrideFenixOverlay == null then
            import "${
              fetchTarball {
                url = "https://github.com/nix-community/fenix/archive/6399553b7a300c77e7f07342904eb696a5b6bf9d.tar.gz";
                sha256 = "sha256-C6tT7K1Lx6VsYw1BY5S3OavtapUvEnDQtmQB5DSgbCc=";
              }
            }/overlay.nix"
          else
            overrideFenixOverlay;
        nativeDir = "${old.src}/native/${with builtins; head (attrNames (readDir "${old.src}/native"))}";
        fenix =
          if toolchain == null then
            extendedPkgs.fenix.stable
          else
            extendedPkgs.fenix.fromToolchainName toolchain;
        native =
          (
            (extendedPkgs.makeRustPlatform {
              inherit (fenix) cargo rustc;
            }).buildRustPackage
            {
              inherit env buildInputs;
              pname = "${old.beamModuleName}-native";
              version = old.version;
              src = nativeDir;
              cargoLock = {
                lockFile = "${nativeDir}/Cargo.lock";
              };
              nativeBuildInputs = [ extendedPkgs.cmake ] ++ nativeBuildInputs;
              doCheck = false;
            }
          ).overrideAttrs
            rustlerPrecompiledOverrides.${old.beamModuleName} or { };

      in
      {
        nativeBuildInputs = [ extendedPkgs.cargo ];

        env.RUSTLER_PRECOMPILED_FORCE_BUILD_ALL = "true";
        env.RUSTLER_PRECOMPILED_GLOBAL_CACHE_PATH = "unused-but-required";

        preConfigure = ''
          mkdir -p priv/native
          for lib in ${native}/lib/*
          do
            dest="$(basename "$lib")"
            if [[ "''${dest##*.}" = "dylib" ]]
            then
              dest="''${dest%.dylib}.so"
            fi
            ln -s "$lib" "priv/native/$dest"
          done
        '';

        preBuild = ''
          suggestion() {
            echo "***********************************************"
            echo "                 deps_nix                      "
            echo
            echo " Rust dependency build failed.                 "
            echo
            echo " If you saw network errors, you might need     "
            echo " to disable compilation on the appropriate     "
            echo " RustlerPrecompiled module in your             "
            echo " application config.                           "
            echo
            echo " We think you need this:                       "
            echo
            echo -n " "
            grep -Rl 'use RustlerPrecompiled' lib \
              | xargs grep 'defmodule' \
              | sed 's/defmodule \(.*\) do/config :${old.beamModuleName}, \1, skip_compilation?: true/'
            echo "***********************************************"
            exit 1
          }
          trap suggestion ERR
        '';
      };

    elixirMake = _unusedArgs: old: {
      preConfigure = ''
        export ELIXIR_MAKE_CACHE_DIR="$TEMPDIR/elixir_make_cache"
      '';
    };

    lazyHtml = _unusedArgs: old: {
      preConfigure = ''
        export ELIXIR_MAKE_CACHE_DIR="$TEMPDIR/elixir_make_cache"
      '';

      postPatch = ''
        substituteInPlace mix.exs \
          --replace-fail "Fine.include_dir()" '"${packages.fine}/src/c_include"' \
          --replace-fail '@lexbor_git_sha "244b84956a6dc7eec293781d051354f351274c46"' '@lexbor_git_sha ""'
      '';

      preBuild = ''
        install -Dm644           -t _build/c/third_party/lexbor/$LEXBOR_GIT_SHA/build           ${lexbor}/lib/liblexbor_static.a
      '';
    };
  };

  defaultOverrides = (
    final: prev:

    let
      apps = {
        crc32cer = [
          {
            name = "portCompiler";
          }
        ];
        explorer = [
          {
            name = "rustlerPrecompiled";
            toolchain = {
              name = "nightly-2025-06-23";
              sha256 = "sha256-UAoZcxg3iWtS+2n8TFNfANFt/GmkuOMDf7QAE0fRxeA=";
            };
          }
        ];
        snappyer = [
          {
            name = "portCompiler";
          }
        ];
      };

      applyOverrides =
        appName: drv:
        let
          allOverridesForApp = builtins.foldl' (
            acc: workaround: acc // (workarounds.${workaround.name} workaround) drv
          ) { } apps.${appName};

        in
        if builtins.hasAttr appName apps then drv.override allOverridesForApp else drv;

    in
    builtins.mapAttrs applyOverrides prev
  );

  self = packages // (defaultOverrides self packages) // (overrides self packages);

  packages =
    with beamPackages;
    with self;
    {

      bandit =
        let
          version = "1.12.0";
          drv = buildMix {
            inherit version;
            name = "bandit";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "bandit";
              sha256 = "45dac82dc86f45cf4a196dee9cc5a8b791d9c9469d996055f055e6ee36c66e20";
            };

            beamDeps = [
              hpax
              plug
              telemetry
              thousand_island
              websock
            ];
          };
        in
        drv;

      castle =
        let
          version = "0.3.1";
          drv = buildMix {
            inherit version;
            name = "castle";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "castle";
              sha256 = "3ee9ca04b069280ab4197fe753562958729c83b3aa08125255116a989e133835";
            };

            beamDeps = [
              forecastle
            ];
          };
        in
        drv;

      castore =
        let
          version = "1.0.20";
          drv = buildMix {
            inherit version;
            name = "castore";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "castore";
              sha256 = "940eafbfd8b14bee649f083bc11b3b54ec555b54c3e4ea8213351ff6fee39c10";
            };
          };
        in
        drv;

      certifi =
        let
          version = "2.16.0";
          drv = buildRebar3 {
            inherit version;
            name = "certifi";

            src = fetchHex {
              inherit version;
              pkg = "certifi";
              sha256 = "8a64f6669d85e9cc0e5086fcf29a5b13de57a13efa23d3582874b9a19303f184";
            };
          };
        in
        drv;

      cowboy =
        let
          version = "2.17.0";
          drv = buildRebar3 {
            inherit version;
            name = "cowboy";

            src = fetchHex {
              inherit version;
              pkg = "cowboy";
              sha256 = "84f0e4c9d5820342cd506472052b79336d0d9d3624e46303f6d0af9dc94e8d5f";
            };

            beamDeps = [
              cowlib
              ranch
            ];
          };
        in
        drv;

      cowboy_telemetry =
        let
          version = "0.4.0";
          drv = buildRebar3 {
            inherit version;
            name = "cowboy_telemetry";

            src = fetchHex {
              inherit version;
              pkg = "cowboy_telemetry";
              sha256 = "7d98bac1ee4565d31b62d59f8823dfd8356a169e7fcbb83831b8a5397404c9de";
            };

            beamDeps = [
              cowboy
              telemetry
            ];
          };
        in
        drv;

      cowlib =
        let
          version = "2.18.0";
          drv = buildRebar3 {
            inherit version;
            name = "cowlib";

            src = fetchHex {
              inherit version;
              pkg = "cowlib";
              sha256 = "c4f89d33a61162d4cfdcb5a1af7e562d80a700b2573cc71020ce6521b152dc1a";
            };
          };
        in
        drv;

      crontab =
        let
          version = "1.2.0";
          drv = buildMix {
            inherit version;
            name = "crontab";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "crontab";
              sha256 = "ebd7ef4d831e1b20fa4700f0de0284a04cac4347e813337978e25b4cc5cc2207";
            };

            beamDeps = [
              ecto
            ];
          };
        in
        drv;

      db_connection =
        let
          version = "2.10.2";
          drv = buildMix {
            inherit version;
            name = "db_connection";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "db_connection";
              sha256 = "510b14482330f1af6490a2fa0efd8d4f1435d1529b165647df22ac0f2df0fa93";
            };

            beamDeps = [
              telemetry
            ];
          };
        in
        drv;

      decimal =
        let
          version = "3.1.1";
          drv = buildMix {
            inherit version;
            name = "decimal";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "decimal";
              sha256 = "c5f25f2ced74a0587d03e6023f595db8e924c9d3922c8c8ffd9edfc4498cf1f6";
            };
          };
        in
        drv;

      delta_crdt =
        let
          version = "0.6.5";
          drv = buildMix {
            inherit version;
            name = "delta_crdt";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "delta_crdt";
              sha256 = "c6ae23a525d30f96494186dd11bf19ed9ae21d9fe2c1f1b217d492a7cc7294ae";
            };

            beamDeps = [
              merkle_map
              telemetry
            ];
          };
        in
        drv;

      ecto =
        let
          version = "3.14.1";
          drv = buildMix {
            inherit version;
            name = "ecto";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "ecto";
              sha256 = "24b991956796700f467d0a3ef3d303138a3ef9ddddf8b98f43758ee067b20a30";
            };

            beamDeps = [
              decimal
              jason
              telemetry
            ];
          };
        in
        drv;

      ecto_sql =
        let
          version = "3.14.0";
          drv = buildMix {
            inherit version;
            name = "ecto_sql";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "ecto_sql";
              sha256 = "f4d8d36faf294c9417b5a37ec7ac8217ee2abdef5fcf197ba690f361548d3949";
            };

            beamDeps = [
              db_connection
              decimal
              ecto
              postgrex
              telemetry
            ];
          };
        in
        drv;

      finch =
        let
          version = "0.23.0";
          drv = buildMix {
            inherit version;
            name = "finch";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "finch";
              sha256 = "80e58d3f936f57e3fdf404f83a3642897ae6d9fb642934e46da4d8fe761b99d5";
            };

            beamDeps = [
              mime
              mint
              nimble_options
              nimble_pool
              telemetry
            ];
          };
        in
        drv;

      floki =
        let
          version = "0.38.4";
          drv = buildMix {
            inherit version;
            name = "floki";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "floki";
              sha256 = "bdb34645eee8e79845c7edaca2d4099a52804ee4d4a3ecc683a69451f0244973";
            };
          };
        in
        drv;

      forecastle =
        let
          version = "0.1.3";
          drv = buildMix {
            inherit version;
            name = "forecastle";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "forecastle";
              sha256 = "07e1ffa79c56f3e0ead59f17c0163a747dafc210ca8f244a7e65a4bfa98dc96d";
            };
          };
        in
        drv;

      gun =
        let
          version = "2.4.1";
          drv = buildRebar3 {
            inherit version;
            name = "gun";

            src = fetchHex {
              inherit version;
              pkg = "gun";
              sha256 = "1450575b4d393aa0811322727b90ad1dd94b5c10026f54a1641785bcbd250384";
            };

            beamDeps = [
              cowlib
            ];
          };
        in
        drv;

      horde =
        let
          version = "0.10.0";
          drv = buildMix {
            inherit version;
            name = "horde";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "horde";
              sha256 = "0b51c435cb698cac9bf9c17391dce3ebb1376ae6154c81f077fc61db771b9432";
            };

            beamDeps = [
              delta_crdt
              libring
              telemetry
              telemetry_poller
            ];
          };
        in
        drv;

      hpax =
        let
          version = "1.0.4";
          drv = buildMix {
            inherit version;
            name = "hpax";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "hpax";
              sha256 = "afc7cb142ebcc2d01ce7816190b98ce5dd49e799111b24249f3443d730f377ca";
            };
          };
        in
        drv;

      jason =
        let
          version = "1.4.5";
          drv = buildMix {
            inherit version;
            name = "jason";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "jason";
              sha256 = "b0c823996102bcd0239b3c2444eb00409b72f6a140c1950bc8b457d836b30684";
            };

            beamDeps = [
              decimal
            ];
          };
        in
        drv;

      libcluster =
        let
          version = "3.5.0";
          drv = buildMix {
            inherit version;
            name = "libcluster";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "libcluster";
              sha256 = "ebf6561fcedd765a4cd43b4b8c04b1c87f4177b5fb3cbdfe40a780499d72f743";
            };

            beamDeps = [
              jason
              telemetry
            ];
          };
        in
        drv;

      libcluster_postgres =
        let
          version = "0.2.0";
          drv = buildMix {
            inherit version;
            name = "libcluster_postgres";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "libcluster_postgres";
              sha256 = "ab2e952371c5a0a0fcb263216c7eae2a2267977b3bb3236650daed3054a93edd";
            };

            beamDeps = [
              libcluster
              postgrex
            ];
          };
        in
        drv;

      libring =
        let
          version = "1.7.0";
          drv = buildMix {
            inherit version;
            name = "libring";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "libring";
              sha256 = "070e3593cb572e04f2c8470dd0c119bc1817a7a0a7f88229f43cf0345268ec42";
            };
          };
        in
        drv;

      logger_json =
        let
          version = "7.0.4";
          drv = buildMix {
            inherit version;
            name = "logger_json";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "logger_json";
              sha256 = "d1369f8094e372db45d50672c3b91e8888bcd695fdc444a37a0734e96717c45c";
            };

            beamDeps = [
              decimal
              ecto
              jason
              plug
              telemetry
            ];
          };
        in
        drv;

      lua =
        let
          version = "0.4.0";
          drv = buildMix {
            inherit version;
            name = "lua";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "lua";
              sha256 = "648e17ab9faa1ab1a788fa58ed608366a7026d0eeaec2f311510c065817c4067";
            };

            beamDeps = [
              luerl
            ];
          };
        in
        drv;

      luerl =
        let
          version = "1.5.1";
          drv = buildRebar3 {
            inherit version;
            name = "luerl";

            src = fetchHex {
              inherit version;
              pkg = "luerl";
              sha256 = "abf88d849baa0d5dca93b245a8688d4de2ee3d588159bb2faf51e15946509390";
            };
          };
        in
        drv;

      merkle_map =
        let
          version = "0.2.2";
          drv = buildMix {
            inherit version;
            name = "merkle_map";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "merkle_map";
              sha256 = "383107f0503f230ac9175e0631647c424efd027e89ea65ab5ea12eeb54257aaf";
            };
          };
        in
        drv;

      mime =
        let
          version = "2.0.7";
          drv = buildMix {
            inherit version;
            name = "mime";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "mime";
              sha256 = "6171188e399ee16023ffc5b76ce445eb6d9672e2e241d2df6050f3c771e80ccd";
            };
          };
        in
        drv;

      mint =
        let
          version = "1.9.3";
          drv = buildMix {
            inherit version;
            name = "mint";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "mint";
              sha256 = "5f7c9342480c069dbbc4eeac3490303c9e01870ff01a7f1d29b6107054fc1e74";
            };

            beamDeps = [
              castore
              hpax
            ];
          };
        in
        drv;

      nimble_options =
        let
          version = "1.1.1";
          drv = buildMix {
            inherit version;
            name = "nimble_options";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "nimble_options";
              sha256 = "821b2470ca9442c4b6984882fe9bb0389371b8ddec4d45a9504f00a66f650b44";
            };
          };
        in
        drv;

      nimble_parsec =
        let
          version = "1.4.2";
          drv = buildMix {
            inherit version;
            name = "nimble_parsec";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "nimble_parsec";
              sha256 = "4b21398942dda052b403bbe1da991ccd03a053668d147d53fb8c4e0efe09c973";
            };
          };
        in
        drv;

      nimble_pool =
        let
          version = "1.1.0";
          drv = buildMix {
            inherit version;
            name = "nimble_pool";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "nimble_pool";
              sha256 = "af2e4e6b34197db81f7aad230c1118eac993acc0dae6bc83bac0126d4ae0813a";
            };
          };
        in
        drv;

      nostrum =
        let
          version = "0.11.0-dev";
          drv = buildMix {
            inherit version;
            name = "nostrum";
            appConfigPath = ./config;

            src = fetchFromGitHub {
              owner = "dssecret";
              repo = "nostrum";
              rev = "b1ef88e6268decec083ad49171448cf39c83e533";
              hash = "sha256-LSLEYSQfYJYxvyLMV/rWrWgzG+hPOkUyNVHYo25ejmA=";
            };

            beamDeps = [
              jason
              gun
              salchicha
              certifi
              mime
              telemetry
              castle
              sourceror
            ];
          };
        in
        drv;

      oban =
        let
          version = "2.23.0";
          drv = buildMix {
            inherit version;
            name = "oban";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "oban";
              sha256 = "8e5f0cec5abecce78dd08cb14dc5438db90ec3884987b44773ce76fe60dd3f81";
            };

            beamDeps = [
              ecto_sql
              jason
              postgrex
              telemetry
            ];
          };
        in
        drv;

      oban_met =
        let
          version = "1.2.0";
          drv = buildMix {
            inherit version;
            name = "oban_met";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "oban_met";
              sha256 = "5c81fd33beeb172603cf83bea760298eeb8709d584fbe79ae2d07b09917d6110";
            };

            beamDeps = [
              oban
            ];
          };
        in
        drv;

      oban_web =
        let
          version = "2.12.6";
          drv = buildMix {
            inherit version;
            name = "oban_web";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "oban_web";
              sha256 = "1ade7bbbde1a731c9e4aa23f9f7c8a3f2871e734c6bc46fa4e4384688a69921d";
            };

            beamDeps = [
              jason
              oban
              oban_met
              phoenix
              phoenix_html
              phoenix_live_view
              phoenix_pubsub
            ];
          };
        in
        drv;

      octo_fetch =
        let
          version = "0.5.0";
          drv = buildMix {
            inherit version;
            name = "octo_fetch";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "octo_fetch";
              sha256 = "6226cc3c14ca948ee9f25fb0446322e5c288e215da9beba7899b6b5f4cd3ccb0";
            };

            beamDeps = [
              castore
              ssl_verify_fun
            ];
          };
        in
        drv;

      peep =
        let
          version = "4.4.0";
          drv = buildMix {
            inherit version;
            name = "peep";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "peep";
              sha256 = "f289959a9e5fcf92f5a4becaf4dd0df95c58841368f6ad0574b8ea830a7c1453";
            };

            beamDeps = [
              nimble_options
              plug
              telemetry
              telemetry_metrics
            ];
          };
        in
        drv;

      phoenix =
        let
          version = "1.8.9";
          drv = buildMix {
            inherit version;
            name = "phoenix";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "phoenix";
              sha256 = "3477e2dd5a4f61820341169031bdfe21275f659923bea9c5c0ea2aa1c3fcc046";
            };

            beamDeps = [
              bandit
              jason
              phoenix_pubsub
              phoenix_template
              plug
              plug_cowboy
              plug_crypto
              telemetry
              websock_adapter
            ];
          };
        in
        drv;

      phoenix_html =
        let
          version = "4.3.0";
          drv = buildMix {
            inherit version;
            name = "phoenix_html";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "phoenix_html";
              sha256 = "3eaa290a78bab0f075f791a46a981bbe769d94bc776869f4f3063a14f30497ad";
            };
          };
        in
        drv;

      phoenix_live_view =
        let
          version = "1.2.7";
          drv = buildMix {
            inherit version;
            name = "phoenix_live_view";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "phoenix_live_view";
              sha256 = "61e97938a4fcca6d6f2c836925623abf2f52a572cc8c6085e4074f3f6337e0eb";
            };

            beamDeps = [
              jason
              phoenix
              phoenix_html
              phoenix_template
              plug
              telemetry
            ];
          };
        in
        drv;

      phoenix_pubsub =
        let
          version = "2.2.0";
          drv = buildMix {
            inherit version;
            name = "phoenix_pubsub";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "phoenix_pubsub";
              sha256 = "adc313a5bf7136039f63cfd9668fde73bba0765e0614cba80c06ac9460ff3e96";
            };
          };
        in
        drv;

      phoenix_template =
        let
          version = "1.0.4";
          drv = buildMix {
            inherit version;
            name = "phoenix_template";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "phoenix_template";
              sha256 = "2c0c81f0e5c6753faf5cca2f229c9709919aba34fab866d3bc05060c9c444206";
            };

            beamDeps = [
              phoenix_html
            ];
          };
        in
        drv;

      plug =
        let
          version = "1.20.3";
          drv = buildMix {
            inherit version;
            name = "plug";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "plug";
              sha256 = "be266aee1b8536ef6409d58cf39a3121319f0ec47cfa1b24024485aa0e76ad76";
            };

            beamDeps = [
              mime
              plug_crypto
              telemetry
            ];
          };
        in
        drv;

      plug_cowboy =
        let
          version = "2.9.0";
          drv = buildMix {
            inherit version;
            name = "plug_cowboy";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "plug_cowboy";
              sha256 = "2002bafba4f3a45b55a58e68d70211b153a7ed18d37edb1ceb6e96e7a92c422e";
            };

            beamDeps = [
              cowboy
              cowboy_telemetry
              plug
            ];
          };
        in
        drv;

      plug_crypto =
        let
          version = "2.1.1";
          drv = buildMix {
            inherit version;
            name = "plug_crypto";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "plug_crypto";
              sha256 = "6470bce6ffe41c8bd497612ffde1a7e4af67f36a15eea5f921af71cf3e11247c";
            };
          };
        in
        drv;

      postgrex =
        let
          version = "0.22.3";
          drv = buildMix {
            inherit version;
            name = "postgrex";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "postgrex";
              sha256 = "f018c13752b2b46e8d35d7e2d84c3276557cbfd880769109021a1d0ee36c1cfe";
            };

            beamDeps = [
              db_connection
              decimal
              jason
            ];
          };
        in
        drv;

      prom_ex =
        let
          version = "1.12.0";
          drv = buildMix {
            inherit version;
            name = "prom_ex";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "prom_ex";
              sha256 = "6357484941489ba2fee64bb1e9f2a1e86309545304f9e90144e3c10e553c958b";
            };

            beamDeps = [
              ecto
              finch
              jason
              oban
              octo_fetch
              peep
              phoenix
              phoenix_live_view
              plug
              plug_cowboy
              telemetry
              telemetry_metrics
              telemetry_metrics_prometheus_core
              telemetry_poller
            ];
          };
        in
        drv;

      ranch =
        let
          version = "2.2.0";
          drv = buildRebar3 {
            inherit version;
            name = "ranch";

            src = fetchHex {
              inherit version;
              pkg = "ranch";
              sha256 = "fa0b99a1780c80218a4197a59ea8d3bdae32fbff7e88527d7d8a4787eff4f8e7";
            };
          };
        in
        drv;

      salchicha =
        let
          version = "0.5.0";
          drv = buildMix {
            inherit version;
            name = "salchicha";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "salchicha";
              sha256 = "b3e0575cd5a01672d9cefc4ec50bd56662a4d970e2ae39d8de6cf82f09012fc8";
            };
          };
        in
        drv;

      solid =
        let
          version = "0.18.0";
          drv = buildMix {
            inherit version;
            name = "solid";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "solid";
              sha256 = "7704681c11c880308fe1337acf7690083f884076b612d38b7dccb5a1bd016068";
            };

            beamDeps = [
              nimble_parsec
            ];
          };
        in
        drv;

      sourceror =
        let
          version = "1.12.0";
          drv = buildMix {
            inherit version;
            name = "sourceror";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "sourceror";
              sha256 = "755703683bd014ebcd5de9acc24b68fb874a660a568d1d63f8f98cd8a6ef9cd0";
            };
          };
        in
        drv;

      ssl_verify_fun =
        let
          version = "1.1.7";
          drv = buildMix {
            inherit version;
            name = "ssl_verify_fun";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "ssl_verify_fun";
              sha256 = "fe4c190e8f37401d30167c8c405eda19469f34577987c76dde613e838bbc67f8";
            };
          };
        in
        drv;

      telemetry =
        let
          version = "1.4.2";
          drv = buildRebar3 {
            inherit version;
            name = "telemetry";

            src = fetchHex {
              inherit version;
              pkg = "telemetry";
              sha256 = "928f6495066506077862c0d1646609eed891a4326bee3126ba54b60af61febb1";
            };
          };
        in
        drv;

      telemetry_metrics =
        let
          version = "1.1.0";
          drv = buildMix {
            inherit version;
            name = "telemetry_metrics";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "telemetry_metrics";
              sha256 = "e7b79e8ddfde70adb6db8a6623d1778ec66401f366e9a8f5dd0955c56bc8ce67";
            };

            beamDeps = [
              telemetry
            ];
          };
        in
        drv;

      telemetry_metrics_prometheus_core =
        let
          version = "1.2.1";
          drv = buildMix {
            inherit version;
            name = "telemetry_metrics_prometheus_core";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "telemetry_metrics_prometheus_core";
              sha256 = "5e2c599da4983c4f88a33e9571f1458bf98b0cf6ba930f1dc3a6e8cf45d5afb6";
            };

            beamDeps = [
              telemetry
              telemetry_metrics
            ];
          };
        in
        drv;

      telemetry_poller =
        let
          version = "1.3.0";
          drv = buildRebar3 {
            inherit version;
            name = "telemetry_poller";

            src = fetchHex {
              inherit version;
              pkg = "telemetry_poller";
              sha256 = "51f18bed7128544a50f75897db9974436ea9bfba560420b646af27a9a9b35211";
            };

            beamDeps = [
              telemetry
            ];
          };
        in
        drv;

      thousand_island =
        let
          version = "1.5.0";
          drv = buildMix {
            inherit version;
            name = "thousand_island";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "thousand_island";
              sha256 = "708923d40523e43cf99041ab37a0d4b0ec426ac6438fa3716ab23d919eaeb412";
            };

            beamDeps = [
              telemetry
            ];
          };
        in
        drv;

      tornex =
        let
          version = "0.6.1-dev";
          drv = buildMix {
            inherit version;
            name = "tornex";
            appConfigPath = ./config;

            src = fetchFromGitHub {
              owner = "Tornium";
              repo = "Tornex";
              rev = "6f56a185d6bdbcdc923c2285b10b55060254177f";
              hash = "sha256-1V+5kKFn8+QrtKTDX4DUUCPxEozPdk0nH/Y5/S8LDnc=";
            };

            beamDeps = [
              horde
              finch
              telemetry
              prom_ex
              plug_cowboy
              torngen_elixir_client
              torngen
            ];
          };
        in
        drv;

      torngen =
        let
          version = "0.1.11";
          drv = buildMix {
            inherit version;
            name = "torngen";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "torngen";
              sha256 = "d6c087af5dee1d5951fcee72fddd0dbe92c11485a0b9d047a6ccb0f5ef13f04c";
            };

            beamDeps = [
              plug
            ];
          };
        in
        drv;

      torngen_elixir_client =
        let
          version = "6.1.1";
          drv = buildMix {
            inherit version;
            name = "torngen_elixir_client";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "torngen_elixir_client";
              sha256 = "b7aa5bdfb886df63e223adaa9f1ad774c4415e1c81024828e6260cfd65c9daf5";
            };

            beamDeps = [
              torngen
            ];
          };
        in
        drv;

      websock =
        let
          version = "0.5.3";
          drv = buildMix {
            inherit version;
            name = "websock";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "websock";
              sha256 = "6105453d7fac22c712ad66fab1d45abdf049868f253cf719b625151460b8b453";
            };
          };
        in
        drv;

      websock_adapter =
        let
          version = "0.6.0";
          drv = buildMix {
            inherit version;
            name = "websock_adapter";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "websock_adapter";
              sha256 = "50021a85bce8f203b086705d9e0c5415e2c7eb05d319111b0428fe71f9934617";
            };

            beamDeps = [
              bandit
              plug
              plug_cowboy
              websock
            ];
          };
        in
        drv;

    };
in
self
