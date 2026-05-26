FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --quiet

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

RUN DJANGO_SETTINGS_MODULE=config.settings.production \
    SECRET_KEY=build-time-dummy \
    python manage.py collectstatic --noinput

EXPOSE 7000

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]
