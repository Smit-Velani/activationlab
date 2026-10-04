install:
	pip install -r requirements.txt
test:
	pytest -q
run:
	python manage.py migrate && python manage.py runserver
docker-up:
	docker compose up --build
docker-down:
	docker compose down
