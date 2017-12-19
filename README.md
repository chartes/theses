Theses de l'Ecole 
===

## Missions

- Capitainiser les textes
- Attributions des identifiants (URN)
- Développement des métadonnées des `__cts__.xml` 
	- Y compris l'ensemble des métadonnées DC pour les oeuvres via `cpt:structured-metadata`

## Schéma à modifier

- Insérer des `change` (Exemple : https://github.com/PerseusDL/canonical-latinLit/blob/master/data/phi0134/phi002/phi0134.phi002.perseus-lat2.xml#L78-L99) 
- Redéfinir le schéma RNG 
	- Proposer des changements à faire avec Vincent Jolivet @editions
	- Restructuration du noeud `/TEI/text` (back et front par exemple)
	- Modèle de métadonnées pour exprimer ce qui est dans le CSV
	- En nécessaire très certainement : ajout de l'attribut `@n` pour les `div` voire `p`
- (Optionnel) Insérer les métadonnées dans le fichier TEI à partir du CSV

## Notes

Référent : Vincent Jolivet, @editions

- Difficulté : 6/10
- Répétitivité : 6/10
- Schéma à utiliser : TEI
- Equipe plus grande acceptée : jusque 6 à 8 personnes.
