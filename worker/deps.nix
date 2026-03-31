{
  lib,
  beamPackages,
  cmake,
  extend,
  lexbor,
  fetchFromGitHub,
  overrides ? (x: y: { }),
  overrideFenixOverlay ? null,
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
          (extendedPkgs.makeRustPlatform {
            inherit (fenix) cargo rustc;
          }).buildRustPackage
            {
              pname = "${old.packageName}-native";
              version = old.version;
              src = nativeDir;
              cargoLock = {
                lockFile = "${nativeDir}/Cargo.lock";
              };
              nativeBuildInputs = [
                extendedPkgs.cmake
              ];
              doCheck = false;
            };

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

        buildPhase = ''
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
              | sed 's/defmodule \(.*\) do/config :${old.packageName}, \1, skip_compilation?: true/'
            echo "***********************************************"
            exit 1
          }
          trap suggestion ERR
          ${old.buildPhase}
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
        substituteInPlace mix.exs           --replace-fail "Fine.include_dir()" '"${packages.fine}/src/c_include"'           --replace-fail '@lexbor_git_sha "244b84956a6dc7eec293781d051354f351274c46"' '@lexbor_git_sha ""'
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
          version = "1.10.4";
          drv = buildMix {
            inherit version;
            name = "bandit";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "bandit";
              sha256 = "a5faf501042ac1f31d736d9d4a813b3db4ef812e634583b6a457b0928798a51d";
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
          version = "1.0.18";
          drv = buildMix {
            inherit version;
            name = "castore";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "castore";
              sha256 = "f393e4fe6317829b158fb74d86eb681f737d2fe326aa61ccf6293c4104957e34";
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
          version = "2.14.2";
          drv = buildRebar3 {
            inherit version;
            name = "cowboy";

            src = fetchHex {
              inherit version;
              pkg = "cowboy";
              sha256 = "569081da046e7b41b5df36aa359be71a0c8874e5b9cff6f747073fc57baf1ab9";
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
          version = "2.16.0";
          drv = buildRebar3 {
            inherit version;
            name = "cowlib";

            src = fetchHex {
              inherit version;
              pkg = "cowlib";
              sha256 = "7f478d80d66b747344f0ea7708c187645cfcc08b11aa424632f78e25bf05db51";
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
          version = "2.9.0";
          drv = buildMix {
            inherit version;
            name = "db_connection";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "db_connection";
              sha256 = "17d502eacaf61829db98facf6f20808ed33da6ccf495354a41e64fe42f9c509c";
            };

            beamDeps = [
              telemetry
            ];
          };
        in
        drv;

      decimal =
        let
          version = "2.3.0";
          drv = buildMix {
            inherit version;
            name = "decimal";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "decimal";
              sha256 = "a4d66355cb29cb47c3cf30e71329e58361cfcb37c34235ef3bf1d7bf3773aeac";
            };
          };
        in
        drv;

      ecto =
        let
          version = "3.13.5";
          drv = buildMix {
            inherit version;
            name = "ecto";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "ecto";
              sha256 = "df9efebf70cf94142739ba357499661ef5dbb559ef902b68ea1f3c1fabce36de";
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
          version = "3.13.5";
          drv = buildMix {
            inherit version;
            name = "ecto_sql";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "ecto_sql";
              sha256 = "aa36751f4e6a2b56ae79efb0e088042e010ff4935fc8684e74c23b1f49e25fdc";
            };

            beamDeps = [
              db_connection
              ecto
              postgrex
              telemetry
            ];
          };
        in
        drv;

      finch =
        let
          version = "0.21.0";
          drv = buildMix {
            inherit version;
            name = "finch";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "finch";
              sha256 = "87dc6e169794cb2570f75841a19da99cfde834249568f2a5b121b809588a4377";
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
          version = "0.38.1";
          drv = buildMix {
            inherit version;
            name = "floki";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "floki";
              sha256 = "e744bf0db7ee34b2c8b62767f04071107af0516a81144b9a2f73fe0494200e5b";
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
          version = "2.2.0";
          drv = buildRebar3 {
            inherit version;
            name = "gun";

            src = fetchHex {
              inherit version;
              pkg = "gun";
              sha256 = "76022700c64287feb4df93a1795cff6741b83fb37415c40c34c38d2a4645261a";
            };

            beamDeps = [
              cowlib
            ];
          };
        in
        drv;

      hpax =
        let
          version = "1.0.3";
          drv = buildMix {
            inherit version;
            name = "hpax";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "hpax";
              sha256 = "8eab6e1cfa8d5918c2ce4ba43588e894af35dbd8e91e6e55c817bca5847df34a";
            };
          };
        in
        drv;

      jason =
        let
          version = "1.4.4";
          drv = buildMix {
            inherit version;
            name = "jason";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "jason";
              sha256 = "c5eb0cab91f094599f94d55bc63409236a8ec69a21a67814529e8d5f6cc90b3b";
            };

            beamDeps = [
              decimal
            ];
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
          version = "1.7.1";
          drv = buildMix {
            inherit version;
            name = "mint";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "mint";
              sha256 = "fceba0a4d0f24301ddee3024ae116df1c3f4bb7a563a731f45fdfeb9d39a231b";
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
              rev = "108219b016c9ae288ab8d14903ceacf69d9abb78";
              hash = "sha256-YhacWbHwhJH6nPr6snW1fmTk5/qnEErFMxnF7Zj63s0=";
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
          version = "2.21.1";
          drv = buildMix {
            inherit version;
            name = "oban";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "oban";
              sha256 = "8162a160924cf4a25905fed2a9242e7787d88e320e3b5b0dcf324eb17c51c4e6";
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
          version = "1.1.0";
          drv = buildMix {
            inherit version;
            name = "oban_met";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "oban_met";
              sha256 = "535af16a369f94c1ef31b15f4d5de991b07c105eb8689061b326183c52ba6793";
            };

            beamDeps = [
              oban
            ];
          };
        in
        drv;

      oban_web =
        let
          version = "2.12.1";
          drv = buildMix {
            inherit version;
            name = "oban_web";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "oban_web";
              sha256 = "d6ee45d6e8c5ed9fbb6213a6cb22870055c0f52eee6f437281e935cf92c408d7";
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
          version = "3.5.0";
          drv = buildMix {
            inherit version;
            name = "peep";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "peep";
              sha256 = "5a73a99c6e60062415efeb7e536a663387146463a3d3df1417da31fd665ac210";
            };

            beamDeps = [
              nimble_options
              plug
              telemetry_metrics
            ];
          };
        in
        drv;

      phoenix =
        let
          version = "1.8.5";
          drv = buildMix {
            inherit version;
            name = "phoenix";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "phoenix";
              sha256 = "83b2bb125127e02e9f475c8e3e92736325b5b01b0b9b05407bcb4083b7a32485";
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
          version = "1.1.28";
          drv = buildMix {
            inherit version;
            name = "phoenix_live_view";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "phoenix_live_view";
              sha256 = "24faad535b65089642c3a7d84088109dc58f49c1f1c5a978659855d643466353";
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
          version = "1.19.1";
          drv = buildMix {
            inherit version;
            name = "plug";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "plug";
              sha256 = "560a0017a8f6d5d30146916862aaf9300b7280063651dd7e532b8be168511e62";
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
          version = "2.8.0";
          drv = buildMix {
            inherit version;
            name = "plug_cowboy";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "plug_cowboy";
              sha256 = "9cbfaaf17463334ca31aed38ea7e08a68ee37cabc077b1e9be6d2fb68e0171d0";
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
          version = "0.22.0";
          drv = buildMix {
            inherit version;
            name = "postgrex";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "postgrex";
              sha256 = "a68c4261e299597909e03e6f8ff5a13876f5caadaddd0d23af0d0a61afcc5d84";
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
          version = "1.11.0";
          drv = buildMix {
            inherit version;
            name = "prom_ex";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "prom_ex";
              sha256 = "76b074bc3730f0802978a7eb5c7091a65473eaaf07e99ec9e933138dcc327805";
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
          version = "1.4.1";
          drv = buildRebar3 {
            inherit version;
            name = "telemetry";

            src = fetchHex {
              inherit version;
              pkg = "telemetry";
              sha256 = "2172e05a27531d3d31dd9782841065c50dd5c3c7699d95266b2edd54c2dafa1c";
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
          version = "1.4.3";
          drv = buildMix {
            inherit version;
            name = "thousand_island";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "thousand_island";
              sha256 = "6e4ce09b0fd761a58594d02814d40f77daff460c48a7354a15ab353bb998ea0b";
            };

            beamDeps = [
              telemetry
            ];
          };
        in
        drv;

      tornex =
        let
          version = "0.5.0";
          drv = buildMix {
            inherit version;
            name = "tornex";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "tornex";
              sha256 = "b57abbc91479d943440ecaffeb95aed0dea10be21f2edf43af79a10cf0e662e6";
            };

            beamDeps = [
              finch
              plug_cowboy
              prom_ex
              telemetry
              torngen
              torngen_elixir_client
            ];
          };
        in
        drv;

      torngen =
        let
          version = "0.1.10";
          drv = buildMix {
            inherit version;
            name = "torngen";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "torngen";
              sha256 = "2ad8606b08d6f85885e8d352c86a77f9e4f99ebd334f6c5eaf0cb036c3fb1317";
            };

            beamDeps = [
              plug
            ];
          };
        in
        drv;

      torngen_elixir_client =
        let
          version = "5.5.3+torngen-v0.1.10";
          drv = buildMix {
            inherit version;
            name = "torngen_elixir_client";
            appConfigPath = ./config;

            src = fetchFromGitHub {
              owner = "Tornium";
              repo = "torngen_elixir_client";
              rev = "188c7ab35fafa5c5f2f2738bfc2668775c069172";
              hash = "sha256-Ua99eQ3F3RCz9Wm5rjLvnKxvoUP7laTw+zlDKh7fh7g=";
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
          version = "0.5.9";
          drv = buildMix {
            inherit version;
            name = "websock_adapter";
            appConfigPath = ./config;

            src = fetchHex {
              inherit version;
              pkg = "websock_adapter";
              sha256 = "5534d5c9adad3c18a0f58a9371220d75a803bf0b9a3d87e6fe072faaeed76a08";
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
