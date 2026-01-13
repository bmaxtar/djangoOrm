from django.shortcuts import render
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F
from django.db.models import Count, Min, Max, Avg, Sum
from django.db.models import Value, F, Func, ExpressionWrapper, DecimalField
from django.db.models.functions import Concat
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db import connection
from store.models import Product
from tags.models import TaggedItem
from store.models import Product, Order, OrderItem, Customer, Collection


# ========== FONCTION PRINCIPALE ==========
def say_hello(request):
    """Fonction principale qui retourne la page d'accueil."""
    return render(request, 'hello.html', {'name': 'Maxtar'})


# ========== EXEMPLES DE REQUÊTES BASIQUES ==========
def basic_queries():
    """
    Exemples de requêtes basiques sur les produits :
    - Récupérer tous les produits
    - Itérer sur les résultats
    - Vérifier l'existence d'un produit
    """
    # Récupérer tous les produits du modèle
    query_set = Product.objects.all()
    
    # Itérer sur les produits et afficher chacun
    for product in query_set:
        print(product)
    
    # Vérifier si un produit avec l'ID 1 existe dans la base de données
    exists = Product.objects.filter(pk=1).exists()


# ========== EXEMPLES DE FILTRES SIMPLES ==========
def filter_queries():
    """
    Exemples de filtres simples :
    - Recherche par contenu (icontains)
    - Filtrer par condition numérique (lt = less than)
    - Chaîner plusieurs filtres
    """
    # Filtrer les produits dont le titre contient 'coffee' (insensible à la casse)
    queryset = Product.objects.filter(title__icontains='coffee')
    
    # Filtrer par deux conditions : l'inventaire < 10 ET le prix < 20
    queryset = Product.objects.filter(inventory__lt=10).filter(unit_price__lt=20)


# ========== EXEMPLES DE REQUÊTES AVEC OPÉRATEURS LOGIQUES ==========
def complex_filters():
    """
    Exemples avec les opérateurs logiques Q :
    - Utiliser l'opérateur OR (|)
    - Utiliser l'opérateur AND (&) et NOT (~)
    - Combiner plusieurs conditions
    """
    # Filtrer avec OR : inventaire < 10 OU prix < 20
    queryset = Product.objects.filter(
        Q(inventory__lt=10) | Q(unit_price__lt=20)
    )
    
    # Filtrer avec AND et NOT : inventaire < 10 ET SANS prix < 20
    # Le ~ signifie NOT (négation)
    queryset = Product.objects.filter(
        Q(inventory__lt=10) & ~Q(unit_price__lt=20)
    )
    
    # Filtrer en comparant deux champs : produits où inventaire = prix unitaire
    queryset = Product.objects.filter(inventory=F('unit_price'))


# ========== EXEMPLES DE COMMANDES DE TRI ==========
def ordering_queries():
    """
    Exemples de tri des données :
    - order_by() pour trier les résultats
    - earliest() et latest() pour récupérer des cas spécifiques
    """
    # Récupérer le produit avec le plus petit prix
    product = Product.objects.order_by('unit_price')[0]
    
    # Récupérer le produit ayant le prix minimum (méthode alternative)
    product = Product.objects.earliest('unit_price')[0]
    
    # Récupérer le produit ayant le prix maximum
    product = Product.objects.latest('unit_price')[0]


# ========== EXEMPLES DE PROJECTION (values et values_list) ==========
def projection_queries():
    """
    Exemples de sélection de colonnes spécifiques :
    - values_list() pour obtenir les données sous forme de tuples
    - Sélectionner des champs liés via les relations
    """
    # Récupérer seulement l'ID, titre et le titre de la collection associée
    product = Product.objects.values_list('id', 'title', 'collection__title')


# ========== EXEMPLES DE REQUÊTES IMBRIQUÉES ==========
def subquery_example():
    """
    Exemple de requête imbriquée :
    - Récupérer les produits qui ont des commandes
    - Trier et limiter les résultats
    """
    # Récupérer les produits commandés, sans doublons, triés par titre
    ordered_items = Product.objects.filter(
        id__in=OrderItem.objects.values('product_id').distinct()
    ).order_by('title')


# ========== EXEMPLES D'OPTIMISATION DE REQUÊTES ==========
def query_optimization():
    """
    Exemples d'optimisation pour éviter les requêtes SQL multiples :
    - select_related() pour les relations ForeignKey et OneToOne
    - prefetch_related() pour les relations ManyToMany et reverse ForeignKey
    """
    # Optimiser en récupérant la collection avec le produit (1 seule requête)
    product = Product.objects.select_related('collection').all()
    
    # Optimiser en récupérant les promotions et la collection avec les produits
    product = Product.objects.prefetch_related('promotions').select_related('collection').all()
    
    # Exemple plus complexe : récupérer les commandes avec client et articles avec produits
    orders = Order.objects.select_related('customer').prefetch_related('items__product').order_by('-placed_at')[:5]


# ========== EXEMPLES D'AGRÉGATIONS ==========
def aggregation_queries():
    """
    Exemples d'agrégations pour obtenir des statistiques :
    - Count : nombre d'éléments
    - Min/Max : valeurs minimum et maximum
    - Avg : moyenne
    - Sum : somme
    """
    # Obtenir les statistiques sur tous les produits
    result = Product.objects.aggregate(
        count=Count('id'),
        min_price=Min('unit_price'),
        max_price=Max('unit_price'),
        avg_price=Avg('unit_price'),
        sum_inventory=Sum('inventory')
    )
    
    # Obtenir les statistiques pour une collection spécifique (ID = 3)
    result = Product.objects.filter(collection__id=3).aggregate(
        count=Count('id'),
        min_price=Min('unit_price'),
        max_price=Max('unit_price'),
        avg_price=Avg('unit_price'),
        sum_inventory=Sum('inventory')
    )


# ========== EXEMPLES D'ANNOTATIONS ==========
def annotation_examples():
    """
    Exemples d'annotations pour ajouter des champs calculés :
    - Concaténer des champs (nom + prénom)
    - Compter les commandes par client
    - Créer des champs calculés avec expressions
    """
    # Créer un champ 'full_name' en concaténant prénom et nom
    queryset = Customer.objects.annotate(
        full_name=Func(F('first_name'), Value(' '), F('last_name'), function='CONCAT')
    )
    
    # Alternative plus simple avec Concat
    queryset = Customer.objects.annotate(
        full_name=Concat('first_name', Value(' '), 'last_name')
    )
    
    # Compter le nombre de commandes par client
    queryset = Customer.objects.annotate(
        orders_count=Count('order')
    )


# ========== EXEMPLES D'EXPRESSIONS COMPLEXES ==========
def expression_examples():
    """
    Exemples d'ExpressionWrapper pour les calculs complexes :
    - Calculer un prix réduit (20% de réduction)
    - Utiliser des opérations mathématiques
    """
    # Créer une expression pour calculer le prix avec 20% de réduction
    discounted_price = ExpressionWrapper(
        F('unit_price') * 0.8,
        output_field=DecimalField()
    )
    
    # Ajouter le prix réduit à chaque produit
    queryset = Product.objects.annotate(
        discounted_price=discounted_price
    )


# ========== EXEMPLE D'UTILISATION DE CONTENTTYPES ==========
def tagged_items_example():
    """
    Exemple d'utilisation des tags avec le ContentTypes framework :
    - Récupérer les tags associés à un produit
    """
    # Récupérer tous les tags du produit avec l'ID 1
    TaggedItem.objects.get_tags_for(Product, 1)


# ========== EXEMPLES D'ACCÈS AUX DONNÉES ==========
def data_access_examples():
    """
    Exemples d'accès aux données :
    - Accéder par index pour un seul résultat
    - Convertir en liste
    """
    # Récupérer tous les produits
    queryset = Product.objects.all()
    
    # Accéder au premier produit par index
    queryset[0]
    
    # Convertir le queryset en liste (évalue la requête)
    list(queryset)


# ========== EXEMPLES DE MISE À JOUR ==========
def update_examples():
    """
    Exemples de mise à jour d'objets :
    - Mettre à jour via save()
    - Mettre à jour via update() pour les opérations en masse
    """
    # Mettre à jour via save() : récupérer, modifier et sauvegarder
    collection = Collection.objects.get(pk=11)
    collection.featured_product = None
    collection.save()
    
    # Mettre à jour directement via update() : plus efficace pour plusieurs objets
    Collection.objects.filter(pk=11).update(featured_product=None)


# ========== EXEMPLES DE SUPPRESSION ==========
def delete_examples():
    """
    Exemples de suppression d'objets :
    - Supprimer un seul objet
    - Supprimer plusieurs objets avec filter()
    """
    # Créer une instance et la supprimer
    collection = Collection(pk=11)
    collection.delete()
    
    # Supprimer tous les objets correspondant à un filtre
    # Supprimer les collections avec un ID supérieur à 5
    Collection.objects.filter(id__gt=5).delete()


# ========== EXEMPLE DE TRANSACTION ==========
def transaction_example():
    """
    Exemple d'utilisation des transactions :
    - Assurer l'atomicité des opérations
    - Annuler toutes les modifications en cas d'erreur
    - @transaction.atomic() comme décorateur
    """
    # Utiliser un context manager pour les transactions
    with transaction.atomic():
        # Créer une commande
        order = Order()
        order.customer_id = 1
        order.save()
        
        # Créer un article pour la commande
        item = OrderItem()
        item.order = order
        item.product_id = -1  # ID volontairement invalide pour démonstration
        item.quantity = 1
        item.unit_price = 10
        item.save()
        
        # Si une erreur se produit, la transaction est annulée et rien n'est sauvegardé


# ========== EXEMPLE DE REQUÊTES SQL BRUTES ==========
def raw_sql_example():
    """
    Exemple d'utilisation de requêtes SQL brutes :
    - cursor.execute() pour des requêtes SELECT
    - cursor.callproc() pour appeler des procédures stockées
    """
    # Utiliser un cursor pour exécuter du SQL brut
    with connection.cursor() as cursor:
        # Exécuter une requête SELECT brute
        cursor.execute('SELECT * FROM store_product')
        raw_query_results = cursor.fetchall()
        print(raw_query_results)
        
        # Appeler une procédure stockée (exemple avec paramètres)
        cursor.callproc('get_customers', [1, 2])
        raw_query_results = cursor.fetchall()
        print(raw_query_results) 

