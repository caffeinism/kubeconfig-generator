FROM python:3.11.1-slim-buster

RUN pip install flask pyyaml oic gunicorn[gevent]

COPY src /src

WORKDIR /src

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-k", "gevent", "--workers", "2", "app:create_app(config_path='/login-config/config.yaml')"]
