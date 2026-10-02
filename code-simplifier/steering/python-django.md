# Django Code Simplification Guide

This guide covers Django-specific patterns, conventions,
and best practices for writing elegant, maintainable code.

## Table of Contents

1. [Django Conventions](#django-conventions)
2. [Models and QuerySet Optimization](#models-and-queryset-optimization)
3. [Views (CBV vs FBV)](#views-cbv-vs-fbv)
4. [Forms](#forms)
5. [Templates](#templates)
6. [Middleware](#middleware)
7. [Signals](#signals)
8. [Testing](#testing)
9. [Common Patterns](#common-patterns)

---

## Django Conventions

### Project Structure

Follow Django's standard project structure and keep apps cohesive:

```
config/
├── settings/
│   ├── base.py
│   ├── dev.py
│   └── prod.py
├── urls.py
└── wsgi.py
apps/
├── users/
├── orders/
└── billing/
manage.py
```

### Naming Conventions

```python
# Apps - plural or domain-focused
users, orders, billing

# Models - singular, PascalCase
User, Order, OrderItem

# Database tables - app_label_modelname
users_user, orders_order

# URLs - nouns, plural resources
path("orders/", order_list)
path("orders/<int:pk>/", order_detail)

# Templates - app namespace folders
orders/order_list.html
orders/order_detail.html
```

---

## Models and QuerySet Optimization

### Model Organization

```python
from django.db import models
from django.utils import timezone

class Order(models.Model):
    # 1. Constants
    STATUS_PENDING = "pending"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETED, "Completed"),
    ]

    # 2. Fields
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    completed_at = models.DateTimeField(null=True, blank=True)

    # 3. Manager / QuerySet
    class QuerySet(models.QuerySet):
        def completed(self):
            return self.filter(status=Order.STATUS_COMPLETED)

        def recent(self, days=30):
            cutoff = timezone.now() - timezone.timedelta(days=days)
            return self.filter(created_at__gte=cutoff)

    objects = QuerySet.as_manager()

    # 4. Business Logic
    def mark_completed(self):
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "completed_at"])

    def is_completed(self):
        return self.status == self.STATUS_COMPLETED
```

### Avoid Fat Queries in Views

```python
# Bad - repeated query logic
completed_orders = Order.objects.filter(status="completed", user=request.user)
recent_orders = Order.objects.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))

# Good - reusable QuerySet methods
completed_orders = Order.objects.completed().filter(user=request.user)
recent_orders = Order.objects.recent(30)
```

### QuerySet Optimization

```python
# Bad - N+1 queries
orders = Order.objects.all()
for order in orders:
    print(order.user.email)

# Good - select_related for FK
orders = Order.objects.select_related("user").all()
for order in orders:
    print(order.user.email)

# Good - prefetch_related for M2M or reverse FK
orders = Order.objects.prefetch_related("items__product").all()

# Good - defer or only for large tables
users = User.objects.only("id", "email")
```

### Bulk Operations

```python
# Bad - save in a loop
for item in items:
    OrderItem.objects.create(order=order, **item)

# Good - bulk_create
OrderItem.objects.bulk_create(
    [OrderItem(order=order, **item) for item in items]
)
```

---

## Views (CBV vs FBV)

### Prefer CBVs for CRUD

```python
# Bad - bloated FBV with mixed concerns
@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if request.method == "POST":
        form = OrderNoteForm(request.POST)
        if form.is_valid():
            form.save(order=order)
            return redirect("orders:detail", pk=order.pk)
    else:
        form = OrderNoteForm()
    return render(request, "orders/order_detail.html", {"order": order, "form": form})

# Good - CBV with clear separation
class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/order_detail.html"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class OrderNoteCreateView(LoginRequiredMixin, CreateView):
    form_class = OrderNoteForm

    def form_valid(self, form):
        form.instance.order_id = self.kwargs["pk"]
        return super().form_valid(form)
```

### Prefer FBVs for Simple Endpoints

```python
# Good - concise FBV for a simple endpoint
@require_POST
def order_archive(request, pk):
    Order.objects.filter(pk=pk, user=request.user).update(status=Order.STATUS_COMPLETED)
    return redirect("orders:list")
```

---

## Forms

### Keep Validation in Forms

```python
# Bad - validation in the view
if request.POST.get("quantity", 0) < 1:
    form.add_error("quantity", "Must be at least 1")

# Good - validation in the form
class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity < 1:
            raise forms.ValidationError("Must be at least 1")
        return quantity
```

### Prefer ModelForm for CRUD

```python
# Bad - manual assignment
order = Order()
order.user = request.user
order.total = form.cleaned_data["total"]
order.save()

# Good - use ModelForm with commit=False
order = form.save(commit=False)
order.user = request.user
order.save()
```

---

## Templates

### Keep Templates Logic-Light

```django
{# Bad - heavy logic in template #}
{% for order in orders %}
  {% if order.status == "completed" and order.total > 100 %}
    <li>{{ order.id }} - VIP</li>
  {% endif %}
{% endfor %}

{# Good - precompute in view or manager #}
{% for order in vip_orders %}
  <li>{{ order.id }} - VIP</li>
{% endfor %}
```

### Use Template Tags and Filters

```python
# Good - reusable template filter
from django import template

register = template.Library()

@register.filter
def currency(value):
    return f"${value:,.2f}"
```

```django
{{ order.total|currency }}
```

---

## Middleware

### Keep Middleware Focused

```python
# Bad - middleware doing multiple responsibilities
class RequestMiddleware:
    def __call__(self, request):
        request.start = timezone.now()
        request.user_agent = request.META.get("HTTP_USER_AGENT")
        if request.user.is_authenticated:
            request.user.last_seen = timezone.now()
            request.user.save(update_fields=["last_seen"])
        response = self.get_response(request)
        response["X-Request-Time"] = str(timezone.now() - request.start)
        return response

# Good - single responsibility middleware
class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = timezone.now()
        response = self.get_response(request)
        response["X-Request-Time"] = str(timezone.now() - start)
        return response
```

---

## Signals

### Use Signals Sparingly

```python
# Bad - hidden side effects everywhere
@receiver(post_save, sender=Order)
def send_order_email(sender, instance, created, **kwargs):
    if created:
        send_email(instance.user.email)

# Good - explicit orchestration in service
class OrderService:
    def create_order(self, user, items):
        order = Order.objects.create(user=user, total=0)
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, **item) for item in items]
        )
        send_email(user.email)
        return order
```

### Good Signal Use Cases

```python
# Good - decoupled audit logging
@receiver(post_save, sender=Order)
def log_order_change(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    AuditLog.objects.create(
        entity="order",
        entity_id=instance.id,
        action=action,
    )
```

---

## Testing

### Use Factories and Fixtures

```python
# Bad - verbose setup in every test
user = User.objects.create(email="user@example.com")
order = Order.objects.create(user=user, total=100)

# Good - factory usage
user = UserFactory()
order = OrderFactory(user=user, total=100)
```

### Use Client and RequestFactory Appropriately

```python
# Good - integration-style test
response = client.get("/orders/")
assert response.status_code == 200

# Good - unit-style view test
request = rf.get("/orders/")
response = OrderListView.as_view()(request)
assert response.status_code == 200
```

### Use pytest-django or Django TestCase

```python
# Good - pytest fixture style
@pytest.mark.django_db
def test_order_total_calculation(order_factory):
    order = order_factory(total=50)
    assert order.total == 50

# Good - Django TestCase
class OrderModelTests(TestCase):
    def test_mark_completed(self):
        order = OrderFactory()
        order.mark_completed()
        self.assertEqual(order.status, Order.STATUS_COMPLETED)
```

---

## Common Patterns

### Service Layer for Business Logic

```python
# Bad - business logic in view
class OrderCreateView(CreateView):
    def form_valid(self, form):
        order = form.save()
        for item in self.request.POST.getlist("items"):
            OrderItem.objects.create(order=order, product_id=item)
        send_email(order.user.email)
        return super().form_valid(form)

# Good - service class
class OrderService:
    def create_order(self, user, items):
        order = Order.objects.create(user=user, total=0)
        OrderItem.objects.bulk_create(
            [OrderItem(order=order, product_id=item) for item in items]
        )
        send_email(user.email)
        return order
```

### Class-Based Views Mixins

```python
# Good - mixins for shared behavior
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class OrderAdminListView(StaffRequiredMixin, ListView):
    model = Order
```

### Repository Style for Complex Queries

```python
# Good - simple repository wrapper
class OrderRepository:
    def find_with_items(self, order_id):
        return Order.objects.select_related("user").prefetch_related("items").get(id=order_id)

    def recent_for_user(self, user, days=30):
        return Order.objects.filter(user=user).recent(days)
```

---

## Django Simplification Checklist

- [ ] Apps are organized by domain with clear boundaries
- [ ] Query logic is in QuerySet/Manager methods
- [ ] select_related/prefetch_related used to prevent N+1
- [ ] Views are thin; use CBVs for CRUD
- [ ] Forms handle validation and normalization
- [ ] Templates are logic-light and use custom filters/tags
- [ ] Middleware is single-responsibility
- [ ] Signals are limited to decoupled side effects
- [ ] Tests use factories and focus on behavior
- [ ] Service layer for complex business logic
- [ ] Bulk operations for batch writes

---

## Additional Resources

- Django Documentation: https://docs.djangoproject.com/
- Django Best Practices: https://github.com/HackSoftware/Django-Styleguide
- Two Scoops of Django: https://www.feldroy.com/books/two-scoops-of-django

**Django Version Recommendation**: Use Django 4.2+ or 5.x with Python
3.10+ for best features and support.
