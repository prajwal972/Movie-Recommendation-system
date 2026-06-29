FROM python:3.12-slim

WORKDIR /workspace

# curl is needed for the container HEALTHCHECK below
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-fetch NLTK corpora at build time so the container has no first-request delay
RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

COPY app/ ./app/
COPY models/ ./models/
COPY data/processed_movies.csv ./data/processed_movies.csv
COPY data/final_movies.csv ./data/final_movies.csv

# database/cinematch.db is created automatically on first run. Mount this as a
# volume in production or every container restart starts with an empty DB:
#   docker run -v cinematch_data:/workspace/database ...
VOLUME ["/workspace/database"]

WORKDIR /workspace/app

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:${PORT}/_stcore/health || exit 1

ENV PORT=8501

CMD sh -c "streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true"