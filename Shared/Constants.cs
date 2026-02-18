namespace mahl.Shared;

public static class Constants
{
    public const int NumberOfSearchSuggestions = 50;
    public const int ShoppingListTitleMaxLength = 30;
    public const int ShoppingListDescriptionMaxLength = 100;
    public const string TraceIdString = "TraceId";
}

public static class RouteBases
{
    public const string ShoppingList = "/api/shoppingList";
    public const string ShoppingListItem = "/api/shoppingListItem";
    public const string Suggestions = "/api/suggestions";
}
