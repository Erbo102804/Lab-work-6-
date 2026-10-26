from django.urls import reverse_lazy
from django.views.generic import (CreateView, DeleteView, DetailView,
                                  ListView, UpdateView)

from .forms import ProductForm
from .models import Product


class ProductListView(ListView):          # Read (список)
    model = Product
    context_object_name = 'products'

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        return qs.filter(name__icontains=q) if q else qs


class ProductDetailView(DetailView):      # Read (один объект)
    model = Product


class ProductCreateView(CreateView):      # Create
    model = Product
    form_class = ProductForm


class ProductUpdateView(UpdateView):      # Update
    model = Product
    form_class = ProductForm


class ProductDeleteView(DeleteView):      # Delete
    model = Product
    success_url = reverse_lazy('crud:list')
