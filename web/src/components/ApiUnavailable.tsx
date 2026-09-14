export function ApiUnavailable() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
      <h1 className="text-xl font-semibold text-neutral-900">
        Couldn&apos;t reach the server
      </h1>
      <p className="mt-2 max-w-sm text-neutral-500">
        The API may still be starting up. Refresh in a few seconds and try
        again.
      </p>
    </div>
  );
}
