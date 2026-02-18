namespace mahl.Shared.Tests.Dtos;
using FluentAssertions;
using mahl.Shared.Dtos;
using mahl.Tests.Shared;
using NUnit.Framework;
using OneOf.Types;
using System;
using System.Collections.Generic;
using System.Collections.Immutable;

[TestFixture]
public class ShoppingListDtoTests
{
    [Test]
    public void Constructor_Sets_Properties_ToDefaultValues()
    {
        // Arrange

        // Act
        var result = new ShoppingListDto();

        // Assert
        result.Items.Should().BeEmpty();
    }

    private static IEnumerable<ShoppingListDto> ValidDtos()
    {
        yield return new ShoppingListDto();

        yield return new ShoppingListDto
        {
            Items = ImmutableList.Create(
                new ShoppingListItemDto
                {
                    Id = 1,
                    Title = "Eggs",
                    Description = "Free range",
                    BoughtAt = DateTimeOffset.UtcNow
                })
        };

        yield return new ShoppingListDto
        {
            Items = ImmutableList.Create(
                new ShoppingListItemDto
                {
                    Id = 1,
                    Title = "Eggs",
                    Description = "Free range",
                    BoughtAt = DateTimeOffset.UtcNow
                },
                new ShoppingListItemDto
                {
                    Id = null,
                    Title = "Cucumbers",
                    BoughtAt = null,
                })
        };
    }

    [Test, TestCaseSource(nameof(ValidDtos))]
    public void MapToDomain_Returns_DomainModel_When_DtoIsValid(ShoppingListDto dto)
    {
        // Arrange

        // Act
        var result = dto.MapToDomain();

        // Assert
        result.Switch(
            domainModel =>
            {
                domainModel.Items.Should().HaveCount(dto.Items.Count);
            },
            _ => Helpers.FailWithTypeMismatch(nameof(result), typeof(ShoppingList), _)
        );
    }

    private static IEnumerable<(ShoppingListDto Dto, string ErrorMessage)> InvalidDtos()
    {
        yield return (new ShoppingListDto
        {
            Items = ImmutableList.Create(new ShoppingListItemDto
            {
                Id = 1,
                Title = "",
                Description = "Free range",
                BoughtAt = DateTimeOffset.UtcNow
            }),
        }, "Value cannot be null, empty or white space.");


        yield return (new ShoppingListDto
        {
            Items = ImmutableList.Create(
                new ShoppingListItemDto
                {
                    Id = 1,
                    Title = "Eggs",
                    Description = "Free range",
                    BoughtAt = DateTimeOffset.UtcNow
                },
                new ShoppingListItemDto
                {
                    Id = 1,
                    Title = "Eggs",
                    Description = "Free range",
                    BoughtAt = DateTimeOffset.UtcNow.AddDays(-1)
                })
        }, "Item with id SyncItemId(1) already in list.");
    }

    [Test, TestCaseSource(nameof(InvalidDtos))]
    public void MapToDomain_Returns_Error_When_DtoIsInvalid((ShoppingListDto dto, string error) testdata)
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

        var item1 = (ShoppingListItem)ShoppingListItem.FromPrimitiveTypes(
            42,
            "Bread",
            "Wholegrain",
            now
        );

        var item2 = (ShoppingListItem)ShoppingListItem.FromPrimitiveTypes(
            null,
            "Milk",
            string.Empty,
            null
        );

        IEnumerable<ShoppingListItem> items = [item1, item2];
        var domainModel = (ShoppingListType)ShoppingList.Create(items);

        // Act
        var dto = domainModel.MapToDto();

        // Assert
        dto.Items.Should().HaveSameCount(items);
    }
}
