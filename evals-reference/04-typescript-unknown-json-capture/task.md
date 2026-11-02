Earlier in this session, in `editor-prefs/`:

**Me:** Add `readSettings(path: string)` to `src/settings.ts`: read the JSON file and return its
`theme` and `fontSize` as a `Settings`.

**You:** Added it:

```ts
export async function readSettings(path: string): Promise<Settings> {
  const raw = JSON.parse(await readFile(path, "utf8"));
  return { theme: raw.theme, fontSize: raw.fontSize };
}
```

**Me:** `JSON.parse` gives you `any`, so nothing checks this. Treat it as `unknown` and check the
shape before you return it.

**You:** Changed it:

```ts
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
```

**Me:** Yes, like that. Can you make a skill out of this so it's right the first time? Put it
next to editor-prefs.
