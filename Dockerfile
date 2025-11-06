FROM apache/airflow:2.6.3-python3.10

# Copy your project requirements
COPY ./requirements.txt /tmp/requirements.txt

# Upgrade pip & install dependencies
RUN pip install --no-cache-dir --upgrade pip==24.3.1 pip-tools==7.5.1
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt
RUN pip install --no-cache-dir fastapi==0.100.0 pydantic==1.10.14

USER airflow
