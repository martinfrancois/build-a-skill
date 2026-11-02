import { readFile } from "node:fs/promises";

export interface Settings {
  theme: string;
  fontSize: number;
}

export const defaultSettings: Settings = { theme: "light", fontSize: 14 };
