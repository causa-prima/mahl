using System.Net;
using System.Net.Http.Json;
using AwesomeAssertions;
using mahl.Server.Tests.Helpers;
using Xunit;

namespace mahl.Server.Tests;

public class ETagMiddlewareTests : EndpointsTestsBase
{
#pragma warning disable CA1812 // instantiated by JSON deserializer via reflection
    private sealed record CreateIngredientRequest(string Name, string DefaultUnit);
    private sealed record IngredientResponse(Guid Id, string Name, string DefaultUnit);
#pragma warning restore CA1812

    [Fact]
    public async Task ETagMiddleware_Get200_SetsQuotedNonEmptyETagHeader()
    {
        // Given: an empty ingredients collection (no seed)
        // When: a GET collection request is made
        var response = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);

        // Then: a non-empty, RFC-7232 strong (quoted) ETag header is returned
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        response.Headers.ETag.Should().NotBeNull();
        response.Headers.ETag.Tag.Should().StartWith("\"").And.EndWith("\"");
        response.Headers.ETag.Tag.Trim('"').Should().NotBeEmpty();
    }

    [Fact]
    public async Task ETagMiddleware_IfNoneMatchMatchesETag_Returns304WithoutBody()
    {
        // Given: the ETag of the current collection state
        var firstResponse = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);
        var etag = firstResponse.Headers.ETag!.Tag;

        // When: the same ETag is sent via If-None-Match
        using var request = new HttpRequestMessage(HttpMethod.Get, "/api/ingredients");
        request.Headers.TryAddWithoutValidation("If-None-Match", etag);
        var response = await Client.SendAsync(request, TestContext.Current.CancellationToken);

        // Then: 304 Not Modified with the ETag header and no body
        response.StatusCode.Should().Be(HttpStatusCode.NotModified);
        response.Headers.ETag!.Tag.Should().Be(etag);
        var body = await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken);
        body.Should().BeEmpty();
    }

    [Fact]
    public async Task ETagMiddleware_IfNoneMatchStaleETag_Returns200WithBodyAndETag()
    {
        // Given: a stale/wrong ETag that does not match the current collection state.
        // Value is an arbitrary non-matching token – exact content is irrelevant (verbatim compare).
        const string staleEtag = "\"STALE0000000000000000000000000000000000000000000000000000000000\"";

        // When: the stale ETag is sent via If-None-Match
        using var request = new HttpRequestMessage(HttpMethod.Get, "/api/ingredients");
        request.Headers.TryAddWithoutValidation("If-None-Match", staleEtag);
        var response = await Client.SendAsync(request, TestContext.Current.CancellationToken);

        // Then: 200 OK with the body and the real (non-stale) ETag header.
        // Body is asserted non-empty (proves it was sent, not stripped as in a 304) without
        // pinning the endpoint's exact serialization – that belongs in an endpoint test.
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        response.Headers.ETag!.Tag.Should().NotBe(staleEtag);
        var body = await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken);
        body.Should().NotBeNullOrEmpty();
    }

    [Fact]
    public async Task ETagMiddleware_ContentChangedAfterPost_SameStaleIfNoneMatch_Returns200WithDifferentETag()
    {
        // Given: the ETag of the empty collection
        var emptyResponse = await Client.GetAsync("/api/ingredients", TestContext.Current.CancellationToken);
        var emptyEtag = emptyResponse.Headers.ETag!.Tag;

        // Given: the collection content changes via POST
        var createRequest = new CreateIngredientRequest(Name: "Tomaten", DefaultUnit: "Stück");
        await Client.PostAsJsonAsync("/api/ingredients", createRequest, TestContext.Current.CancellationToken);

        // When: the now-stale empty-collection ETag is sent via If-None-Match
        using var request = new HttpRequestMessage(HttpMethod.Get, "/api/ingredients");
        request.Headers.TryAddWithoutValidation("If-None-Match", emptyEtag);
        var response = await Client.SendAsync(request, TestContext.Current.CancellationToken);

        // Then: 200 OK (not 304) with a different ETag — the hash is content-sensitive
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        response.Headers.ETag!.Tag.Should().NotBe(emptyEtag);
    }

    [Fact]
    public async Task ETagMiddleware_PostRequest_PassesThroughWithoutETag()
    {
        // Given: a valid create request
        var createRequest = new CreateIngredientRequest(Name: "Tomaten", DefaultUnit: "Stück");

        // When: a non-GET (POST) request is made
        var response = await Client.PostAsJsonAsync("/api/ingredients", createRequest, TestContext.Current.CancellationToken);

        // Then: the response passes through untouched — 201 Created, body intact, no content-hash ETag
        response.StatusCode.Should().Be(HttpStatusCode.Created);
        response.Headers.ETag.Should().BeNull();
        var body = await response.Content.ReadFromJsonAsync<IngredientResponse>(TestContext.Current.CancellationToken);
        body.Should().BeEquivalentTo(
            new IngredientResponse(Id: body!.Id, Name: "Tomaten", DefaultUnit: "Stück"));
        // Id is server-generated; round-tripped value compared against itself, name/unit pinned exactly.
    }

    [Fact]
    public async Task ETagMiddleware_GetNon200Response_PassesThroughWithoutETag()
    {
        // Given: a route that does not exist (will produce a 404)
        // When: a GET request hits that route
        var response = await Client.GetAsync("/api/does-not-exist", TestContext.Current.CancellationToken);

        // Then: the non-200 response passes through without a content-hash ETag
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        response.Headers.ETag.Should().BeNull();
    }
}
