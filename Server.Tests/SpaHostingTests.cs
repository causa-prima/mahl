using System.Net;
using AwesomeAssertions;
using mahl.Server.Tests.Helpers;
using Xunit;

namespace mahl.Server.Tests;

// Kategorie nach ADR-S106-3: Protokoll-/Infrastruktur-Mechanik (Auslieferung der SPA, ADR-S150-2) –
// kein Gherkin-Szenario, weil E2E gegen den Vite-Dev-Server läuft und das Verhalten dort nicht sieht.
// EndpointsTestsBase trotz fehlender DB-Nutzung: Dort wird die Test-Factory samt Web-Root (index.html, Asset) gebaut.
[Collection(PostgresCollectionDefinition.Name)]
public class SpaHostingTests(PostgresContainerFixture postgres) : EndpointsTestsBase(postgres)
{
    // ADR-S150-2
    // Testdaten: /zutatn ist die unbekannte Adresse aus features/navigation.feature; /apix liegt knapp neben
    // dem API-Präfix und pinnt die Grenze des Constraints (nur /api und /api/… sind ausgenommen); der
    // Rezept-Pfad ist ein Direktlink auf ein Rezept (ADR-S135-5).
    [Theory]
    [InlineData("/")]
    [InlineData("/zutatn")]
    [InlineData("/apix")]
    [InlineData("/recipes/0192f6a0-0000-7000-8000-000000000001")]
    public async Task SpaHosting_ClientPathWithoutFileOrEndpoint_ReturnsIndexHtml(string path)
    {
        // Given: a path that is neither a file nor an endpoint
        // When: the client route is requested
        var response = await Client.GetAsync(path, TestContext.Current.CancellationToken);

        // Then: the index.html is returned, the client routing evaluates the address
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        (response.Content.Headers.ContentType?.MediaType).Should().Be("text/html");
        (await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken))
            .Should().Be(TestWebApplicationFactory.IndexHtml);
    }

    // ADR-S150-2
    [Fact]
    public async Task SpaHosting_ExistingStaticFile_ReturnsFileItself()
    {
        // Given: a static file in the web root
        // When: the file is requested
        var response = await Client.GetAsync(TestWebApplicationFactory.AssetPath, TestContext.Current.CancellationToken);

        // Then: the file is returned, not the index.html
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        (await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken))
            .Should().Be(TestWebApplicationFactory.AssetJs);
    }

    // ADR-S150-2
    [Fact]
    public async Task SpaHosting_MissingFileWithExtension_Returns404WithoutBody()
    {
        // Given: a path with a file extension, but no such file in the web root
        // When: it is requested
        var response = await Client.GetAsync("/assets/fehlt.js", TestContext.Current.CancellationToken);

        // Then: 404 with an empty body – not the index.html
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        (await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken)).Should().BeEmpty();
    }

    // ADR-S150-2
    [Fact]
    public async Task SpaHosting_HeadOnClientPath_Returns200WithoutBody()
    {
        // Given: a client path without an endpoint
        // When: it is requested with HEAD
        using var request = new HttpRequestMessage(HttpMethod.Head, "/zutatn");
        var response = await Client.SendAsync(request, TestContext.Current.CancellationToken);

        // Then: 200 like GET, but without a body – HEAD is a read request
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        (await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken)).Should().BeEmpty();
    }

    // ADR-S150-2
    [Fact]
    public async Task SpaHosting_PostOnClientPath_Returns405WithoutBody()
    {
        // Given: a client path without an endpoint
        // When: it is requested with POST
        var response = await Client.PostAsync("/zutatn", content: null, TestContext.Current.CancellationToken);

        // Then: 405 with an empty body – the fallback serves only reads, no HTML for a non-GET request
        response.StatusCode.Should().Be(HttpStatusCode.MethodNotAllowed);
        (await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken)).Should().BeEmpty();
    }

    // ADR-S150-2
    [Theory]
    [InlineData("/api/unbekannt")]
    [InlineData("/api")]
    [InlineData("/API/unbekannt")]
    public async Task SpaHosting_UnknownApiPath_Returns404WithoutBody(string path)
    {
        // Given: a path at or below /api without an endpoint
        // When: it is requested
        var response = await Client.GetAsync(path, TestContext.Current.CancellationToken);

        // Then: 404 with an empty body – no HTML
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        (await response.Content.ReadAsStringAsync(TestContext.Current.CancellationToken)).Should().BeEmpty();
    }

    // ADR-S150-2
    // Annahme: /api/ingredients kennt kein PUT und /api/recipes kein DELETE – sonst bricht der Test aus
    // fachfremdem Grund.
    [Theory]
    [InlineData("PUT", "/api/ingredients")]
    [InlineData("DELETE", "/api/recipes")]
    public async Task SpaHosting_WrongMethodOnExistingApiPath_Returns405(string method, string path)
    {
        // Given: an existing API path that does not serve this method
        // When: it is requested with the wrong method
        using var request = new HttpRequestMessage(new HttpMethod(method), path);
        var response = await Client.SendAsync(request, TestContext.Current.CancellationToken);

        // Then: 405 stays – the fallback must not turn it into 404
        response.StatusCode.Should().Be(HttpStatusCode.MethodNotAllowed);
    }
}
