namespace mahl.Server.Data;

using mahl.Server.Data.DatabaseTypes;

public static class SeedDataExtensions
{
    public static async Task SeedDatabase(this WebApplication app)
    {
        using var scope = app.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<MahlDbContext>();

        if (db.Ingredients.Any())
            return; // Already seeded

        // ============================================================
        // 1. INGREDIENTS
        // ============================================================
        var ingredients = new List<IngredientDbType>
        {
            // Basis-Zutaten (AlwaysInStock = true)
            new() { Name = "Salz",          DefaultUnit = "g",       AlwaysInStock = true  },
            new() { Name = "Pfeffer",        DefaultUnit = "g",       AlwaysInStock = true  },
            new() { Name = "Olivenöl",       DefaultUnit = "ml",      AlwaysInStock = true  },
            new() { Name = "Zucker",         DefaultUnit = "g",       AlwaysInStock = true  },
            // Grundzutaten
            new() { Name = "Mehl",           DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Butter",         DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Eier",           DefaultUnit = "Stück",   AlwaysInStock = false },
            new() { Name = "Milch",          DefaultUnit = "ml",      AlwaysInStock = false },
            // Gemüse & Kräuter
            new() { Name = "Zwiebel",        DefaultUnit = "Stück",   AlwaysInStock = false },
            new() { Name = "Knoblauch",      DefaultUnit = "Zehe",    AlwaysInStock = false },
            new() { Name = "Paprika",        DefaultUnit = "Stück",   AlwaysInStock = false },
            new() { Name = "Tomaten",        DefaultUnit = "Stück",   AlwaysInStock = false },
            new() { Name = "Kürbis (Hokkaido)", DefaultUnit = "g",   AlwaysInStock = false },
            new() { Name = "Pilze",          DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Petersilie",     DefaultUnit = "EL",      AlwaysInStock = false },
            new() { Name = "Basilikum",      DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Frühlingszwiebeln", DefaultUnit = "Bund", AlwaysInStock = false },
            // Hülsenfrüchte & Getreide
            new() { Name = "Rote Linsen",    DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Kidneybohnen (Dose)", DefaultUnit = "Dose", AlwaysInStock = false },
            new() { Name = "Mais (Dose)",    DefaultUnit = "Dose",    AlwaysInStock = false },
            new() { Name = "Risottoreis",    DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Gnocchi",        DefaultUnit = "g",       AlwaysInStock = false },
            // Milchprodukte
            new() { Name = "Sahne",          DefaultUnit = "ml",      AlwaysInStock = false },
            new() { Name = "Emmentaler",     DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Parmesan",       DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Mozzarella (Streukäse)", DefaultUnit = "g", AlwaysInStock = false },
            new() { Name = "Schafskäse",     DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Kräuterfrischkäse", DefaultUnit = "g",   AlwaysInStock = false },
            new() { Name = "Creme Fraiche",  DefaultUnit = "g",       AlwaysInStock = false },
            // Konserven & Fertigprodukte
            new() { Name = "Tomaten (passiert)", DefaultUnit = "ml",  AlwaysInStock = false },
            new() { Name = "Tomatenmark",    DefaultUnit = "EL",      AlwaysInStock = false },
            new() { Name = "Gemüsebrühe",    DefaultUnit = "ml",      AlwaysInStock = false },
            new() { Name = "Blätterteig (Rolle)", DefaultUnit = "Stück", AlwaysInStock = false },
            // Gewürze & Backen
            new() { Name = "Paprikapulver",  DefaultUnit = "TL",      AlwaysInStock = false },
            new() { Name = "Muskat",         DefaultUnit = "Prise",   AlwaysInStock = false },
            new() { Name = "Kräuter der Provence", DefaultUnit = "TL", AlwaysInStock = false },
            new() { Name = "Currypulver",    DefaultUnit = "EL",      AlwaysInStock = false },
            new() { Name = "Backpulver",     DefaultUnit = "TL",      AlwaysInStock = false },
            new() { Name = "Vanillezucker",  DefaultUnit = "Pck",     AlwaysInStock = false },
            new() { Name = "Puderzucker",    DefaultUnit = "TL",      AlwaysInStock = false },
            // Sonstiges
            new() { Name = "Hackfleisch",    DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Trocken-Hefe",   DefaultUnit = "g",       AlwaysInStock = false },
            new() { Name = "Käse (Scheiben)", DefaultUnit = "Scheiben", AlwaysInStock = false },
            new() { Name = "Gewürzgurken",   DefaultUnit = "Stück",   AlwaysInStock = false },
            new() { Name = "Röstzwiebeln",   DefaultUnit = "g",       AlwaysInStock = false },
        };

        db.Ingredients.AddRange(ingredients);
        await db.SaveChangesAsync();

        // Helper: get ingredient by 1-based index (matching SQL seed order)
        IngredientDbType Ing(int oneBasedIndex) => ingredients[oneBasedIndex - 1];

        // ============================================================
        // 2. RECIPES with ingredients and steps
        // ============================================================

        var chiliSinCarne = new RecipeDbType
        {
            Title = "Chili sin Carne",
            SourceUrl = "https://emmikochteinfach.de/chili-sin-carne-rezept-schnell-einfach/",
            Ingredients =
            [
                new() { Ingredient = Ing(18), Quantity = 125,  Unit = "g"      },
                new() { Ingredient = Ing(32), Quantity = 250,  Unit = "ml"     },
                new() { Ingredient = Ing(11), Quantity = 1,    Unit = "Stück"  },
                new() { Ingredient = Ing(10), Quantity = 2,    Unit = "Zehe"   },
                new() { Ingredient = Ing(9),  Quantity = 1,    Unit = "Stück"  },
                new() { Ingredient = Ing(19), Quantity = 2,    Unit = "Dose"   },
                new() { Ingredient = Ing(20), Quantity = 1,    Unit = "Dose"   },
                new() { Ingredient = Ing(30), Quantity = 1,    Unit = "Dose"   },
                new() { Ingredient = Ing(31), Quantity = 2,    Unit = "EL"     },
                new() { Ingredient = Ing(34), Quantity = 2,    Unit = "TL"     },
                new() { Ingredient = Ing(1),  Quantity = 1,    Unit = "TL"     },
                new() { Ingredient = Ing(4),  Quantity = 1,    Unit = "Prise"  },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Die Kidneybohnen abwaschen (so werden sie bekömmlicher), den Mais abtropfen lassen. Zwiebel, Knoblauch und Paprika fein würfeln." },
                new() { StepNumber = 2, Instruction = "Olivenöl in einem großen Topf erhitzen und darin Zwiebel, Knoblauch und Paprikawürfel gemeinsam 2-3 Minuten andünsten. Rote Linsen sowie 2 EL Tomatenmark hineingeben, verrühren und kurz andünsten." },
                new() { StepNumber = 3, Instruction = "Mit Gemüsebrühe ablöschen. Stückige Tomaten sowie die Kidneybohnen und den Mais dazugeben. Mit Paprikapulver, 1 TL Salz und 1 Prise Zucker würzen." },
                new() { StepNumber = 4, Instruction = "Alles gut miteinander verrühren und mit halb geöffnetem Deckel bei mittlerer Hitze für 15 Minuten köcheln lassen. Ab und zu umrühren. Zum Schluss noch einmal abschmecken." },
            ],
        };

        var lasagne = new RecipeDbType
        {
            Title = "Lasagne",
            Ingredients =
            [
                new() { Ingredient = Ing(9),  Quantity = 1,   Unit = "Stück"  },
                new() { Ingredient = Ing(10), Quantity = 2,   Unit = "Zehe"   },
                new() { Ingredient = Ing(30), Quantity = 1,   Unit = "Pkg"    },
                new() { Ingredient = Ing(18), Quantity = 150, Unit = "g"      },
                new() { Ingredient = Ing(32), Quantity = 300, Unit = "ml"     },
                new() { Ingredient = Ing(26), Quantity = 200, Unit = "g"      },
                new() { Ingredient = Ing(3),  Quantity = 2,   Unit = "EL"     },
                new() { Ingredient = Ing(1),  Quantity = 1,   Unit = "TL"     },
                new() { Ingredient = Ing(2),  Quantity = 1,   Unit = "Prise"  },
                new() { Ingredient = Ing(36), Quantity = 1,   Unit = "TL"     },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Zwiebeln und Knoblauch schälen, kleinschneiden, und in Olivenöl glasig braten." },
                new() { StepNumber = 2, Instruction = "Passierte Tomaten, rote Linsen und Gemüsebrühe hinzugeben. Mit den Gewürzen abschmecken und 25 Minuten köcheln lassen. Bei Bedarf mit Tomatenmark andicken." },
                new() { StepNumber = 3, Instruction = "In der Zwischenzeit Nudeln und Béchamelsauce zubereiten." },
                new() { StepNumber = 4, Instruction = "Den Backofen auf 180 °C Umluft vorheizen. Abwechselnd Sauce, Nudelplatte und Béchamelsauce schichten. Am Schluss mit dem Streukäse bedecken und für 30 Minuten im Backofen backen." },
            ],
        };

        var kaesespätzle = new RecipeDbType
        {
            Title = "Käsespätzle",
            Ingredients =
            [
                new() { Ingredient = Ing(5),  Quantity = 300, Unit = "g"      },
                new() { Ingredient = Ing(7),  Quantity = 3,   Unit = "Stück"  },
                new() { Ingredient = Ing(9),  Quantity = 1,   Unit = "Stück"  },
                new() { Ingredient = Ing(24), Quantity = 200, Unit = "g"      },
                new() { Ingredient = Ing(6),  Quantity = 1,   Unit = "EL"     },
                new() { Ingredient = Ing(23), Quantity = 100, Unit = "g"      },
                new() { Ingredient = Ing(1),  Quantity = 1,   Unit = "Prise"  },
                new() { Ingredient = Ing(2),  Quantity = 1,   Unit = "Prise"  },
                new() { Ingredient = Ing(35), Quantity = 1,   Unit = "Prise"  },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Das Mehl mit den Eier, dem Wasser, dem Muskat und etwas Salz vermengen. Anschließend 5 Minuten stehen lassen. Viel Wasser zum Kochen bringen und salzen." },
                new() { StepNumber = 2, Instruction = "Den Spätzleteig auf ein Brett geben und das in kleinen Würsten in das Wasser schaben. 2-3 Minuten kochen lassen. Anschließend herausnehmen und abtropfen lassen." },
                new() { StepNumber = 3, Instruction = "Die Zwiebel kleinschneiden und in der Butter kurz anbraten. Mit Sahne aufgießen. Die Spätzle und den Käse hinzugeben. Mit Salz, Pfeffer und Muskat abschmecken." },
            ],
        };

        var pilzRisotto = new RecipeDbType
        {
            Title = "Pilz-Risotto",
            Ingredients =
            [
                new() { Ingredient = Ing(14), Quantity = 250,  Unit = "g"      },
                new() { Ingredient = Ing(6),  Quantity = 50,   Unit = "g"      },
                new() { Ingredient = Ing(9),  Quantity = 1,    Unit = "Stück"  },
                new() { Ingredient = Ing(10), Quantity = 1,    Unit = "Zehe"   },
                new() { Ingredient = Ing(15), Quantity = 1,    Unit = "EL"     },
                new() { Ingredient = Ing(21), Quantity = 250,  Unit = "g"      },
                new() { Ingredient = Ing(32), Quantity = 1000, Unit = "ml"     },
                new() { Ingredient = Ing(1),  Quantity = 1,    Unit = "Prise"  },
                new() { Ingredient = Ing(2),  Quantity = 1,    Unit = "Prise"  },
                new() { Ingredient = Ing(25), Quantity = 50,   Unit = "g"      },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Zwiebel und Knoblauch fein würfeln, Pilze in Scheiben schneiden." },
                new() { StepNumber = 2, Instruction = "Die Hälfte der Butter in einem Topf zerlassen. Dann die Zwiebel und Knoblauch darin schmoren. Wenn die Zwiebel weich und goldgelb ist, die Petersilie und die Pilze hinzugeben. Bei mäßiger Hitze einige Minuten garen." },
                new() { StepNumber = 3, Instruction = "Den Reis hinzufügen und ein paar Minuten unter ständigem Rühren braten." },
                new() { StepNumber = 4, Instruction = "1/8 l Brühe hinzugeben und bei mittlerer Hitze kochen lassen, bis die Brühe vollständig absorbiert ist. Den Vorgang wiederholen bis die Brühe aufgebraucht ist." },
                new() { StepNumber = 5, Instruction = "Die restliche Butter und den Parmesan unterrühren. Mit Salz und Pfeffer würzen." },
            ],
        };

        var gnocchiKürbisAuflauf = new RecipeDbType
        {
            Title = "Gnocchi-Kürbis-Auflauf",
            Ingredients =
            [
                new() { Ingredient = Ing(41), Quantity = 300, Unit = "g"      },
                new() { Ingredient = Ing(9),  Quantity = 1,   Unit = "Stück"  },
                new() { Ingredient = Ing(10), Quantity = 1,   Unit = "Zehe"   },
                new() { Ingredient = Ing(31), Quantity = 1,   Unit = "EL"     },
                new() { Ingredient = Ing(32), Quantity = 250, Unit = "ml"     },
                new() { Ingredient = Ing(13), Quantity = 300, Unit = "g"      },
                new() { Ingredient = Ing(29), Quantity = 100, Unit = "g"      },
                new() { Ingredient = Ing(22), Quantity = 500, Unit = "g"      },
                new() { Ingredient = Ing(26), Quantity = 200, Unit = "g"      },
                new() { Ingredient = Ing(16), Quantity = 5,   Unit = "g"      },
                new() { Ingredient = Ing(1),  Quantity = 1,   Unit = "Prise"  },
                new() { Ingredient = Ing(2),  Quantity = 1,   Unit = "Prise"  },
                new() { Ingredient = Ing(37), Quantity = 1,   Unit = "EL"     },
                new() { Ingredient = Ing(3),  Quantity = 1,   Unit = "EL"     },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Den Kürbis würfeln, Zwiebel und Knoblauch hacken." },
                new() { StepNumber = 2, Instruction = "Die Gnocchi kochen. Währenddessen Zwiebel und Knoblauch in einer Pfanne mit etwas Öl anschwitzen. Das Hackfleisch zugeben und krümelig braten. Mit Salz, Pfeffer und Currypulver würzig abschmecken." },
                new() { StepNumber = 3, Instruction = "Das Tomatenmark zugeben und kurz mitrösten lassen. Die Gemüsebrühe angießen und den würfelig geschnittenen Kürbis ebenfalls zugeben. Zugedeckt ca. 5 Minuten dünsten lassen." },
                new() { StepNumber = 4, Instruction = "Danach Creme Fraiche, Basilikum und die Gnocchi zugeben und alles gut miteinander vermischen. In eine Auflaufform füllen und den Mozzarella darüber verteilen." },
                new() { StepNumber = 5, Instruction = "Im vorgeheizten Backofen bei 180°C Umluft ca. 15 Minuten überbacken." },
            ],
        };

        var burger = new RecipeDbType
        {
            Title = "Burger",
            Ingredients =
            [
                new() { Ingredient = Ing(43), Quantity = 6,  Unit = "Scheiben" },
                new() { Ingredient = Ing(12), Quantity = 1,  Unit = "Stück"    },
                new() { Ingredient = Ing(44), Quantity = 6,  Unit = "Stück"    },
                new() { Ingredient = Ing(45), Quantity = 50, Unit = "g"        },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Burger-Buns und Linsenbratlinge zubereiten. Die Linsenbratlinge dabei mit dem Käse bedeckt braten." },
                new() { StepNumber = 2, Instruction = "Tomaten und Gewürzgurken kleinschneiden." },
                new() { StepNumber = 3, Instruction = "Burger-Buns aufschneiden, mit Sauce bestreichen, Linsenbratlinge, Tomaten, Gewürzgurken und Röstzwiebeln belegen." },
            ],
        };

        var blätterteigFrühling = new RecipeDbType
        {
            Title = "Blätterteigschnecken (Frühling)",
            Ingredients =
            [
                new() { Ingredient = Ing(33), Quantity = 1, Unit = "Stück"  },
                new() { Ingredient = Ing(17), Quantity = 1, Unit = "Bund"   },
                new() { Ingredient = Ing(28), Quantity = 200, Unit = "g"    },
                new() { Ingredient = Ing(1),  Quantity = 1, Unit = "Prise"  },
                new() { Ingredient = Ing(2),  Quantity = 1, Unit = "Prise"  },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Frühlingszwiebeln kleinhacken und mit Kräuterfrischkäse, Pfeffer und Salz vermengen." },
                new() { StepNumber = 2, Instruction = "Blätterteig ausrollen und Füllung gleichmäßig darauf verteilen." },
                new() { StepNumber = 3, Instruction = "Alles einrollen und in etwa 0,5-1 cm dicke Scheiben schneiden." },
                new() { StepNumber = 4, Instruction = "Die Schnecken auf einem Blech verteilen und 25 Minuten bei 200°C backen." },
            ],
        };

        var blätterteigSchaf = new RecipeDbType
        {
            Title = "Blätterteigschnecken (Schaf)",
            Ingredients =
            [
                new() { Ingredient = Ing(33), Quantity = 1,   Unit = "Stück"  },
                new() { Ingredient = Ing(12), Quantity = 2,   Unit = "Stück"  },
                new() { Ingredient = Ing(27), Quantity = 150, Unit = "g"      },
                new() { Ingredient = Ing(1),  Quantity = 1,   Unit = "Prise"  },
                new() { Ingredient = Ing(2),  Quantity = 1,   Unit = "Prise"  },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Tomaten und Schafskäse kleinhacken, gut vermengen und mit Pfeffer und Salz abschmecken." },
                new() { StepNumber = 2, Instruction = "Blätterteig ausrollen und Füllung gleichmäßig darauf verteilen." },
                new() { StepNumber = 3, Instruction = "Alles einrollen und in etwa 0,5-1 cm dicke Scheiben schneiden." },
                new() { StepNumber = 4, Instruction = "Die Schnecken auf einem Blech verteilen und 25 Minuten bei 200°C backen." },
            ],
        };

        var waffeln = new RecipeDbType
        {
            Title = "Waffeln",
            SourceUrl = "https://www.chefkoch.de/rezepte/662351168076093/Geheimes-Waffelrezept.html",
            Ingredients =
            [
                new() { Ingredient = Ing(4),  Quantity = 100,  Unit = "g"      },
                new() { Ingredient = Ing(6),  Quantity = 100,  Unit = "g"      },
                new() { Ingredient = Ing(7),  Quantity = 2,    Unit = "Stück"  },
                new() { Ingredient = Ing(39), Quantity = 0.5m, Unit = "Pck"    },
                new() { Ingredient = Ing(5),  Quantity = 200,  Unit = "g"      },
                new() { Ingredient = Ing(38), Quantity = 1,    Unit = "TL"     },
                new() { Ingredient = Ing(1),  Quantity = 1,    Unit = "Prise"  },
                new() { Ingredient = Ing(8),  Quantity = 200,  Unit = "ml"     },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Eier mit Zucker und Butter schaumig rühren." },
                new() { StepNumber = 2, Instruction = "Mehl, Backpulver und Salz dazugeben und verrühren." },
                new() { StepNumber = 3, Instruction = "Nach und nach die Milch unterrühren." },
                new() { StepNumber = 4, Instruction = "Im Waffeleisen einzeln abbacken." },
            ],
        };

        var pizzateig = new RecipeDbType
        {
            Title = "Pizzateig",
            Ingredients =
            [
                new() { Ingredient = Ing(5),  Quantity = 420, Unit = "g"   },
                new() { Ingredient = Ing(42), Quantity = 1,   Unit = "g"   },
                new() { Ingredient = Ing(1),  Quantity = 6,   Unit = "g"   },
                new() { Ingredient = Ing(40), Quantity = 1,   Unit = "TL"  },
            ],
            Steps =
            [
                new() { StepNumber = 1, Instruction = "Die Zutaten (Mehl, lauwarmes Wasser, Hefe, Salz, Puderzucker) zu einem leicht klebrigen Teig verkneten." },
                new() { StepNumber = 2, Instruction = "Bei Zimmertemperatur mindestens 3 Stunden gehen lassen, besser noch für 24 Stunden im Kühlschrank gehen lassen und ein bis zwei Stunden vor dem Backen aus dem Kühlschrank nehmen." },
                new() { StepNumber = 3, Instruction = "Den Teig nochmals kurz kneten und bis zur Verwendung bei Zimmertemperatur nochmals gehen lassen." },
                new() { StepNumber = 4, Instruction = "Den Teig in zwei Teile teilen, ausrollen, und nach Belieben belegen." },
            ],
        };

        db.Recipes.AddRange(chiliSinCarne, lasagne, kaesespätzle, pilzRisotto, gnocchiKürbisAuflauf,
                            burger, blätterteigFrühling, blätterteigSchaf, waffeln, pizzateig);
        await db.SaveChangesAsync();
    }
}
