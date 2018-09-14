# Ecrire un devoir maison

Le format PLDM est un ensemble de déclaration de couple clé, valeur. 

Les clés suivante sont obligatoires:

'title' : Chaîne de caractère représentant le titre du devoir maison

'introduction': Chaîne de caractère représentant l'introduction du devoir maison

'maxmembers': Entier représentant le nombre d'étudiant par groupe

'id_course': Entier représentant l'identifiant du cours auquel le devoir est associé

'date.group': Date à laquelle les étudiants peuvent créer un groupe sous forme JJ/MM/AAAA-HH:mm

'date.deposit_end': Date à laquelle les étudiants doivent déposer leurs devoirs sous forme JJ/MM/AAAA-HH:mm

'deposit.number': Entier représentant le nombre de dépôt possible

'deposit.size': Entier représentant la taille maximale d'un dépôt

'deposit.late': Booléen indiquant si l'étudiant peut déposer en retard

'extension': String représentant l'extension du fichier à déposer

Exemple:

```
title=Prog C test
introduction==
Dans tout programme, le programmeur fait appel à des données. Ces données peuvent
prendre des valeurs qui peuvent évoluer pendant toute l’exécution du programme. On
parle alors de variables . Une variable a un type qui détermine les valeurs que la variable
peut prendre ainsi que les opérations pouvant s’y appliquer. Nous utiliserons les types
standards de C suivant : int, float et char.
==
maxmembers=3
date.group=29/09/2018-23:55
date.deposit_end=06/09/2019-16:34
deposit.number=2
deposit.size=10
deposit.late=False
id_course=1
extension=pdf
```

