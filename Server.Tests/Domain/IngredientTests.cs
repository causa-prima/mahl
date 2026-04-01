namespace mahl.Server.Tests.Domain;

using FluentAssertions;
using mahl.Server.Domain;
using mahl.Server.Tests.Helpers;
using NUnit.Framework;
using OneOf.Types;

[TestFixture]
public class IngredientTests
{
    // Create

    [Test]
    public void ParameterlessConstructor_Throws()
    {
        Action act = () => new Ingredient();

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Valid instances can only be created with Create.");
    }

    [Test]
    public void Id_DefaultInstance_Throws()
    {
        var ingredient = default(Ingredient);

        Action act = () => { var _ = ingredient.Id; };

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("Uninitialized");
    }

    [Test]
    public void Create_ValidArgs_ReturnsIngredientWithId()
    {
        var id = Guid.NewGuid();

        var result = Ingredient.Create(id, "Butter", "g");

        result.Value.Should().BeOfType<Ingredient>().Which.Satisfy(i =>
        {
            i.Id.Should().Be(id);
            ((string)i.Name).Should().Be("Butter");
            ((string)i.DefaultUnit).Should().Be("g");
        });
    }

    [Test]
    public void Create_TrimsWhitespace()
    {
        var result = Ingredient.Create(Guid.NewGuid(), "  Salz  ", "  TL  ");

        result.Value.Should().BeOfType<Ingredient>().Which.Satisfy(i =>
        {
            ((string)i.Name).Should().Be("Salz");
            ((string)i.DefaultUnit).Should().Be("TL");
        });
    }

    [TestCase("")]
    [TestCase("   ")]
    [TestCase("\t")]
    [TestCase("\n")]
    [TestCase(" \t\n ")]
    public void Create_InvalidName_ReturnsError(string invalidName)
    {
        var result = Ingredient.Create(Guid.NewGuid(), invalidName, "g");

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Name darf nicht leer sein.");
    }

    [Test]
    public void Create_EmptyDefaultUnit_ReturnsError()
    {
        var result = Ingredient.Create(Guid.NewGuid(), "Butter", "");

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Einheit darf nicht leer sein.");
    }

    [Test]
    public void Create_EmptyNameTakesPrecedenceOverEmptyUnit()
    {
        var result = Ingredient.Create(Guid.NewGuid(), "", "");

        result.Value.Should().BeOfType<Error<string>>()
            .Which.Value.Should().Be("Name darf nicht leer sein.");
    }

}
