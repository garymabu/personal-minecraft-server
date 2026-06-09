# Backup of the world + custom packs (run with the server stopped).
# Image-provided packs (vanilla*, chemistry*, editor) are excluded since
# they're recreated by the container on start.
WORLD ?= Bedrock level
BACKUP_DIR ?= backup
TS := $(shell date +%Y%m%d-%H%M%S)

.PHONY: up down logs creative survival backup restore install-packs uninstall-pack

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

backup:
	@mkdir -p "$(BACKUP_DIR)"
	@running=$$(docker ps -q -f name=minecraft-server-base); \
	if [ -n "$$running" ]; then echo "Stopping server..."; docker compose stop; fi; \
	echo "Archiving world + custom packs -> $(BACKUP_DIR)/world-$(TS).tar.gz"; \
	tar -czf "$(BACKUP_DIR)/world-$(TS).tar.gz" \
		--exclude='data/behavior_packs/vanilla*' \
		--exclude='data/behavior_packs/chemistry*' \
		--exclude='data/behavior_packs/editor' \
		--exclude='data/behavior_packs/experimental_*' \
		--exclude='data/behavior_packs/server_*' \
		--exclude='data/resource_packs/vanilla*' \
		--exclude='data/resource_packs/chemistry*' \
		--exclude='data/resource_packs/editor' \
		"data/worlds/$(WORLD)" \
		data/behavior_packs \
		data/resource_packs \
		data/development_behavior_packs \
		data/development_resource_packs \
		packs; \
	status=$$?; \
	if [ -n "$$running" ]; then echo "Starting server..."; docker compose start; fi; \
	exit $$status
	@echo "Done."

# Restore a world tarball. Usage: make restore FILE=backup/world-YYYYMMDD-HHMMSS.tar.gz
restore:
	@test -n "$(FILE)" || (echo "Usage: make restore FILE=backup/world-...tar.gz" && exit 1)
	@rm -rf "data/worlds/$(WORLD)"
	@tar -xzf "$(FILE)"
	@echo "Restored $(FILE)"

# Uninstall an add-on by folder-name substring. Usage: make uninstall-pack PACK=Herobrine
# Server must be down. Make a backup first.
uninstall-pack:
	@test -n "$(PACK)" || (echo "Usage: make uninstall-pack PACK=<folder-name-substring>" && exit 1)
	@test -z "$$(docker ps -q -f name=minecraft-server-base)" || \
		(echo "Stop the server first: make down" && exit 1)
	@python3 scripts/uninstall_pack.py "$(PACK)" "data/worlds/$(WORLD)"

# Install every .mcaddon/.mcpack in packs/ into the active world.
# Server must be down. Make a backup first.
install-packs:
	@test -z "$$(docker ps -q -f name=minecraft-server-base)" || \
		(echo "Stop the server first: make down" && exit 1)
	@python3 scripts/install_packs.py "data/worlds/$(WORLD)"