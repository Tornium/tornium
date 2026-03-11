{ python3, tornium_commons, tornium_celery, src, ...}:

let 
  pythonEnv = python3.withPackages (packages: with packages; [
    gunicorn

    authlib
    flask
    flask-cors
    flask-login
    pynacl

    pandas
    scikit-learn
    xgboost

    tornium_commons
    tornium_celery
  ]);
in {
  inherit pythonEnv;

  srcDir = src;
  wsgi = "app:app";
  gunicornCmd = "${pythonEnv}/bin/gunicorn";
}
