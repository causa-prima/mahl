namespace mahl.Shared;
using System.Collections.Generic;

public record struct BulkUpdateResult(IEnumerable<ShoppingListItem> UpdatedItems,
                                      IEnumerable<ShoppingListItem> FailedItems,
                                      IEnumerable<(ShoppingListItem item, string error)> ErrorItems) { }
