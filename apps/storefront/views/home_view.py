from functools import cache
from unicodedata import category
from django.shortcuts import render
from products.models import Category, Product

class HomeView():

    def index():
        category = cache.get('category', default=[])

        if not category:
            category = Category.objects.filter(status=True)
            cache.set('category', category, timeout=60*60*24*7)
        
        context = {
            "category": category
        }

        return render('storefront/index.html', context=context)