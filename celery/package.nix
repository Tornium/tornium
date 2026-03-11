{ lib, python3Packages, src, tornium_commons, python-liquid, ...}:

python3Packages.buildPythonPackage {
  pname = "tornium_celery";
  version = "0.4.0";
  pyproject = true;

  src = builtins.path{
    path = "${src}";
    name = "tornium-celery";
  };

  build-system = with python3Packages; [ setuptools wheel ];
  propagatedBuildInputs = with python3Packages; [
    celery
    redis
    requests
    python-liquid
    orjson

    tornium_commons
  ];

  # TODO: tornium_celery needs to be modified so it doesn't attempt to read from the Config file 
  # or at least not fail on it
  # pythonImportsCheck = [ "tornium_celery" ];

  meta = with lib; {
    description = "Tornium Celery tasks and worker";
    license = licenses.gpl3Only;
  };
}
