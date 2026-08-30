# Gerado pelo Django 5.2.17 em 2026-08-29 05:29

import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=2)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Filial',
                'verbose_name_plural': 'Filiais',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('segment', models.CharField(choices=[('retail', 'Varejo'), ('small_business', 'Pequena empresa'), ('corporate', 'Corporativo'), ('strategic', 'Estratégico')], max_length=20)),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=2)),
                ('status', models.CharField(choices=[('active', 'Ativo'), ('inactive', 'Inativo')], default='active', max_length=10)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['name'],
                'indexes': [models.Index(fields=['segment', 'status'], name='ops_customer_seg_status_idx')],
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('promised_at', models.DateTimeField()),
                ('delivered_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('processing', 'Em processamento'), ('shipped', 'Enviado'), ('delivered', 'Entregue'), ('delayed', 'Atrasado'), ('cancelled', 'Cancelado')], max_length=12)),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='operations.branch')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='operations.customer')),
            ],
            options={
                'verbose_name': 'Pedido',
                'verbose_name_plural': 'Pedidos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=150)),
                ('category', models.CharField(choices=[('electronics', 'Eletrônicos'), ('office', 'Escritório'), ('supplies', 'Suprimentos'), ('equipment', 'Equipamentos'), ('accessories', 'Acessórios')], max_length=20)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Produto',
                'verbose_name_plural': 'Produtos',
                'ordering': ['sku'],
                'constraints': [models.CheckConstraint(condition=models.Q(('unit_price__gte', 0)), name='product_unit_price_non_negative')],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField()),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='operations.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='operations.product')),
            ],
            options={
                'verbose_name': 'Item do pedido',
                'verbose_name_plural': 'Itens dos pedidos',
            },
        ),
        migrations.CreateModel(
            name='Inventory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_quantity', models.PositiveIntegerField()),
                ('minimum_quantity', models.PositiveIntegerField()),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_items', to='operations.branch')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_items', to='operations.product')),
            ],
            options={
                'verbose_name': 'Estoque',
                'verbose_name_plural': 'Estoques',
                'ordering': ['branch__name', 'product__sku'],
            },
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('delivery', 'Entrega'), ('product', 'Produto'), ('billing', 'Faturamento'), ('service', 'Atendimento'), ('other', 'Outro')], max_length=12)),
                ('priority', models.CharField(choices=[('low', 'Baixa'), ('medium', 'Média'), ('high', 'Alta'), ('critical', 'Crítica')], max_length=12)),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('open', 'Aberto'), ('in_progress', 'Em andamento'), ('resolved', 'Resolvido')], max_length=12)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='operations.customer')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tickets', to='operations.order')),
            ],
            options={
                'verbose_name': 'Chamado',
                'verbose_name_plural': 'Chamados',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['-created_at'], name='ops_order_created_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['status', '-created_at'], name='ops_order_status_created_idx'),
        ),
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(condition=models.Q(('total_amount__gte', 0)), name='order_total_non_negative'),
        ),
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(condition=models.Q(('promised_at__gt', models.F('created_at'))), name='order_promise_after_creation'),
        ),
        migrations.AddConstraint(
            model_name='order',
            constraint=models.CheckConstraint(condition=models.Q(('delivered_at__isnull', True), ('delivered_at__gte', models.F('created_at')), _connector='OR'), name='order_delivery_after_creation'),
        ),
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.CheckConstraint(condition=models.Q(('quantity__gt', 0)), name='order_item_quantity_positive'),
        ),
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.CheckConstraint(condition=models.Q(('unit_price__gte', 0)), name='order_item_price_non_negative'),
        ),
        migrations.AddConstraint(
            model_name='inventory',
            constraint=models.UniqueConstraint(fields=('branch', 'product'), name='unique_inventory_branch_product'),
        ),
        migrations.AddConstraint(
            model_name='inventory',
            constraint=models.CheckConstraint(condition=models.Q(('current_quantity__gte', 0)), name='inventory_current_non_negative'),
        ),
        migrations.AddConstraint(
            model_name='inventory',
            constraint=models.CheckConstraint(condition=models.Q(('minimum_quantity__gte', 0)), name='inventory_minimum_non_negative'),
        ),
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['status', '-created_at'], name='ops_ticket_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='ticket',
            index=models.Index(fields=['category', '-created_at'], name='ops_ticket_cat_created_idx'),
        ),
        migrations.AddConstraint(
            model_name='ticket',
            constraint=models.CheckConstraint(condition=models.Q(('closed_at__isnull', True), ('closed_at__gte', models.F('created_at')), _connector='OR'), name='ticket_close_after_creation'),
        ),
    ]
