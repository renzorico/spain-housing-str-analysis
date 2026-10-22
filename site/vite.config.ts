import { defineConfig } from "vite";

// Relative base so the build works on a GitHub Pages project URL
// (https://<user>.github.io/<repo>/) without knowing the repo name.
export default defineConfig({
  base: "./",
  build: { outDir: "dist", sourcemap: false },
});
