FROM python:3.13

# Install Poetry
ENV POETRY_VERSION=2.0.1
RUN curl -sSL https://install.python-poetry.org | python3 -

# Додаємо Poetry до PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory inside the container
WORKDIR /app

# Copy the pyproject.toml file from the root
COPY pyproject.toml ./pyproject.toml
COPY alembic.ini ./alembic.ini

# Install dependencies without creating a virtual environment
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi


# Copy the project directory into the container
COPY app /app

# Set the working directory to the backend directory
WORKDIR /app

# Expose the application port
EXPOSE 8000

# Start the FastAPI development server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]