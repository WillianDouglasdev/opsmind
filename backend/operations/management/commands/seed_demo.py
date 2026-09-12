"""Gera o cenário fictício; não é um importador incremental de dados externos.

Catálogos, probabilidades e ordem das chamadas ao RNG fazem parte da demonstração.
Alterá-los pode mudar os números esperados pelos testes, mesmo mantendo a seed 42.
"""

import random
import time
from datetime import date, datetime, time as datetime_time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from operations.demo import DEMO_REFERENCE_DATE
from operations.models import (
    ActionItem,
    Branch,
    Customer,
    Inventory,
    Order,
    OrderItem,
    PipelineIssue,
    PipelineRun,
    Product,
    Ticket,
)

RANDOM_SEED = 42
# A data fixa faz a história da empresa permanecer igual em qualquer dia de execução.
DEMO_DATE = DEMO_REFERENCE_DATE
HISTORY_DAYS = 180

FULL_DATASET = {
    "customers": 250,
    "products": 40,
    "orders": 2500,
    "tickets": 500,
}

SMALL_DATASET = {
    "customers": 40,
    "products": 30,
    "orders": 100,
    "tickets": 35,
}

BRANCHES = [
    ("Belo Horizonte", "Belo Horizonte", "MG"),
    ("Contagem", "Contagem", "MG"),
    ("Betim", "Betim", "MG"),
    ("Nova Lima", "Nova Lima", "MG"),
    ("Sete Lagoas", "Sete Lagoas", "MG"),
]

PRODUCTS = [
    ("Monitor Office 24", Product.Category.ELECTRONICS),
    ("Teclado Comfort Slim", Product.Category.ACCESSORIES),
    ("Mouse Precision Flow", Product.Category.ACCESSORIES),
    ("Notebook Stand Flex", Product.Category.OFFICE),
    ("Headset Office Plus", Product.Category.ELECTRONICS),
    ("Webcam Conference HD", Product.Category.ELECTRONICS),
    ("Dock Station Connect", Product.Category.ELECTRONICS),
    ("Cadeira Task Ergonomic", Product.Category.OFFICE),
    ("Mesa Modular Work", Product.Category.OFFICE),
    ("Kit Organização Desk", Product.Category.OFFICE),
    ("Impressora Label Pro", Product.Category.EQUIPMENT),
    ("Leitor Barcode Fast", Product.Category.EQUIPMENT),
    ("Switch Network 16", Product.Category.ELECTRONICS),
    ("Access Point Business", Product.Category.ELECTRONICS),
    ("Cabo Network Pack", Product.Category.SUPPLIES),
    ("Filtro de Linha Safe", Product.Category.ACCESSORIES),
    ("Suporte Monitor Duo", Product.Category.OFFICE),
    ("Router Business AX", Product.Category.ELECTRONICS),
    ("Nobreak Office 1200", Product.Category.EQUIPMENT),
    ("Projetor Meeting View", Product.Category.ELECTRONICS),
    ("Tela Projection Flex", Product.Category.OFFICE),
    ("Fragmentadora Secure", Product.Category.EQUIPMENT),
    ("Laminadora Office A4", Product.Category.EQUIPMENT),
    ("Calculadora Desk Pro", Product.Category.OFFICE),
    ("Papel Multiuso Premium", Product.Category.SUPPLIES),
    ("Etiqueta Térmica Pack", Product.Category.SUPPLIES),
    ("Scanner Pro X2", Product.Category.EQUIPMENT),
    ("Toner Office Yield", Product.Category.SUPPLIES),
    ("Kit Cabos Universal", Product.Category.ACCESSORIES),
    ("Hub Connect 8", Product.Category.ELECTRONICS),
    ("Adaptador Display Pro", Product.Category.ACCESSORIES),
    ("Maleta Equipment Safe", Product.Category.ACCESSORIES),
    ("Quadro Meeting Glass", Product.Category.OFFICE),
    ("Organizador Archive Box", Product.Category.SUPPLIES),
    ("Caneta Marker Kit", Product.Category.SUPPLIES),
    ("Grampeador Heavy Desk", Product.Category.OFFICE),
    ("Bateria Backup Unit", Product.Category.EQUIPMENT),
    ("Sensor Access Control", Product.Category.EQUIPMENT),
    ("Terminal Check Compact", Product.Category.EQUIPMENT),
    ("Kit Cleaning Tech", Product.Category.SUPPLIES),
]

CUSTOMER_PREFIXES = [
    "Áurea",
    "Cedro",
    "Horizonte",
    "Prisma",
    "Serra Azul",
    "Vale Norte",
    "Ponte Nova",
    "Eixo Central",
    "Lume",
    "Vereda",
]

CUSTOMER_SUFFIXES = [
    "Comercial",
    "Distribuição",
    "Soluções",
    "Suprimentos",
    "Serviços",
]

CUSTOMER_CITIES = [
    "Belo Horizonte",
    "Contagem",
    "Betim",
    "Nova Lima",
    "Sete Lagoas",
    "Sabará",
    "Ribeirão das Neves",
    "Santa Luzia",
]

TICKET_DESCRIPTIONS = {
    Ticket.Category.DELIVERY: [
        "Entrega não recebida dentro do prazo informado.",
        "Pedido consta como enviado, mas ainda não chegou.",
        "Cliente solicita nova previsão para a entrega atrasada.",
        "Mercadoria chegou depois da data combinada com a operação.",
        "Rastreamento sem atualização e prazo de entrega vencido.",
    ],
    Ticket.Category.PRODUCT: [
        "Produto recebido com item divergente do pedido.",
        "Embalagem apresentou avaria durante o recebimento.",
        "Cliente solicita troca de uma unidade com defeito.",
        "Especificação recebida não corresponde ao item solicitado.",
    ],
    Ticket.Category.BILLING: [
        "Valor da nota precisa ser conferido com o pedido.",
        "Cliente solicita segunda via do documento de cobrança.",
        "Condição de pagamento diverge da negociação registrada.",
    ],
    Ticket.Category.SERVICE: [
        "Cliente solicita atualização sobre o atendimento em andamento.",
        "Dúvida sobre o processo de instalação do equipamento.",
        "Necessário retorno da equipe responsável pelo pedido.",
    ],
    Ticket.Category.OTHER: [
        "Solicitação geral encaminhada para avaliação operacional.",
        "Cliente pede confirmação dos dados cadastrados no pedido.",
        "Contato realizado para esclarecer uma informação comercial.",
    ],
}


class Command(BaseCommand):
    help = "Popula o banco com o cenário sintético e determinístico do OpsMind."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove os dados operacionais e as ações da demo antes de recriá-los.",
        )
        parser.add_argument(
            "--small",
            action="store_true",
            help="Gera um conjunto reduzido, destinado aos testes automatizados.",
        )

    def handle(self, *args, **options) -> None:
        if self._has_operational_data() and not options["reset"]:
            self.stdout.write(
                self.style.WARNING(
                    "Dados operacionais já existem. Use --reset para recriar a demo."
                )
            )
            return

        started_at = time.perf_counter()
        counts = SMALL_DATASET if options["small"] else FULL_DATASET

        # A seed fixa mantém o mesmo cenário em SQLite, PostgreSQL e nos testes.
        rng = random.Random(RANDOM_SEED)

        # Se uma etapa falhar, evitamos deixar apenas parte da empresa criada no banco.
        with transaction.atomic():
            if options["reset"]:
                self._clear_operational_data()

            branches = self._create_branches()
            customers = self._create_customers(rng, counts["customers"])
            products = self._create_products(rng, counts["products"])
            orders = self._create_orders(rng, counts["orders"], branches, customers)
            self._create_order_items(rng, orders, products)
            self._create_inventory(rng, branches, products)
            self._create_tickets(rng, counts["tickets"], orders, customers)

        elapsed = time.perf_counter() - started_at
        self.stdout.write(self.style.SUCCESS("Demo operacional criada com sucesso."))
        self.stdout.write(
            " | ".join(
                [
                    f"filiais={Branch.objects.count()}",
                    f"clientes={Customer.objects.count()}",
                    f"produtos={Product.objects.count()}",
                    f"estoques={Inventory.objects.count()}",
                    f"pedidos={Order.objects.count()}",
                    f"itens={OrderItem.objects.count()}",
                    f"chamados={Ticket.objects.count()}",
                    f"tempo={elapsed:.2f}s",
                ]
            )
        )

    def _has_operational_data(self) -> bool:
        # É uma proteção contra duplicação da demo, não um upsert: até uma carga
        # parcial impede nova geração. Não reutilize esse critério numa futura ETL.
        return any(
            model.objects.exists()
            for model in (Branch, Customer, Product, Inventory, Order, Ticket)
        )

    def _clear_operational_data(self) -> None:
        # As ações também são limpas para que a demonstração volte ao estado inicial.
        for model in (
            PipelineIssue,
            PipelineRun,
            ActionItem,
            Ticket,
            OrderItem,
            Order,
            Inventory,
            Product,
            Customer,
            Branch,
        ):
            model.objects.all().delete()

    def _create_branches(self) -> list[Branch]:
        created_at = self._aware_datetime(DEMO_DATE - timedelta(days=720), 9, 0)
        branches = [
            Branch(name=name, city=city, state=state, created_at=created_at)
            for name, city, state in BRANCHES
        ]
        return Branch.objects.bulk_create(branches)

    def _create_customers(self, rng: random.Random, count: int) -> list[Customer]:
        customers = []
        # A demo precisa de uma amostra estratégica relevante, inclusive no dataset pequeno.
        strategic_count = max(6, round(count * 0.08))

        for index in range(count):
            if index < strategic_count:
                segment = Customer.Segment.STRATEGIC
            else:
                segment = rng.choices(
                    [
                        Customer.Segment.RETAIL,
                        Customer.Segment.SMALL_BUSINESS,
                        Customer.Segment.CORPORATE,
                    ],
                    weights=[28, 42, 30],
                    k=1,
                )[0]

            prefix = CUSTOMER_PREFIXES[index % len(CUSTOMER_PREFIXES)]
            suffix = CUSTOMER_SUFFIXES[(index // len(CUSTOMER_PREFIXES)) % len(CUSTOMER_SUFFIXES)]
            customers.append(
                Customer(
                    name=f"{prefix} {suffix} {index + 1:03d}",
                    segment=segment,
                    city=rng.choice(CUSTOMER_CITIES),
                    state="MG",
                    status=(
                        Customer.Status.INACTIVE
                        if rng.random() < 0.05
                        else Customer.Status.ACTIVE
                    ),
                    created_at=self._aware_datetime(
                        DEMO_DATE - timedelta(days=rng.randint(190, 900)),
                        10,
                        rng.randint(0, 59),
                    ),
                )
            )

        return Customer.objects.bulk_create(customers, batch_size=500)

    def _create_products(self, rng: random.Random, count: int) -> list[Product]:
        # Os preços nascem em centavos para evitar arredondamento de ponto flutuante.
        category_prices = {
            Product.Category.ELECTRONICS: (28000, 240000),
            Product.Category.OFFICE: (4500, 165000),
            Product.Category.SUPPLIES: (1800, 48000),
            Product.Category.EQUIPMENT: (45000, 320000),
            Product.Category.ACCESSORIES: (2500, 68000),
        }
        products = []

        for index, (name, category) in enumerate(PRODUCTS[:count], start=1):
            minimum_cents, maximum_cents = category_prices[category]
            products.append(
                Product(
                    sku=f"P{index:03d}",
                    name=name,
                    category=category,
                    unit_price=Decimal(rng.randint(minimum_cents, maximum_cents)) / 100,
                    created_at=self._aware_datetime(
                        DEMO_DATE - timedelta(days=rng.randint(240, 700)),
                        9,
                        rng.randint(0, 59),
                    ),
                )
            )

        return Product.objects.bulk_create(products, batch_size=100)

    def _create_orders(
        self,
        rng: random.Random,
        count: int,
        branches: list[Branch],
        customers: list[Customer],
    ) -> list[Order]:
        history_start = DEMO_DATE - timedelta(days=HISTORY_DAYS - 1)
        demo_end = self._aware_datetime(DEMO_DATE, 23, 59)
        strategic = [c for c in customers if c.segment == Customer.Segment.STRATEGIC]
        regular = [c for c in customers if c.segment != Customer.Segment.STRATEGIC]
        orders = []

        for _ in range(count):
            created_date = history_start + timedelta(days=rng.randint(0, HISTORY_DAYS - 1))
            created_at = self._aware_datetime(
                created_date,
                rng.randint(7, 18),
                rng.randint(0, 59),
            )
            branch = rng.choices(branches, weights=[19, 25, 19, 18, 19], k=1)[0]
            customer = (
                rng.choice(strategic)
                if rng.random() < 0.30
                else rng.choice(regular)
            )
            promised_at = created_at + timedelta(days=rng.randint(3, 9))

            age_in_days = (DEMO_DATE - created_date).days
            # O período recente concentra o aumento que será detectado pelo dashboard.
            if age_in_days <= 29:
                delay_probability = 0.16
            elif age_in_days <= 59:
                delay_probability = 0.11
            else:
                delay_probability = 0.085

            # Contagem fica pior que a média, mas ainda recebe muitos pedidos sem atraso.
            if branch.city == "Contagem":
                delay_probability += 0.065
            if customer.segment == Customer.Segment.STRATEGIC:
                delay_probability += 0.02

            is_delayed = promised_at <= demo_end and rng.random() < delay_probability

            delivered_at = None
            if is_delayed:
                status = Order.Status.DELAYED
                possible_delivery = promised_at + timedelta(days=rng.randint(1, 8))
                if possible_delivery <= demo_end and rng.random() < 0.74:
                    delivered_at = possible_delivery
            elif rng.random() < 0.03:
                status = Order.Status.CANCELLED
            elif promised_at > demo_end:
                status = rng.choices(
                    [Order.Status.PENDING, Order.Status.PROCESSING, Order.Status.SHIPPED],
                    weights=[25, 40, 35],
                    k=1,
                )[0]
            else:
                status = Order.Status.DELIVERED
                delivered_at = max(
                    created_at + timedelta(hours=20),
                    promised_at - timedelta(days=rng.randint(0, 2)),
                )

            order = Order(
                customer=customer,
                branch=branch,
                created_at=created_at,
                promised_at=promised_at,
                delivered_at=delivered_at,
                status=status,
                total_amount=Decimal("0.00"),
            )
            orders.append(order)

        return Order.objects.bulk_create(orders, batch_size=500)

    def _create_order_items(
        self,
        rng: random.Random,
        orders: list[Order],
        products: list[Product],
    ) -> None:
        # P018 e P027 aparecem mais nos atrasos para criar uma associação investigável com o estoque.
        critical_products = [p for p in products if p.sku in {"P018", "P027"}]
        items = []

        for order in orders:
            item_count = rng.choices([1, 2, 3, 4], weights=[8, 40, 38, 14], k=1)[0]
            selected_products = []

            critical_probability = 0.10
            if order.status == Order.Status.DELAYED:
                critical_probability = 0.72 if order.branch.city == "Contagem" else 0.55
            if critical_products and rng.random() < critical_probability:
                selected_products.append(rng.choice(critical_products))

            available_products = [p for p in products if p not in selected_products]
            selected_products.extend(
                rng.sample(available_products, k=item_count - len(selected_products))
            )

            total = Decimal("0.00")
            for product in selected_products:
                quantity = (
                    rng.randint(2, 8)
                    if order.customer.segment == Customer.Segment.STRATEGIC
                    else rng.randint(1, 5)
                )
                items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=product.unit_price,
                    )
                )
                total += product.unit_price * quantity

            order.total_amount = total

        OrderItem.objects.bulk_create(items, batch_size=1000)
        Order.objects.bulk_update(orders, ["total_amount"], batch_size=500)

    def _create_inventory(
        self,
        rng: random.Random,
        branches: list[Branch],
        products: list[Product],
    ) -> None:
        critical_levels = {
            ("Contagem", "P018"): (5, 24),
            ("Contagem", "P027"): (4, 20),
            ("Belo Horizonte", "P018"): (14, 22),
            ("Betim", "P027"): (9, 18),
            ("Nova Lima", "P018"): (25, 20),
            ("Nova Lima", "P027"): (24, 18),
            ("Sete Lagoas", "P018"): (27, 21),
            ("Sete Lagoas", "P027"): (23, 19),
            ("Belo Horizonte", "P027"): (26, 20),
            ("Betim", "P018"): (28, 22),
        }
        inventory_items = []
        updated_at = self._aware_datetime(DEMO_DATE, 20, 0)

        # O estoque representa um snapshot atual; a demo não mantém movimentações históricas.
        for branch in branches:
            for product in products:
                if product.sku in {"P018", "P027"}:
                    current_quantity, minimum_quantity = critical_levels[(branch.city, product.sku)]
                else:
                    minimum_quantity = rng.randint(10, 30)
                    current_quantity = minimum_quantity + rng.randint(22, 135)

                inventory_items.append(
                    Inventory(
                        branch=branch,
                        product=product,
                        current_quantity=current_quantity,
                        minimum_quantity=minimum_quantity,
                        updated_at=updated_at,
                    )
                )

        Inventory.objects.bulk_create(inventory_items, batch_size=500)

    def _create_tickets(
        self,
        rng: random.Random,
        count: int,
        orders: list[Order],
        customers: list[Customer],
    ) -> None:
        demo_end = self._aware_datetime(DEMO_DATE, 23, 59)
        delayed_orders = [o for o in orders if o.status == Order.Status.DELAYED]
        recent_cutoff = self._aware_datetime(DEMO_DATE - timedelta(days=29), 0, 0)
        recent_delayed = [o for o in delayed_orders if o.created_at >= recent_cutoff]
        contagem_delayed = [o for o in recent_delayed if o.branch.city == "Contagem"]
        strategic_delayed = [
            o for o in recent_delayed if o.customer.segment == Customer.Segment.STRATEGIC
        ]
        tickets = []

        for _ in range(count):
            period_roll = rng.random()
            # Também elevamos chamados de entrega recentes para reforçar o mesmo sinal operacional.
            if period_roll < 0.40:
                age_days = rng.randint(0, 29)
                delivery_probability = 0.64
            elif period_roll < 0.62:
                age_days = rng.randint(30, 59)
                delivery_probability = 0.36
            else:
                age_days = rng.randint(60, HISTORY_DAYS - 1)
                delivery_probability = 0.25

            created_at = self._aware_datetime(
                DEMO_DATE - timedelta(days=age_days),
                rng.randint(8, 19),
                rng.randint(0, 59),
            )
            is_delivery = rng.random() < delivery_probability

            if is_delivery and delayed_orders:
                if age_days <= 29 and contagem_delayed and rng.random() < 0.48:
                    order = rng.choice(contagem_delayed)
                elif age_days <= 29 and strategic_delayed and rng.random() < 0.38:
                    order = rng.choice(strategic_delayed)
                elif age_days <= 29 and recent_delayed:
                    order = rng.choice(recent_delayed)
                else:
                    order = rng.choice(delayed_orders)

                customer = order.customer
                category = Ticket.Category.DELIVERY
                # Um chamado de entrega não pode aparecer antes de o prazo do pedido vencer.
                created_at = max(created_at, order.promised_at + timedelta(hours=8))
                created_at = min(created_at, demo_end)
            else:
                order = rng.choice(orders) if rng.random() < 0.72 else None
                customer = order.customer if order else rng.choice(customers)
                category = rng.choices(
                    [
                        Ticket.Category.PRODUCT,
                        Ticket.Category.BILLING,
                        Ticket.Category.SERVICE,
                        Ticket.Category.OTHER,
                    ],
                    weights=[32, 23, 30, 15],
                    k=1,
                )[0]

            if category == Ticket.Category.DELIVERY:
                priority = rng.choices(
                    [
                        Ticket.Priority.LOW,
                        Ticket.Priority.MEDIUM,
                        Ticket.Priority.HIGH,
                        Ticket.Priority.CRITICAL,
                    ],
                    weights=[7, 37, 43, 13],
                    k=1,
                )[0]
            else:
                priority = rng.choices(
                    [Ticket.Priority.LOW, Ticket.Priority.MEDIUM, Ticket.Priority.HIGH],
                    weights=[24, 55, 21],
                    k=1,
                )[0]

            ticket_age = max(0, (demo_end - created_at).days)
            resolved_probability = 0.30 if ticket_age <= 14 else 0.76
            if rng.random() < resolved_probability:
                possible_close = created_at + timedelta(days=rng.randint(1, 7))
                if possible_close <= demo_end:
                    status = Ticket.Status.RESOLVED
                    closed_at = possible_close
                else:
                    status = Ticket.Status.IN_PROGRESS
                    closed_at = None
            else:
                status = rng.choice([Ticket.Status.OPEN, Ticket.Status.IN_PROGRESS])
                closed_at = None

            tickets.append(
                Ticket(
                    customer=customer,
                    order=order,
                    category=category,
                    priority=priority,
                    description=rng.choice(TICKET_DESCRIPTIONS[category]),
                    status=status,
                    created_at=created_at,
                    closed_at=closed_at,
                )
            )

        Ticket.objects.bulk_create(tickets, batch_size=500)

    @staticmethod
    def _aware_datetime(target_date: date, hour: int, minute: int) -> datetime:
        naive_value = datetime.combine(target_date, datetime_time(hour, minute))
        return timezone.make_aware(naive_value)
