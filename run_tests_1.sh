export NO_PROXY=localhost
rm -r instance/downloads
dropdb --if-exists toxchellow
createdb --encoding=UTF8 toxchellow
waitress-serve --host=0.0.0.0 --port=8080 --call chellow:create_app
