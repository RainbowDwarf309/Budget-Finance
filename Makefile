run:
	docker run -d -v db:/home/db --rm --env-file .env --name tg_bot tg_bot:latest
build:
	docker build -t tg_bot:latest .
stop:
	docker stop tg_bot
rename:
	docker tag tg_bot:latest rainbowdwarf/tg_bot:latest
push_docker:
	docker push rainbowdwarf/tg_bot:latest
