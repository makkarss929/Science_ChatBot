FROM openfabric/openfabric-pyenv:0.1.9-3.8

RUN mkdir cognitive-assistant
WORKDIR /cognitive-assistant
COPY . .
RUN poetry install -vvv --no-dev
RUN pip install -r requirements.txt
EXPOSE 80


# Uncomment for using traditional way
# CMD ["sh","start.sh"]

# Uncomment for using Fast API.
CMD ["uvicorn", "app:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]