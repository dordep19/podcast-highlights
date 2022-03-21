# podcast-highlights

Extract the most engaging and representative segments of your podcast.

## Development

This project will be using python virtual envs.

```
cd podcast-highlights
source env/bin/activate
```

This activates the virtual env and dependencies can now be installed local to the repository.

```
pip install -r requirements.txt
```

To run the podcast highlights server in development mode:

```
uvicorn server:app --reload
```

NLP tasks are executed using spaCy's pipeline for the English language that has been trained on written text (blogs, news, comments).

```
python3 -m spacy download en_core_web_lg
```
