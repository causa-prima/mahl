namespace mahl.Shared.Tests.Dtos;
using FluentAssertions;
using mahl.Shared.Dtos;
using mahl.Shared.Types;
using mahl.Tests.Shared;
using NUnit.Framework;
using OneOf.Types;
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

[TestFixture]
public class ShoppingListItemDtoTests
{
    [Test]
    public void Constructor_Sets_Properties_ToDefaultValues()
    {
        // Arrange

        // Act
        var result = new ShoppingListItemDto();

        // Assert
        result.Id.Should().BeNull();
        result.Title.Should().Be(string.Empty);
        result.Description.Should().Be(string.Empty);
        result.BoughtAt.Should().BeNull();
    }

    [Test]
    public void Instance_PassesValidation_When_DtoIsValid()
    {
        // Arrange
        var dto = new ShoppingListItemDto
        {
            Title = "Milk",
            Description = "2L low-fat",
            BoughtAt = DateTimeOffset.UtcNow
        };

        var context = new ValidationContext(dto);
        var results = new List<ValidationResult>();

        // Act
        var isValid = Validator.TryValidateObject(dto, context, results, true);

        // Assert
        isValid.Should().BeTrue();
        results.Should().BeEmpty();
    }

    [TestCase("")]
    [TestCase("A")]
    [TestCase("A very long title that is longer than the allowed limit for the title property")]
    public void Instance_FailsValidation_When_TitleIsInvalid(string title)
    {
        // Arrange
        var dto = new ShoppingListItemDto
        {
            Title = title,
            Description = "Test"
        };

        var context = new ValidationContext(dto);
        var results = new List<ValidationResult>();

        // Act
        var isValid = Validator.TryValidateObject(dto, context, results, true);

        // Assert
        isValid.Should().BeFalse();
        results.Should().ContainSingle()
            .Which.MemberNames.Should().Contain("Title");
    }

    private static IEnumerable<ShoppingListItemDto> ValidDtos()
    {
        yield return new ShoppingListItemDto
        {
            Id = 1,
            Title = "Eggs",
            Description = "Free range",
            BoughtAt = DateTimeOffset.UtcNow
        };

        yield return new ShoppingListItemDto
        {
            Id = null,
            Title = "Cucumbers",
            BoughtAt = null,
        };
    }

    [Test, TestCaseSource(nameof(ValidDtos))]
    public void MapToDomain_Returns_DomainModel_When_DtoIsValid(ShoppingListItemDto dto)
    {
        // Arrange

        // Act
        var result = dto.MapToDomain();

        // Assert
        result.Switch(
            domainModel =>
            {
                domainModel.Id.Should().Be((SyncItemId)dto.Id);
                domainModel.Title.Should().Be(NonEmptyTrimmedString.Create(dto.Title).AsT0.Value);
                domainModel.Description.Should().Be((TrimmedString)dto.Description);
                if (dto.BoughtAt.HasValue)
                    domainModel.BoughtAt.Switch(
                        date => date.Should().Be(dto.BoughtAt.Value),
                        unknown => Helpers.FailWithTypeMismatch(nameof(domainModel.BoughtAt), typeof(DateTimeOffset), unknown)
                    );
                else
                    domainModel.BoughtAt.Switch(
                        date => Helpers.FailWithTypeMismatch(nameof(domainModel.BoughtAt), typeof(Unknown), date),
                        unknown => { }
                    );
            },
            _ => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingListItem), _)
        );
    }

    private static IEnumerable<(ShoppingListItemDto Dto, string ErrorMessage)> InvalidDtos()
    {
        yield return (new ShoppingListItemDto
        {
            Id = 1,
            Title = "",
            Description = "Free range",
            BoughtAt = DateTimeOffset.UtcNow
        }, "Value cannot be null, empty or white space.");

        yield return (new ShoppingListItemDto
        {
            Id = null,
            Title = "A very long title that is longer than the allowed limit for the title property",
            BoughtAt = null,
        }, "Title must not be longer than 30 characters.");
    }

    [Test, TestCaseSource(nameof(InvalidDtos))]
    public void MapToDomain_Returns_Error_When_DtoIsInvalid((ShoppingListItemDto dto, string error) testdata)
    {
        // Arrange
        var (dto, errorMessage) = testdata;

        // Act
        var result = dto.MapToDomain();

        // Assert
        result.Switch(
            domainModel => Helpers.FailWithTypeMismatch(nameof(result), typeof(Error<string>), domainModel),
            error => error.Value.Should().Be(errorMessage)
        );
    }

    [Test]
    public void MapToDto_Returns_Dto()
    {
        // Arrange
        var now = DateTimeOffset.UtcNow;

        var domainModel = (ShoppingListItem)ShoppingListItem.FromPrimitiveTypes(
            42,
            "Bread",
            "Wholegrain",
            now
        );

        // Act
        var dto = domainModel.MapToDto();

        // Assert
        dto.Id.Should().Be(domainModel.Id);
        dto.Title.Should().Be(domainModel.Title);
        dto.Description.Should().Be(domainModel.Description);
        dto.BoughtAt.Should().Be(now);
    }

    [Test]
    public void MapToDto_SetsBoughtAtToNull_When_BoughtAtHasValueUnknownInDomainModel()
    {
        // Arrange
        var domainModel = (ShoppingListItem)ShoppingListItem.FromPrimitiveTypes(
            2,
            "Water",
            "Still",
            null
        );

        // Act
        var dto = domainModel.MapToDto();

        // Assert
        dto.BoughtAt.Should().BeNull();
    }
}
