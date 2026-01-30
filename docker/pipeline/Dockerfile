# NYC Taxi Dataflow Pipeline Docker Image
# Used for Dataflow Flex Templates
FROM gcr.io/dataflow-templates-base/python311-template-launcher-base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLEX_TEMPLATE_PYTHON_PY_FILE=/app/src/pipeline/main.py \
    FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE=/app/requirements.txt

# Set working directory
WORKDIR /app

# Copy requirements (generated from pyproject.toml)
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Ensure the pipeline module is importable
ENV PYTHONPATH=/app

# Entry point is handled by the Flex Template launcher
