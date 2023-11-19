docker-image:
	docker build -f ./Dockerfile -t "downloader:latest" .
.PHONY: docker-image

docker-compose-up: docker-image
	docker compose -f docker-compose-dev.yaml up -d --build
	docker compose -f docker-compose-dev.yaml logs -f
.PHONY: docker-compose-up

docker-compose-down:
	docker compose -f docker-compose-dev.yaml stop -t 10
	docker compose -f docker-compose-dev.yaml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker compose -f docker-compose-dev.yaml logs -f
.PHONY: docker-compose-logs