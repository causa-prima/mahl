export function extractErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const resp = (error as { response?: { data?: unknown } }).response;
    if (resp?.data && typeof resp.data === 'object' && 'detail' in resp.data) {
      return String((resp.data as { detail: unknown }).detail);
    }
    if (resp?.data && typeof resp.data === 'string') return resp.data;
  }
  if (error instanceof Error && error.message) return error.message;
  return 'Ein unbekannter Fehler ist aufgetreten.';
}
