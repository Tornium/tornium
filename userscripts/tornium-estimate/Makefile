build:
	esbuild ./entrypoint.js --bundle --banner:js="$$(cat header.js)" --outfile=../tornium-estimate.user.js --format=iife --preserve-symlinks

format:
	biome format . --write
