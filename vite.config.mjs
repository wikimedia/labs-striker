import path from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
    base: "/static",
    build: {
        manifest: true,
        outDir: "static/vite/",
        rollupOptions: {
            input: [
                "static/css/striker.less",
                "static/js/parsley-bootstrap.mjs",
                "static/js/password-strength.mjs",
                "static/js/striker.mjs",
            ],
            output: {
                assetFileNames: "[name]-[hash][extname]",
                chunkFileNames: "[name]-[hash].js",
                entryFileNames: "[name]-[hash].js",
            }
        },
    },
    resolve: {
        alias: {
            "../fonts": path.resolve("static/fonts"),
        }
    }
});
