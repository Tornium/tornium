build:
	esbuild ./entrypoint.js --bundle --banner:js="$$(cat header.js)" --outfile=../tornium-retaliations.user.js --format=iife

format:
	biome format . --write
