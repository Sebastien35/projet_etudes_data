FROM apache/airflow:latest


COPY ./requirements.txt /tmp/requirements.txt
RUN python -m venv venv
RUN . ./venv/bin/activate
RUN pip install "pip<25" "pip-tools<7.6" --upgrade --force-reinstall
RUN pip install --no-cache-dir --upgrade -r /tmp/requirements.txt

USER airflow