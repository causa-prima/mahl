-- ============================================================================
-- SEED DATA für Mahl-App (SKELETON Phase)
-- ============================================================================
-- Generiert aus echten Rezepten der Familie
-- Verwendung: dotnet run --seed-data
-- ============================================================================

-- ============================================================================
-- 1. INGREDIENTS (Zutaten)
-- ============================================================================
-- Standard-Zutaten die in vielen Rezepten vorkommen + spezifische Zutaten

INSERT INTO "Ingredient" ("Name", "DefaultUnit", "AlwaysInStock", "DeletedAt") VALUES
-- Basis-Zutaten (AlwaysInStock = true)
('Salz', 'g', true, NULL),
('Pfeffer', 'g', true, NULL),
('Olivenöl', 'ml', true, NULL),
('Zucker', 'g', true, NULL),
('Mehl', 'g', false, NULL),
('Butter', 'g', false, NULL),
('Eier', 'Stück', false, NULL),
('Milch', 'ml', false, NULL),

-- Gemüse & Kräuter
('Zwiebel', 'Stück', false, NULL),
('Knoblauch', 'Zehe', false, NULL),
('Paprika', 'Stück', false, NULL),
('Tomaten', 'Stück', false, NULL),
('Kürbis (Hokkaido)', 'g', false, NULL),
('Pilze', 'g', false, NULL),
('Petersilie', 'EL', false, NULL),
('Basilikum', 'g', false, NULL),
('Frühlingszwiebeln', 'Bund', false, NULL),

-- Hülsenfrüchte & Getreide
('Rote Linsen', 'g', false, NULL),
('Kidneybohnen (Dose)', 'Dose', false, NULL),
('Mais (Dose)', 'Dose', false, NULL),
('Risottoreis', 'g', false, NULL),
('Gnocchi', 'g', false, NULL),

-- Milchprodukte
('Sahne', 'ml', false, NULL),
('Emmentaler', 'g', false, NULL),
('Parmesan', 'g', false, NULL),
('Mozzarella (Streukäse)', 'g', false, NULL),
('Schafskäse', 'g', false, NULL),
('Kräuterfrischkäse', 'g', false, NULL),
('Creme Fraiche', 'g', false, NULL),

-- Konserven & Fertigprodukte
('Tomaten (passiert)', 'ml', false, NULL),
('Tomatenmark', 'EL', false, NULL),
('Gemüsebrühe', 'ml', false, NULL),
('Blätterteig (Rolle)', 'Stück', false, NULL),

-- Gewürze & Backen
('Paprikapulver', 'TL', false, NULL),
('Muskat', 'Prise', false, NULL),
('Kräuter der Provence', 'TL', false, NULL),
('Currypulver', 'EL', false, NULL),
('Backpulver', 'TL', false, NULL),
('Vanillezucker', 'Pck', false, NULL),
('Puderzucker', 'TL', false, NULL),

-- Sonstiges
('Hackfleisch', 'g', false, NULL),
('Trocken-Hefe', 'g', false, NULL),
('Käse (Scheiben)', 'Scheiben', false, NULL),
('Gewürzgurken', 'Stück', false, NULL),
('Röstzwiebeln', 'g', false, NULL);

-- ============================================================================
-- 2. RECIPES (Rezepte)
-- ============================================================================

INSERT INTO "Recipe" ("Title", "Source", "BasePortionAmount", "BasePortionUnit", "DeletedAt") VALUES
('Chili sin Carne', 'https://emmikochteinfach.de/chili-sin-carne-rezept-schnell-einfach/', 2, 'Personen', NULL),
('Lasagne', NULL, 4, 'Personen', NULL),
('Käsespätzle', NULL, 2, 'Personen', NULL),
('Pilz-Risotto', NULL, 2, 'Personen', NULL),
('Gnocchi-Kürbis-Auflauf', NULL, 2, 'Personen', NULL),
('Burger', NULL, 2, 'Personen', NULL),
('Blätterteigschnecken (Frühling)', NULL, 12, 'Stück', NULL),
('Blätterteigschnecken (Schaf)', NULL, 12, 'Stück', NULL),
('Waffeln', 'https://www.chefkoch.de/rezepte/662351168076093/Geheimes-Waffelrezept.html', 2, 'Personen', NULL),
('Pizzateig', NULL, 2, 'Pizzen', NULL);

-- ============================================================================
-- 3. RECIPE INGREDIENTS (Rezept-Zutaten-Zuordnung)
-- ============================================================================
-- Annahme: RecipeId startet bei 1, IngredientId startet bei 1

-- Rezept 1: Chili sin Carne
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(1, 18, 125, 'g'),      -- Rote Linsen
(1, 32, 250, 'ml'),     -- Gemüsebrühe
(1, 11, 1, 'Stück'),    -- Paprika
(1, 10, 2, 'Zehe'),     -- Knoblauch
(1, 9, 1, 'Stück'),     -- Zwiebel
(1, 19, 2, 'Dose'),     -- Kidneybohnen
(1, 20, 1, 'Dose'),     -- Mais
(1, 30, 1, 'Dose'),     -- Tomaten (passiert)
(1, 31, 2, 'EL'),       -- Tomatenmark
(1, 34, 2, 'TL'),       -- Paprikapulver
(1, 1, 1, 'TL'),        -- Salz
(1, 4, 1, 'Prise');     -- Zucker

-- Rezept 2: Lasagne
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(2, 9, 1, 'Stück'),     -- Zwiebel
(2, 10, 2, 'Zehe'),     -- Knoblauch
(2, 30, 1, 'Pkg'),      -- Tomaten (passiert)
(2, 18, 150, 'g'),      -- Rote Linsen
(2, 32, 300, 'ml'),     -- Gemüsebrühe
(2, 26, 200, 'g'),      -- Mozzarella (Streukäse)
(2, 3, 2, 'EL'),        -- Olivenöl
(2, 1, 1, 'TL'),        -- Salz
(2, 2, 1, 'Prise'),     -- Pfeffer
(2, 36, 1, 'TL');       -- Kräuter der Provence

-- Rezept 3: Käsespätzle
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(3, 5, 300, 'g'),       -- Mehl
(3, 7, 3, 'Stück'),     -- Eier
(3, 9, 1, 'Stück'),     -- Zwiebel
(3, 24, 200, 'g'),      -- Emmentaler
(3, 6, 1, 'EL'),        -- Butter
(3, 23, 100, 'g'),      -- Sahne
(3, 1, 1, 'Prise'),     -- Salz
(3, 2, 1, 'Prise'),     -- Pfeffer
(3, 35, 1, 'Prise');    -- Muskat

-- Rezept 4: Pilz-Risotto
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(4, 14, 250, 'g'),      -- Pilze
(4, 6, 50, 'g'),        -- Butter
(4, 9, 1, 'Stück'),     -- Zwiebel
(4, 10, 1, 'Zehe'),     -- Knoblauch
(4, 15, 1, 'EL'),       -- Petersilie
(4, 21, 250, 'g'),      -- Risottoreis
(4, 32, 1000, 'ml'),    -- Gemüsebrühe
(4, 1, 1, 'Prise'),     -- Salz
(4, 2, 1, 'Prise'),     -- Pfeffer
(4, 25, 50, 'g');       -- Parmesan

-- Rezept 5: Gnocchi-Kürbis-Auflauf
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(5, 41, 300, 'g'),      -- Hackfleisch
(5, 9, 1, 'Stück'),     -- Zwiebel
(5, 10, 1, 'Zehe'),     -- Knoblauch
(5, 31, 1, 'EL'),       -- Tomatenmark
(5, 32, 250, 'ml'),     -- Gemüsebrühe
(5, 13, 300, 'g'),      -- Kürbis (Hokkaido)
(5, 29, 100, 'g'),      -- Creme Fraiche
(5, 22, 500, 'g'),      -- Gnocchi
(5, 26, 200, 'g'),      -- Mozzarella (Streukäse)
(5, 16, 5, 'g'),        -- Basilikum
(5, 1, 1, 'Prise'),     -- Salz
(5, 2, 1, 'Prise'),     -- Pfeffer
(5, 37, 1, 'EL'),       -- Currypulver
(5, 3, 1, 'EL');        -- Olivenöl

-- Rezept 6: Burger
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(6, 43, 6, 'Scheiben'), -- Käse (Scheiben)
(6, 12, 1, 'Stück'),    -- Tomaten
(6, 44, 6, 'Stück'),    -- Gewürzgurken
(6, 45, 50, 'g');       -- Röstzwiebeln

-- Rezept 7: Blätterteigschnecken (Frühling)
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(7, 33, 1, 'Stück'),    -- Blätterteig (Rolle)
(7, 17, 1, 'Bund'),     -- Frühlingszwiebeln
(7, 28, 200, 'g'),      -- Kräuterfrischkäse
(7, 1, 1, 'Prise'),     -- Salz
(7, 2, 1, 'Prise');     -- Pfeffer

-- Rezept 8: Blätterteigschnecken (Schaf)
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(8, 33, 1, 'Stück'),    -- Blätterteig (Rolle)
(8, 12, 2, 'Stück'),    -- Tomaten
(8, 27, 150, 'g'),      -- Schafskäse
(8, 1, 1, 'Prise'),     -- Salz
(8, 2, 1, 'Prise');     -- Pfeffer

-- Rezept 9: Waffeln
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(9, 4, 100, 'g'),       -- Zucker
(9, 6, 100, 'g'),       -- Butter
(9, 7, 2, 'Stück'),     -- Eier
(9, 39, 0.5, 'Pck'),    -- Vanillezucker
(9, 5, 200, 'g'),       -- Mehl
(9, 38, 1, 'TL'),       -- Backpulver
(9, 1, 1, 'Prise'),     -- Salz
(9, 8, 200, 'ml');      -- Milch

-- Rezept 10: Pizzateig
INSERT INTO "RecipeIngredient" ("RecipeId", "IngredientId", "Amount", "Unit") VALUES
(10, 5, 420, 'g'),      -- Mehl
(10, 42, 1, 'g'),       -- Trocken-Hefe
(10, 1, 6, 'g'),        -- Salz
(10, 40, 1, 'TL');      -- Puderzucker

-- ============================================================================
-- 4. RECIPE STEPS (Zubereitungsschritte)
-- ============================================================================

-- Rezept 1: Chili sin Carne
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(1, 1, 'Die Kidneybohnen abwaschen (so werden sie bekömmlicher), den Mais abtropfen lassen. Zwiebel, Knoblauch und Paprika fein würfeln.'),
(1, 2, 'Olivenöl in einem großen Topf erhitzen und darin Zwiebel, Knoblauch und Paprikawürfel gemeinsam 2-3 Minuten andünsten. Rote Linsen sowie 2 EL Tomatenmark hineingeben, verrühren und kurz andünsten.'),
(1, 3, 'Mit Gemüsebrühe ablöschen. Stückige Tomaten sowie die Kidneybohnen und den Mais dazugeben. Mit Paprikapulver, 1 TL Salz und 1 Prise Zucker würzen.'),
(1, 4, 'Alles gut miteinander verrühren und mit halb geöffnetem Deckel bei mittlerer Hitze für 15 Minuten köcheln lassen. Ab und zu umrühren. Zum Schluss noch einmal abschmecken.');

-- Rezept 2: Lasagne
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(2, 1, 'Zwiebeln und Knoblauch schälen, kleinschneiden, und in Olivenöl glasig braten.'),
(2, 2, 'Passierte Tomaten, rote Linsen und Gemüsebrühe hinzugeben. Mit den Gewürzen abschmecken und 25 Minuten köcheln lassen. Bei Bedarf mit Tomatenmark andicken.'),
(2, 3, 'In der Zwischenzeit Nudeln und Béchamelsauce zubereiten.'),
(2, 4, 'Den Backofen auf 180 °C Umluft vorheizen. Abwechselnd Sauce, Nudelplatte und Béchamelsauce schichten. Am Schluss mit dem Streukäse bedecken und für 30 Minuten im Backofen backen.');

-- Rezept 3: Käsespätzle
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(3, 1, 'Das Mehl mit den Eier, dem Wasser, dem Muskat und etwas Salz vermengen. Anschließend 5 Minuten stehen lassen. Viel Wasser zum Kochen bringen und salzen.'),
(3, 2, 'Den Spätzleteig auf ein Brett geben und das in kleinen Würsten in das Wasser schaben. 2-3 Minuten kochen lassen. Anschließend herausnehmen und abtropfen lassen.'),
(3, 3, 'Die Zwiebel kleinschneiden und in der Butter kurz anbraten. Mit Sahne aufgießen. Die Spätzle und den Käse hinzugeben. Mit Salz, Pfeffer und Muskat abschmecken.');

-- Rezept 4: Pilz-Risotto
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(4, 1, 'Zwiebel und Knoblauch fein würfeln, Pilze in Scheiben schneiden.'),
(4, 2, 'Die Hälfte der Butter in einem Topf zerlassen. Dann die Zwiebel und Knoblauch darin schmoren. Wenn die Zwiebel weich und goldgelb ist, die Petersilie und die Pilze hinzugeben. Bei mäßiger Hitze einige Minuten garen.'),
(4, 3, 'Den Reis hinzufügen und ein paar Minuten unter ständigem Rühren braten.'),
(4, 4, '1/8 l Brühe hinzugeben und bei mittlerer Hitze kochen lassen, bis die Brühe vollständig absorbiert ist. Den Vorgang wiederholen bis die Brühe aufgebraucht ist.'),
(4, 5, 'Die restliche Butter und den Parmesan unterrühren. Mit Salz und Pfeffer würzen.');

-- Rezept 5: Gnocchi-Kürbis-Auflauf
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(5, 1, 'Den Kürbis würfeln, Zwiebel und Knoblauch hacken.'),
(5, 2, 'Die Gnocchi kochen. Währenddessen Zwiebel und Knoblauch in einer Pfanne mit etwas Öl anschwitzen. Das Hackfleisch zugeben und krümelig braten. Mit Salz, Pfeffer und Currypulver würzig abschmecken.'),
(5, 3, 'Das Tomatenmark zugeben und kurz mitrösten lassen. Die Gemüsebrühe angießen und den würfelig geschnittenen Kürbis ebenfalls zugeben. Zugedeckt ca. 5 Minuten dünsten lassen.'),
(5, 4, 'Danach Creme Fraiche, Basilikum und die Gnocchi zugeben und alles gut miteinander vermischen. In eine Auflaufform füllen und den Mozzarella darüber verteilen.'),
(5, 5, 'Im vorgeheizten Backofen bei 180°C Umluft ca. 15 Minuten überbacken.');

-- Rezept 6: Burger
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(6, 1, 'Burger-Buns und Linsenbratlinge zubereiten. Die Linsenbratlinge dabei mit dem Käse bedeckt braten.'),
(6, 2, 'Tomaten und Gewürzgurken kleinschneiden.'),
(6, 3, 'Burger-Buns aufschneiden, mit Sauce bestreichen, Linsenbratlinge, Tomaten, Gewürzgurken und Röstzwiebeln belegen.');

-- Rezept 7: Blätterteigschnecken (Frühling)
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(7, 1, 'Frühlingszwiebeln kleinhacken und mit Kräuterfrischkäse, Pfeffer und Salz vermengen.'),
(7, 2, 'Blätterteig ausrollen und Füllung gleichmäßig darauf verteilen.'),
(7, 3, 'Alles einrollen und in etwa 0,5-1 cm dicke Scheiben schneiden.'),
(7, 4, 'Die Schnecken auf einem Blech verteilen und 25 Minuten bei 200°C backen.');

-- Rezept 8: Blätterteigschnecken (Schaf)
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(8, 1, 'Tomaten und Schafskäse kleinhacken, gut vermengen und mit Pfeffer und Salz abschmecken.'),
(8, 2, 'Blätterteig ausrollen und Füllung gleichmäßig darauf verteilen.'),
(8, 3, 'Alles einrollen und in etwa 0,5-1 cm dicke Scheiben schneiden.'),
(8, 4, 'Die Schnecken auf einem Blech verteilen und 25 Minuten bei 200°C backen.');

-- Rezept 9: Waffeln
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(9, 1, 'Eier mit Zucker und Butter schaumig rühren.'),
(9, 2, 'Mehl, Backpulver und Salz dazugeben und verrühren.'),
(9, 3, 'Nach und nach die Milch unterrühren.'),
(9, 4, 'Im Waffeleisen einzeln abbacken.');

-- Rezept 10: Pizzateig
INSERT INTO "RecipeStep" ("RecipeId", "StepNumber", "Description") VALUES
(10, 1, 'Die Zutaten (Mehl, lauwarmes Wasser, Hefe, Salz, Puderzucker) zu einem leicht klebrigen Teig verkneten.'),
(10, 2, 'Bei Zimmertemperatur mindestens 3 Stunden gehen lassen, besser noch für 24 Stunden im Kühlschrank gehen lassen und ein bis zwei Stunden vor dem Backen aus dem Kühlschrank nehmen.'),
(10, 3, 'Den Teig nochmals kurz kneten und bis zur Verwendung bei Zimmertemperatur nochmals gehen lassen.'),
(10, 4, 'Den Teig in zwei Teile teilen, ausrollen, und nach Belieben belegen.');

-- ============================================================================
-- SEED DATA ENDE
-- ============================================================================
-- Hinweis: Sub-Rezepte (Linsenbratlinge, Burger-Buns, Béchamelsauce) sind
-- hier NICHT enthalten, da sie separate Rezepte wären. In SKELETON werden
-- diese als einfache Text-Notizen in den Schritten belassen.
-- ============================================================================
