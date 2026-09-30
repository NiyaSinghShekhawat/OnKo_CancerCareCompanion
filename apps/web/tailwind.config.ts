import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        onko: {
          teal: "#006761",
          tealaccent: "#00837B",
          tealdark: "#00534E",
          softteal: "#E5F3F1",
          canvas: "#F4F6F5",
          surface: "#F8FAF9",
          hover: "#EEF1F0",
          line: "#E1E6E4",
          ink: "#17201E",
          muted: "#53605D",
          sos: "#C9362B",
          amber: "#B7791F",
          amberbg: "#FFF7DF",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(23, 32, 30, 0.04), 0 8px 24px rgba(23, 32, 30, 0.035)",
      },
      fontFamily: { sans: ["var(--font-body)", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
} satisfies Config;
