build:
	esbuild ./entrypoint.js --bundle --banner:js="$$(cat header.js)" --footer:js="})();" --outfile=../tornium-crimes.user.js --format=iife --preserve-symlinks

format:
	biome format . --write
