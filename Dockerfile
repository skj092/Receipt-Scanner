FROM python:3.10-slim AS builder

#RUN apt-get update && apt-get install build-essential -y

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean

# install PDM
RUN pip install -U pip setuptools wheel pip pdm
# RUN pip install pdm

# copy files
COPY pyproject.toml pdm.lock /project/

# install dependencies and project into the local packages directory
WORKDIR /project
RUN mkdir __pypackages__ && pdm install --prod --no-lock --no-editable



# run stage
FROM python:3.10-slim
WORKDIR /project
# retrieve packages from build stage


# Add any additional dependencies here if needed
RUN apt-get update && apt-get install -y poppler-utils
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/__pypackages__/3.10/lib /project/pkgs
COPY src/ /project/src
# set command/entrypoint, adapt to fit your needs
# CMD ["sleep", "26000000"]

CMD ["python","-m" , "gunicorn", "--bind=0.0.0.0:52207", "src.app:app","-k" ,"uvicorn.workers.UvicornWorker" , "--max-requests","40", "--timeout", "180", "--workers" ,"10", "--max-requests-jitter" , "10"]

