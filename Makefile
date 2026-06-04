up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

creative:
	docker exec -it minecraft-server-base send-command gamemode creative garymabu

survival:
	docker exec -it minecraft-server-base send-command gamemode survival garymabu