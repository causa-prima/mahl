namespace mahl.Server.Tests;

using FluentAssertions;
using mahl.Server.Data.DatabaseTypes;
using mahl.Server.Dtos;
using Microsoft.AspNetCore.Mvc;
using System.Net;
using System.Net.Http.Json;

[FixtureLifeCycle(LifeCycle.InstancePerTestCase)]
[Parallelizable(ParallelScope.All)]
[TestFixture]
public class IngredientsEndpointsTests : EndpointsTestsBase
{
    [Test]
    public async Task GetAll_EmptyDb_Returns200WithEmptyList()
    {
        var response = await Client.GetAsync("/api/ingredients");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var items = await response.Content.ReadFromJsonAsync<List<IngredientDto>>();
        items.Should().BeEmpty();
    }

    [Test]
    public async Task GetAll_ReturnsSortedByName()
    {
        SeedIngredients([
            AnIngredient("Zwiebel", "Stück"),
            AnIngredient("Apfel",   "Stück"),
            AnIngredient("Mehl",    "g"),
        ]);

        var items = await Client.GetFromJsonAsync<List<IngredientDto>>("/api/ingredients");

        items!.Select(i => i.Name).Should().Equal("Apfel", "Mehl", "Zwiebel");
    }

    [Test]
    public async Task GetAll_ExcludesSoftDeletedIngredients()
    {
        SeedIngredients([
            AnIngredient("Aktiv"),
            AnIngredient("Gelöscht", deletedAt: DateTimeOffset.UtcNow),
        ]);

        var items = await Client.GetFromJsonAsync<List<IngredientDto>>("/api/ingredients");

        var aktiv = GetAllIngredientsFromDb().Single(i => string.Equals(i.Name, "Aktiv", StringComparison.Ordinal));
        items!.Should().BeEquivalentTo([new IngredientDto(Id: aktiv.Id, Name: "Aktiv", DefaultUnit: "g", AlwaysInStock: false)]);
    }

    [Test]
    public async Task GetAll_WithDbInconsistency_Returns500()
    {
        SeedIngredients([new Server.Data.DatabaseTypes.IngredientDbType { Name = "", DefaultUnit = "g" }]);

        var response = await Client.GetAsync("/api/ingredients");

        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);
    }

    // GET /api/ingredients/{id}

    [Test]
    public async Task GetById_ExistingId_Returns200WithCorrectData()
    {
        SeedIngredients([AnIngredient("Salz", alwaysInStock: true)]);
        var id = GetAllIngredientsFromDb()[0].Id;

        var dto = await Client.GetFromJsonAsync<IngredientDto>($"/api/ingredients/{id}");

        dto.Should().BeEquivalentTo(new IngredientDto(Id: id, Name: "Salz", DefaultUnit: "g", AlwaysInStock: true));
    }

    [Test]
    public async Task GetById_UnknownId_Returns404()
    {
        var response = await Client.GetAsync($"/api/ingredients/{Guid.NewGuid()}");
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Test]
    public async Task GetById_SoftDeletedIngredient_Returns404()
    {
        SeedIngredients([AnIngredient(deletedAt: DateTimeOffset.UtcNow)]);
        var id = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.GetAsync($"/api/ingredients/{id}");

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    // POST /api/ingredients

    [Test]
    public async Task Create_ValidData_Returns201WithCreatedIngredient()
    {
        var response = await Client.PostAsJsonAsync("/api/ingredients",
            new CreateIngredientDto(Name: "Butter", DefaultUnit: "g"));

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var created = await response.Content.ReadFromJsonAsync<IngredientDto>();
        var inDb = GetAllIngredientsFromDb();
        inDb.Should().BeEquivalentTo(
            [new IngredientDbType { Id = created!.Id, Name = "Butter", DefaultUnit = "g", AlwaysInStock = false, DeletedAt = null }]);
        created.Should().BeEquivalentTo(new IngredientDto(Id: inDb[0].Id, Name: "Butter", DefaultUnit: "g", AlwaysInStock: false));
    }

    [Test]
    public async Task Create_TrimsNameAndUnit()
    {
        var response = await Client.PostAsJsonAsync("/api/ingredients",
            new CreateIngredientDto(Name: "  Butter  ", DefaultUnit: "  g  "));

        var created = await response.Content.ReadFromJsonAsync<IngredientDto>();
        var inDb = GetAllIngredientsFromDb();
        inDb.Should().BeEquivalentTo(
            [new IngredientDbType { Id = created!.Id, Name = "Butter", DefaultUnit = "g", AlwaysInStock = false, DeletedAt = null }]);
        created.Should().BeEquivalentTo(new IngredientDto(Id: inDb[0].Id, Name: "Butter", DefaultUnit: "g", AlwaysInStock: false));
    }

    [TestCase("",      "g",  "Name darf nicht leer sein.")]
    [TestCase("   ",   "g",  "Name darf nicht leer sein.")]
    [TestCase("Butter","",   "Einheit darf nicht leer sein.")]
    [TestCase("Butter","   ","Einheit darf nicht leer sein.")]
    public async Task Create_InvalidInput_Returns422WithMessage(string name, string unit, string expectedMessage)
    {
        var response = await Client.PostAsJsonAsync("/api/ingredients",
            new CreateIngredientDto(Name: name, DefaultUnit: unit));

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
        var body = await response.Content.ReadAsStringAsync();
        body.Should().Be($"\"{expectedMessage}\"");
        GetAllIngredientsFromDb().Should().BeEmpty();
    }

    [Test]
    public async Task Create_DuplicateName_Returns409WithConflictMessage()
    {
        SeedIngredients([AnIngredient("Butter")]);
        var stateBeforeAction = GetAllIngredientsFromDb();

        var response = await Client.PostAsJsonAsync("/api/ingredients",
            new CreateIngredientDto(Name: "Butter", DefaultUnit: "ml"));

        response.StatusCode.Should().Be(HttpStatusCode.Conflict);
        var body = await response.Content.ReadAsStringAsync();
        body.Should().Be("\"Eine Zutat mit dem Namen 'Butter' existiert bereits.\"");
        GetAllIngredientsFromDb().Should().BeEquivalentTo(stateBeforeAction);
    }

    [Test]
    public async Task Create_SameNameAsSoftDeleted_Returns409WithSoftDeletedId()
    {
        SeedIngredients([AnIngredient("Butter", deletedAt: DateTimeOffset.UtcNow)]);
        var stateBeforeAction = GetAllIngredientsFromDb();

        var response = await Client.PostAsJsonAsync("/api/ingredients",
            new CreateIngredientDto(Name: "Butter", DefaultUnit: "ml"));

        response.StatusCode.Should().Be(HttpStatusCode.Conflict);
        var body = await response.Content.ReadFromJsonAsync<SoftDeletedConflictDto>();
        body.Should().BeEquivalentTo(new SoftDeletedConflictDto(Code: "ingredient_soft_deleted", Id: stateBeforeAction[0].Id));
        GetAllIngredientsFromDb().Should().BeEquivalentTo(stateBeforeAction);
    }

    [Test]
    public async Task Create_ValidData_LocationHeaderPointsToNewResource()
    {
        var response = await Client.PostAsJsonAsync("/api/ingredients",
            new CreateIngredientDto(Name: "Butter", DefaultUnit: "g"));

        var id = GetAllIngredientsFromDb()[0].Id;
        response.Headers.Location!.ToString().Should().Be($"/api/ingredients/{id}");
    }

    // DELETE /api/ingredients/{id}

    [Test]
    public async Task Delete_ExistingId_Returns204AndSoftDeletes()
    {
        SeedIngredients([AnIngredient("Butter")]);
        var stateBeforeAction = GetAllIngredientsFromDb();

        var response = await Client.DeleteAsync($"/api/ingredients/{stateBeforeAction[0].Id}");

        response.StatusCode.Should().Be(HttpStatusCode.NoContent);
        var inDb = GetAllIngredientsFromDb();
        inDb.Should().BeEquivalentTo(stateBeforeAction, options => options.Excluding(i => i.DeletedAt));
        inDb[0].DeletedAt.Should().NotBeNull();
    }

    [Test]
    public async Task Delete_NonExistingId_Returns404()
    {
        var response = await Client.DeleteAsync($"/api/ingredients/{Guid.NewGuid()}");
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        GetAllIngredientsFromDb().Should().BeEmpty();
    }

    // POST /api/ingredients/{id}/restore

    [Test]
    public async Task Restore_SoftDeletedId_Returns200AndReactivates()
    {
        SeedIngredients([AnIngredient("Butter", deletedAt: DateTimeOffset.UtcNow)]);
        var id = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.PostAsync($"/api/ingredients/{id}/restore", null);

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var dto = await response.Content.ReadFromJsonAsync<IngredientDto>();
        var inDb = GetAllIngredientsFromDb()[0];
        dto.Should().BeEquivalentTo(new IngredientDto(Id: id, Name: "Butter", DefaultUnit: "g", AlwaysInStock: false));
        inDb.Should().BeEquivalentTo(new IngredientDbType { Id = id, Name = "Butter", DefaultUnit = "g", AlwaysInStock = false, DeletedAt = null });
    }

    [Test]
    public async Task Restore_ActiveIngredient_Returns409()
    {
        SeedIngredients([AnIngredient("Butter")]);
        var id = GetAllIngredientsFromDb()[0].Id;
        var stateBeforeAction = GetAllIngredientsFromDb();

        var response = await Client.PostAsync($"/api/ingredients/{id}/restore", null);

        response.StatusCode.Should().Be(HttpStatusCode.Conflict);
        var body = await response.Content.ReadAsStringAsync();
        body.Should().Be("\"Zutat ist bereits aktiv.\"");
        GetAllIngredientsFromDb().Should().BeEquivalentTo(stateBeforeAction);
    }

    [Test]
    public async Task Restore_UnknownId_Returns404()
    {
        var response = await Client.PostAsync($"/api/ingredients/{Guid.NewGuid()}/restore", null);
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Test]
    public async Task Delete_AlreadySoftDeleted_Returns404()
    {
        SeedIngredients([AnIngredient(deletedAt: DateTimeOffset.UtcNow)]);
        var stateBeforeAction = GetAllIngredientsFromDb();

        var response = await Client.DeleteAsync($"/api/ingredients/{stateBeforeAction[0].Id}");

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        GetAllIngredientsFromDb().Should().BeEquivalentTo(stateBeforeAction);
    }

    [Test]
    public async Task GetById_CorruptIngredient_Returns500WithProblemDetails()
    {
        SeedIngredients([new IngredientDbType { Name = "", DefaultUnit = "g" }]);
        var id = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.GetAsync($"/api/ingredients/{id}");

        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);
        response.Content.Headers.ContentType!.MediaType.Should().Be("application/problem+json");
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Detail.Should().Be($"DB inconsistency in Ingredient #{id}: Name darf nicht leer sein.");
    }

    [Test]
    public async Task Create_UniqueName_WhenOtherActiveIngredientsExist_Returns201()
    {
        SeedIngredients([AnIngredient("Apfel")]);
        var apfelId = GetAllIngredientsFromDb()[0].Id;

        var response = await Client.PostAsJsonAsync("/api/ingredients",
            new CreateIngredientDto(Name: "Butter", DefaultUnit: "g"));

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var created = await response.Content.ReadFromJsonAsync<IngredientDto>();
        GetAllIngredientsFromDb().Should().BeEquivalentTo(
            [
                new IngredientDbType { Id = apfelId, Name = "Apfel", DefaultUnit = "g", AlwaysInStock = false, DeletedAt = null },
                new IngredientDbType { Id = created!.Id, Name = "Butter", DefaultUnit = "g", AlwaysInStock = false, DeletedAt = null }
            ]);
    }
}
