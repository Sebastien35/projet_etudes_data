# projet_etudes

# How to run :

Only works with the environment vars.
Use make to run the project. Commands are defined in makefile.
- make install-all : install all requirements
- make run1 : run the pipeline ingest_from_bluesky
- make run2 : run the pipeline nlp_transform
- make run3 : run the pipeline vectorisation and save model locally
- make quickstart will run vectorisation will install dependencies, run the vectorisation pipeline and start both the api and the web app
