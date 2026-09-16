export function ApiUnavailable() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
      <h1 className="font-serif text-xl font-medium text-ink">
        Couldn&apos;t reach the server
      </h1>
      <p className="mt-2 max-w-sm text-ink/60">
        The API may still be starting up. Refresh in a few seconds and try
        again.
      </p>
    </div>
  );
}
