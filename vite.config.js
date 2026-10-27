import { defineConfig } from "vite";

export default defineConfig({
  // GitHub Pages serves this project under /Ai-Medical-Chatbot/
  base: "/Ai-Medical-Chatbot/",
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
});
