using System.Security.Cryptography;

namespace mahl.Server.Middleware;

// ADR-S058-1/-2/-3, ADR-S000-12, ADR-S084-1/-2: GET-Collection-Endpoints liefern einen
// Content-Hash-ETag (SHA-256 des serialisierten Response-Body) und beantworten If-None-Match
// mit 304. Bewusst nur Single-Tag-Vergleich (ordinal/verbatim) – kein RFC-7232-Listen-/`*`-
// Support (YAGNI): der einzige Konsument (conditionalGet.ts) sendet stets genau einen ETag.
internal static class ETagMiddleware
{
    public static void UseCollectionETag(this WebApplication app) =>
        app.Use(async (context, next) =>
        {
            if (HttpMethods.IsGet(context.Request.Method))
                await InterceptGetAsync(context, next);
            else
                await next(context);
        });

    private static async Task InterceptGetAsync(HttpContext context, RequestDelegate next)
    {
        var originalBody = context.Response.Body;
        using var buffer = new MemoryStream();
        context.Response.Body = buffer;
        await next(context);
        context.Response.Body = originalBody;
        await ApplyETagAndWriteAsync(context, buffer);
    }

    private static async Task ApplyETagAndWriteAsync(HttpContext context, MemoryStream buffer)
    {
        if (context.Response.StatusCode == StatusCodes.Status200OK)
        {
            var etag = $"\"{Convert.ToHexString(SHA256.HashData(buffer.ToArray()))}\"";
            context.Response.Headers.ETag = etag;

            if (context.Request.Headers.IfNoneMatch == etag)
            {
                context.Response.StatusCode = StatusCodes.Status304NotModified;
                // 304 trägt keinen Body – die vom inneren Handler gesetzte Content-Length des
                // 200-Body wäre sonst falsch; null entfernt den Header (RFC 7232 §4.1).
                context.Response.ContentLength = null;
                return;
            }
        }

        buffer.Position = 0;
        await buffer.CopyToAsync(context.Response.Body);
    }
}
