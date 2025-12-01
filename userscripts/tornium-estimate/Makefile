build:
	esbuild ./entrypoint.js --bundle --banner:js="$$(cat header.js)" --outfile=../tornium-estimate.user.js --format=iife

format:
	biome format . --write
