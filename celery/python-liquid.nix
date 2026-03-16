{ python3Packages, fetchPypi }:

python3Packages.buildPythonPackage rec {
  pname = "python_liquid";
  version = "2.1.0";
  pyproject = true;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-pMKrskrEDe2Mm6hE67++eKPkHG/hCnu+lBRFglabc9A=";
  };

  propagatedBuildInputs = with python3Packages; [
    markupsafe
    python-dateutil
    babel
    pytz
  ];

  build-system = with python3Packages; [ hatchling ];
}
