build:
	esbuild ./entrypoint.js --bundle --banner:js="$$(cat header.js)" --footer:js="})();" --outfile=../tornium-crimes.user.js --format=esm --preserve-symlinks

format:
	biome format . --write
