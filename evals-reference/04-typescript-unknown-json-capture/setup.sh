#!/usr/bin/env bash
# Rebuilds the state at the end of the session: the project committed as it was before the first
# prompt, and the version the user accepted left in the working tree, not yet committed. Tessl
# uploads only declared scenario files, so the accepted version is written from this script.
set -euo pipefail
cd editor-prefs
if [ ! -d .git ]; then
  git init -q -b main
  git add -A
  git -c user.name=Dev -c user.email=dev@example.com commit -q -m "Settings type and defaults"
fi
mkdir -p "$(dirname src/settings.ts)"
cat > src/settings.ts <<'SESSION_FILE'
import { readFile } from "node:fs/promises";

export interface Settings {
  theme: string;
  fontSize: number;
}

export const defaultSettings: Settings = { theme: "light", fontSize: 14 };

export async function readSettings(path: string): Promise<Settings> {
  const raw: unknown = JSON.parse(await readFile(path, "utf8"));
  if (!isSettings(raw)) {
    throw new Error(`${path} is not a settings file: expected theme and fontSize`);
  }
  return { theme: raw.theme, fontSize: raw.fontSize };
}

function isSettings(value: unknown): value is Settings {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as Record<string, unknown>).theme === "string" &&
    typeof (value as Record<string, unknown>).fontSize === "number"
  );
}
SESSION_FILE
