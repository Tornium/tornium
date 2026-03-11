{ lib, python3Packages, src, ...}:

python3Packages.buildPythonPackage {
  pname = "tornium_commons";
  version = "0.4.0";
  pyproject = true;

  src = builtins.path{
    path = "${src}";
    name = "tornium-commons";
  };

  build-system = with python3Packages; [ setuptools wheel ];
  propagatedBuildInputs = with python3Packages; [
    boltons
    pydantic
    peewee
    psycopg2
    redis
    requests
  ];

  pythonImportsCheck = [ "tornium_commons" ];

  meta = with lib; {
    description = "Reusable components for Tornium";
    license = licenses.gpl3Only;
  };
}
