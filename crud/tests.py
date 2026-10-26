from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import resolve, reverse

from .forms import ProductForm
from .models import Product
from . import views


def make_product(**kw):
    data = dict(name='Ноутбук', description='Тест', price=Decimal('500.00'), quantity=3)
    data.update(kw)
    return Product.objects.create(**data)


# ---------------------------------------------------------------- Модель
class ProductModelTests(TestCase):
    def test_str_returns_name(self):
        """__str__ возвращает название товара"""
        self.assertEqual(str(make_product(name='Мышь')), 'Мышь')

    def test_default_quantity_is_zero(self):
        """Количество по умолчанию равно 0"""
        p = Product.objects.create(name='X', price=1)
        self.assertEqual(p.quantity, 0)

    def test_created_at_auto_filled(self):
        """Поле created_at заполняется автоматически"""
        self.assertIsNotNone(make_product().created_at)

    def test_negative_price_invalid(self):
        """Отрицательная цена не проходит валидацию"""
        p = Product(name='X', price=Decimal('-1'))
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_name_required(self):
        """Пустое название не проходит валидацию"""
        with self.assertRaises(ValidationError):
            Product(name='', price=1).full_clean()

    def test_get_absolute_url(self):
        """get_absolute_url ведёт на страницу товара"""
        p = make_product()
        self.assertEqual(p.get_absolute_url(), f'/{p.pk}/')

    def test_ordering_newest_first(self):
        """Товары сортируются от новых к старым"""
        a, b = make_product(name='A'), make_product(name='B')
        self.assertEqual(list(Product.objects.all()), [b, a])


# ---------------------------------------------------------------- Форма
class ProductFormTests(TestCase):
    def test_valid_form(self):
        """Форма с корректными данными валидна"""
        f = ProductForm({'name': 'A', 'description': '', 'price': '10', 'quantity': 1})
        self.assertTrue(f.is_valid())

    def test_empty_form_invalid(self):
        """Пустая форма невалидна и содержит ошибки обязательных полей"""
        f = ProductForm({})
        self.assertFalse(f.is_valid())
        self.assertIn('name', f.errors)
        self.assertIn('price', f.errors)

    def test_negative_quantity_invalid(self):
        """Отрицательное количество отклоняется формой"""
        f = ProductForm({'name': 'A', 'price': '10', 'quantity': -5})
        self.assertFalse(f.is_valid())


# ---------------------------------------------------------------- URL
class UrlTests(TestCase):
    def test_urls_resolve_to_views(self):
        """URL-адреса сопоставлены с нужными представлениями"""
        self.assertEqual(resolve('/').func.view_class, views.ProductListView)
        self.assertEqual(resolve('/create/').func.view_class, views.ProductCreateView)
        self.assertEqual(resolve('/1/').func.view_class, views.ProductDetailView)
        self.assertEqual(resolve('/1/edit/').func.view_class, views.ProductUpdateView)
        self.assertEqual(resolve('/1/delete/').func.view_class, views.ProductDeleteView)


# ---------------------------------------------------------------- CRUD
class CreateViewTests(TestCase):
    def test_create_page_get(self):
        """GET /create/ отдаёт форму (200, нужный шаблон)"""
        r = self.client.get(reverse('crud:create'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'crud/product_form.html')

    def test_create_post_valid(self):
        """POST с валидными данными создаёт товар и делает редирект"""
        r = self.client.post(reverse('crud:create'),
                             {'name': 'Новый', 'description': 'd', 'price': '99.90', 'quantity': 5})
        p = Product.objects.get(name='Новый')
        self.assertRedirects(r, p.get_absolute_url())
        self.assertEqual(p.price, Decimal('99.90'))

    def test_create_post_invalid(self):
        """POST с невалидными данными не создаёт товар и показывает ошибки"""
        r = self.client.post(reverse('crud:create'), {'name': '', 'price': ''})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertTrue(r.context['form'].errors)


class ReadViewTests(TestCase):
    def setUp(self):
        self.p = make_product(name='Монитор')

    def test_list_status_and_template(self):
        """Список товаров: код 200 и шаблон product_list.html"""
        r = self.client.get(reverse('crud:list'))
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'crud/product_list.html')

    def test_list_contains_product(self):
        """Созданный товар виден в списке"""
        self.assertContains(self.client.get(reverse('crud:list')), 'Монитор')

    def test_list_empty_message(self):
        """При пустой базе выводится сообщение «Товаров пока нет»"""
        Product.objects.all().delete()
        self.assertContains(self.client.get(reverse('crud:list')), 'Товаров пока нет')

    def test_list_search(self):
        """Поиск ?q= фильтрует товары по названию"""
        make_product(name='Клавиатура')
        r = self.client.get(reverse('crud:list'), {'q': 'Клав'})
        names = [p.name for p in r.context['products']]
        self.assertEqual(names, ['Клавиатура'])

    def test_detail_ok(self):
        """Страница товара: код 200, виден контекст product"""
        r = self.client.get(self.p.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['product'], self.p)

    def test_detail_404(self):
        """Несуществующий товар возвращает 404"""
        self.assertEqual(self.client.get(reverse('crud:detail', args=[9999])).status_code, 404)


class UpdateViewTests(TestCase):
    def setUp(self):
        self.p = make_product(name='Старое')
        self.url = reverse('crud:update', args=[self.p.pk])

    def test_update_get_prefilled(self):
        """GET формы редактирования подставляет текущие данные"""
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['form'].initial['name'], 'Старое')

    def test_update_post_valid(self):
        """POST с новыми данными изменяет товар"""
        self.client.post(self.url, {'name': 'Новое', 'description': '', 'price': '1', 'quantity': 2})
        self.p.refresh_from_db()
        self.assertEqual(self.p.name, 'Новое')
        self.assertEqual(self.p.quantity, 2)

    def test_update_post_invalid(self):
        """POST с пустым названием не меняет товар"""
        self.client.post(self.url, {'name': '', 'price': '1', 'quantity': 2})
        self.p.refresh_from_db()
        self.assertEqual(self.p.name, 'Старое')

    def test_update_404(self):
        """Редактирование несуществующего товара даёт 404"""
        self.assertEqual(self.client.get(reverse('crud:update', args=[9999])).status_code, 404)


class DeleteViewTests(TestCase):
    def setUp(self):
        self.p = make_product()
        self.url = reverse('crud:delete', args=[self.p.pk])

    def test_delete_confirm_page(self):
        """GET показывает страницу подтверждения, товар не удаляется"""
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, 'crud/product_confirm_delete.html')
        self.assertEqual(Product.objects.count(), 1)

    def test_delete_post(self):
        """POST удаляет товар и перенаправляет на список"""
        r = self.client.post(self.url)
        self.assertRedirects(r, reverse('crud:list'))
        self.assertFalse(Product.objects.exists())

    def test_delete_404(self):
        """Удаление несуществующего товара даёт 404"""
        self.assertEqual(self.client.post(reverse('crud:delete', args=[9999])).status_code, 404)
