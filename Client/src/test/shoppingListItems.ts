import { screen, within } from '@testing-library/react'

// Je Eintrag der Liste "Einkaufsliste" die nicht-leeren Textzeilen (Blatt-Elemente): Name, darunter die Menge.
// Blätter ohne Text (z.B. ein Icon) zählen nicht. Voraussetzung: Name und Menge sind getrennte Elemente.
export const listedItems = (): string[][] => within(screen.getByRole('list', { name: 'Einkaufsliste' }))
  .getAllByRole('listitem')
  .map((item) => [...item.querySelectorAll('*')]
    .filter((el) => el.children.length === 0)
    .map((el) => el.textContent)
    .filter((text) => text !== ''))
