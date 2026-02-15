ENV := $(PWD)/.env
include $(ENV)
export

MIX_ENV ?= prod

daemon:
	_build/$(MIX_ENV)/rel/tornium/bin/tornium daemon

start:
	_build/$(MIX_ENV)/rel/tornium/bin/tornium start

restart:
	_build/$(MIX_ENV)/rel/tornium/bin/tornium restart

stop:
	_build/$(MIX_ENV)/rel/tornium/bin/tornium stop

release:
	@echo "Using env $(MIX_ENV)"
	mix phx.gen.release
	mix release

remote:
	_build/$(MIX_ENV)/rel/tornium/bin/tornium remote

migrate:
	_build/$(MIX_ENV)/rel/tornium/bin/tornium eval "Tornium.Release.migrate"

rollback:
	_build/$(MIX_ENV)/rel/tornium/bin/tornium eval "Tornium.Release.rollback"

