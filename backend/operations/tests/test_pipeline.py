import json
from decimal import Decimal

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient

from operations.ingestion.runner import PipelineExecutionError, run_orders_pipeline
from operations.models import (
    Branch, Customer, Order, OrderItem, PipelineIssue, PipelineRun, Product,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogs():
    branch = Branch.objects.create(name="Contagem", city="Contagem", state="MG")
    customer = Customer.objects.create(
        name="Cliente Pipeline", segment=Customer.Segment.CORPORATE,
        city="Contagem", state="MG",
    )
    product = Product.objects.create(
        sku="P001", name="Produto Pipeline", category=Product.Category.ELECTRONICS,
        unit_price=Decimal("20.00"),
    )
    return branch, customer, product


def record(**changes):
    payload = {
        "external_id": "ERP-TEST-001",
        "branch": "Contagem",
        "customer": "Cliente Pipeline",
        "created_at": "2026-08-20T09:00:00-03:00",
        "promised_at": "2026-08-25T18:00:00-03:00",
        "delivered_at": "2026-08-24T16:00:00-03:00",
        "status": "delivered",
        "total_amount": "40.00",
        "items": [{"sku": "P001", "quantity": 2, "unit_price": "20.00"}],
    }
    payload.update(changes)
    return payload


def source_file(tmp_path, records):
    path = tmp_path / "orders.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def test_valid_execution_loads_order_and_records_success(tmp_path, catalogs):
    run = run_orders_pipeline(source_file(tmp_path, [record()]))

    order = Order.objects.get(source_system="demo_erp", external_id="ERP-TEST-001")
    assert run.status == PipelineRun.Status.SUCCESS
    assert (run.records_received, run.records_valid, run.records_rejected) == (1, 1, 0)
    assert run.records_loaded == 1
    assert run.quality_percentage == 100.0
    assert run.published_at is not None
    assert order.total_amount == Decimal("40.00")
    assert list(order.items.values_list("quantity", "unit_price")) == [(2, Decimal("20.00"))]
    assert all(step["status"] == "success" for step in run.steps.values())


def test_invalid_record_is_traced_and_valid_record_continues(tmp_path, catalogs):
    invalid_branch = record(external_id="ERP-BAD-BRANCH", branch="Inexistente")
    invalid_timezone = record(
        external_id="ERP-BAD-DATE",
        created_at="2026-08-20T09:00:00",
    )
    invalid_total = record(external_id="ERP-BAD-TOTAL", total_amount="NaN")
    run = run_orders_pipeline(source_file(
        tmp_path,
        [record(), invalid_branch, invalid_timezone, invalid_total],
    ))

    assert run.status == PipelineRun.Status.WARNING
    assert (run.records_received, run.records_valid, run.records_rejected, run.records_loaded) == (4, 1, 3, 1)
    assert run.quality_percentage == 25.0
    issues = {issue.record_identifier: issue for issue in run.issues.all()}
    assert issues["ERP-BAD-BRANCH"].code == "unknown_branch"
    assert "Inexistente" in issues["ERP-BAD-BRANCH"].message
    assert issues["ERP-BAD-DATE"].code == "invalid_datetime"
    assert issues["ERP-BAD-TOTAL"].code == "invalid_total"
    assert run.steps["validate"]["status"] == "warning"


def test_source_duplicate_is_rejected(tmp_path, catalogs):
    duplicate = record(total_amount="60.00", items=[{"sku": "P001", "quantity": 3, "unit_price": "20.00"}])
    run = run_orders_pipeline(source_file(tmp_path, [record(), duplicate]))
    assert run.records_loaded == 1
    assert PipelineIssue.objects.get(run=run).code == "duplicate_external_id"


def test_missing_source_records_failed_run_without_publication(tmp_path, catalogs):
    with pytest.raises(PipelineExecutionError) as captured:
        run_orders_pipeline(tmp_path / "missing.json")
    run = captured.value.run
    assert run.status == PipelineRun.Status.FAILED
    assert run.steps["extract"]["status"] == "failed"
    assert run.finished_at is not None
    assert run.published_at is None
    assert "JSON" in run.error_message


def test_idempotency_updates_same_business_order_and_items(tmp_path, catalogs):
    path = source_file(tmp_path, [record()])
    first = run_orders_pipeline(path)
    path = source_file(tmp_path, [record(
        status="processing", delivered_at=None, total_amount="60.00",
        items=[{"sku": "P001", "quantity": 3, "unit_price": "20.00"}],
    )])
    second = run_orders_pipeline(path)

    assert first.pk != second.pk
    assert Order.objects.filter(source_system="demo_erp", external_id="ERP-TEST-001").count() == 1
    order = Order.objects.get(external_id="ERP-TEST-001")
    assert (order.status, order.total_amount, order.items.get().quantity) == (
        Order.Status.PROCESSING, Decimal("60.00"), 3,
    )


def test_load_is_atomic_when_item_persistence_fails(tmp_path, catalogs, monkeypatch):
    import operations.ingestion.load as load_module

    original = OrderItem.objects.bulk_create

    def fail(_items):
        raise RuntimeError("Falha controlada no loader")

    monkeypatch.setattr(load_module.OrderItem.objects, "bulk_create", fail)
    with pytest.raises(PipelineExecutionError) as captured:
        run_orders_pipeline(source_file(tmp_path, [record()]))
    assert captured.value.run.status == PipelineRun.Status.FAILED
    assert captured.value.run.steps["load"]["status"] == "failed"
    assert captured.value.run.error_message == "Falha durante a etapa load."
    assert not Order.objects.filter(external_id="ERP-TEST-001").exists()
    monkeypatch.setattr(load_module.OrderItem.objects, "bulk_create", original)


def test_pipeline_api_without_execution():
    client = APIClient()
    response = client.get("/api/data/pipelines/")
    assert response.status_code == 200
    assert response.data == [{
        "pipeline_key": "orders",
        "name": "Pedidos",
        "description": "Exportação demonstrativa do ERP para a base operacional.",
        "latest_run": None,
        "last_published_at": None,
    }]
    detail = client.get("/api/data/pipelines/orders/")
    assert detail.status_code == 200
    assert detail.data["recent_runs"] == []


def test_pipeline_api_status_history_and_issue_detail(tmp_path, catalogs):
    first = run_orders_pipeline(source_file(tmp_path, [record()]))
    second = run_orders_pipeline(source_file(tmp_path, [record(), record(external_id="ERP-BAD", branch="X")]))
    client = APIClient()

    detail = client.get("/api/data/pipelines/orders/")
    assert detail.status_code == 200
    assert detail.data["latest_run"]["id"] == second.pk
    assert detail.data["latest_run"]["quality_percentage"] == 50.0
    assert [item["id"] for item in detail.data["recent_runs"]] == [second.pk, first.pk]
    assert detail.data["last_published_at"] is not None

    run_detail = client.get(f"/api/data/pipelines/orders/runs/{second.pk}/")
    assert run_detail.status_code == 200
    assert run_detail.data["issues"][0]["record_identifier"] == "ERP-BAD"
    assert client.get("/api/data/pipelines/unknown/").status_code == 404
    assert client.get("/api/data/pipelines/orders/runs/99999/").status_code == 404


def test_management_command_reports_summary_and_failure(tmp_path, catalogs, capsys):
    call_command("run_data_pipeline", "orders", source=source_file(tmp_path, [record()]))
    output = capsys.readouterr().out
    assert "Status: success" in output
    assert "Qualidade: 100.00%" in output
    with pytest.raises(CommandError):
        call_command("run_data_pipeline", "orders", source=tmp_path / "missing.json")


def test_versioned_demo_source_proves_all_expected_rejections():
    call_command("seed_demo", small=True, verbosity=0)
    source = settings.BASE_DIR / "data" / "source" / "orders.json"
    run = run_orders_pipeline(source)

    assert (run.records_received, run.records_valid, run.records_rejected, run.records_loaded) == (16, 12, 4, 12)
    assert run.quality_percentage == 75.0
    assert set(run.issues.values_list("code", flat=True)) == {
        "duplicate_external_id", "unknown_branch", "invalid_unit_price", "invalid_delivered_at",
    }


def test_failed_latest_run_preserves_last_real_publication(tmp_path, catalogs):
    successful = run_orders_pipeline(source_file(tmp_path, [record()]))
    with pytest.raises(PipelineExecutionError):
        run_orders_pipeline(tmp_path / "missing.json")

    response = APIClient().get("/api/data/pipelines/orders/")
    assert response.data["latest_run"]["status"] == "failed"
    assert parse_datetime(response.data["last_published_at"]) == successful.published_at
